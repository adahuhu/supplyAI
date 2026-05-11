"""mk_sku_forecast_daily — 未来逐日预测销量表（数据表设计 §4.8）.

一致性约束:
  forecast_daily(快照表) ≈ AVG(forecast_qty in window),误差 ≤ 0.01
  快照与逐日预测必须同 calc_run_id,同事务写入。
"""
from __future__ import annotations

from datetime import date
from decimal import Decimal

from sqlalchemy import BigInteger, Date, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class MkSkuForecastDaily(Base):
    """每个 MSKU 未来逐日预测."""

    __tablename__ = "mk_sku_forecast_daily"
    __table_args__ = (
        Index(
            "uq_mk_sku_forecast_daily_run_tmm_date",
            "calc_run_id", "tenant_id", "mall_id", "msku", "forecast_date",
            unique=True,
        ),
        Index("ix_mk_sku_forecast_daily_calc_run", "calc_run_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    calc_run_id: Mapped[str] = mapped_column(String(64))
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str] = mapped_column(String(64, collation="BINARY"))
    forecast_date: Mapped[date] = mapped_column(Date)
    day_offset: Mapped[int] = mapped_column(Integer)  # D0/D1/D2...
    forecast_qty: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    forecast_source: Mapped[str | None] = mapped_column(String(30))
    sales_multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("1"))
    is_adjusted: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[str] = mapped_column(String(20), default="derived")

    def __repr__(self) -> str:
        return (
            f"<MkSkuForecastDaily msku={self.msku!r} d{self.day_offset} "
            f"qty={self.forecast_qty}>"
        )
