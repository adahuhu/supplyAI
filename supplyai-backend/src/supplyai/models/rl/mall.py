"""rl_mall — 店铺表（数据表设计 §3.2）."""
from __future__ import annotations

from datetime import datetime
from decimal import Decimal

from sqlalchemy import BigInteger, DateTime, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base


class RlMall(Base):
    """店铺主数据 — Amazon / Walmart 等多平台共用."""

    __tablename__ = "rl_mall"

    mall_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger, index=True)
    account: Mapped[str | None] = mapped_column(String(30))
    mall_name: Mapped[str | None] = mapped_column(String(50))
    mall_info_id: Mapped[str | None] = mapped_column(String(32))
    seller_id: Mapped[str | None] = mapped_column(String(100))
    status: Mapped[str | None] = mapped_column(String(10))
    mall_status: Mapped[str | None] = mapped_column(String(10))
    mall_type: Mapped[str | None] = mapped_column(String(20))
    type: Mapped[int | None]
    country_code: Mapped[str | None] = mapped_column(String(5))
    country: Mapped[str | None] = mapped_column(String(30))
    region: Mapped[str | None] = mapped_column(String(15))
    marketplace_id: Mapped[str | None] = mapped_column(String(100))
    aws_region: Mapped[str | None] = mapped_column(String(20))
    settlement_currency: Mapped[str | None] = mapped_column(String(10))
    transaction_rate: Mapped[Decimal] = mapped_column(Numeric(14, 4), default=Decimal("0"))
    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)
    del_flag: Mapped[int] = mapped_column(BigInteger, default=0, index=True)

    def __repr__(self) -> str:
        return f"<RlMall id={self.mall_id} name={self.mall_name!r} country={self.country_code}>"
