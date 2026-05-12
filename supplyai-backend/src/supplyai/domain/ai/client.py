"""AiClient Protocol — 隔离 mock / DashScope / 未来其它模型."""
from __future__ import annotations

from typing import Any, AsyncIterator, Literal, Protocol

from pydantic import BaseModel, Field


class ChatMessage(BaseModel):
    role: Literal["system", "user", "assistant", "tool"]
    content: str
    tool_call_id: str | None = None


class ToolDef(BaseModel):
    """4 个 Tool 之一的定义(name / description / parameters JSON Schema)."""

    name: str
    description: str
    parameters: dict[str, Any]


class ToolCall(BaseModel):
    id: str
    name: str
    arguments: dict[str, Any]


class ChatResponse(BaseModel):
    """模型响应."""

    content: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    finish_reason: Literal["stop", "tool_calls", "length", "content_filter"] = "stop"


class StreamDelta(BaseModel):
    """流式响应增量片段.

    一次 chat_stream 调用会 yield 多个 StreamDelta,直到 finish_reason 出现表示结束。
    - reasoning 段: reasoning_text=<thinking token>, text="", finish_reason=None
    - content   段: text=<答复 token>,               reasoning_text="", finish_reason=None
    - 工具调用段:   tool_calls=[...], finish_reason='tool_calls'(终止)
    - 文本完成段:   text='',          finish_reason='stop'(终止)
    """

    text: str = ""
    reasoning_text: str = ""
    tool_calls: list[ToolCall] = Field(default_factory=list)
    finish_reason: str | None = None


class AiClient(Protocol):
    """LLM 客户端抽象接口.

    生产实现:`DashScopeClient`(Qwen3.6-plus, OpenAI 兼容).
    业务代码 / Orchestrator 只依赖此接口;切换模型不动业务。
    """

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> ChatResponse: ...

    def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> AsyncIterator[StreamDelta]: ...
