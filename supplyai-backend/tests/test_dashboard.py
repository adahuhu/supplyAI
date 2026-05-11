"""Dashboard API 端点测试 — 全部 POST."""
from __future__ import annotations

from httpx import AsyncClient


async def test_dashboard_snapshot_returns_risk_counts(client: AsyncClient) -> None:
    """POST /dashboard/snapshot 返回风险等级分布(基于 seed 数据 48 SKU)."""
    response = await client.post(
        "/api/supplyai/dashboard/snapshot",
        json={"tenant_id": 100228},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    # 与 seed 风险目标分布一致(constants.RISK_DISTRIBUTION)
    assert data["risk_counts"] == {"p1": 12, "p2": 14, "p3": 12, "safe": 10}


async def test_dashboard_snapshot_returns_calc_run_id(client: AsyncClient) -> None:
    """快照必带 calc_run_id 用于一致性追踪."""
    response = await client.post(
        "/api/supplyai/dashboard/snapshot",
        json={"tenant_id": 100228},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["calc_run_id"] == "DEMO-20260509-080000"


async def test_dashboard_snapshot_returns_suggest_summary(client: AsyncClient) -> None:
    """快照包含建议采购合计字段."""
    response = await client.post(
        "/api/supplyai/dashboard/snapshot",
        json={"tenant_id": 100228},
    )
    assert response.status_code == 200
    data = response.json()
    # seed 中 48 SKU,40 个建议采购,总量 30315
    assert data["suggest_sku_count"] == 40
    assert data["suggest_total_qty"] == 30315
    assert data["stockout_7_count"] == 12  # P1 数量
    # 多币种结构
    amount = data["suggest_total_amount"]
    assert amount["base"]["currency"] == "USD"
    assert amount["base"]["amount"] > 0
    assert isinstance(amount["by_currency"], list)
