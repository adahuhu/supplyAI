"""mk_calc_run — 计算批次表（数据表设计 §4.6）.

保证同一行字段来自同一次有效计算;
所有 mk_supply_sku_daily_stat / mk_sku_forecast_daily 均关联 calc_run_id。
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkCalcRun(Base):
    """计算批次记录."""

    __tablename__ = "mk_calc_run"
    __table_args__ = (
        Index("ix_mk_calc_run_tenant_date", "tenant_id", "stat_date"),
        Index("ix_mk_calc_run_status", "status"),
    )

    calc_run_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    stat_date: Mapped[date] = mapped_column(Date)
    run_type: Mapped[str] = mapped_column(String(20))  # scheduled / rule_changed / manual
    run_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_sales_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_inventory_at: Mapped[datetime | None] = mapped_column(DateTime)
    source_inbound_at: Mapped[datetime | None] = mapped_column(DateTime)
    rule_version: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str] = mapped_column(String(20), default="running")  # running / success / failed
    error_message: Mapped[str | None] = mapped_column(String(500))
    source_type: Mapped[str] = mapped_column(String(20), default="derived")

    def __repr__(self) -> str:
        return (
            f"<MkCalcRun id={self.calc_run_id} tenant={self.tenant_id} "
            f"date={self.stat_date} status={self.status}>"
        )
