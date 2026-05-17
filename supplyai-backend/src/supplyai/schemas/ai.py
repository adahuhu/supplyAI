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


DecisionScenario = Literal[
    "risk_queue",
    "holiday_readiness",
    "plan_comparison",
    "rule_impact",
    "single_sku_replenishment",
]


class DecisionCardRequest(BaseModel):
    tenant_id: int
    scenario: DecisionScenario
    context: dict[str, Any] = Field(default_factory=dict)


class DecisionCardResponse(BaseModel):
    role: Literal["assistant"] = "assistant"
    content: str
    scenario: DecisionScenario
    card: dict[str, Any] = Field(default_factory=dict)
    calc_run_id: str | None = None
    source: Literal["backend"] = "backend"
    status: AiStatus = "ok"


class SmartDecisionRequest(BaseModel):
    """POST /ai/smart-decision/stream 请求体 — 与 ChatRequest 格式一致."""

    tenant_id: int
    messages: list[ChatRequestMessage] = Field(default_factory=list)
    context: dict[str, Any] = Field(default_factory=dict)

    def to_chat_request(self) -> ChatRequest:
        """退化到 chat 时,直接转换为 ChatRequest."""
        return ChatRequest(
            tenant_id=self.tenant_id,
            messages=self.messages,
            context=self.context,
        )
