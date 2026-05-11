"""rl_inventory_detail — 本地库存明细表（数据表设计 §3.11）.

注意:真实表中存在大小写不规范字段(`Inventory_value` / `mall_Identify_code`),
本模型用 `mapped_column("DBColName", ...)` 显式映射,ORM 层用规范小写名。
"""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class RlInventoryDetail(Base):
    """本地库存明细 — 仓库 + sku + 店铺 粒度的当前快照."""

    __tablename__ = "rl_inventory_detail"
    __table_args__ = (
        Index("ix_rl_inventory_detail_key", "key"),
        Index("ix_rl_inventory_detail_sku", "sku", "tenant_id", "warehouse_id"),
        Index("ix_rl_inventory_detail_mall", "tenant_id", "mall_id", "msku"),
    )

    detail_id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    key: Mapped[str | None] = mapped_column(String(350))  # 唯一key:warehouse_id-sku-mall_id-fnsku
    product_id: Mapped[int | None] = mapped_column(BigInteger)
    sku: Mapped[str | None] = mapped_column(String(255))
    warehouse_id: Mapped[int | None] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(50, collation="BINARY"))
    # 真实表大写字段名 mall_Identify_code,SQLAlchemy 显式映射
    mall_identify_code: Mapped[str | None] = mapped_column("mall_Identify_code", String(30))
    mall_type: Mapped[int | None] = mapped_column(Integer)  # 0=Amazon, 1=Walmart

    # 核心库存量
    available_quantity: Mapped[int | None] = mapped_column(Integer)
    available_locked_quantity: Mapped[int | None] = mapped_column(Integer)
    defective_quantity: Mapped[int | None] = mapped_column(Integer)
    defective_locked_quantity: Mapped[int | None] = mapped_column(Integer)

    # 成本(decimal 24,4)
    unit_price: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_logistics_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    unit_inventory_cost: Mapped[Decimal] = mapped_column(Numeric(24, 4), default=Decimal("0"))
    # 真实表大写字段 Inventory_value
    inventory_value: Mapped[Decimal | None] = mapped_column("Inventory_value", Numeric(24, 4))
    total_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    total_inventory_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))

    owners: Mapped[str | None] = mapped_column(String(255))  # 负责人 ids 逗号分隔
    dept_id: Mapped[int | None] = mapped_column(BigInteger)
    country_code: Mapped[str | None] = mapped_column(String(5))
    country: Mapped[str | None] = mapped_column(String(10))
    remark: Mapped[str | None] = mapped_column(String(255))

    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    def __repr__(self) -> str:
        return (
            f"<RlInventoryDetail id={self.detail_id} sku={self.sku!r} "
            f"warehouse={self.warehouse_id} avail={self.available_quantity}>"
        )
