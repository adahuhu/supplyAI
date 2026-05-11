"""rl_amz_sales_daily_report — 销量日报表（数据表设计 §3.9 / §5.1）."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class RlAmzSalesDailyReport(Base):
    """每日销量 / 销售额 / 订单量 — MSKU + 店铺 + 日期 粒度."""

    __tablename__ = "rl_amz_sales_daily_report"
    __table_args__ = (
        Index(
            "uq_rl_sales_tymm",
            "tenant_id", "year_month_day", "mall_id", "msku",
            unique=True,
        ),
        Index("ix_rl_sales_listing", "listing_id"),
        Index("ix_rl_sales_date", "year_month_day"),
        Index("ix_rl_sales_msku_mall", "msku", "mall_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(50, collation="BINARY"))
    year_month_day: Mapped[str | None] = mapped_column(String(15))  # YYYY-MM-DD
    listing_id: Mapped[int | None] = mapped_column(BigInteger)
    asin: Mapped[str | None] = mapped_column(String(50))
    parent_asin: Mapped[str | None] = mapped_column(String(50))
    country: Mapped[str | None] = mapped_column(String(50))
    country_code: Mapped[str | None] = mapped_column(String(10))
    currency_code: Mapped[str | None] = mapped_column(String(5))
    item_name: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(String(255))
    image_url_px75: Mapped[str | None] = mapped_column(String(255))
    sales_volume: Mapped[int | None] = mapped_column(Integer)
    sales: Mapped[Decimal] = mapped_column(Numeric(10, 2), default=Decimal("0"))
    order_quantity: Mapped[int | None] = mapped_column(Integer)
    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return (
            f"<RlAmzSalesDailyReport msku={self.msku!r} mall={self.mall_id} "
            f"date={self.year_month_day} qty={self.sales_volume}>"
        )
