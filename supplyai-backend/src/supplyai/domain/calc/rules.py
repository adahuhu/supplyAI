"""Rule Resolver — 三层作用范围匹配纯函数.

scope_type 优先级: sku > store > global > default
lead_time_days = purchase_duration + delivery + qc + max(logistics_days)
"""
from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime

StockScopeItem = str

DEFAULT_STOCK_SCOPE: tuple[StockScopeItem, ...] = ("fba_available",)
VALID_STOCK_SCOPE: tuple[StockScopeItem, ...] = (
    "fba_available",
    "fba_inbound",
    "local_actual",
    "local_plan",
)


@dataclass(frozen=True)
class ReplenishmentRule:
    """对应 mk_replenishment_rule ORM 的纯数据形态."""

    rule_id: str
    scope_type: str  # global / store / sku
    mall_id: int | None
    msku: str | None
    safety_days: int
    purchase_duration_days: int
    delivery_days: int
    qc_days: int
    enabled: bool
    logistics_days: tuple[int, ...] = ()
    stock_scope: tuple[StockScopeItem, ...] = DEFAULT_STOCK_SCOPE
    updated_at: datetime | None = None


@dataclass
class ResolvedRule:
    rule_id: str | None  # None = 默认兜底
    scope_type: str  # sku / store / global / default
    safety_days: int
    lead_time_days: int
    stock_scope: tuple[StockScopeItem, ...] = DEFAULT_STOCK_SCOPE


_SCOPE_PRIORITY = {"sku": 3, "store": 2, "global": 1}

DEFAULT_SAFETY_DAYS = 14
DEFAULT_LEAD_TIME_DAYS = 20


def _updated_at_rank(rule: ReplenishmentRule) -> float:
    if rule.updated_at is None:
        return 0.0
    return rule.updated_at.timestamp()


def normalize_stock_scope(value: object) -> tuple[StockScopeItem, ...]:
    """归一化库存参与口径;为空或非法时回到默认:仅 FBA 可用."""
    if not isinstance(value, (list, tuple)):
        return DEFAULT_STOCK_SCOPE
    out: list[StockScopeItem] = []
    for item in value:
        key = str(item or "").strip()
        if key in VALID_STOCK_SCOPE and key not in out:
            out.append(key)
    return tuple(out) or DEFAULT_STOCK_SCOPE


def _matches(rule: ReplenishmentRule, mall_id: int | None, msku: str) -> bool:
    if not rule.enabled:
        return False
    if rule.scope_type == "global":
        return True
    if rule.scope_type == "store":
        return rule.mall_id == mall_id
    if rule.scope_type == "sku":
        return rule.mall_id == mall_id and rule.msku == msku
    return False


def _lead_time(rule: ReplenishmentRule) -> int:
    logistics_days = max(rule.logistics_days, default=0)
    return (
        rule.purchase_duration_days
        + rule.delivery_days
        + rule.qc_days
        + logistics_days
    )


def resolve_rule(
    *, rules: list[ReplenishmentRule], mall_id: int | None, msku: str
) -> ResolvedRule:
    """从候选规则中按优先级挑出最具体的一条;无匹配返回默认."""
    matched = [r for r in rules if _matches(r, mall_id, msku)]
    if not matched:
        return ResolvedRule(
            rule_id=None,
            scope_type="default",
            safety_days=DEFAULT_SAFETY_DAYS,
            lead_time_days=DEFAULT_LEAD_TIME_DAYS,
            stock_scope=DEFAULT_STOCK_SCOPE,
        )
    best = max(
        matched,
        key=lambda r: (
            _SCOPE_PRIORITY.get(r.scope_type, 0),
            _updated_at_rank(r),
        ),
    )
    return ResolvedRule(
        rule_id=best.rule_id,
        scope_type=best.scope_type,
        safety_days=best.safety_days,
        lead_time_days=_lead_time(best),
        stock_scope=normalize_stock_scope(best.stock_scope),
    )
