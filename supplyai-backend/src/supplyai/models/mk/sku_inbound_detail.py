"""mk_sku_inbound_detail — 在途明细表（数据表设计 §4.9）.

FBA 平台侧 working / shipped / receiving 已由 rl_amz_manage_fba_inventory 支撑。
本表保留:本地采购在途、调拨在途、待加工、本地入库等真实源表暂未提供的数据。
"""
from __future__ import annotations

from datetime import date

from sqlalchemy import BigInteger, Date, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkSkuInboundDetail(Base):
    """本地侧在途单据."""

    __tablename__ = "mk_sku_inbound_detail"
    __table_args__ = (
        Index("ix_mk_sku_inbound_detail_tmm", "tenant_id", "mall_id", "msku"),
        Index("ix_mk_sku_inbound_detail_arrival", "expected_arrival_date"),
    )

    inbound_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(64, collation="BINARY"))
    sku: Mapped[str | None] = mapped_column(String(64))
    inbound_type: Mapped[str] = mapped_column(String(30))  # purchase / transfer / local_receiving / processing
    inbound_status: Mapped[str] = mapped_column(String(30))  # in_transit / receiving / pending
    logistics_type: Mapped[str | None] = mapped_column(String(30), nullable=True)  # sea / sea_express / sea_air_express / air / truck / express
    qty: Mapped[int] = mapped_column(Integer)
    expected_arrival_date: Mapped[date | None] = mapped_column(Date)
    source_order_no: Mapped[str | None] = mapped_column(String(64))
    source_type: Mapped[str] = mapped_column(String(20), default="mock")

    def __repr__(self) -> str:
        return (
            f"<MkSkuInboundDetail id={self.inbound_id} type={self.inbound_type} "
            f"status={self.inbound_status} qty={self.qty}>"
        )
