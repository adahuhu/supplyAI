"""Rule Resolver 单元测试 — 命中三层作用范围."""
from __future__ import annotations

import pytest

from supplyai.domain.calc.rules import (
    ReplenishmentRule,
    ResolvedRule,
    resolve_rule,
)


def _rule(
    rule_id: str,
    scope: str,
    *,
    mall_id: int | None = None,
    msku: str | None = None,
    safety_days: int = 14,
    delivery_days: int = 20,
    enabled: bool = True,
) -> ReplenishmentRule:
    return ReplenishmentRule(
        rule_id=rule_id,
        scope_type=scope,
        mall_id=mall_id,
        msku=msku,
        safety_days=safety_days,
        purchase_duration_days=0,
        delivery_days=delivery_days,
        qc_days=0,
        enabled=enabled,
    )


def test_resolve_no_rules_returns_default() -> None:
    """完全没有规则时,返回内置默认值."""
    out = resolve_rule(rules=[], mall_id=1001, msku="MSKU-X")
    assert isinstance(out, ResolvedRule)
    assert out.scope_type == "default"
    assert out.safety_days == 14
    assert out.lead_time_days == 20  # default
    assert out.rule_id is None


def test_resolve_global_only() -> None:
    rules = [_rule("r-global", "global", safety_days=7, delivery_days=15)]
    out = resolve_rule(rules=rules, mall_id=1001, msku="MSKU-X")
    assert out.rule_id == "r-global"
    assert out.scope_type == "global"
    assert out.safety_days == 7
    assert out.lead_time_days == 15


def test_resolve_store_overrides_global() -> None:
    """store 规则优先于 global."""
    rules = [
        _rule("r-global", "global", safety_days=7),
        _rule("r-store", "store", mall_id=1001, safety_days=20),
    ]
    out = resolve_rule(rules=rules, mall_id=1001, msku="MSKU-X")
    assert out.rule_id == "r-store"
    assert out.safety_days == 20


def test_resolve_sku_overrides_store() -> None:
    """sku 规则优先级最高."""
    rules = [
        _rule("r-global", "global", safety_days=7),
        _rule("r-store", "store", mall_id=1001, safety_days=20),
        _rule("r-sku", "sku", mall_id=1001, msku="MSKU-X", safety_days=5),
    ]
    out = resolve_rule(rules=rules, mall_id=1001, msku="MSKU-X")
    assert out.rule_id == "r-sku"
    assert out.safety_days == 5


def test_resolve_skips_disabled() -> None:
    """enabled=False 不参与匹配."""
    rules = [
        _rule("r-global", "global", safety_days=7),
        _rule("r-sku", "sku", mall_id=1001, msku="MSKU-X", safety_days=5, enabled=False),
    ]
    out = resolve_rule(rules=rules, mall_id=1001, msku="MSKU-X")
    assert out.rule_id == "r-global"
    assert out.safety_days == 7


def test_resolve_store_only_matches_correct_mall() -> None:
    """store 规则只对该店铺生效."""
    rules = [_rule("r-store-1001", "store", mall_id=1001, safety_days=20)]
    out = resolve_rule(rules=rules, mall_id=1002, msku="MSKU-X")
    assert out.rule_id is None  # 没匹配,fallback 默认
    assert out.scope_type == "default"


def test_resolve_lead_time_sums_components() -> None:
    """lead_time_days = purchase_duration + delivery + qc."""
    rule = ReplenishmentRule(
        rule_id="r-x",
        scope_type="global",
        mall_id=None,
        msku=None,
        safety_days=10,
        purchase_duration_days=5,
        delivery_days=20,
        qc_days=3,
        enabled=True,
    )
    out = resolve_rule(rules=[rule], mall_id=1001, msku="MSKU-X")
    assert out.lead_time_days == 28
