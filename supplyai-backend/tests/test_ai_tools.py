"""AI Tools + 调度循环测试.

Tools(技术方案 §7.5):
  - query_stockout_risk        — 查全局风险队列
  - query_replenishment_advice — 查 SKU 备货建议
  - query_sku_detail           — 查 SKU 详情快照
  - generate_purchase_draft    — 生成采购草稿(必须二次确认)

调度循环:
  - 模型返回 finish_reason='tool_calls' → 执行工具 → 把结果作为 'tool' role 回传
  - 循环至 finish_reason='stop' 或达到 max_iterations
"""
from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import async_session_factory
from supplyai.domain.ai.client import (
    ChatMessage,
    ChatResponse,
    ToolCall,
    ToolDef,
)
from supplyai.domain.ai.orchestrator import AiOrchestrator
from supplyai.domain.ai.tools import build_tools, execute_tool


# ============ Tool 注册 ============


def test_build_tools_returns_full_set() -> None:
    tools = build_tools()
    names = sorted(t.name for t in tools)
    assert names == sorted([
        "query_stockout_risk",
        "query_replenishment_advice",
        "query_sku_detail",
        "generate_purchase_draft",
        "compare_logistics_options",
        "simulate_event_demand",
    ])
    for t in tools:
        assert isinstance(t, ToolDef)
        assert t.parameters.get("type") == "object"


# ============ 工具实际执行 — 真实 DB ============


async def test_execute_query_stockout_risk_uses_real_data() -> None:
    async with async_session_factory() as session:
        out = await execute_tool(
            "query_stockout_risk",
            {"tenant_id": 100228, "limit": 3},
            session,
        )
    assert "rows" in out
    assert len(out["rows"]) <= 3
    if out["rows"]:
        assert "priority" in out["rows"][0]
        assert "action_hint" in out["rows"][0]


async def test_execute_query_sku_detail_returns_summary() -> None:
    """先用 list 拿一个真实 listing_id,再 query_sku_detail."""
    from supplyai.repositories.dashboard_repo import DashboardRepository
    from supplyai.repositories.sku_repo import SkuRepository

    async with async_session_factory() as session:
        run_id = await DashboardRepository(session).latest_calc_run_id(100228)
        rows, _ = await SkuRepository(session).list_skus(
            calc_run_id=run_id, tenant_id=100228, page=1, page_size=1
        )
        listing_id = rows[0][0].listing_id
        out = await execute_tool(
            "query_sku_detail",
            {"tenant_id": 100228, "listing_id": listing_id},
            session,
        )
    assert "summary" in out
    assert out["summary"]["msku"]
    assert "forecast_trend" in out  # 含预测序列


async def test_execute_generate_purchase_draft_requires_confirmed_flag() -> None:
    """未传 confirmed=True 时,工具必须返回预览 + 提示二次确认,不能直接落库."""
    async with async_session_factory() as session:
        out = await execute_tool(
            "generate_purchase_draft",
            {
                "tenant_id": 100228,
                "items": [{"msku": "MS40060", "mall_id": 1004, "suggest_qty": 100}],
                "confirmed": False,
            },
            session,
        )
    assert out["status"] == "needs_confirmation"
    assert "draft_ids" not in out  # 没有真正创建
    assert out["preview"]["item_count"] == 1


async def test_execute_generate_purchase_draft_confirmed_creates_drafts() -> None:
    """confirmed=True 时落库."""
    async with async_session_factory() as session:
        out = await execute_tool(
            "generate_purchase_draft",
            {
                "tenant_id": 100228,
                "items": [{"msku": "MS40060", "mall_id": 1004, "suggest_qty": 50}],
                "confirmed": True,
            },
            session,
        )
        await session.commit()
    assert out["status"] == "created"
    assert len(out["draft_ids"]) == 1


async def test_execute_unknown_tool_returns_error() -> None:
    async with async_session_factory() as session:
        out = await execute_tool("nonexistent_tool", {}, session)
    assert out.get("error")


# ============ Orchestrator 调度循环 ============


@dataclass
class _ScriptedClient:
    """按预设序列回放 LLM 响应的伪客户端."""
    responses: list[ChatResponse]
    calls: list[dict[str, Any]] = field(default_factory=list)

    async def chat(self, messages, tools=None, max_tokens=1024, temperature=0.2):
        self.calls.append({
            "n_messages": len(messages),
            "tools": [t.name for t in tools] if tools else [],
        })
        return self.responses.pop(0)


async def test_orchestrator_no_tool_call_passes_through() -> None:
    """模型直接回 stop 时,orchestrator 一轮就返回."""
    client = _ScriptedClient(responses=[
        ChatResponse(content="P1 共 12 个", finish_reason="stop"),
    ])
    async with async_session_factory() as session:
        orch = AiOrchestrator(client, session=session, tenant_id=100228)
        out = await orch.run([ChatMessage(role="user", content="风险如何")])
    assert out.content == "P1 共 12 个"
    assert out.tool_iterations == 0


async def test_orchestrator_executes_tool_call_and_loops() -> None:
    """模型 → tool_call → 执行 → 模型 → stop."""
    client = _ScriptedClient(responses=[
        # 第 1 轮:模型决定调工具
        ChatResponse(
            content="",
            finish_reason="tool_calls",
            tool_calls=[ToolCall(
                id="call_1",
                name="query_stockout_risk",
                arguments={"tenant_id": 100228, "limit": 3},
            )],
        ),
        # 第 2 轮:模型基于工具结果给最终答案
        ChatResponse(content="共 3 个 P1 SKU", finish_reason="stop"),
    ])
    async with async_session_factory() as session:
        orch = AiOrchestrator(client, session=session, tenant_id=100228)
        out = await orch.run([ChatMessage(role="user", content="哪些紧急")])

    assert out.content == "共 3 个 P1 SKU"
    assert out.tool_iterations == 1
    # 第 2 次调 LLM 时,messages 里应已含 tool 结果
    assert client.calls[1]["n_messages"] > client.calls[0]["n_messages"]


async def test_orchestrator_max_iterations_caps() -> None:
    """模型疯狂调工具时,达到上限后应基于工具 JSON 生成确定性摘要."""
    # 永远回 tool_calls 的死循环模型
    looping_resp = ChatResponse(
        content="",
        finish_reason="tool_calls",
        tool_calls=[ToolCall(id="x", name="query_stockout_risk", arguments={"tenant_id": 100228})],
    )
    client = _ScriptedClient(responses=[looping_resp, looping_resp, looping_resp])
    async with async_session_factory() as session:
        orch = AiOrchestrator(client, session=session, tenant_id=100228, max_iterations=3)
        out = await orch.run([ChatMessage(role="user", content="x")])
    assert out.tool_iterations == 3
    assert out.finish_reason == "stop"
    assert "工具调用上限" not in out.content
    assert "简化提问" not in out.content
    assert "确定数据" in out.content
    assert "查询到" in out.content
    assert len(client.calls) == 3


async def test_orchestrator_overrides_model_provided_tenant_id() -> None:
    """安全边界:模型即使主动传 tenant_id=1,Orchestrator 必须强制覆盖为请求 tenant.
    避免越权查别的租户数据。
    """
    captured_args: dict = {}

    class _CapturingClient:
        async def chat(self, messages, tools=None, max_tokens=1024, temperature=0.2):
            return ChatResponse(
                content="",
                finish_reason="tool_calls",
                tool_calls=[ToolCall(
                    id="x",
                    name="query_stockout_risk",
                    arguments={"tenant_id": 1, "limit": 3},  # 模型传了错的 tenant
                )],
            )

    # patch execute_tool 来捕获实际传入的 args
    import supplyai.domain.ai.orchestrator as orch_mod

    original = orch_mod.execute_tool

    async def _capture(name, args, session):
        captured_args.update(args)
        return {"rows": [], "total": 0}

    orch_mod.execute_tool = _capture
    try:
        # 模型还会再被调一次(stop),给个简单 stop 响应
        class _Two:
            calls = 0
            async def chat(self, messages, tools=None, max_tokens=1024, temperature=0.2):
                self.calls += 1
                if self.calls == 1:
                    return ChatResponse(
                        content="", finish_reason="tool_calls",
                        tool_calls=[ToolCall(id="x", name="query_stockout_risk",
                                              arguments={"tenant_id": 1, "limit": 3})],
                    )
                return ChatResponse(content="ok", finish_reason="stop")

        async with async_session_factory() as session:
            orch = AiOrchestrator(_Two(), session=session, tenant_id=100228)
            await orch.run([ChatMessage(role="user", content="x")])
    finally:
        orch_mod.execute_tool = original

    assert captured_args["tenant_id"] == 100228, "模型传的 tenant 必须被覆盖"


async def test_orchestrator_tool_error_recovers() -> None:
    """工具执行抛错时,把错误作为 tool 结果回传,允许模型继续."""
    client = _ScriptedClient(responses=[
        ChatResponse(
            content="",
            finish_reason="tool_calls",
            tool_calls=[ToolCall(
                id="call_e",
                name="nonexistent_tool",
                arguments={},
            )],
        ),
        ChatResponse(content="工具不可用,请用其他方式查询。", finish_reason="stop"),
    ])
    async with async_session_factory() as session:
        orch = AiOrchestrator(client, session=session, tenant_id=100228)
        out = await orch.run([ChatMessage(role="user", content="查一下")])
    assert "工具不可用" in out.content
    assert out.tool_iterations == 1
