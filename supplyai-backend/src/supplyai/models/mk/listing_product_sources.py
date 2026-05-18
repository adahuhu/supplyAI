"""mk_listing_product_sources — SupplyAI 商品主物化表（数据表设计 §4.2）.

汇总 rl_amz_all_listing + rl_amz_listing_detail + rl_product 三表;
Phase 1 按每次 mk_calc_run 前重建/刷新,避免详情页 / 列表 join 三张真实表。
保留 FBA / FBM 全量;FBA-only 限制只在备货计算 / 列表查询层做。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class MkListingProductSources(Base):
    """商品主物化表 — listing 维度,1 行 / listing_id."""

    __tablename__ = "mk_listing_product_sources"
    __table_args__ = (
        Index(
            "uq_mk_listing_product_sources_lid",
            "tenant_id", "listing_id",
            unique=True,
        ),
        Index("ix_mk_lps_msku_mall", "tenant_id", "msku", "mall_id"),
        Index("ix_mk_lps_delivery_method", "delivery_method"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    listing_id: Mapped[int] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str] = mapped_column(String(50, collation="BINARY"))
    sku: Mapped[str | None] = mapped_column(String(255))
    asin: Mapped[str | None] = mapped_column(String(15))
    fnsku: Mapped[str | None] = mapped_column(String(15))
    delivery_method: Mapped[str | None] = mapped_column(String(5))  # FBA / FBM
    listing_status: Mapped[str | None] = mapped_column(String(15))
    title: Mapped[str | None] = mapped_column(Text)  # listing 标题
    product_name: Mapped[str | None] = mapped_column(String(255))  # ERP 仓库品名
    image_url: Mapped[str | None] = mapped_column(String(500))
    brand: Mapped[str | None] = mapped_column(String(100))
    category: Mapped[str | None] = mapped_column(String(250))
    label_ids: Mapped[str | None] = mapped_column(String(255))
    country_code: Mapped[str | None] = mapped_column(String(10))
    country: Mapped[str | None] = mapped_column(String(50))
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    sale_price: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    currency: Mapped[str | None] = mapped_column(String(10))
    owner: Mapped[str | None] = mapped_column(String(255))  # 负责人 ids 或姓名
    refreshed_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<MkListingProductSources listing={self.listing_id} msku={self.msku!r} "
            f"method={self.delivery_method}>"
        )
