"""mk_replenishment_rule — 补货规则表（数据表设计 §4.3）."""
from __future__ import annotations

from datetime import datetime

from sqlalchemy import BigInteger, CheckConstraint, DateTime, Index, Integer, JSON, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class MkReplenishmentRule(Base):
    """补货规则 — 三层作用范围:global / store / sku."""

    __tablename__ = "mk_replenishment_rule"
    __table_args__ = (
        Index("ix_mk_replenishment_rule_scope", "tenant_id", "scope_type", "mall_id", "msku"),
        # 数据表设计 §4.3 SKU 特配约束
        CheckConstraint(
            "scope_type != 'sku' OR (mall_id IS NOT NULL AND msku IS NOT NULL AND msku != '')",
            name="ck_replenishment_rule_sku_scope",
        ),
    )

    rule_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    scope_type: Mapped[str] = mapped_column(String(20))  # global / store / sku
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    msku: Mapped[str | None] = mapped_column(String(64, collation="BINARY"))
    safety_days: Mapped[int] = mapped_column(Integer, default=14)
    purchase_duration_days: Mapped[int] = mapped_column(Integer, default=0)
    delivery_days: Mapped[int] = mapped_column(Integer, default=0)
    qc_days: Mapped[int] = mapped_column(Integer, default=0)
    stock_scope_json: Mapped[list | None] = mapped_column(JSON, default=list)
    rule_version: Mapped[str | None] = mapped_column(String(30))
    enabled: Mapped[int] = mapped_column(Integer, default=1)
    updated_by: Mapped[str | None] = mapped_column(String(50))
    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_type: Mapped[str] = mapped_column(String(20), default="mock")

    def __repr__(self) -> str:
        return (
            f"<MkReplenishmentRule id={self.rule_id} scope={self.scope_type} "
            f"safety={self.safety_days}>"
        )
