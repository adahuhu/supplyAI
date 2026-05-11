"""POST /api/supplyai/skus/trends 测试 — 详情页历史销量 + 未来预测序列."""
from __future__ import annotations

from httpx import AsyncClient


async def _pick_listing_id(client: AsyncClient) -> int:
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    return resp.json()["rows"][0]["id"]


async def test_trends_returns_history_and_forecast(client: AsyncClient) -> None:
    """返回历史 + 预测两段序列."""
    listing_id = await _pick_listing_id(client)
    resp = await client.post(
        "/api/supplyai/skus/trends",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "history" in data
    assert "forecast" in data
    assert isinstance(data["history"], list)
    assert isinstance(data["forecast"], list)


async def test_trends_history_default_window_90(client: AsyncClient) -> None:
    """默认历史窗口 90 天(seed 也是 90 天)."""
    listing_id = await _pick_listing_id(client)
    resp = await client.post(
        "/api/supplyai/skus/trends",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    history = resp.json()["history"]
    assert 80 <= len(history) <= 90
    point = history[0]
    assert "date" in point
    assert "qty" in point


async def test_trends_history_window_overridable(client: AsyncClient) -> None:
    """history_days 可缩短窗口."""
    listing_id = await _pick_listing_id(client)
    resp = await client.post(
        "/api/supplyai/skus/trends",
        json={"tenant_id": 100228, "listing_id": listing_id, "history_days": 14},
    )
    history = resp.json()["history"]
    assert len(history) <= 14


async def test_trends_forecast_uses_seeded_45(client: AsyncClient) -> None:
    """预测段使用 mk_sku_forecast_daily(seed 45 天)."""
    listing_id = await _pick_listing_id(client)
    resp = await client.post(
        "/api/supplyai/skus/trends",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    forecast = resp.json()["forecast"]
    assert 30 <= len(forecast) <= 45
    point = forecast[0]
    assert "date" in point and "qty" in point


async def test_trends_404_for_unknown_listing(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/skus/trends",
        json={"tenant_id": 100228, "listing_id": 99999999},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "SKU_NOT_FOUND"
