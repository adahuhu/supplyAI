"""rl_amz_all_listing — Listing 主表（数据表设计 §3.3）."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class RlAmzAllListing(Base):
    """Amazon Listing 主表 — MSKU + 店铺粒度."""

    __tablename__ = "rl_amz_all_listing"
    __table_args__ = (
        Index("uq_rl_amz_all_listing_tmm", "tenant_id", "msku", "mall_id", unique=True),
        Index("ix_rl_amz_all_listing_asin", "tenant_id", "asin"),
        Index("ix_rl_amz_all_listing_status", "tenant_id", "status"),
    )

    listing_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    country_code: Mapped[str | None] = mapped_column(String(5))
    country: Mapped[str | None] = mapped_column(String(10))
    amz_listing_id: Mapped[str | None] = mapped_column(String(15))
    asin: Mapped[str | None] = mapped_column(String(15))
    parent_asin: Mapped[str | None] = mapped_column(String(15))
    item_name: Mapped[str | None] = mapped_column(Text)
    # MSKU - 真实表用 utf8mb4_0900_bin (区分大小写); SQLite 用 BINARY collation
    msku: Mapped[str] = mapped_column(String(50, collation="BINARY"))
    fnsku: Mapped[str | None] = mapped_column(String(15))
    delivery_method: Mapped[str | None] = mapped_column(String(5))  # FBA / FBM
    fulfillment_channel: Mapped[str | None] = mapped_column(String(20))
    status: Mapped[str | None] = mapped_column(
        String(15), default="INACTIVE"
    )  # ACTIVE / INACTIVE / INCOMPLETE / DELETE
    product_type: Mapped[str | None] = mapped_column(String(100))
    price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    platform_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fba_estimated_fee: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fbm_available_stock: Mapped[int | None] = mapped_column(BigInteger)
    open_date: Mapped[date | None] = mapped_column(Date)
    asin_type: Mapped[str | None] = mapped_column(
        String(20), default="INDEPENDENT"
    )  # PARENT / CHILD / INDEPENDENT
    label_ids: Mapped[str | None] = mapped_column(String(255))
    default_currency: Mapped[str] = mapped_column(String(20), default="")
    last_pull_time: Mapped[datetime | None] = mapped_column(DateTime)
    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    def __repr__(self) -> str:
        return (
            f"<RlAmzAllListing id={self.listing_id} msku={self.msku!r} "
            f"mall={self.mall_id} method={self.delivery_method}>"
        )
