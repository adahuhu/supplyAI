"""AI Orchestrator — 工具调度循环.

流程:
  1. 把 user message + system prompt + tools 喂给 LLM
  2. 模型 finish_reason='stop' → 直接返回
  3. 模型 finish_reason='tool_calls' → 执行所有 tool_calls,把结果作为 'tool' 角色回传
  4. 循环步 1-3,直到 stop 或达到 max_iterations 上限
"""
from __future__ import annotations

import json
import logging
from dataclasses import dataclass
from typing import Any, AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession

from supplyai.domain.ai.client import AiClient, ChatMessage
from supplyai.domain.ai.foundation import SYSTEM_PROMPT
from supplyai.domain.ai.tools import build_tools, execute_tool

logger = logging.getLogger(__name__)


@dataclass
class OrchestratorOutput:
    content: str
    tool_iterations: int
    finish_reason: str


# 流式事件类型
# - tool_start: {"type":"tool_start","name":"...","arguments":{...}}
# - tool_end:   {"type":"tool_end","name":"...","ok":bool,"summary":"..."}
# - delta:      {"type":"delta","text":"..."}
# - done:       {"type":"done","finish_reason":"stop","tool_iterations":N}
# - error:      {"type":"error","message":"..."}
StreamEvent = dict[str, Any]


class AiOrchestrator:
    """组合 LLM + Tools + 调度循环."""

    def __init__(
        self,
        ai_client: AiClient,
        *,
        session: AsyncSession,
        tenant_id: int,
        max_iterations: int = 5,
        system_prompt: str = SYSTEM_PROMPT,
        context: dict | None = None,
    ) -> None:
        self._ai = ai_client
        self._session = session
        self._tenant_id = tenant_id
        self._max_iter = max_iterations
        self._system_prompt = system_prompt
        self._context = context or {}
        self._tools = build_tools()

    def _build_context_message(self) -> str | None:
        """把用户调用上下文渲染成 system message 让模型知道当前视角."""
        ctx = self._context
        if not ctx:
            return None
        parts: list[str] = ["【当前用户上下文】"]
        page = ctx.get("current_page")
        if page:
            parts.append(f"当前页面: {page}")
        sku = ctx.get("sku") or {}
        if sku:
            sku_summary = []
            if sku.get("msku"):
                sku_summary.append(f"MSKU={sku['msku']}")
            if sku.get("store_name"):
                sku_summary.append(f"店铺={sku['store_name']}")
            if sku.get("mall_id"):
                sku_summary.append(f"mall_id={sku['mall_id']}")
            if sku.get("country_code"):
                sku_summary.append(f"国家={sku['country_code']}")
            if sku.get("priority"):
                sku_summary.append(f"风险={sku['priority']}")
            if sku.get("listing_id"):
                sku_summary.append(f"listing_id={sku['listing_id']}")
            if sku_summary:
                parts.append("用户当前查看 SKU: " + ", ".join(sku_summary))
        filters = ctx.get("filters") or {}
        if filters:
            ff = []
            if filters.get("mall_id"):
                ff.append(f"mall_id={filters['mall_id']}")
            if filters.get("country_code"):
                ff.append(f"country={filters['country_code']}")
            if filters.get("owner"):
                ff.append(f"owner={filters['owner']}")
            if ff:
                parts.append("用户在 Dashboard 已选过滤: " + ", ".join(ff))
        parts.append(
            "查询工具时,请基于上述上下文自动设置 mall_ids/country_codes/owners 参数;"
            "用户问'这个 SKU/这个店铺'就用上述值,不要反问。"
        )
        return "\n".join(parts)

    @staticmethod
    def _cap_fallback_text() -> str:
        return (
            "我已经读取了可用数据，但本轮工具调用达到保护上限。"
            "请先基于上方已展示的风险卡片和工具结果处理最高优先级项；"
            "如需继续追问，可以直接问某一个 SKU、某个店铺或某个动作。"
        )

    def _summarize_after_cap(self, msgs: list[ChatMessage]) -> str:
        """达到工具上限后,只用已返回的 tool JSON 生成确定性摘要.

        不再调用 LLM,避免模型在"总结已有结果"时扩写或编造数字。
        """
        summaries: list[str] = []
        for msg in msgs:
            if msg.role != "tool" or not msg.content:
                continue
            try:
                payload = json.loads(msg.content)
            except json.JSONDecodeError:
                continue
            summary = _deterministic_tool_summary(payload)
            if summary:
                summaries.append(summary)
        if not summaries:
            return self._cap_fallback_text()
        # 保留最后几次工具结果,避免长对话里重复堆叠旧数据。
        return (
            "本轮已达到工具调用保护上限，我先基于已经查到的确定数据给出结论：\n"
            + "\n".join(f"{i + 1}. {text}" for i, text in enumerate(summaries[-3:]))
            + "\n如需继续深入，请直接指定某个 SKU、店铺或动作，我会基于该对象继续查询。"
        )

    async def run(self, user_messages: list[ChatMessage]) -> OrchestratorOutput:
        msgs: list[ChatMessage] = [
            ChatMessage(role="system", content=self._system_prompt),
        ]
        ctx_msg = self._build_context_message()
        if ctx_msg:
            msgs.append(ChatMessage(role="system", content=ctx_msg))
        msgs.extend(user_messages)
        iterations = 0
        last_finish = "stop"
        last_content = ""

        for _ in range(self._max_iter):
            resp = await self._ai.chat(messages=msgs, tools=self._tools)
            last_finish = resp.finish_reason
            last_content = resp.content

            if resp.finish_reason != "tool_calls" or not resp.tool_calls:
                return OrchestratorOutput(
                    content=resp.content,
                    tool_iterations=iterations,
                    finish_reason=resp.finish_reason,
                )

            # 模型决定调工具:把"assistant + tool_calls 的占位消息"和"工具结果"都加到历史
            msgs.append(ChatMessage(
                role="assistant",
                content=resp.content or "",
            ))
            for tc in resp.tool_calls:
                # tenant_id 强制覆盖 — 权限边界,不允许模型决定查哪个租户
                args = dict(tc.arguments or {})
                args["tenant_id"] = self._tenant_id
                result = await execute_tool(tc.name, args, self._session)
                msgs.append(ChatMessage(
                    role="tool",
                    content=json.dumps(result, ensure_ascii=False),
                    tool_call_id=tc.id,
                ))
            iterations += 1

        # 命中 max_iterations 上限
        logger.warning("ai_orchestrator_capped iterations=%d", iterations)
        content = self._summarize_after_cap(msgs)
        return OrchestratorOutput(
            content=content or last_content or self._cap_fallback_text(),
            tool_iterations=iterations,
            finish_reason="stop",
        )

    async def run_stream(
        self, user_messages: list[ChatMessage]
    ) -> AsyncIterator[StreamEvent]:
        """流式调度 — 每轮单次 chat_stream(stream=True, tools=...).

        实时累积 text + tool_calls;`finish_reason` 出现后决定分支:
          - finish_reason='tool_calls':执行工具,把结果回灌,进下一轮
          - 其它(stop/length/...):整段对话结束

        相比早期"先非流式探路再重发流式"的版本,这版只调一次 DashScope —
        token 消耗减半,首字延迟减少 ~50%。

        事件序列示例:
            delta..delta → (finish 'tool_calls') tool_start → tool_end →
            delta..delta → done
        """
        msgs: list[ChatMessage] = [
            ChatMessage(role="system", content=self._system_prompt),
        ]
        ctx_msg = self._build_context_message()
        if ctx_msg:
            msgs.append(ChatMessage(role="system", content=ctx_msg))
        msgs.extend(user_messages)
        iterations = 0

        for _ in range(self._max_iter):
            accumulated_text = ""
            tool_calls: list = []
            finish_reason = "stop"

            async for delta in self._ai.chat_stream(messages=msgs, tools=self._tools):
                # reasoning(思维链)增量 — 不入 assistant 历史,只透给客户端展示
                if delta.reasoning_text and not delta.finish_reason:
                    yield {"type": "reasoning_delta", "text": delta.reasoning_text}
                # 文本增量 — 实时透给客户端,同时累积进 assistant 上下文
                if delta.text:
                    accumulated_text += delta.text
                    if not delta.finish_reason:
                        yield {"type": "delta", "text": delta.text}
                if delta.finish_reason:
                    finish_reason = delta.finish_reason
                    if delta.tool_calls:
                        tool_calls = list(delta.tool_calls)
                    if delta.text and finish_reason != "tool_calls":
                        yield {"type": "delta", "text": delta.text}
                    if delta.reasoning_text:
                        yield {"type": "reasoning_delta", "text": delta.reasoning_text}
                    break

            if finish_reason != "tool_calls" or not tool_calls:
                yield {
                    "type": "done",
                    "finish_reason": finish_reason,
                    "tool_iterations": iterations,
                }
                return

            # 走工具分支 — 把累积的 assistant 内容入历史,逐个工具执行
            msgs.append(ChatMessage(role="assistant", content=accumulated_text or ""))
            for tc in tool_calls:
                args = dict(tc.arguments or {})
                args["tenant_id"] = self._tenant_id
                yield {
                    "type": "tool_start",
                    "name": tc.name,
                    "arguments": {k: v for k, v in args.items() if k != "tenant_id"},
                }
                ok = True
                summary = ""
                try:
                    result = await execute_tool(tc.name, args, self._session)
                    summary = _short_tool_summary(tc.name, result)
                    msgs.append(ChatMessage(
                        role="tool",
                        content=json.dumps(result, ensure_ascii=False),
                        tool_call_id=tc.id,
                    ))
                except Exception as e:  # noqa: BLE001
                    ok = False
                    summary = f"{e.__class__.__name__}: {e}"
                    msgs.append(ChatMessage(
                        role="tool",
                        content=json.dumps({"error": summary}, ensure_ascii=False),
                        tool_call_id=tc.id,
                    ))
                yield {"type": "tool_end", "name": tc.name, "ok": ok, "summary": summary}
            iterations += 1

        logger.warning("ai_orchestrator_stream_capped iterations=%d", iterations)
        content = self._summarize_after_cap(msgs)
        yield {
            "type": "delta",
            "text": content,
        }
        yield {
            "type": "done",
            "finish_reason": "stop",
            "tool_iterations": iterations,
        }


def _short_tool_summary(name: str, result: Any) -> str:
    """把 tool 返回的 dict / list 压缩成一行人类可读摘要,用于流式 UI 展示."""
    if isinstance(result, dict):
        if "rows" in result and isinstance(result["rows"], list):
            return f"返回 {len(result['rows'])} 条"
        if "error" in result:
            return f"失败:{result['error']}"
        return f"返回 {len(result)} 字段"
    if isinstance(result, list):
        return f"返回 {len(result)} 条"
    return "完成"


def _deterministic_tool_summary(payload: Any) -> str:
    """从工具 JSON 中抽取确定字段生成保守摘要."""
    if not isinstance(payload, dict):
        return ""
    if payload.get("error"):
        return f"有一次工具查询失败:{payload['error']}"

    rows = payload.get("rows")
    if isinstance(rows, list):
        total = payload.get("total", len(rows))
        if not rows:
            return f"查询返回 0 条记录,总数 {total}。"
        bits = [f"查询到 {len(rows)} 条记录,总数 {total}"]
        top = rows[:3]
        item_texts = []
        for row in top:
            if not isinstance(row, dict):
                continue
            sku = row.get("sku") or row.get("msku") or row.get("title") or row.get("name")
            risk = row.get("priority") or row.get("risk_level")
            fba_days = (
                row.get("fba_sellable_days")
                or row.get("fba_sellable")
                or row.get("sellable_days")
            )
            suggest_qty = row.get("suggest_qty") or row.get("suggested_qty")
            parts = [str(sku)] if sku else []
            if risk:
                parts.append(f"风险 {risk}")
            if fba_days is not None:
                parts.append(f"FBA 可售 {fba_days} 天")
            if suggest_qty is not None:
                parts.append(f"建议采购 {suggest_qty}")
            if parts:
                item_texts.append("、".join(parts))
        if item_texts:
            bits.append("Top 项: " + "; ".join(item_texts))
        calc_run_id = payload.get("calc_run_id")
        if calc_run_id:
            bits.append(f"计算批次 {calc_run_id}")
        return "；".join(bits) + "。"

    summary = payload.get("summary")
    if isinstance(summary, dict):
        msku = summary.get("msku") or summary.get("sku")
        risk = summary.get("priority") or summary.get("risk_level")
        fba_days = summary.get("fba_sellable_days") or summary.get("fba_sellable")
        suggest_qty = summary.get("suggest_qty") or summary.get("suggested_qty")
        parts = []
        if msku:
            parts.append(f"SKU {msku}")
        if risk:
            parts.append(f"风险 {risk}")
        if fba_days is not None:
            parts.append(f"FBA 可售 {fba_days} 天")
        if suggest_qty is not None:
            parts.append(f"建议采购 {suggest_qty}")
        if parts:
            return "；".join(parts) + "。"

    plans = payload.get("plans")
    if isinstance(plans, list) and plans:
        plan_texts = []
        for plan in plans[:3]:
            if not isinstance(plan, dict):
                continue
            mode = plan.get("mode")
            days = plan.get("days")
            cost = plan.get("estimated_cost")
            parts = [str(mode)] if mode else []
            if days is not None:
                parts.append(f"{days} 天")
            if cost is not None:
                parts.append(f"预估成本 {cost}")
            if parts:
                plan_texts.append("、".join(parts))
        if plan_texts:
            return "物流方案对比: " + "; ".join(plan_texts) + "。"

    status = payload.get("status")
    if status == "needs_confirmation":
        preview = payload.get("preview") or {}
        return (
            f"采购计划仍需二次确认:共 {preview.get('item_count', 0)} 项,"
            f"总数量 {preview.get('total_qty', 0)}。"
        )
    if status == "created":
        return f"采购计划已创建 {payload.get('created_count', 0)} 条。"

    note = payload.get("note")
    if isinstance(note, str) and note:
        return note

    return ""
