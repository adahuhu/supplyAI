"""POST /dashboard/filters — 顶部过滤器选项 + 计数."""
from __future__ import annotations

from httpx import AsyncClient


async def test_filters_returns_stores_countries_owners(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/filters", json={"tenant_id": 100228}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "stores" in data
    assert "countries" in data
    assert "owners" in data


async def test_filters_stores_match_seed_six(client: AsyncClient) -> None:
    """seed 6 个店铺,应该都返回."""
    resp = await client.post(
        "/api/supplyai/dashboard/filters", json={"tenant_id": 100228}
    )
    stores = resp.json()["stores"]
    assert len(stores) == 6
    # 每项必须有 value/label/count
    for s in stores:
        assert s["value"]
        assert s["label"]
        assert s["count"] > 0


async def test_filters_countries_match_seed_six(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/filters", json={"tenant_id": 100228}
    )
    countries = resp.json()["countries"]
    codes = sorted(c["value"] for c in countries)
    assert codes == ["CA", "DE", "FR", "JP", "UK", "US"]


async def test_filters_total_count_consistent_with_list(
    client: AsyncClient,
) -> None:
    """所有 stores 的 count 加起来应等于列表总数 48."""
    resp = await client.post(
        "/api/supplyai/dashboard/filters", json={"tenant_id": 100228}
    )
    total_by_store = sum(s["count"] for s in resp.json()["stores"])
    assert total_by_store == 48


async def test_filters_includes_brands_and_categories(client: AsyncClient) -> None:
    """seed 4 个品牌(NORDIC/AURORA/SAKURA/MOMENT) + 多个分类."""
    resp = await client.post(
        "/api/supplyai/dashboard/filters", json={"tenant_id": 100228}
    )
    data = resp.json()
    assert "brands" in data
    assert "categories" in data
    assert len(data["brands"]) >= 1
    assert len(data["categories"]) >= 1
    for b in data["brands"]:
        assert b["count"] > 0
    for c in data["categories"]:
        assert c["count"] > 0
