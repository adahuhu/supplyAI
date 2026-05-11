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
