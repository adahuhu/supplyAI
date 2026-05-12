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
        return OrchestratorOutput(
            content=last_content or "[已达工具调用上限,请简化提问]",
            tool_iterations=iterations,
            finish_reason="length",
        )

    async def run_stream(
        self, user_messages: list[ChatMessage]
    ) -> AsyncIterator[StreamEvent]:
        """流式调度.

        策略:每轮先用非流式 chat() 判断要不要 tool;一旦 finish_reason='stop' 的轮次,
        改用 chat_stream() 重发同样的消息,把 LLM 的文本回复以 delta 流式吐给客户端。
        这样 tool 阶段保持简单,只在"最后一段产文" 段做真流式 — 收益最大,实现最小。

        事件序列示例:
            tool_start → tool_end → tool_start → tool_end → delta..delta → done
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
            resp = await self._ai.chat(messages=msgs, tools=self._tools)

            if resp.finish_reason != "tool_calls" or not resp.tool_calls:
                # 最终回复 — 切到流式重发,真增量吐给客户端
                async for delta in self._ai.chat_stream(messages=msgs, tools=self._tools):
                    if delta.text and not delta.finish_reason:
                        yield {"type": "delta", "text": delta.text}
                    if delta.finish_reason:
                        # 兜底:流式实现不可用时,resp.content 至少能保证有内容
                        yield {
                            "type": "done",
                            "finish_reason": delta.finish_reason or "stop",
                            "tool_iterations": iterations,
                        }
                        return
                # 没拿到任何 delta(client.chat_stream 没实现?)— 用 resp.content 兜底
                if resp.content:
                    yield {"type": "delta", "text": resp.content}
                yield {
                    "type": "done",
                    "finish_reason": resp.finish_reason or "stop",
                    "tool_iterations": iterations,
                }
                return

            # 模型决定调工具 — 仍按 sync 路径
            msgs.append(ChatMessage(role="assistant", content=resp.content or ""))
            for tc in resp.tool_calls:
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
        yield {
            "type": "delta",
            "text": "[已达工具调用上限,请简化提问]",
        }
        yield {
            "type": "done",
            "finish_reason": "length",
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
