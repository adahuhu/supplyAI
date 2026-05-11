"""Stock 聚合单元测试."""
from __future__ import annotations

import pytest

from supplyai.domain.calc.stock import StockBreakdown, aggregate_stock, fba_inbound_total


def test_fba_inbound_total_sums_three_legs() -> None:
    assert fba_inbound_total(working=10, shipped=20, receiving=5) == 35


def test_fba_inbound_total_handles_none() -> None:
    assert fba_inbound_total(working=None, shipped=20, receiving=None) == 20


def test_aggregate_stock_full() -> None:
    """完整 6 项库存相加."""
    result = aggregate_stock(
        fba_available=100,
        fba_inbound_working=10,
        fba_inbound_shipped=20,
        fba_inbound_receiving=5,
        local_actual=30,
        local_plan=15,
    )
    assert isinstance(result, StockBreakdown)
    assert result.fba_available == 100
    assert result.fba_inbound == 35
    assert result.local_actual == 30
    assert result.local_plan == 15
    assert result.total_stock == 180


def test_aggregate_stock_treats_none_as_zero() -> None:
    result = aggregate_stock(
        fba_available=None,
        fba_inbound_working=None,
        fba_inbound_shipped=None,
        fba_inbound_receiving=None,
        local_actual=None,
        local_plan=None,
    )
    assert result.total_stock == 0
    assert result.fba_inbound == 0


def test_aggregate_stock_excludes_reserved() -> None:
    """fba_reserved 不进 total_stock(预留库存仅展示)."""
    result = aggregate_stock(
        fba_available=100,
        fba_inbound_working=0,
        fba_inbound_shipped=0,
        fba_inbound_receiving=0,
        local_actual=0,
        local_plan=0,
        fba_reserved=50,  # 即使传入也不参与合计
    )
    assert result.total_stock == 100


def test_sellable_days_basic() -> None:
    from supplyai.domain.calc.stock import sellable_days

    assert sellable_days(stock=100, daily=10) == pytest.approx(10.0)


def test_sellable_days_zero_daily_returns_inf_marker() -> None:
    """daily=0 → 返回 None(前端展示为 ∞ 或"-")."""
    from supplyai.domain.calc.stock import sellable_days

    assert sellable_days(stock=100, daily=0) is None


def test_sellable_days_zero_stock() -> None:
    from supplyai.domain.calc.stock import sellable_days

    assert sellable_days(stock=0, daily=10) == pytest.approx(0.0)
