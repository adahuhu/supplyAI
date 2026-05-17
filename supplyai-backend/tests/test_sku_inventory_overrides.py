"""POST /api/supplyai/skus/inventory-overrides/upsert — SKU 趋势库存点位保存."""
from __future__ import annotations

from httpx import AsyncClient


async def _pick_listing_id(client: AsyncClient) -> int:
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    assert resp.status_code == 200, resp.text
    return resp.json()["rows"][0]["id"]


async def test_inventory_override_upsert_is_returned_by_trends(
    client: AsyncClient,
) -> None:
    """库存点位修改必须落后端,并随 SKU 趋势接口返回给前端恢复."""
    listing_id = await _pick_listing_id(client)

    save_resp = await client.post(
        "/api/supplyai/skus/inventory-overrides/upsert",
        json={
            "tenant_id": 100228,
            "listing_id": listing_id,
            "day_offset": 11,
            "forecast_date": "2000-01-01",
            "stock_qty": 1000,
            "updated_by": "pytest",
        },
    )
    assert save_resp.status_code == 200, save_resp.text
    saved = save_resp.json()
    assert saved["listing_id"] == listing_id
    assert saved["day_offset"] == 11
    assert saved["stock_qty"] == 1000
    assert saved["forecast_date"] != "2000-01-01"

    trends_resp = await client.post(
        "/api/supplyai/skus/trends",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    assert trends_resp.status_code == 200, trends_resp.text
    overrides = trends_resp.json()["inventory_overrides"]
    assert any(
        row["day_offset"] == 11
        and row["stock_qty"] == 1000
        and row["listing_id"] == listing_id
        for row in overrides
    )
