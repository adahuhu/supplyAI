"""SKU API 端点测试 — 全部 POST."""
from __future__ import annotations

from httpx import AsyncClient


async def test_skus_list_returns_paginated(client: AsyncClient) -> None:
    """POST /skus/list 返回分页结果."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page": 1, "page_size": 10},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "rows" in data
    assert "total" in data
    assert data["total"] == 48  # seed 48 SKU
    assert len(data["rows"]) == 10  # page_size


async def test_skus_list_default_sort_by_risk_then_stockout(
    client: AsyncClient,
) -> None:
    """默认排序: P1 > P2 > P3 > safe; 同档按 stockout_date 升序."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page": 1, "page_size": 48},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    # 前 12 行都是 P1
    for r in rows[:12]:
        assert r["priority"] == "p1"
    # 接下来 14 行是 P2
    for r in rows[12:26]:
        assert r["priority"] == "p2"


async def test_skus_list_filter_by_priority(client: AsyncClient) -> None:
    """按 priority 筛选."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "priorities": ["p1"], "page_size": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 12
    for r in data["rows"]:
        assert r["priority"] == "p1"


async def test_skus_list_filter_by_recent_stockout(client: AsyncClient) -> None:
    """7 天内断货筛选使用实际 FBA 断货事件,不是未来可售天数."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "stockout_within_days": 7, "page_size": 50},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["total"] == 3
    assert all(r["stockout_recent_7"] is True for r in data["rows"])


async def test_skus_list_filter_by_mall(client: AsyncClient) -> None:
    """按 mall_id 筛选."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "mall_ids": [1001], "page_size": 50},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert all(r["mall_id"] == 1001 for r in rows)


async def test_skus_list_only_returns_fba(client: AsyncClient) -> None:
    """Phase 1 只返回 FBA(数据表设计 §11)."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 50},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    for r in rows:
        assert r["delivery_method"] == "FBA"


async def test_skus_list_row_has_calc_run_id(client: AsyncClient) -> None:
    """每行返回 calc_run_id 用于一致性追踪."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert rows[0]["calc_run_id"] == "DEMO-20260509-080000"


async def test_skus_list_includes_critical_fields(client: AsyncClient) -> None:
    """返回字段覆盖列表关键列(field-mapping-v2 §2)."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    assert response.status_code == 200
    row = response.json()["rows"][0]
    expected_fields = {
        "id", "msku", "sku", "asin", "product_name",
        "store_name", "country_code", "priority", "delivery_method",
        "label_ids", "tags",
        "future_daily", "total_stock", "fba_sellable_days", "sellable_days",
        "stockout_date", "purchase_date", "suggest", "suggest_qty",
        "suggest_amount_base", "base_currency",
        "calc_run_id", "last_updated",
    }
    missing = expected_fields - set(row.keys())
    assert not missing, f"缺少字段:{missing}"
    assert row["label_ids"]
    assert row["tags"]


async def test_skus_list_has_varied_mock_tags(client: AsyncClient) -> None:
    """演示数据应有多类运营标签,避免所有 SKU 标签相同."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 48},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    label_sets = {row["label_ids"] for row in rows}
    tags = {tag for row in rows for tag in row["tags"]}
    assert len(label_sets) >= 8
    assert {"清仓", "爆款", "新品", "大促", "低库存"}.issubset(tags)


async def test_skus_list_keyword_matches_fnsku(client: AsyncClient) -> None:
    """关键字搜索应覆盖列表可见标识,包含 FNSKU."""
    first = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    assert first.status_code == 200
    fnsku = first.json()["rows"][0]["fnsku"]
    assert fnsku

    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "keyword": fnsku, "page_size": 50},
    )
    assert response.status_code == 200, response.text
    rows = response.json()["rows"]
    assert rows, f"FNSKU {fnsku} 应能搜到对应 SKU"
    assert any(r["fnsku"] == fnsku for r in rows)


async def test_skus_list_includes_financial_amount_fields(
    client: AsyncClient,
) -> None:
    """备货计划财务列需要收入、支出、成本、毛利润、毛利率字段."""
    response = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    assert response.status_code == 200
    row = response.json()["rows"][0]
    for field in ("revenue_7d", "expense_7d", "cost_7d", "gross_profit_7d", "gross_margin"):
        assert field in row
