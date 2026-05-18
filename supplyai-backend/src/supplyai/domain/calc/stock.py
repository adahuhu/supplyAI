"""库存聚合模块 — 纯函数.

公式(数据表设计 §4.7):
  fba_inbound = working + shipped + receiving
  total_stock = fba_available + fba_inbound + local_actual + local_plan
  sellable_days = total_stock / forecast_daily(daily=0 → None)

fba_reserved 仅展示,不进 total_stock。
"""
from __future__ import annotations

from dataclasses import dataclass

from supplyai.domain.calc.rules import DEFAULT_STOCK_SCOPE, normalize_stock_scope


def _z(v: int | None) -> int:
    return v or 0


@dataclass
class StockBreakdown:
    fba_available: int
    fba_inbound: int  # working + shipped + receiving
    local_actual: int
    local_plan: int
    total_stock: int


def fba_inbound_total(
    working: int | None, shipped: int | None, receiving: int | None
) -> int:
    return _z(working) + _z(shipped) + _z(receiving)


def aggregate_stock(
    *,
    fba_available: int | None,
    fba_inbound_working: int | None,
    fba_inbound_shipped: int | None,
    fba_inbound_receiving: int | None,
    local_actual: int | None,
    local_plan: int | None,
    fba_reserved: int | None = None,  # noqa: ARG001 — 不参与合计,签名保留以记录契约
) -> StockBreakdown:
    inbound = fba_inbound_total(
        fba_inbound_working, fba_inbound_shipped, fba_inbound_receiving
    )
    available = _z(fba_available)
    la = _z(local_actual)
    lp = _z(local_plan)
    return StockBreakdown(
        fba_available=available,
        fba_inbound=inbound,
        local_actual=la,
        local_plan=lp,
        total_stock=available + inbound + la + lp,
    )


def sellable_days(*, stock: int | float, daily: int | float) -> float | None:
    """可售天数. daily=0 时返回 None(前端按 ∞/- 展示)."""
    if daily == 0:
        return None
    return float(stock) / float(daily)


def participating_stock(
    stock: StockBreakdown, scope: object = DEFAULT_STOCK_SCOPE
) -> int:
    """按规则配置计算参与备货判断的库存量."""
    total = 0
    for item in normalize_stock_scope(scope):
        if item == "fba_available":
            total += stock.fba_available
        elif item == "fba_inbound":
            total += stock.fba_inbound
        elif item == "local_actual":
            total += stock.local_actual
        elif item == "local_plan":
            total += stock.local_plan
    return total
