"""POST /dashboard/holidays — 节日色带配置."""
from __future__ import annotations

from httpx import AsyncClient


async def test_holidays_returns_list(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/holidays", json={"tenant_id": 100228}
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "holidays" in data
    assert isinstance(data["holidays"], list)


async def test_holidays_each_has_required_fields(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/dashboard/holidays", json={"tenant_id": 100228}
    )
    holidays = resp.json()["holidays"]
    if not holidays:
        return  # 允许空列表(无节日数据时)
    for h in holidays:
        assert h["id"]
        assert h["name"]
        assert h["peak_date"]  # YYYY-MM-DD
        assert "days_before" in h
        assert "days_after" in h
        assert h["sales_multiplier"] > 0


async def test_holidays_seed_has_at_least_one(client: AsyncClient) -> None:
    """seed 应有至少一个节日(Mother's Day 2026-05-11)."""
    resp = await client.post(
        "/api/supplyai/dashboard/holidays", json={"tenant_id": 100228}
    )
    holidays = resp.json()["holidays"]
    assert len(holidays) >= 1
