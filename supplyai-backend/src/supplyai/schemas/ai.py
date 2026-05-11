"""AI 域 DTO."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field

AiStatus = Literal["ok", "partial", "degraded"]


class ExplainRequest(BaseModel):
    tenant_id: int
    listing_id: int
    calc_run_id: str | None = None


class ExplainResponse(BaseModel):
    """SKU 风险解释 — 含 LLM 文本 + 上下文."""

    explanation: str
    context: dict[str, Any] = Field(default_factory=dict)
    model: str = "mock"
    status: AiStatus = "ok"


class ChatRequestMessage(BaseModel):
    role: Literal["user", "assistant", "system"]
    content: str


class ChatRequest(BaseModel):
    tenant_id: int
    messages: list[ChatRequestMessage] = Field(default_factory=list)
    # 用户当前视角:current_page / sku / filters,会注入到 system message 供模型调工具用
    context: dict[str, Any] = Field(default_factory=dict)


class ChatResponseMessage(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str
    model: str = "mock"
    finish_reason: str = "stop"
    status: AiStatus = "ok"
