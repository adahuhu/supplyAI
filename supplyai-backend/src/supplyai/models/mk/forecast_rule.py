"""mk_forecast_rule — 销量预测规则表（数据表设计 §4.5）."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    JSON,
    BigInteger,
    CheckConstraint,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkForecastRule(Base):
    """销量预测规则 — 三层作用范围 + 三种预测模式."""

    __tablename__ = "mk_forecast_rule"
    __table_args__ = (
        Index("ix_mk_forecast_rule_scope", "tenant_id", "scope_type", "mall_id", "msku"),
        CheckConstraint(
            "scope_type != 'sku' OR (mall_id IS NOT NULL AND msku IS NOT NULL AND msku != '')",
            name="ck_forecast_rule_sku_scope",
        ),
    )

    rule_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    scope_type: Mapped[str] = mapped_column(String(20))  # global / store / sku
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(64, collation="BINARY"))
    forecast_mode: Mapped[str] = mapped_column(String(20), default="default")  # fixed / dynamic / default
    fixed_daily_sales: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    default_daily_sales: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    weight_3d: Mapped[int] = mapped_column(Integer, default=0)
    weight_7d: Mapped[int] = mapped_column(Integer, default=0)
    weight_15d: Mapped[int] = mapped_column(Integer, default=0)
    weight_30d: Mapped[int] = mapped_column(Integer, default=0)
    denoise_enabled: Mapped[int] = mapped_column(Integer, default=0)
    abnormal_dates_json: Mapped[list | dict | None] = mapped_column(JSON)
    abnormal_sales_rule_json: Mapped[list | dict | None] = mapped_column(JSON)
    allow_empty_rule: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str | None] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_type: Mapped[str] = mapped_column(String(20), default="mock")

    def __repr__(self) -> str:
        return (
            f"<MkForecastRule id={self.rule_id} mode={self.forecast_mode} "
            f"scope={self.scope_type}>"
        )
