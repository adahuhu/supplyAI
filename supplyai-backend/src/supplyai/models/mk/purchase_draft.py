"""mk_purchase_draft — 采购草稿表（数据表设计 §4.11）.

Phase 1 仅作演示动作闭环;不做真实采购回写。
表名不带 _mock 后缀,后续生产化通过 source_type 区分。
"""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, DateTime, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkPurchaseDraft(Base):
    """采购草稿."""

    __tablename__ = "mk_purchase_draft"
    __table_args__ = (
        Index("ix_mk_purchase_draft_calc_run", "calc_run_id"),
        Index("ix_mk_purchase_draft_status", "status"),
    )

    draft_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    calc_run_id: Mapped[str | None] = mapped_column(String(64))
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(64, collation="BINARY"))
    sku: Mapped[str | None] = mapped_column(String(64))
    suggest_qty: Mapped[int] = mapped_column(Integer)
    supplier_name: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str] = mapped_column(String(20), default="draft")  # draft / confirmed / redirected
    created_by: Mapped[str | None] = mapped_column(String(50))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)
    source_type: Mapped[str] = mapped_column(String(20), default="mock")

    def __repr__(self) -> str:
        return (
            f"<MkPurchaseDraft id={self.draft_id} msku={self.msku!r} "
            f"qty={self.suggest_qty} status={self.status}>"
        )
