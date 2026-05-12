"""测试专用 AI 客户端 stub — 不在产线代码里出现.

仅供 tests/conftest.py 通过依赖注入挤掉 DashScopeClient,
让 /ai/* 端点测试不依赖外网 / API key。
"""
from __future__ import annotations

from typing import AsyncIterator

from supplyai.domain.ai.client import ChatMessage, ChatResponse, StreamDelta, ToolDef


class StubAiClient:
    """简化的 echo 风格客户端 — 专门给单元测试用.

    - 关键字命中时返回固定话术(便于断言)
    - 默认回 echo 兜底
    - 不会触发 tool_calls(orchestrator 测试用专门的 ScriptedClient)
    """

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> ChatResponse:
        last_user = next(
            (m.content for m in reversed(messages) if m.role == "user"),
            "",
        )
        if "风险" in last_user or "断货" in last_user:
            return ChatResponse(
                content="当前 P1 紧急 SKU 共 12 个,7 天内将断货 8 个。",
                finish_reason="stop",
            )
        if "采购" in last_user:
            return ChatResponse(
                content="建议优先处理 P1 风险 SKU。",
                finish_reason="stop",
            )
        return ChatResponse(
            content=f"[stub] 收到提问:{last_user[:60]}",
            finish_reason="stop",
        )

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> AsyncIterator[StreamDelta]:
        """流式 stub — 把 chat() 的同步回复切成 2 个 delta 模拟流式."""
        resp = await self.chat(messages, tools, max_tokens, temperature)
        full = resp.content or ""
        mid = max(1, len(full) // 2)
        yield StreamDelta(text=full[:mid])
        yield StreamDelta(text=full[mid:], finish_reason="stop")
