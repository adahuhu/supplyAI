"""Suggest 计算单元测试."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from supplyai.domain.calc.suggest import (
    SuggestInput,
    SuggestOutput,
    coverage_demand,
    compute_suggest,
)


def test_coverage_demand_basic() -> None:
    """coverage_demand = (lead_time + safety_days) * forecast_daily."""
    assert coverage_demand(forecast_daily=10, lead_time_days=20, safety_days=10) == pytest.approx(300.0)


def test_coverage_demand_zero_daily() -> None:
    assert coverage_demand(forecast_daily=0, lead_time_days=20, safety_days=10) == pytest.approx(0.0)


def test_compute_suggest_under_coverage_recommends_purchase() -> None:
    """库存不足时建议采购."""
    out = compute_suggest(
        SuggestInput(
            forecast_daily=10,
            total_stock=100,  # 100 库存
            lead_time_days=20,
            safety_days=10,  # 需要 30 天 = 300
        )
    )
    assert isinstance(out, SuggestOutput)
    assert out.coverage_demand == pytest.approx(300.0)
    assert out.suggest_qty == 200
    assert out.suggest_purchase is True


def test_compute_suggest_above_coverage_no_purchase() -> None:
    """库存超过 coverage 不建议采购."""
    out = compute_suggest(
        SuggestInput(
            forecast_daily=10,
            total_stock=500,
            lead_time_days=20,
            safety_days=10,
        )
    )
    assert out.suggest_qty == 0
    assert out.suggest_purchase is False


def test_compute_suggest_ceil_rounding() -> None:
    """suggest_qty 向上取整."""
    out = compute_suggest(
        SuggestInput(
            forecast_daily=3.7,
            total_stock=0,
            lead_time_days=10,
            safety_days=0,
        )
    )
    # coverage = 37, suggest = ceil(37 - 0) = 37
    assert out.suggest_qty == 37


def test_compute_suggest_zero_daily_no_purchase() -> None:
    """无需求时不建议采购."""
    out = compute_suggest(
        SuggestInput(
            forecast_daily=0,
            total_stock=0,
            lead_time_days=20,
            safety_days=10,
        )
    )
    assert out.suggest_qty == 0
    assert out.suggest_purchase is False


def test_compute_suggest_purchase_date_back_from_stockout() -> None:
    """purchase_date = stockout_date - lead_time(若不为空)."""
    out = compute_suggest(
        SuggestInput(
            forecast_daily=10,
            total_stock=100,
            lead_time_days=20,
            safety_days=10,
            today=date(2026, 5, 10),
            stockout_date=date(2026, 5, 30),
        )
    )
    # 5/30 - 20 = 5/10
    assert out.suggest_purchase_date == date(2026, 5, 10)


def test_compute_suggest_amount_with_unit_cost() -> None:
    """suggest_amount = suggest_qty * unit_cost,base 用 fx_rate."""
    out = compute_suggest(
        SuggestInput(
            forecast_daily=10,
            total_stock=0,
            lead_time_days=10,
            safety_days=0,
            unit_cost=Decimal("3.5"),
            currency="EUR",
            fx_rate_to_base=Decimal("1.1"),  # EUR→USD
        )
    )
    # qty=100,amount = 350 EUR,base = 385 USD
    assert out.suggest_qty == 100
    assert out.suggest_amount == pytest.approx(350.0)
    assert out.suggest_amount_base == pytest.approx(385.0)
    assert out.currency == "EUR"
    assert out.base_currency == "USD"
