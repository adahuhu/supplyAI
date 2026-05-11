"""规则域 DTO."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

ScopeType = Literal["global", "store", "sku"]


class RuleListRequest(BaseModel):
    tenant_id: int
    scope_types: list[ScopeType] | None = None
    mall_id: int | None = None
    enabled_only: bool = False
    page: int = 1
    page_size: int = 50


class RuleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    tenant_id: int
    scope_type: ScopeType
    mall_id: int | None
    msku: str | None
    safety_days: int
    purchase_duration_days: int
    delivery_days: int
    qc_days: int
    rule_version: str | None
    enabled: bool
    updated_by: str | None
    updated_at: datetime


class RuleListResponse(BaseModel):
    rows: list[RuleDTO] = Field(default_factory=list)
    total: int
    page: int = 1
    page_size: int = 50


class RuleUpsertRequest(BaseModel):
    tenant_id: int
    rule_id: str | None = None  # 不传 = 新建
    scope_type: ScopeType
    mall_id: int | None = None
    msku: str | None = None
    safety_days: int = 14
    purchase_duration_days: int = 0
    delivery_days: int = 0
    qc_days: int = 0
    rule_version: str | None = None
    enabled: bool = True
    updated_by: str | None = None


class RuleStateRequest(BaseModel):
    tenant_id: int
    rule_id: str


# ── 销量预测规则 ─────────────────────────────────────


class ForecastRuleDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    rule_id: str
    tenant_id: int
    scope_type: ScopeType
    mall_id: int | None
    msku: str | None
    forecast_mode: Literal["fixed", "dynamic", "default"]
    fixed_daily_sales: float | None
    default_daily_sales: float | None
    weight_3d: int
    weight_7d: int
    weight_15d: int
    weight_30d: int
    denoise_enabled: bool
    abnormal_dates_json: list | dict | None
    enabled_label: str | None = None  # UI 展示


class ForecastRuleListRequest(BaseModel):
    tenant_id: int
    scope_types: list[ScopeType] | None = None
    page: int = 1
    page_size: int = 50


class ForecastRuleListResponse(BaseModel):
    rows: list[ForecastRuleDTO] = Field(default_factory=list)
    total: int
    page: int = 1
    page_size: int = 50


class ForecastRuleUpsertRequest(BaseModel):
    tenant_id: int
    rule_id: str | None = None
    scope_type: ScopeType
    mall_id: int | None = None
    msku: str | None = None
    forecast_mode: Literal["fixed", "dynamic", "default"] = "default"
    fixed_daily_sales: float | None = None
    default_daily_sales: float | None = None
    weight_3d: int = 0
    weight_7d: int = 0
    weight_15d: int = 0
    weight_30d: int = 0
    denoise_enabled: bool = False
    abnormal_dates_json: list | dict | None = None
    updated_by: str | None = None
