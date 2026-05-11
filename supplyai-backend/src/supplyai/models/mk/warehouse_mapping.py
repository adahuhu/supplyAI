"""mk_warehouse_mapping — 仓库类型映射表（数据表设计 §4.1.1）.

Phase 1 用 mock 补齐;生产前换 rl_warehouse 真实仓库表。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class MkWarehouseMapping(Base):
    """仓库 ID → 类型映射 — 用于识别本地仓 / FBA 仓 / 海外仓 / 虚拟仓."""

    __tablename__ = "mk_warehouse_mapping"
    __table_args__ = (
        Index("uq_mk_warehouse_mapping_tw", "tenant_id", "warehouse_id", unique=True),
        Index("ix_mk_warehouse_mapping_type", "warehouse_type"),
        Index("ix_mk_warehouse_mapping_local", "include_in_local_actual"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    warehouse_id: Mapped[int] = mapped_column(BigInteger)
    warehouse_name: Mapped[str | None] = mapped_column(String(100))
    # local / fba_transfer / overseas / virtual / unknown
    warehouse_type: Mapped[str] = mapped_column(String(30))
    # Phase 1 仅 local 计入 local_actual
    include_in_local_actual: Mapped[int] = mapped_column(Integer, default=0)
    source_type: Mapped[str] = mapped_column(String(20), default="mock")
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )

    def __repr__(self) -> str:
        return (
            f"<MkWarehouseMapping wh={self.warehouse_id} type={self.warehouse_type} "
            f"local={bool(self.include_in_local_actual)}>"
        )
