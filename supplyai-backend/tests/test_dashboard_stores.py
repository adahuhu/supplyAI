"""POST /dashboard/stores — 侧栏"店铺空间"风险摘要."""
from __future__ import annotations

from httpx import AsyncClient


async def test_stores_returns_six_seeded_stores(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/stores", json={"tenant_id": 100228}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "rows" in data
    assert len(data["rows"]) == 6


async def test_stores_each_row_has_required_fields(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/stores", json={"tenant_id": 100228}
    )
    rows = resp.json()["rows"]
    for r in rows:
        assert "mall_id" in r
        assert "mall_name" in r
        assert "country_code" in r
        assert "sku_count" in r
        assert "p1_count" in r
        assert "p2_count" in r
        assert "p3_count" in r
        assert "safe_count" in r
        # 总数 = 各风险级合计
        assert r["sku_count"] == r["p1_count"] + r["p2_count"] + r["p3_count"] + r["safe_count"]


async def test_stores_total_sku_count_matches_list_total(
    client: AsyncClient,
) -> None:
    """所有店铺 sku_count 加起来 = 列表总数 48."""
    resp = await client.post(
        "/api/supplyai/dashboard/stores", json={"tenant_id": 100228}
    )
    total = sum(r["sku_count"] for r in resp.json()["rows"])
    assert total == 48


async def test_stores_p1_total_matches_dashboard_p1(
    client: AsyncClient,
) -> None:
    """所有店铺 p1_count 合计 = dashboard.snapshot.risk_counts.p1."""
    snap = await client.post(
        "/api/supplyai/dashboard/snapshot", json={"tenant_id": 100228}
    )
    expected = snap.json()["risk_counts"]["p1"]

    stores = await client.post(
        "/api/supplyai/dashboard/stores", json={"tenant_id": 100228}
    )
    actual = sum(r["p1_count"] for r in stores.json()["rows"])
    assert actual == expected
