"""mk_supply_sku_daily_stat — 备货计划核心快照表（数据表设计 §4.7）.

列表 / Dashboard 优先读这张表,不实时聚合明细。
关键公式:
  total_stock = fba_available + working + shipped + receiving + local_actual + local_plan
  suggest_qty = CEIL(max(0, coverage_demand - total_stock))
  fba_sellable_days = (fba_available + working + shipped + receiving) / forecast_daily
"""
from __future__ import annotations

from datetime import date, datetime
from decimal import Decimal

from sqlalchemy import BigInteger, Date, DateTime, Index, Integer, Numeric, String
from sqlalchemy.orm import Mapped, mapped_column

from supplyai.models.base import Base, BigIntPk


class MkSupplySkuDailyStat(Base):
    """备货计划核心结果快照 — 41+ 字段."""

    __tablename__ = "mk_supply_sku_daily_stat"
    __table_args__ = (
        Index(
            "uq_mk_supply_sku_daily_stat_run_tmm",
            "calc_run_id", "tenant_id", "mall_id", "msku",
            unique=True,
        ),
        Index("ix_mk_supply_sku_risk", "risk_level"),
        Index("ix_mk_supply_sku_stockout", "stockout_date"),
        Index("ix_mk_supply_sku_suggest", "suggest_purchase"),
        Index("ix_mk_supply_sku_calc_run", "calc_run_id"),
    )

    id: Mapped[int] = mapped_column(BigIntPk, primary_key=True, autoincrement=True)
    calc_run_id: Mapped[str] = mapped_column(String(64))
    tenant_id: Mapped[int] = mapped_column(BigInteger)
    stat_date: Mapped[date] = mapped_column(Date)

    # SKU 标识
    listing_id: Mapped[int | None] = mapped_column(BigInteger)
    mall_id: Mapped[int | None] = mapped_column(BigInteger)
    country_code: Mapped[str | None] = mapped_column(String(10))
    msku: Mapped[str] = mapped_column(String(64, collation="BINARY"))
    fnsku: Mapped[str | None] = mapped_column(String(64))
    sku: Mapped[str | None] = mapped_column(String(64))
    asin: Mapped[str | None] = mapped_column(String(16))
    product_name: Mapped[str | None] = mapped_column(String(200))
    label_ids: Mapped[str | None] = mapped_column(String(255))
    listing_status: Mapped[str | None] = mapped_column(String(20))
    delivery_method: Mapped[str | None] = mapped_column(String(20))  # FBA / FBM
    risk_level: Mapped[str] = mapped_column(String(10))  # p1 / p2 / p3 / safe

    # 财务
    yesterday_sales: Mapped[int | None] = mapped_column(Integer)
    yesterday_revenue: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    revenue_7d: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    expense_7d: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    cost_7d: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    gross_profit_7d: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    gross_margin: Mapped[Decimal | None] = mapped_column(Numeric(5, 4))
    financial_estimate_type: Mapped[str | None] = mapped_column(String(20))  # allocated / actual / hidden

    # 销量窗口
    sales_7d: Mapped[int | None] = mapped_column(Integer)
    sales_30d: Mapped[int | None] = mapped_column(Integer)
    sales_60d: Mapped[int | None] = mapped_column(Integer)
    sales_90d: Mapped[int | None] = mapped_column(Integer)

    # 销量预测
    forecast_daily: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    forecast_source: Mapped[str | None] = mapped_column(String(30))  # fixed/dynamic/default/denoised/raw
    coverage_demand: Mapped[Decimal | None] = mapped_column(Numeric(12, 2))
    last_7d_raw_daily: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    last_7d_denoised_daily: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # FBA 库存(5 项,reserved 仅展示)
    fba_available: Mapped[int | None] = mapped_column(Integer)
    fba_inbound_working: Mapped[int | None] = mapped_column(Integer)
    fba_inbound_shipped: Mapped[int | None] = mapped_column(Integer)
    fba_inbound_receiving: Mapped[int | None] = mapped_column(Integer)
    fba_reserved: Mapped[int | None] = mapped_column(Integer)

    # 本地库存
    local_actual: Mapped[int | None] = mapped_column(Integer)
    local_plan: Mapped[int | None] = mapped_column(Integer)

    # 总库存与可售天数
    total_stock: Mapped[int | None] = mapped_column(Integer)
    sellable_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    fba_sellable_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))
    local_sellable_days: Mapped[Decimal | None] = mapped_column(Numeric(10, 2))

    # 时效与建议
    safety_days: Mapped[int | None] = mapped_column(Integer)
    stockout_date: Mapped[date | None] = mapped_column(Date)
    lead_time_days: Mapped[int | None] = mapped_column(Integer)
    suggest_purchase: Mapped[int] = mapped_column(Integer, default=0)
    suggest_qty: Mapped[int] = mapped_column(Integer, default=0)
    suggest_purchase_date: Mapped[date | None] = mapped_column(Date)

    # 多币种
    unit_cost: Mapped[Decimal | None] = mapped_column(Numeric(24, 4))
    currency: Mapped[str | None] = mapped_column(String(10))
    base_currency: Mapped[str | None] = mapped_column(String(10), default="USD")
    fx_rate_to_base: Mapped[Decimal | None] = mapped_column(Numeric(18, 8))
    fx_rate_as_of: Mapped[datetime | None] = mapped_column(DateTime)
    suggest_amount: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))
    suggest_amount_base: Mapped[Decimal | None] = mapped_column(Numeric(14, 2))

    updated_at: Mapped[datetime] = mapped_column(
        DateTime, default=datetime.utcnow, onupdate=datetime.utcnow
    )
    source_type: Mapped[str] = mapped_column(String(20), default="derived")

    def __repr__(self) -> str:
        return (
            f"<MkSupplySkuDailyStat msku={self.msku!r} mall={self.mall_id} "
            f"risk={self.risk_level} suggest={self.suggest_qty}>"
        )
