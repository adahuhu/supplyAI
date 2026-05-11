"""rl_amz_manage_fba_inventory — FBA 库存管理表（数据表设计 §5.2）.

提供 FBA 可售 / 计划入库 / 标发在途 / 入库中 / 预留 等多维库存口径。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class RlAmzManageFbaInventory(Base):
    """FBA 库存数据 — 唯一键 tenant + mall + msku."""

    __tablename__ = "rl_amz_manage_fba_inventory"
    __table_args__ = (
        Index(
            "uq_rl_amz_manage_fba_inventory_tmm",
            "tenant_id", "mall_id", "msku",
            unique=True,
        ),
    )

    manage_inventory_id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(50, collation="BINARY"))
    fnsku: Mapped[str | None] = mapped_column(String(15))
    asin: Mapped[str | None] = mapped_column(String(15))

    # 核心库存口径(均含义参见数据表设计 §5.2)
    afn_fulfillable_quantity: Mapped[int | None] = mapped_column(Integer)  # FBA 可售
    afn_inbound_working_quantity: Mapped[int | None] = mapped_column(Integer)  # 计划入库
    afn_inbound_shipped_quantity: Mapped[int | None] = mapped_column(Integer)  # 标发在途
    afn_inbound_receiving_quantity: Mapped[int | None] = mapped_column(Integer)  # 入库中
    reserved_qty: Mapped[int | None] = mapped_column(Integer)  # 预留总数
    reserved_customerorders: Mapped[int | None] = mapped_column(Integer)  # 买家订单预留
    reserved_fc_transfers: Mapped[int | None] = mapped_column(Integer)  # 运营中心转运预留
    reserved_fc_processing: Mapped[int | None] = mapped_column(Integer)  # 运营中心处理中预留
    afn_unsellable_quantity: Mapped[int | None] = mapped_column(Integer)  # 不可售
    afn_total_quantity: Mapped[int | None] = mapped_column(Integer)  # 总量(含 working / shipped / receiving)

    last_pull_time: Mapped[datetime | None] = mapped_column(DateTime)
    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0)

    def __repr__(self) -> str:
        return (
            f"<RlAmzManageFbaInventory msku={self.msku!r} mall={self.mall_id} "
            f"avail={self.afn_fulfillable_quantity}>"
        )
