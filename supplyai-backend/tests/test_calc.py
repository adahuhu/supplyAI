"""计算批次端点测试 — 全部 POST."""
from __future__ import annotations

from httpx import AsyncClient


async def test_calc_latest_returns_seeded_run(client: AsyncClient) -> None:
    """POST /calc/latest 返回真实 seed 批次,而非 stub."""
    response = await client.post(
        "/api/supplyai/calc/latest",
        json={"tenant_id": 100228},
    )
    assert response.status_code == 200, response.text
    data = response.json()
    # seed 写入的批次 ID
    assert data["calc_run_id"] == "DEMO-20260509-080000"
    assert data["tenant_id"] == 100228
    assert data["status"] == "success"
    assert data["run_type"] in {"scheduled", "manual", "rule_changed"}


async def test_calc_latest_returns_404_when_no_run(client: AsyncClient) -> None:
    """没有任何 success 批次时返回 404."""
    response = await client.post(
        "/api/supplyai/calc/latest",
        json={"tenant_id": 999999},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CALC_RUN_NOT_FOUND"


async def test_calc_status_returns_run_state(client: AsyncClient) -> None:
    """POST /calc/status 查指定批次状态."""
    response = await client.post(
        "/api/supplyai/calc/status",
        json={"calc_run_id": "DEMO-20260509-080000"},
    )
    assert response.status_code == 200
    data = response.json()
    assert data["calc_run_id"] == "DEMO-20260509-080000"
    assert data["status"] == "success"
    assert data["progress"] == 100


async def test_calc_status_404_for_missing_run(client: AsyncClient) -> None:
    """查不存在批次返回 404."""
    response = await client.post(
        "/api/supplyai/calc/status",
        json={"calc_run_id": "NONEXISTENT-RUN"},
    )
    assert response.status_code == 404
    assert response.json()["detail"]["code"] == "CALC_RUN_NOT_FOUND"
