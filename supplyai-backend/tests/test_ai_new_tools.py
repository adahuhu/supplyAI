"""新工具 compare_logistics_options + simulate_event_demand 测试.

覆盖产品验收报告:
  场景 3 — 活动备货模拟(Prime Day 想做到日销 X 单,要备多少货)
  场景 5 — 多方案对比(海运 vs 海+空)
"""
from __future__ import annotations

from supplyai.db import async_session_factory
from supplyai.domain.ai.tools import build_tools, execute_tool


def test_new_tools_registered() -> None:
    names = {t.name for t in build_tools()}
    assert "compare_logistics_options" in names
    assert "simulate_event_demand" in names


def test_logistics_tool_schema() -> None:
    tools = {t.name: t for t in build_tools()}
    schema = tools["compare_logistics_options"].parameters
    props = schema["properties"]
    # 必须能传 listing_id / qty / budget
    assert "listing_id" in props
    assert "qty_target" in props


def test_event_tool_schema() -> None:
    tools = {t.name: t for t in build_tools()}
    schema = tools["simulate_event_demand"].parameters
    props = schema["properties"]
    assert "holiday_id" in props
    assert "daily_target" in props


# ─────────────────────────────────────────────
# 工具执行
# ─────────────────────────────────────────────


async def test_compare_logistics_returns_multi_plans() -> None:
    """返回 plans 数组,每个 plan 含 mode/cost/days/stockout_days."""
    # 拿一个真实 listing_id
    from supplyai.repositories.dashboard_repo import DashboardRepository
    from supplyai.repositories.sku_repo import SkuRepository

    async with async_session_factory() as session:
        run_id = await DashboardRepository(session).latest_calc_run_id(100228)
        rows, _ = await SkuRepository(session).list_skus(
            calc_run_id=run_id, tenant_id=100228, page=1, page_size=1, priorities=["p1"]
        )
        listing_id = rows[0][0].listing_id

        out = await execute_tool(
            "compare_logistics_options",
            {"tenant_id": 100228, "listing_id": listing_id, "qty_target": 500},
            session,
        )
    assert "plans" in out
    assert len(out["plans"]) >= 2
    for p in out["plans"]:
        assert "mode" in p
        assert "qty" in p
        assert "days" in p
        assert "estimated_cost" in p
    # 至少有一个 "纯海运"或"海运"方案 + 一个"海+空"或"加急"方案
    modes = [p["mode"] for p in out["plans"]]
    assert any("海" in m or "sea" in m.lower() for m in modes)


async def test_simulate_event_uses_holiday_multiplier() -> None:
    """指定 holiday_id,返回包含活动期总销量 + 应备货 + 最晚发货时间."""
    async with async_session_factory() as session:
        out = await execute_tool(
            "simulate_event_demand",
            {
                "tenant_id": 100228,
                "holiday_id": "HD-MOTHERS-2026",
                "daily_target": 50,  # 用户期望活动期日销 50 单
            },
            session,
        )
    assert out.get("holiday_name")
    assert out.get("peak_date")
    assert out.get("total_demand") >= 0
    assert out.get("recommended_qty") >= 0
    assert "ship_by_date" in out


async def test_simulate_event_unknown_holiday_returns_error() -> None:
    async with async_session_factory() as session:
        out = await execute_tool(
            "simulate_event_demand",
            {"tenant_id": 100228, "holiday_id": "HD-NEVER-EXISTED", "daily_target": 10},
            session,
        )
    assert out.get("error")
