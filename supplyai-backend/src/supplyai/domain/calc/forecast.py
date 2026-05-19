"""销量预测模块 — 纯函数,无 DB.

输入: 历史销量序列(每日数量)、可选规则参数
输出: forecast_daily(日均预测) + 逐日序列 + 来源标签

策略:
- fixed_daily 提供 → forecast_source = "fixed"
- seasonal_multipliers 提供 → forecast_source = "dynamic"
- denoise=True → forecast_source = "denoised"
- 默认 → forecast_source = "default"(7 日窗口均值)
"""
from __future__ import annotations

import statistics
from dataclasses import dataclass, field
from datetime import date, timedelta


@dataclass
class ForecastSeriesPoint:
    forecast_date: date
    day_offset: int
    forecast_qty: float
    sales_multiplier: float = 1.0


@dataclass
class ForecastInput:
    history: list[float | int]  # 最近 N 天销量,按日期升序
    today: date
    horizon_days: int = 45
    window: int = 7  # 默认均值窗口
    fixed_daily: float | None = None  # fixed 规则
    seasonal_multipliers: list[float] | None = None  # dynamic 规则
    denoise: bool = False


@dataclass
class ForecastOutput:
    forecast_daily: float
    forecast_source: str  # fixed / dynamic / default / denoised
    series: list[ForecastSeriesPoint] = field(default_factory=list)


def moving_average(values: list[float | int], window: int) -> float:
    """末尾 window 项的均值;不足则按实际长度;空列表返回 0."""
    if not values:
        return 0.0
    tail = values[-window:]
    return sum(float(v) for v in tail) / len(tail)


def project_series(
    *,
    start_date: date,
    days: int,
    daily_qty: float,
    multipliers: list[float] | None = None,
) -> list[ForecastSeriesPoint]:
    """从 start_date 向后投影 days 天的逐日预测."""
    points: list[ForecastSeriesPoint] = []
    for i in range(days):
        m = multipliers[i] if multipliers and i < len(multipliers) else 1.0
        qty = daily_qty * m
        points.append(
            ForecastSeriesPoint(
                forecast_date=start_date + timedelta(days=i),
                day_offset=i,
                forecast_qty=qty,
                sales_multiplier=m,
            )
        )
    return points


def _denoise(values: list[float | int]) -> list[float]:
    """去掉离群尖峰 — 用中位数法,对单点突变鲁棒.

    规则: 中位数 m,去掉 v > 3*max(m,1) 的值;
    σ 法在 [10*8, 200] 这类数据上会被异常值自身撑高失效。
    """
    if len(values) < 4:
        return [float(v) for v in values]
    nums = [float(v) for v in values]
    m = statistics.median(nums)
    threshold = 3 * max(m, 1.0)
    return [v for v in nums if v <= threshold]


def compute_forecast(inp: ForecastInput) -> ForecastOutput:
    """主入口 — 派生 forecast_daily + 序列."""
    # 1. fixed 规则优先
    if inp.fixed_daily is not None:
        series = project_series(
            start_date=inp.today,
            days=inp.horizon_days,
            daily_qty=inp.fixed_daily,
        )
        return ForecastOutput(
            forecast_daily=inp.fixed_daily,
            forecast_source="fixed",
            series=series,
        )

    # 2. 历史均值(可选去噪)
    if inp.denoise:
        cleaned = _denoise(inp.history)
        base_daily = moving_average(cleaned, inp.window)
        source = "denoised"
    else:
        base_daily = moving_average(inp.history, inp.window)
        source = "default"

    # 3. 动态(节日)乘数
    if inp.seasonal_multipliers:
        series = project_series(
            start_date=inp.today,
            days=inp.horizon_days,
            daily_qty=base_daily,
            multipliers=inp.seasonal_multipliers,
        )
        # forecast_daily 取序列均值,反映乘数后的整体水平
        avg_qty = sum(p.forecast_qty for p in series) / len(series) if series else 0.0
        return ForecastOutput(
            forecast_daily=avg_qty,
            forecast_source="dynamic",
            series=series,
        )

    series = project_series(
        start_date=inp.today,
        days=inp.horizon_days,
        daily_qty=base_daily,
    )
    return ForecastOutput(
        forecast_daily=base_daily,
        forecast_source=source,
        series=series,
    )
