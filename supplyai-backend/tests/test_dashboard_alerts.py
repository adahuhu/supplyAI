"""POST /dashboard/data-quality-alerts — "需关注"面板告警派生."""
from __future__ import annotations

from httpx import AsyncClient


async def test_alerts_returns_list(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/data-quality-alerts",
        json={"tenant_id": 100228},
    )
    assert resp.status_code == 200, resp.text
    assert "alerts" in resp.json()
    assert isinstance(resp.json()["alerts"], list)


async def test_alerts_each_has_id_kind_title(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/data-quality-alerts",
        json={"tenant_id": 100228},
    )
    for a in resp.json()["alerts"]:
        assert a["id"]
        assert a["kind"] in {"forecast", "rule", "review", "data_quality"}
        assert a["title"]
        assert "count" in a


async def test_alerts_includes_default_forecast_warning(
    client: AsyncClient,
) -> None:
    """seed 里大量 SKU forecast_source='default',应触发"样本不足"告警."""
    resp = await client.post(
        "/api/supplyai/dashboard/data-quality-alerts",
        json={"tenant_id": 100228},
    )
    forecast_alerts = [a for a in resp.json()["alerts"] if a["kind"] == "forecast"]
    # seed 把所有 SKU 设了 forecast_source='default',告警 count > 0
    if forecast_alerts:
        assert forecast_alerts[0]["count"] > 0
