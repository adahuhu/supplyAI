"""mk_stockout_event — 断货事件表（数据表设计 §4.10 / §10）.

生成规则(数据表设计 §10):
  - 打开:fba_available <= 0 且无 open 事件
  - 保持:仍 fba_available <= 0,更新 duration_days
  - 关闭:fba_available > 0,写 end_at
  - 触发条件用 FBA 仓内可售,不计 FBA 在途
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkStockoutEvent(Base):
    """断货事件 — 用于 Dashboard 近 7 天断货趋势 + AI 解释."""

    __tablename__ = "mk_stockout_event"
    __table_args__ = (
        Index("ix_mk_stockout_event_tmm", "tenant_id", "mall_id", "msku"),
        Index("ix_mk_stockout_event_status", "event_status"),
        Index("ix_mk_stockout_event_start", "start_at"),
    )

    event_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(64, collation="BINARY"))
    start_at: Mapped[datetime] = mapped_column(DateTime)
    end_at: Mapped[datetime | None] = mapped_column(DateTime)
    duration_days: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    event_status: Mapped[str] = mapped_column(String(20))  # open / closed
    source_type: Mapped[str] = mapped_column(String(20), default="derived")

    def __repr__(self) -> str:
        return (
            f"<MkStockoutEvent id={self.event_id} msku={self.msku!r} "
            f"status={self.event_status}>"
        )
