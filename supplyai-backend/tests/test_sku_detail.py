"""SKU 详情 API 测试 — POST /skus/detail."""
from __future__ import annotations

from httpx import AsyncClient


async def _pick_listing_id(client: AsyncClient, **filters) -> int:
    """从列表接口取一个真实的 listing_id 用于详情查询."""
    payload = {"tenant_id": 100228, "page_size": 1, **filters}
    resp = await client.post("/api/supplyai/skus/list", json=payload)
    assert resp.status_code == 200
    rows = resp.json()["rows"]
    assert rows, "list 接口必须先有数据"
    return rows[0]["id"]


async def test_skus_detail_returns_summary_fields(client: AsyncClient) -> None:
    """详情包含核心 summary 字段."""
    listing_id = await _pick_listing_id(client)
    response = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "summary" in data
    assert data["summary"]["id"] == listing_id


async def test_skus_detail_includes_forecast_trend(client: AsyncClient) -> None:
    """详情含未来逐日预测序列(seed 含 45 天)."""
    listing_id = await _pick_listing_id(client)
    response = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    data = response.json()
    assert "forecast_trend" in data
    assert isinstance(data["forecast_trend"], list)
    assert len(data["forecast_trend"]) >= 30  # 至少 30 天
    point = data["forecast_trend"][0]
    assert "date" in point and "qty" in point


async def test_skus_detail_includes_inbound_list(client: AsyncClient) -> None:
    """详情含本地侧在途列表(允许为空)."""
    listing_id = await _pick_listing_id(client)
    response = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    data = response.json()
    assert "inbound_list" in data
    assert isinstance(data["inbound_list"], list)


async def test_skus_detail_expands_fba_inbound_breakdown(
    client: AsyncClient,
) -> None:
    """FBA 在途库存应能展开为 working/shipped/receiving 明细."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 48},
    )
    assert response.status_code == 200
    row = next(r for r in response.json()["rows"] if (r.get("fba_inbound") or 0) > 0)

    detail = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": row["id"]},
    )
    assert detail.status_code == 200, detail.text
    inbound = detail.json()["inbound_list"]
    assert any(
        item["inbound_type"].startswith("fba_") for item in inbound
    ), "FBA 平台在途需要拆成可展示明细"


async def test_skus_detail_calc_run_id_consistent(client: AsyncClient) -> None:
    """详情各部分 calc_run_id 一致."""
    listing_id = await _pick_listing_id(client)
    response = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    data = response.json()
    assert data["calc_run_id"] == "DEMO-20260509-080000"
    assert data["summary"]["calc_run_id"] == "DEMO-20260509-080000"


async def test_skus_detail_returns_404_for_unknown_listing(client: AsyncClient) -> None:
    """未知 listing_id 返回 404."""
    response = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": 99999999},
    )
    assert response.status_code == 404
    body = response.json()
    assert body["detail"]["code"] == "SKU_NOT_FOUND"


async def test_skus_detail_includes_data_quality(client: AsyncClient) -> None:
    """详情携带数据质量元信息."""
    listing_id = await _pick_listing_id(client)
    response = await client.post(
        "/api/supplyai/skus/detail",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    data = response.json()
    assert "data_quality" in data
    assert "missing_fields" in data["data_quality"]
    assert "warnings" in data["data_quality"]
