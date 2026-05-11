"""共享 DTO 类型 — 跨域通用."""
from __future__ import annotations

from datetime import datetime
from typing import Generic, Literal, TypeVar

from pydantic import BaseModel, ConfigDict, Field

T = TypeVar("T")


class PageResult(BaseModel, Generic[T]):
    """分页结果 — 列表类 API 通用响应."""

    rows: list[T]
    total: int
    page: int = 1
    page_size: int = 50


class CurrencyAmount(BaseModel):
    """单一币种金额."""

    currency: str
    amount: float


class SuggestTotalAmount(BaseModel):
    """采购金额合计 — 多币种支持."""

    base: CurrencyAmount
    by_currency: list[CurrencyAmount] = Field(default_factory=list)
    fx_rate_as_of: datetime | None = None


class DataQualityWarning(BaseModel):
    """数据质量警告."""

    code: str
    field: str | None = None
    message: str
    severity: Literal["info", "warn", "error"] = "warn"


class DataQuality(BaseModel):
    """数据质量元信息 — 附在 SkuDetail 等 ViewModel 上."""

    missing_fields: list[str] = Field(default_factory=list)
    warnings: list[DataQualityWarning] = Field(default_factory=list)


class ErrorResponse(BaseModel):
    """业务错误响应."""

    model_config = ConfigDict(json_schema_extra={"example": {"code": "FBM_NOT_SUPPORTED", "message": "Phase 1 暂不支持 FBM 备货分析"}})

    code: str
    message: str
