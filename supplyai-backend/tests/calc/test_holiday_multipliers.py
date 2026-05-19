"""节日历史系数预测单元测试."""
from __future__ import annotations

from datetime import date, timedelta
from decimal import Decimal
from types import SimpleNamespace

import pytest

from supplyai.services.calc_service import build_holiday_multipliers


def _holiday(
    holiday_id: str,
    name: str,
    peak: date,
    *,
    mult: str = "1.2",
    country_code: str | None = "US",
):
    return SimpleNamespace(
        holiday_id=holiday_id,
        name=name,
        peak_date=peak,
        days_before=1,
        days_after=1,
        sales_multiplier=Decimal(mult),
        country_code=country_code,
    )


def _sales(day: date, qty: int):
    return SimpleNamespace(year_month_day=day.isoformat(), sales_volume=qty)


def test_future_holiday_uses_matching_historical_sales_coefficient() -> None:
    """未来同类节日优先参考历史实际销量系数,而不是只用配置系数."""
    today = date(2026, 5, 18)
    historical_peak = date(2026, 5, 10)
    future_peak = date(2026, 5, 25)
    rows = []

    for offset in range(14, 2, -1):
        rows.append(_sales(historical_peak - timedelta(days=offset), 10))
    for offset in (-1, 0, 1):
        rows.append(_sales(historical_peak + timedelta(days=offset), 25))

    multipliers = build_holiday_multipliers(
        history_rows=rows,
        holidays=[
            _holiday("mothers-2026", "Mothers Day", historical_peak, mult="1.1"),
            _holiday("mothers-2026-next", "Mothers Day", future_peak, mult="1.1"),
        ],
        country_code="US",
        today=today,
        horizon_days=14,
    )

    assert multipliers is not None
    # 5/24-5/26 使用历史观测 25 / 10 = 2.5,覆盖配置中的 1.1。
    assert multipliers[6] == pytest.approx(2.5)
    assert multipliers[7] == pytest.approx(2.5)
    assert multipliers[8] == pytest.approx(2.5)
    assert multipliers[0] == pytest.approx(1.0)


def test_future_holiday_falls_back_to_configured_multiplier() -> None:
    today = date(2026, 5, 18)

    multipliers = build_holiday_multipliers(
        history_rows=[],
        holidays=[_holiday("prime-2026", "Prime Day", date(2026, 5, 20), mult="1.4")],
        country_code="US",
        today=today,
        horizon_days=5,
    )

    assert multipliers is not None
    assert multipliers[1] == pytest.approx(1.4)
    assert multipliers[2] == pytest.approx(1.4)
    assert multipliers[3] == pytest.approx(1.4)
