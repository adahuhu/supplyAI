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
            "updated_by": "pytest",
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
            "updated_by": "pytest",
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
            "updated_by": "pytest",
        },
    )
    assert update.status_code == 200
    data = update.json()
    assert data["rule_id"] == rule_id
    assert data["safety_days"] == 30


async def test_upsert_reuses_existing_scope_when_rule_id_missing(
    client: AsyncClient,
) -> None:
    """前端保存同一 SKU 规则时不依赖本地 rule_id,后端按作用域覆盖."""
    body = {
        "tenant_id": 100228,
        "scope_type": "sku",
        "mall_id": 909001,
        "msku": "RULE-PERSIST-001",
        "safety_days": 18,
        "purchase_duration_days": 4,
        "delivery_days": 7,
        "qc_days": 2,
        "enabled": True,
        "updated_by": "pytest",
    }
    first = await client.post("/api/supplyai/rules/upsert", json=body)
    assert first.status_code == 200, first.text
    first_data = first.json()

    second = await client.post(
        "/api/supplyai/rules/upsert",
        json={**body, "safety_days": 33, "delivery_days": 11},
    )
    assert second.status_code == 200, second.text
    second_data = second.json()
    assert second_data["rule_id"] == first_data["rule_id"]
    assert second_data["safety_days"] == 33
    assert second_data["delivery_days"] == 11

    listed = await client.post(
        "/api/supplyai/rules/list",
        json={
            "tenant_id": 100228,
            "scope_types": ["sku"],
            "mall_id": 909001,
            "msku": "RULE-PERSIST-001",
            "enabled_only": True,
        },
    )
    assert listed.status_code == 200, listed.text
    rows = listed.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["rule_id"] == first_data["rule_id"]
    assert rows[0]["safety_days"] == 33


async def test_forecast_upsert_reuses_existing_scope_when_rule_id_missing(
    client: AsyncClient,
) -> None:
    """销量预测规则也按同一作用域覆盖,避免刷新后回显旧值."""
    body = {
        "tenant_id": 100228,
        "scope_type": "sku",
        "mall_id": 909002,
        "msku": "FORECAST-PERSIST-001",
        "forecast_mode": "dynamic",
        "weight_3d": 0,
        "weight_7d": 100,
        "weight_15d": 0,
        "weight_30d": 0,
        "denoise_enabled": False,
        "updated_by": "pytest",
    }
    first = await client.post("/api/supplyai/rules/forecast/upsert", json=body)
    assert first.status_code == 200, first.text
    first_data = first.json()

    second = await client.post(
        "/api/supplyai/rules/forecast/upsert",
        json={**body, "weight_3d": 20, "weight_7d": 80},
    )
    assert second.status_code == 200, second.text
    second_data = second.json()
    assert second_data["rule_id"] == first_data["rule_id"]
    assert second_data["weight_3d"] == 20
    assert second_data["weight_7d"] == 80

    listed = await client.post(
        "/api/supplyai/rules/forecast/list",
        json={
            "tenant_id": 100228,
            "scope_types": ["sku"],
            "mall_id": 909002,
            "msku": "FORECAST-PERSIST-001",
        },
    )
    assert listed.status_code == 200, listed.text
    rows = listed.json()["rows"]
    assert len(rows) == 1
    assert rows[0]["rule_id"] == first_data["rule_id"]
    assert rows[0]["weight_3d"] == 20


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
            "updated_by": "pytest",
        },
    )
    rule_id = create.json()["rule_id"]

    resp = await client.post(
        "/api/supplyai/rules/disable",
        json={"tenant_id": 100228, "rule_id": rule_id},
    )
    assert resp.status_code == 200
    assert resp.json()["enabled"] is False
