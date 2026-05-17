"""mk_sku_inventory_override — SKU 趋势图库存点位覆盖.

用户在 SKU 分析页点击库存绿线修改某一天库存后,需要持久化该点位,
以便刷新页面或重新进入详情页时仍能恢复趋势模拟。
"""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, String, UniqueConstraint
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkSkuInventoryOverride(Base):
    """SKU 未来库存点位覆盖 — 按 listing + forecast_date 唯一."""

    __tablename__ = "mk_sku_inventory_override"
    __table_args__ = (
        UniqueConstraint(
            "tenant_id",
            "listing_id",
            "forecast_date",
            name="uq_mk_sku_inventory_override_tlf",
        ),
        Index("ix_mk_sku_inventory_override_listing", "tenant_id", "listing_id"),
        Index("ix_mk_sku_inventory_override_calc_run", "calc_run_id"),
    )

    override_id: Mapped[str] = mapped_column(String(96), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    calc_run_id: Mapped[str | None] = mapped_column(String(64))
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str] = mapped_column(String(64, collation="BINARY"))
    forecast_date: Mapped[date] = mapped_column(Date)
    day_offset: Mapped[int] = mapped_column(Integer)
    stock_qty: Mapped[int] = mapped_column(Integer)
    updated_by: Mapped[str | None] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_type: Mapped[str] = mapped_column(String(20), default="frontend")

    def __repr__(self) -> str:
        return (
            f"<MkSkuInventoryOverride listing={self.listing_id} "
            f"date={self.forecast_date} qty={self.stock_qty}>"
        )
