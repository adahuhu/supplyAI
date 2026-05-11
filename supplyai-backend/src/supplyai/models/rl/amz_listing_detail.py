"""rl_amz_listing_detail — Listing 详情扩展（数据表设计 §3.3）."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class RlAmzListingDetail(Base):
    """Listing 详情扩展 — 与 amz_all_listing 1:1 通过 listing_id 关联."""

    __tablename__ = "rl_amz_listing_detail"
    __table_args__ = (
        Index("uq_rl_amz_listing_detail_tmm", "tenant_id", "mall_id", "msku", unique=True),
        Index("ix_rl_amz_listing_detail_listing", "tenant_id", "listing_id"),
    )

    listing_detail_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    listing_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(50, collation="BINARY"))
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    brand: Mapped[str | None] = mapped_column(Text)
    image_url_px75: Mapped[str | None] = mapped_column(String(255))
    image_url: Mapped[str | None] = mapped_column(String(255))
    product_type: Mapped[str | None] = mapped_column(String(150))
    display_group_title: Mapped[str | None] = mapped_column(String(250))
    display_group_rank: Mapped[int | None]
    classification_title: Mapped[str | None] = mapped_column(String(250))
    classification_rank: Mapped[int | None]
    package_length: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    package_width: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    package_height: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    package_weight: Mapped[Decimal] = mapped_column(Numeric(7, 2), default=Decimal("0"))
    start_selling_date: Mapped[datetime | None] = mapped_column(DateTime)
    first_order_date: Mapped[datetime | None] = mapped_column(DateTime)
    last_pull_time: Mapped[datetime | None] = mapped_column(DateTime)
    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    def __repr__(self) -> str:
        return f"<RlAmzListingDetail id={self.listing_detail_id} listing={self.listing_id}>"
