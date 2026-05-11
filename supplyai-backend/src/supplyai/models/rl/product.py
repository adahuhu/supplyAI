"""rl_product — ERP 产品主数据（数据表设计 §3.3）."""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import JSON, BigInteger, Date, DateTime, Index, Integer, Numeric, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class RlProduct(Base):
    """ERP 产品主数据 — 提供品名 / 负责人 / 采购成本 / 物流配置."""

    __tablename__ = "rl_product"
    __table_args__ = (
        Index("uq_rl_product_un", "del_flag", "sku", "tenant_id", unique=True),
        Index("ix_rl_product_status", "status"),
    )

    product_id: Mapped[int] = mapped_column(Integer, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(Integer)
    type: Mapped[str | None] = mapped_column(String(25))  # ORDINARY / COMBINATION / BUNDLED_PRODUCTS / SPU
    sku: Mapped[str | None] = mapped_column(String(255))
    product_name: Mapped[str | None] = mapped_column(String(255))
    category_id: Mapped[int | None] = mapped_column(BigInteger)
    prod_line_id: Mapped[int | None] = mapped_column(BigInteger)
    brand_id: Mapped[int | None] = mapped_column(BigInteger)
    model: Mapped[str | None] = mapped_column(String(255))
    unit: Mapped[str | None] = mapped_column(String(30))
    status: Mapped[str | None] = mapped_column(
        String(30), default="ON_SALE"
    )  # ON_SALE / A_CLEARANCE / HALT_SALES / DISABLE
    developer_user_id: Mapped[int | None]
    responsible_user_ids: Mapped[str | None] = mapped_column(String(255))  # 逗号分隔
    purchaseer_user_id: Mapped[int | None]
    purchase_delivery_date: Mapped[int] = mapped_column(Integer, default=0)  # 采购交期(天)
    purchase_price: Mapped[Decimal] = mapped_column(Numeric(24, 2), default=Decimal("0"))
    purchasing_notes: Mapped[str | None] = mapped_column(String(500))
    product_logistics_list: Mapped[dict | list | None] = mapped_column(JSON)
    image_url_px75: Mapped[str | None] = mapped_column(Text)
    image_url: Mapped[str | None] = mapped_column(Text)
    team_id: Mapped[int | None] = mapped_column(BigInteger)
    dept_id: Mapped[int | None] = mapped_column(BigInteger)
    development_date: Mapped[date | None] = mapped_column(Date)
    shelve_date: Mapped[date | None] = mapped_column(Date)
    first_order_date: Mapped[date | None] = mapped_column(Date)
    label_ids: Mapped[str | None] = mapped_column(String(255))
    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    updated_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    def __repr__(self) -> str:
        return f"<RlProduct id={self.product_id} sku={self.sku!r} name={self.product_name!r}>"
