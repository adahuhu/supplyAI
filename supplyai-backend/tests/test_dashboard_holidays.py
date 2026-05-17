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


async def test_holiday_upsert_then_delete_removes_from_active_list(client: AsyncClient) -> None:
    """自定义节日应支持创建/编辑/删除,删除后不再参与提醒和计算."""
    holiday_id = "custom-ui-test-2026"

    create_resp = await client.post(
        "/api/supplyai/dashboard/holidays/upsert",
        json={
            "tenant_id": 100228,
            "holiday_id": holiday_id,
            "name": "演示大促",
            "peak_date": "2026-05-20",
            "days_before": 3,
            "days_after": 2,
            "sales_multiplier": 1.8,
            "color": "#8b5cf6",
            "flag": "🎯",
            "country_code": "US",
            "enabled": True,
        },
    )
    assert create_resp.status_code == 200, create_resp.text

    update_resp = await client.post(
        "/api/supplyai/dashboard/holidays/upsert",
        json={
            "tenant_id": 100228,
            "holiday_id": holiday_id,
            "name": "演示大促更新",
            "peak_date": "2026-05-21",
            "days_before": 4,
            "days_after": 1,
            "sales_multiplier": 2.0,
            "color": "#0ea5e9",
            "flag": "🚀",
            "country_code": "US",
            "enabled": True,
        },
    )
    assert update_resp.status_code == 200, update_resp.text
    assert update_resp.json()["name"] == "演示大促更新"

    list_resp = await client.post(
        "/api/supplyai/dashboard/holidays", json={"tenant_id": 100228}
    )
    assert any(h["id"] == holiday_id for h in list_resp.json()["holidays"])

    delete_resp = await client.post(
        "/api/supplyai/dashboard/holidays/delete",
        json={"tenant_id": 100228, "holiday_id": holiday_id},
    )
    assert delete_resp.status_code == 200, delete_resp.text
    assert delete_resp.json() == {"ok": True, "holiday_id": holiday_id}

    after_resp = await client.post(
        "/api/supplyai/dashboard/holidays", json={"tenant_id": 100228}
    )
    assert all(h["id"] != holiday_id for h in after_resp.json()["holidays"])
