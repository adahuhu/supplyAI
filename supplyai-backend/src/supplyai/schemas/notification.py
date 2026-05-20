"""日报推送 DTO."""
from __future__ import annotations

from typing import Any, Literal

from pydantic import BaseModel, Field


NotificationRole = Literal["boss", "operator"]
NotificationChannel = Literal["dingtalk"]


class NotificationPreviewRequest(BaseModel):
    """生成日报推送预览."""

    tenant_id: int
    role: NotificationRole = "boss"
    target_name: str | None = None
    owners: list[str] | None = None
    mall_ids: list[int] | None = None
    country_codes: list[str] | None = None
    detail_url: str | None = None
    channel: NotificationChannel = "dingtalk"


class NotificationSendRequest(NotificationPreviewRequest):
    """发送日报推送."""

    webhook_url: str | None = None


class NotificationMetric(BaseModel):
    label: str
    value: float
    unit: str | None = None


class NotificationSkuRow(BaseModel):
    listing_id: int | None
    msku: str
    product_name: str | None = None
    store_name: str | None = None
    country_code: str | None = None
    sales_7d: int
    revenue_7d: float
    priority: str | None = None
    sellable_days: float | None = None
    stockout_date: str | None = None
    suggest_qty: int | None = None
    reason: str | None = None


class NotificationRiskSummary(BaseModel):
    risk_sku_count: int
    p1_count: int
    p2_count: int
    stockout_7_count: int
    suggest_sku_count: int
    suggest_total_qty: int
    suggest_total_amount: float
    currency: str = "USD"


class NotificationReport(BaseModel):
    role: NotificationRole
    role_label: str
    target_name: str
    scope_label: str
    as_of_date: str
    finance: list[NotificationMetric] = Field(default_factory=list)
    top_skus: list[NotificationSkuRow] = Field(default_factory=list)
    focus_skus: list[NotificationSkuRow] = Field(default_factory=list)
    risk: NotificationRiskSummary
    summary: str
    action_text: str


class NotificationPreviewDTO(BaseModel):
    role: NotificationRole
    role_label: str
    title: str
    subtitle: str
    detail_url: str
    markdown: str
    dingtalk_payload: dict[str, Any]
    report: NotificationReport


class NotificationSendDTO(NotificationPreviewDTO):
    status: Literal["sent", "simulated", "failed"]
    message: str
    provider_response: dict[str, Any] | None = None
