"""Risk 分类单元测试 — 由 fba_sellable_days 派生 priority."""
from __future__ import annotations

import pytest

from supplyai.domain.calc.risk import RiskThresholds, classify_risk


def test_classify_risk_p1_within_7_days() -> None:
    assert classify_risk(fba_sellable_days=0) == "p1"
    assert classify_risk(fba_sellable_days=3.5) == "p1"
    assert classify_risk(fba_sellable_days=7.0) == "p1"  # 边界含右


def test_classify_risk_p2_8_to_15() -> None:
    assert classify_risk(fba_sellable_days=7.5) == "p2"  # >7
    assert classify_risk(fba_sellable_days=10) == "p2"
    assert classify_risk(fba_sellable_days=15.0) == "p2"


def test_classify_risk_p3_16_to_30() -> None:
    assert classify_risk(fba_sellable_days=15.5) == "p3"
    assert classify_risk(fba_sellable_days=30.0) == "p3"


def test_classify_risk_safe_above_30() -> None:
    assert classify_risk(fba_sellable_days=30.5) == "safe"
    assert classify_risk(fba_sellable_days=999) == "safe"


def test_classify_risk_none_means_no_demand() -> None:
    """daily=0 时 sellable_days=None,等同 safe."""
    assert classify_risk(fba_sellable_days=None) == "safe"


def test_classify_risk_custom_thresholds() -> None:
    """支持自定义阈值(后续给租户级配置用)."""
    custom = RiskThresholds(p1_max=3, p2_max=7, p3_max=14)
    assert classify_risk(fba_sellable_days=2, thresholds=custom) == "p1"
    assert classify_risk(fba_sellable_days=5, thresholds=custom) == "p2"
    assert classify_risk(fba_sellable_days=10, thresholds=custom) == "p3"
    assert classify_risk(fba_sellable_days=20, thresholds=custom) == "safe"


def test_stockout_date_for_p1() -> None:
    """p1 / p2 / p3 都需要 stockout_date(today + sellable_days)."""
    from datetime import date

    from supplyai.domain.calc.risk import compute_stockout_date

    today = date(2026, 5, 10)
    assert compute_stockout_date(today=today, fba_sellable_days=5) == date(2026, 5, 15)


def test_stockout_date_none_when_no_demand() -> None:
    from datetime import date

    from supplyai.domain.calc.risk import compute_stockout_date

    assert compute_stockout_date(today=date(2026, 5, 10), fba_sellable_days=None) is None
