"""采购草稿 API 测试 — POST /purchase/draft/*."""
from __future__ import annotations

from httpx import AsyncClient


async def _pick_suggest_sku(client: AsyncClient) -> dict:
    """从列表挑一个 suggest=true 的 SKU."""
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "suggest_only": True, "page_size": 1},
    )
    rows = resp.json()["rows"]
    assert rows, "需要至少一个 suggest 行"
    return rows[0]


# ============ Create ============


async def test_create_draft_from_sku_suggestion(client: AsyncClient) -> None:
    sku = await _pick_suggest_sku(client)
    resp = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": sku["calc_run_id"],
            "items": [
                {
                    "mall_id": sku["mall_id"],
                    "msku": sku["msku"],
                    "sku": sku["sku"],
                    "suggest_qty": sku["suggest_qty"],
                    "supplier_name": "默认供应商",
                }
            ],
        },
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["created_count"] == 1
    assert len(data["draft_ids"]) == 1
    assert data["draft_ids"][0].startswith("DRAFT-")


async def test_create_draft_batch(client: AsyncClient) -> None:
    """一次创建多个."""
    list_resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "suggest_only": True, "page_size": 3},
    )
    rows = list_resp.json()["rows"]

    items = [
        {
            "mall_id": r["mall_id"],
            "msku": r["msku"],
            "sku": r["sku"],
            "suggest_qty": r["suggest_qty"],
        }
        for r in rows
    ]
    resp = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": rows[0]["calc_run_id"],
            "items": items,
        },
    )
    assert resp.status_code == 200
    assert resp.json()["created_count"] == len(items)


async def test_create_draft_rejects_zero_qty(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "items": [{"msku": "X", "suggest_qty": 0}],
        },
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "INVALID_DRAFT_QTY"


# ============ List ============


async def test_list_drafts_filters_by_status(client: AsyncClient) -> None:
    sku = await _pick_suggest_sku(client)
    await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": sku["calc_run_id"],
            "items": [
                {
                    "msku": sku["msku"],
                    "mall_id": sku["mall_id"],
                    "suggest_qty": sku["suggest_qty"],
                }
            ],
        },
    )
    resp = await client.post(
        "/api/supplyai/purchase/draft/list",
        json={"tenant_id": 100228, "statuses": ["draft"], "page_size": 50},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["total"] >= 1
    assert all(r["status"] == "draft" for r in data["rows"])


# ============ Detail ============


async def test_detail_returns_draft(client: AsyncClient) -> None:
    sku = await _pick_suggest_sku(client)
    create = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": sku["calc_run_id"],
            "items": [
                {
                    "msku": sku["msku"],
                    "mall_id": sku["mall_id"],
                    "suggest_qty": sku["suggest_qty"],
                }
            ],
        },
    )
    draft_id = create.json()["draft_ids"][0]

    resp = await client.post(
        "/api/supplyai/purchase/draft/detail",
        json={"tenant_id": 100228, "draft_id": draft_id},
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["draft_id"] == draft_id
    assert data["msku"] == sku["msku"]
    assert data["status"] == "draft"


async def test_detail_404_for_unknown(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/purchase/draft/detail",
        json={"tenant_id": 100228, "draft_id": "nonexistent"},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "DRAFT_NOT_FOUND"


# ============ State machine: confirm / redirect ============


async def test_confirm_transitions_draft_to_confirmed(client: AsyncClient) -> None:
    sku = await _pick_suggest_sku(client)
    create = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": sku["calc_run_id"],
            "items": [
                {
                    "msku": sku["msku"],
                    "mall_id": sku["mall_id"],
                    "suggest_qty": sku["suggest_qty"],
                }
            ],
        },
    )
    draft_id = create.json()["draft_ids"][0]
    resp = await client.post(
        "/api/supplyai/purchase/draft/confirm",
        json={"tenant_id": 100228, "draft_id": draft_id},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "confirmed"


async def test_confirm_rejects_non_draft(client: AsyncClient) -> None:
    """已 confirmed 的不能再 confirm."""
    sku = await _pick_suggest_sku(client)
    create = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": sku["calc_run_id"],
            "items": [
                {
                    "msku": sku["msku"],
                    "mall_id": sku["mall_id"],
                    "suggest_qty": sku["suggest_qty"],
                }
            ],
        },
    )
    draft_id = create.json()["draft_ids"][0]
    await client.post(
        "/api/supplyai/purchase/draft/confirm",
        json={"tenant_id": 100228, "draft_id": draft_id},
    )
    resp = await client.post(
        "/api/supplyai/purchase/draft/confirm",
        json={"tenant_id": 100228, "draft_id": draft_id},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "DRAFT_INVALID_TRANSITION"


async def test_redirect_works_from_any_active_state(client: AsyncClient) -> None:
    """draft 与 confirmed 都可以 redirect."""
    sku = await _pick_suggest_sku(client)
    create = await client.post(
        "/api/supplyai/purchase/draft/create",
        json={
            "tenant_id": 100228,
            "calc_run_id": sku["calc_run_id"],
            "items": [
                {
                    "msku": sku["msku"],
                    "mall_id": sku["mall_id"],
                    "suggest_qty": sku["suggest_qty"],
                }
            ],
        },
    )
    draft_id = create.json()["draft_ids"][0]
    resp = await client.post(
        "/api/supplyai/purchase/draft/redirect",
        json={"tenant_id": 100228, "draft_id": draft_id},
    )
    assert resp.status_code == 200
    assert resp.json()["status"] == "redirected"
