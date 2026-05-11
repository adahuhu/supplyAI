"""Suggest(建议采购) 计算模块.

公式(数据表设计 §4.7):
  coverage_demand = (lead_time + safety_days) * forecast_daily
  suggest_qty     = CEIL(max(0, coverage_demand - total_stock))
  suggest_purchase= suggest_qty > 0
  suggest_amount  = suggest_qty * unit_cost(原币种)
  suggest_amount_base = suggest_amount * fx_rate_to_base
  purchase_date   = stockout_date - lead_time(可空)
"""
from __future__ import annotations

import math
from dataclasses import dataclass
from datetime import date, timedelta
from decimal import Decimal


@dataclass
class SuggestInput:
    forecast_daily: float
    total_stock: int
    lead_time_days: int
    safety_days: int
    today: date | None = None
    stockout_date: date | None = None
    unit_cost: Decimal | None = None
    currency: str | None = None
    fx_rate_to_base: Decimal | None = None
    base_currency: str = "USD"


@dataclass
class SuggestOutput:
    coverage_demand: float
    suggest_qty: int
    suggest_purchase: bool
    suggest_purchase_date: date | None = None
    suggest_amount: float | None = None
    suggest_amount_base: float | None = None
    currency: str | None = None
    base_currency: str = "USD"


def coverage_demand(
    *, forecast_daily: float, lead_time_days: int, safety_days: int
) -> float:
    return float(forecast_daily) * (lead_time_days + safety_days)


def compute_suggest(inp: SuggestInput) -> SuggestOutput:
    cd = coverage_demand(
        forecast_daily=inp.forecast_daily,
        lead_time_days=inp.lead_time_days,
        safety_days=inp.safety_days,
    )
    raw_qty = max(0.0, cd - inp.total_stock)
    qty = math.ceil(raw_qty) if raw_qty > 0 else 0
    purchase = qty > 0

    purchase_date: date | None = None
    if purchase and inp.stockout_date is not None:
        purchase_date = inp.stockout_date - timedelta(days=inp.lead_time_days)

    amount: float | None = None
    amount_base: float | None = None
    if purchase and inp.unit_cost is not None:
        amount = qty * float(inp.unit_cost)
        if inp.fx_rate_to_base is not None:
            amount_base = amount * float(inp.fx_rate_to_base)
        else:
            amount_base = amount  # 同币种无需换算

    return SuggestOutput(
        coverage_demand=cd,
        suggest_qty=qty,
        suggest_purchase=purchase,
        suggest_purchase_date=purchase_date,
        suggest_amount=amount,
        suggest_amount_base=amount_base,
        currency=inp.currency,
        base_currency=inp.base_currency,
    )
