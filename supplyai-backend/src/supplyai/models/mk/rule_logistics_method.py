"""mk_rule_logistics_method — 规则物流方式表（数据表设计 §4.4）.

一个补货规则可配多个物流方式;采购时效计算时取最长。
"""
from __future__ import annotations

from sqlalchemy import BigInteger, Index, Integer, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class MkRuleLogisticsMethod(Base):
    """规则物流方式 — 一对多 mk_replenishment_rule.rule_id."""

    __tablename__ = "mk_rule_logistics_method"
    __table_args__ = (
        Index("ix_mk_rule_logistics_method_rule", "rule_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    rule_id: Mapped[str] = mapped_column(String(64))
    logistics_mode: Mapped[str] = mapped_column(String(30))  # 海运/空运/快船/快递
    logistics_days: Mapped[int] = mapped_column(Integer)
    is_active: Mapped[int] = mapped_column(Integer, default=1)
    source_type: Mapped[str] = mapped_column(String(20), default="mock")

    def __repr__(self) -> str:
        return (
            f"<MkRuleLogisticsMethod rule={self.rule_id} mode={self.logistics_mode!r} "
            f"days={self.logistics_days}>"
        )
