"""AiClient Protocol — 隔离 mock / DashScope / 未来其它模型."""
from __future__ import annotations

from typing import Any, Literal, Protocol

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
