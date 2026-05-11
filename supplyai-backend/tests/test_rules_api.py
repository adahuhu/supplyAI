"""规则 API 测试 — POST /rules/*."""
from __future__ import annotations

from httpx import AsyncClient


async def test_list_rules_returns_seeded_rows(client: AsyncClient) -> None:
    """seed 已写入 4 条全局规则,这里至少能查到."""
    resp = await client.post(
        "/api/supplyai/rules/list",
        json={"tenant_id": 100228},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "rows" in data
    assert data["total"] >= 1


async def test_list_rules_filters_by_scope(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/rules/list",
        json={"tenant_id": 100228, "scope_types": ["global"]},
    )
    rows = resp.json()["rows"]
    for r in rows:
        assert r["scope_type"] == "global"


async def test_upsert_creates_new_rule(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/rules/upsert",
        json={
            "tenant_id": 100228,
            "scope_type": "store",
            "mall_id": 1001,
            "safety_days": 21,
            "purchase_duration_days": 5,
            "delivery_days": 25,
            "qc_days": 3,
            "enabled": True,
            "updated_by": "tester",
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["rule_id"].startswith("RULE-")
    assert data["scope_type"] == "store"
    assert data["safety_days"] == 21


async def test_upsert_updates_existing_rule(client: AsyncClient) -> None:
    create = await client.post(
        "/api/supplyai/rules/upsert",
        json={
            "tenant_id": 100228,
            "scope_type": "store",
            "mall_id": 1002,
            "safety_days": 14,
        },
    )
    rule_id = create.json()["rule_id"]

    update = await client.post(
        "/api/supplyai/rules/upsert",
        json={
            "tenant_id": 100228,
            "rule_id": rule_id,
            "scope_type": "store",
            "mall_id": 1002,
            "safety_days": 30,
        },
    )
    assert update.status_code == 200
    data = update.json()
    assert data["rule_id"] == rule_id
    assert data["safety_days"] == 30


async def test_upsert_sku_scope_requires_mall_and_msku(client: AsyncClient) -> None:
    """sku 范围必须同时给 mall_id + msku."""
    resp = await client.post(
        "/api/supplyai/rules/upsert",
        json={
            "tenant_id": 100228,
            "scope_type": "sku",
            "mall_id": 1001,
            # 缺 msku
            "safety_days": 5,
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "RULE_INVALID_SCOPE"


async def test_disable_rule(client: AsyncClient) -> None:
    """禁用规则后,list 默认仍能查到(enabled 字段标 false)."""
    create = await client.post(
        "/api/supplyai/rules/upsert",
        json={
            "tenant_id": 100228,
            "scope_type": "store",
            "mall_id": 1003,
            "safety_days": 14,
        },
    )
    rule_id = create.json()["rule_id"]

    resp = await client.post(
        "/api/supplyai/rules/disable",
        json={"tenant_id": 100228, "rule_id": rule_id},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
