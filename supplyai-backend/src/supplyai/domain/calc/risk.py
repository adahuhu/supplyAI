"""Risk 分类模块.

阈值(默认):
  p1 ≤ 7 天   — 紧急
  p2 (7, 15]  — 关注
  p3 (15, 30] — 计划
  safe > 30   — 安全(含无需求 None)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import date, timedelta
from typing import Literal

Priority = Literal["p1", "p2", "p3", "safe"]


@dataclass(frozen=True)
class RiskThresholds:
    p1_max: float = 7
    p2_max: float = 15
    p3_max: float = 30


DEFAULT_THRESHOLDS = RiskThresholds()


def classify_risk(
    *,
    fba_sellable_days: float | None,
    thresholds: RiskThresholds = DEFAULT_THRESHOLDS,
) -> Priority:
    if fba_sellable_days is None:
        return "safe"
    if fba_sellable_days <= thresholds.p1_max:
        return "p1"
    if fba_sellable_days <= thresholds.p2_max:
        return "p2"
    if fba_sellable_days <= thresholds.p3_max:
        return "p3"
    return "safe"


def compute_stockout_date(
    *, today: date, fba_sellable_days: float | None
) -> date | None:
    if fba_sellable_days is None:
        return None
    return today + timedelta(days=int(fba_sellable_days))
