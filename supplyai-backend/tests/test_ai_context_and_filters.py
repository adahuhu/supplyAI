"""AI 上下文注入 + 工具按店铺/国家过滤."""
from __future__ import annotations

import pytest
from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.db import async_session_factory
from supplyai.domain.ai.client import ChatMessage, ChatResponse, ToolCall
from supplyai.domain.ai.orchestrator import AiOrchestrator
from supplyai.domain.ai.tools import build_tools, execute_tool


# ─────────────────────────────────────────────
# 工具 schema 必须暴露过滤参数
# ─────────────────────────────────────────────


def test_query_stockout_risk_schema_supports_mall_ids() -> None:
    tools = {t.name: t for t in build_tools()}
    schema = tools["query_stockout_risk"].parameters
    props = schema["properties"]
    assert "mall_ids" in props, "工具未暴露 mall_ids 过滤"
    assert props["mall_ids"]["type"] == "array"
    assert "country_codes" in props
    assert "owners" in props


def test_query_replenishment_advice_schema_supports_store_filters() -> None:
    tools = {t.name: t for t in build_tools()}
    schema = tools["query_replenishment_advice"].parameters
    props = schema["properties"]
    assert "mall_ids" in props
    assert "country_codes" in props


# ─────────────────────────────────────────────
# 工具实际按 mall_ids 过滤
# ─────────────────────────────────────────────


async def test_execute_query_stockout_risk_filters_by_mall() -> None:
    async with async_session_factory() as session:
        all_resp = await execute_tool(
            "query_stockout_risk",
            {"tenant_id": 100228, "limit": 50},
            session,
        )
        single_resp = await execute_tool(
            "query_stockout_risk",
            {"tenant_id": 100228, "limit": 50, "mall_ids": [1001]},
            session,
        )
    all_count = len(all_resp["rows"])
    single_count = len(single_resp["rows"])
    # 单店铺应严格少于全部(seed 6 店铺)
    assert single_count < all_count
    # 所有返回行 mall_id 必须 == 1001
    for r in single_resp["rows"]:
        assert r["mall_id"] == 1001


async def test_execute_query_replenishment_advice_filters_by_country() -> None:
    async with async_session_factory() as session:
        out = await execute_tool(
            "query_replenishment_advice",
            {
                "tenant_id": 100228,
                "country_codes": ["JP"],
                "limit": 50,
                "suggest_only": False,
            },
            session,
        )
    assert out["total"] >= 1
    for r in out["rows"]:
        assert r["country_code"] == "JP"


# ─────────────────────────────────────────────
# Orchestrator 注入用户上下文到 system prompt
# ─────────────────────────────────────────────


async def test_orchestrator_injects_context_into_system_message() -> None:
    """带 context 的 chat 必须把 SKU/筛选信息塞进 system prompt 让模型看到."""
    captured_messages: list[list[ChatMessage]] = []

    class _Capture:
        async def chat(self, messages, tools=None, max_tokens=1024, temperature=0.2):
            captured_messages.append(list(messages))
            return ChatResponse(content="ok", finish_reason="stop")

    async with async_session_factory() as session:
        orch = AiOrchestrator(
            _Capture(),
            session=session,
            tenant_id=100228,
            context={
                "current_page": "sku",
                "sku": {"msku": "MS40060", "mall_id": 1004, "store_name": "Sakura-JP01"},
            },
        )
        await orch.run([ChatMessage(role="user", content="这个 SKU 怎么样?")])

    # 第一轮调 LLM 时,messages 必须含 context 的 system 消息
    msgs = captured_messages[0]
    system_text = " ".join(m.content for m in msgs if m.role == "system")
    assert "MS40060" in system_text
    assert "Sakura-JP01" in system_text or "1004" in system_text


async def test_orchestrator_context_can_drive_filtered_tool_call() -> None:
    """模型基于上下文应能正确传 mall_ids — 通过 ScriptedClient 验证 tool args 正确执行."""
    captured_calls: list[tuple[str, dict]] = []
    import supplyai.domain.ai.orchestrator as orch_mod

    real_exec = orch_mod.execute_tool

    async def _capture(name, args, session):
        captured_calls.append((name, dict(args)))
        return await real_exec(name, args, session)

    orch_mod.execute_tool = _capture
    try:
        class _Scripted:
            calls = 0

            async def chat(self, messages, tools=None, max_tokens=1024, temperature=0.2):
                self.calls += 1
                if self.calls == 1:
                    # 模拟模型从上下文识别到 mall_id=1004,调工具时带上
                    return ChatResponse(
                        content="",
                        finish_reason="tool_calls",
                        tool_calls=[
                            ToolCall(
                                id="c1",
                                name="query_stockout_risk",
                                arguments={"limit": 5, "mall_ids": [1004]},
                            )
                        ],
                    )
                return ChatResponse(content="该店铺紧急 SKU 已查到", finish_reason="stop")

        async with async_session_factory() as session:
            orch = AiOrchestrator(
                _Scripted(),
                session=session,
                tenant_id=100228,
                context={"sku": {"mall_id": 1004}},
            )
            out = await orch.run([ChatMessage(role="user", content="x")])

        assert out.tool_iterations == 1
        # 工具被调时确实接收到 mall_ids
        name, args = captured_calls[0]
        assert args["mall_ids"] == [1004]
        assert args["tenant_id"] == 100228  # 仍强制 tenant 边界
    finally:
        orch_mod.execute_tool = real_exec


# ─────────────────────────────────────────────
# /ai/chat 端点接受 context 参数
# ─────────────────────────────────────────────


async def test_chat_endpoint_accepts_context(client) -> None:
    """API 层 ChatRequest 必须接受 context 字段,不报 422."""
    from httpx import AsyncClient

    resp = await client.post(
        "/api/supplyai/ai/chat",
        json={
            "tenant_id": 100228,
            "messages": [{"role": "user", "content": "这个 SKU 怎么样"}],
            "context": {
                "current_page": "sku",
                "sku": {"msku": "MS40060", "mall_id": 1004},
            },
        },
    )
    assert resp.status_code == 200, resp.text
