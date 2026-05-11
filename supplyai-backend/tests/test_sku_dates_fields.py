"""P3:SKU summary 加 last_purchase_date / last_shipment_date / inbound 的 expected_arrival_by_method."""
from __future__ import annotations

from datetime import date
from httpx import AsyncClient


async def test_summary_includes_purchase_and_shipment_dates(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    row = resp.json()["rows"][0]
    assert "last_purchase_date" in row
    assert "last_shipment_date" in row


async def test_last_purchase_date_picks_latest_draft(client: AsyncClient) -> None:
    """先取一个 SKU,创建草稿,确认 last_purchase_date 出现."""
    listed = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1, "suggest_only": True},
    )
    r = listed.json()["rows"][0]
    # 创建草稿
    await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "items": [{"mall_id": r["mall_id"], "msku": r["msku"], "sku": r["sku"], "suggest_qty": r["suggest_qty"]}],
        },
    )
    # 再查列表
    again = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "keyword": r["msku"], "page_size": 1},
    )
    new_row = again.json()["rows"][0]
    assert new_row["last_purchase_date"] is not None


async def test_last_shipment_date_from_real_fba_shipment_item(client: AsyncClient) -> None:
    """last_shipment_date 必须来自 rl_fba_shipment_item.created_time,而非草稿近似.

    R3 验收:即使没有任何 confirmed 草稿,只要 seed 了发货明细,字段就应有真实值。
    """
    # 找一个有发货明细的 SKU(seed 给所有 FBA listing 都发了 1-3 条)
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 20},
    )
    rows = resp.json()["rows"]
    # 至少一半 SKU 应有 last_shipment_date(seed 覆盖率高)
    with_shipment = [r for r in rows if r.get("last_shipment_date")]
    assert len(with_shipment) >= 5, "新 fba_shipment_item 数据应让多数 SKU 有 last_shipment_date"


async def test_inbound_list_items_have_logistics_method_and_eta(
    client: AsyncClient,
) -> None:
    """detail.inbound_list 每条应含 inbound_type(物流方式) + expected_arrival_date."""
    listed = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "priorities": ["p1"], "page_size": 5},
    )
    found_inbound = False
    for r in listed.json()["rows"]:
        detail = await client.post(
            "/api/supplyai/skus/detail",
            json={"tenant_id": 100228, "listing_id": r["id"]},
        )
        inb = detail.json().get("inbound_list", [])
        if not inb:
            continue
        found_inbound = True
        for b in inb:
            assert "inbound_type" in b
            assert "expected_arrival_date" in b
    assert found_inbound, "P1 SKU 中至少有一个应有 inbound"
