"""采购草稿域 DTO."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field

DraftStatus = Literal["draft", "confirmed", "redirected"]


class DraftItemInput(BaseModel):
    """单条草稿录入项."""

    mall_id: int | None = None
    msku: str
    sku: str | None = None
    suggest_qty: int
    supplier_name: str | None = None


class DraftCreateRequest(BaseModel):
    tenant_id: int
    calc_run_id: str | None = None  # 可选,用于追踪来源
    created_by: str | None = None
    items: list[DraftItemInput]


class DraftCreateResponse(BaseModel):
    created_count: int
    draft_ids: list[str]


class DraftListRequest(BaseModel):
    tenant_id: int
    statuses: list[DraftStatus] | None = None
    calc_run_id: str | None = None
    page: int = 1
    page_size: int = 50


class DraftDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    draft_id: str
    calc_run_id: str | None
    tenant_id: int
    mall_id: int | None
    msku: str | None
    sku: str | None
    suggest_qty: int
    supplier_name: str | None
    status: DraftStatus
    created_by: str | None
    created_at: datetime


class DraftListResponse(BaseModel):
    rows: list[DraftDTO] = Field(default_factory=list)
    total: int
    page: int = 1
    page_size: int = 50


class DraftDetailRequest(BaseModel):
    tenant_id: int
    draft_id: str


class DraftStateRequest(BaseModel):
    """confirm / redirect 共用."""

    tenant_id: int
    draft_id: str
