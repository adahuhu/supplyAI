"""rl_amz_finances_profit_mall_100228 — 店铺级利润 / 费用结算表（数据表设计 §3 / §5.3）.

边界:本表是店铺维度,唯一键 tenant + settlement_date + mall_id,
不含 msku,不能直接给 SKU 级毛利做精确来源。
SKU 级利润通过销售额占比分摊(数据表设计 §5.4)。
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class RlAmzFinancesProfit(Base):
    """店铺日结利润 / 费用 — 提供广告费 / 仓储费 / 平台费用等."""

    __tablename__ = "rl_amz_finances_profit_mall_100228"
    __table_args__ = (
        Index(
            "uq_rl_finances_profit_tdm",
            "tenant_id", "settlement_date", "mall_id",
            unique=True,
        ),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    tenant_id: Mapped[int | None] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    settlement_date: Mapped[date | None] = mapped_column(Date)
    currency_code: Mapped[str | None] = mapped_column(String(10))

    # 广告费
    sp_ads_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    sb_ads_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    sbv_ads_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    sd_ads_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    ads_fee_share: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    product_ads_payment: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # 仓储费
    month_storage_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    permanent_storage_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    excess_storage_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fba_storage_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fba_long_storage_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # 销售额(店铺维度)
    fba_sales: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fbm_sales: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    # 平台费用
    commission: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fba_commission: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fbm_commission: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    fba_shipment_fee: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    created_time: Mapped[datetime | None] = mapped_column(DateTime)
    update_time: Mapped[datetime | None] = mapped_column(DateTime)

    def __repr__(self) -> str:
        return f"<RlAmzFinancesProfit mall={self.mall_id} date={self.settlement_date}>"
