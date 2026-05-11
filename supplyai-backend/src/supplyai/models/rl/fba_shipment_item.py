"""rl_fba_shipment_item — FBA 发货单商品级明细(真实源表镜像).

DDL 来源:数据表设计文档第十章 fba_shipment_item.
Phase 1 通过 seed 生成历史发货数据;Phase 2 切到真实 ETL。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import (
    BigInteger,
    DateTime,
    Index,
    Integer,
    Numeric,
    String,
)
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class RlFbaShipmentItem(Base):
    """FBA 发货单商品行 — 一个发货单(fba_shipment_order_id)含多个 SKU 行."""

    __tablename__ = "rl_fba_shipment_item"
    __table_args__ = (
        Index("ix_rl_fba_shipment_item_tmm", "tenant_id", "mall_id", "msku", "del_flag"),
        Index("ix_rl_fba_shipment_item_order", "fba_shipment_order_id"),
        Index("ix_rl_fba_shipment_item_amz", "amz_shipment_id"),
        Index("ix_rl_fba_shipment_item_created", "tenant_id", "mall_id", "msku", "created_time"),
    )

    fba_shipment_item_id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    fba_shipment_order_id: Mapped[int | None] = mapped_column(BigInteger)
    fba_shipment_order_no: Mapped[str | None] = mapped_column(String(15))  # SP230203004

    country_code: Mapped[str | None] = mapped_column(String(5))
    country: Mapped[str | None] = mapped_column(String(10))
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(50, collation="BINARY"))
    mall_identify_code: Mapped[str | None] = mapped_column("mall_Identify_code", String(30))
    asin: Mapped[str | None] = mapped_column(String(20))
    product_id: Mapped[int | None] = mapped_column(BigInteger)
    sku: Mapped[str] = mapped_column(String(255))
    amz_shipment_id: Mapped[str | None] = mapped_column(String(30))  # 货件编号

    # 数量
    quantity_declare: Mapped[int] = mapped_column(Integer, default=0)
    quantity_shipped: Mapped[int] = mapped_column(Integer, default=0)
    quantity_deduct: Mapped[int] = mapped_column(Integer, default=0)

    # 包装(用于物流估算)
    package_weight: Mapped[float] = mapped_column(default=0.0)  # 毛重 g
    package_length: Mapped[float] = mapped_column(default=0.0)  # cm
    package_width: Mapped[float] = mapped_column(default=0.0)
    package_height: Mapped[float] = mapped_column(default=0.0)
    item_remark: Mapped[str | None] = mapped_column(String(50))

    # 成本(出库带出)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_logistics_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_warehouse_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    unit_outbound_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_apportionment_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_logistic_price: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    estimate_unit_logistic_price: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_other_price: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    estimate_unit_other_price: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_inventory_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_accessories_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))

    # 元数据
    created_by: Mapped[int | None] = mapped_column(BigInteger)
    created_time: Mapped[datetime | None] = mapped_column(DateTime)  # 发货创建时间(关键)
    update_by: Mapped[int | None] = mapped_column(BigInteger)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0)
    dept_id: Mapped[int | None] = mapped_column(BigInteger)
    print_transparentPlan_flag: Mapped[int] = mapped_column(Integer, default=0)

    def __repr__(self) -> str:
        return (
            f"<RlFbaShipmentItem id={self.fba_shipment_item_id} "
            f"order={self.fba_shipment_order_no!r} msku={self.msku!r} qty={self.quantity_shipped}>"
        )
