"""POST /api/supplyai/dashboard/risk-queue 测试."""
from __future__ import annotations

from httpx import AsyncClient


async def test_risk_queue_returns_top_n_default(client: AsyncClient) -> None:
    """默认返回 top 10 高优先级 SKU(P1 优先,然后 P2)."""
    response = await client.post(
        "/api/supplyai/dashboard/risk-queue",
        json={"tenant_id": 100228},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    assert "rows" in data
    assert len(data["rows"]) == 10
    # 默认全部应为 P1 — seed 共 12 个 P1
    for r in data["rows"]:
        assert r["priority"] == "p1"


async def test_risk_queue_supports_limit(client: AsyncClient) -> None:
    """支持自定义 limit."""
    response = await client.post(
        "/api/supplyai/dashboard/risk-queue",
        json={"tenant_id": 100228, "limit": 20},
    )
    assert response.status_code == 200
    data = response.json()
    assert len(data["rows"]) == 20
    # 前 12 个 P1,接下来 8 个 P2
    assert all(r["priority"] == "p1" for r in data["rows"][:12])
    assert all(r["priority"] == "p2" for r in data["rows"][12:20])


async def test_risk_queue_filters_by_priority(client: AsyncClient) -> None:
    """指定 priorities 时只返回筛选范围内."""
    response = await client.post(
        "/api/supplyai/dashboard/risk-queue",
        json={"tenant_id": 100228, "priorities": ["p2"], "limit": 50},
    )
    assert response.status_code == 200
    rows = response.json()["rows"]
    assert len(rows) == 14  # seed 14 P2
    for r in rows:
        assert r["priority"] == "p2"


async def test_risk_queue_each_row_has_action_hint(client: AsyncClient) -> None:
    """每行带 action_hint 字段(给前端今日动作面板用)."""
    response = await client.post(
        "/api/supplyai/dashboard/risk-queue",
        json={"tenant_id": 100228, "limit": 1},
    )
    assert response.status_code == 200
    row = response.json()["rows"][0]
    assert "action_hint" in row
    assert row["action_hint"] in {"urgent_purchase", "follow_up", "review", "ok"}


async def test_risk_queue_calc_run_id_consistent(client: AsyncClient) -> None:
    """calc_run_id 使用最新成功批次."""
    response = await client.post(
        "/api/supplyai/dashboard/risk-queue",
        json={"tenant_id": 100228, "limit": 1},
    )
    data = response.json()
    assert data["calc_run_id"] == "DEMO-20260509-080000"
    assert data["rows"][0]["calc_run_id"] == "DEMO-20260509-080000"
