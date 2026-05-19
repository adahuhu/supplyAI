"""导出域 DTO."""
from __future__ import annotations

from datetime import datetime
from typing import Literal

from pydantic import BaseModel, ConfigDict

ExportStatus = Literal["pending", "running", "success", "failed", "expired"]
Priority = Literal["p1", "p2", "p3", "safe"]


class ExportSkuListRequest(BaseModel):
    """SKU 列表导出请求 — 复用列表筛选器."""

    tenant_id: int
    calc_run_id: str | None = None
    priorities: list[Priority] | None = None
    mall_ids: list[int] | None = None
    country_codes: list[str] | None = None
    tags: list[str] | None = None
    keyword: str | None = None
    suggest_only: bool = False
    created_by: str | None = None


class ExportTaskDTO(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    task_id: str
    tenant_id: int
    status: ExportStatus
    row_count: int | None = None
    file_url: str | None = None  # 同步完成后填,Phase 1 是本地路径
    error_message: str | None = None
    created_at: datetime
    updated_at: datetime


class ExportTaskRequest(BaseModel):
    tenant_id: int
    task_id: str
