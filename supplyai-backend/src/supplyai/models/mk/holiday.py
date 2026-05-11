"""mk_holiday — 节日表(销量乘数 + 影响窗口).

前端 SKU 详情页节日色带渲染 + Calc Engine 动态预测乘数都用这张表.
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkHoliday(Base):
    """节日记录 — peak_date 前后 N 天叠加销量乘数."""

    __tablename__ = "mk_holiday"
    __table_args__ = (
        Index("ix_mk_holiday_tenant_peak", "tenant_id", "peak_date"),
    )

    holiday_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    name: Mapped[str] = mapped_column(String(64))
    peak_date: Mapped[date] = mapped_column(Date)
    days_before: Mapped[int] = mapped_column(Integer, default=0)
    days_after: Mapped[int] = mapped_column(Integer, default=0)
    sales_multiplier: Mapped[Decimal] = mapped_column(Numeric(8, 4), default=Decimal("1"))
    color: Mapped[str | None] = mapped_column(String(20))  # 前端色带颜色
    flag: Mapped[str | None] = mapped_column(String(8))  # emoji
    country_code: Mapped[str | None] = mapped_column(String(10))
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_type: Mapped[str] = mapped_column(String(20), default="mock")

    def __repr__(self) -> str:
        return f"<MkHoliday id={self.holiday_id} name={self.name!r} peak={self.peak_date}>"
