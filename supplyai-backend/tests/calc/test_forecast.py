"""Forecast 模块单元测试 — 纯函数,无 DB."""
from __future__ import annotations

from datetime import date
from decimal import Decimal

import pytest

from supplyai.domain.calc.forecast import (
    ForecastInput,
    ForecastOutput,
    compute_forecast,
    moving_average,
    project_series,
)


def test_moving_average_simple_window() -> None:
    """7 日均值 = sum(last_7)/7."""
    history = [10, 10, 10, 10, 10, 10, 10]
    assert moving_average(history, window=7) == pytest.approx(10.0)


def test_moving_average_skips_zero_pad_when_short() -> None:
    """历史不足 window 时按实际长度计算,不补零."""
    history = [20, 30]
    assert moving_average(history, window=7) == pytest.approx(25.0)


def test_moving_average_empty_returns_zero() -> None:
    assert moving_average([], window=7) == 0.0


def test_project_series_constant() -> None:
    """forecast_daily 恒定时,序列每天都是该值."""
    points = project_series(
        start_date=date(2026, 5, 10),
        days=3,
        daily_qty=12.5,
    )
    assert len(points) == 3
    assert points[0].forecast_date == date(2026, 5, 10)
    assert points[0].forecast_qty == pytest.approx(12.5)
    assert points[2].forecast_date == date(2026, 5, 12)


def test_project_series_with_seasonal_multiplier() -> None:
    """传入 multiplier 序列时按位相乘."""
    points = project_series(
        start_date=date(2026, 5, 10),
        days=3,
        daily_qty=10.0,
        multipliers=[1.0, 1.5, 2.0],
    )
    assert points[0].forecast_qty == pytest.approx(10.0)
    assert points[1].forecast_qty == pytest.approx(15.0)
    assert points[2].forecast_qty == pytest.approx(20.0)
    assert points[1].sales_multiplier == pytest.approx(1.5)


def test_compute_forecast_default_uses_7d_avg() -> None:
    """默认策略: last_7d 均值,无 fixed/dynamic 规则."""
    out = compute_forecast(
        ForecastInput(
            history=[20, 30, 25, 28, 22, 31, 26],  # 最近 7 天 → avg ≈ 26
            today=date(2026, 5, 10),
            horizon_days=3,
        )
    )
    assert out.forecast_daily == pytest.approx(26.0, rel=0.05)
    assert out.forecast_source == "default"
    assert len(out.series) == 3


def test_compute_forecast_fixed_rule_overrides() -> None:
    """fixed 规则直接锁定 forecast_daily,不用历史."""
    out = compute_forecast(
        ForecastInput(
            history=[1, 1, 1, 1, 1, 1, 1],
            today=date(2026, 5, 10),
            horizon_days=2,
            fixed_daily=50.0,
        )
    )
    assert out.forecast_daily == 50.0
    assert out.forecast_source == "fixed"
    assert out.series[0].forecast_qty == pytest.approx(50.0)


def test_compute_forecast_dynamic_multiplier() -> None:
    """dynamic 规则: 在历史均值基础上叠加节日乘数."""
    out = compute_forecast(
        ForecastInput(
            history=[10] * 7,
            today=date(2026, 5, 10),
            horizon_days=3,
            seasonal_multipliers=[1.0, 2.0, 3.0],
        )
    )
    assert out.forecast_source == "dynamic"
    assert out.series[1].forecast_qty == pytest.approx(20.0)
    assert out.series[2].forecast_qty == pytest.approx(30.0)
    assert out.series[2].sales_multiplier == pytest.approx(3.0)
    # forecast_daily 取窗口均值 (10+20+30)/3 = 20
    assert out.forecast_daily == pytest.approx(20.0)


def test_compute_forecast_no_history_returns_zero() -> None:
    out = compute_forecast(
        ForecastInput(history=[], today=date(2026, 5, 10), horizon_days=3)
    )
    assert out.forecast_daily == 0.0
    assert out.forecast_source == "default"
    assert all(p.forecast_qty == 0 for p in out.series)


def test_compute_forecast_denoise_drops_outliers() -> None:
    """denoise 模式: 去掉超过 3σ 的尖峰再求均值."""
    history = [10, 10, 10, 10, 10, 10, 10, 10, 200]  # 9 项,200 是噪声
    out = compute_forecast(
        ForecastInput(
            history=history,
            today=date(2026, 5, 10),
            horizon_days=2,
            denoise=True,
        )
    )
    # 去掉 200 后均值仍约 10
    assert out.forecast_daily == pytest.approx(10.0, abs=2.0)
    assert out.forecast_source == "denoised"
