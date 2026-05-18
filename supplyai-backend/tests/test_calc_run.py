"""POST /calc/run — Calc Engine 端到端测试.

依赖 seed 数据: 48 FBA listings + 90 天 rl_amz_sales_daily_report.
"""
from __future__ import annotations

import math

from httpx import AsyncClient
import pytest


async def test_calc_run_creates_new_calc_run_record(client: AsyncClient) -> None:
    """POST /calc/run 返回新批次,status=success."""
    resp = await client.post(
        "/api/supplyai/calc/run",
        json={"tenant_id": 100228, "run_type": "manual"},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert data["calc_run_id"].startswith("RUN-")
    assert data["tenant_id"] == 100228
    assert data["run_type"] == "manual"
    assert data["status"] == "success"


async def test_calc_run_then_dashboard_uses_new_run(client: AsyncClient) -> None:
    """新批次跑完后,dashboard 默认应取最新 calc_run_id(就是新跑的)."""
    run_resp = await client.post(
        "/api/supplyai/calc/run",
        json={"tenant_id": 100228},
    )
    new_id = run_resp.json()["calc_run_id"]

    snap = await client.post(
        "/api/supplyai/dashboard/snapshot",
        json={"tenant_id": 100228},
    )
    assert snap.status_code == 200
    assert snap.json()["calc_run_id"] == new_id


async def test_calc_run_produces_48_snapshots(client: AsyncClient) -> None:
    """48 FBA listings → 48 snapshot 行."""
    run_resp = await client.post(
        "/api/supplyai/calc/run", json={"tenant_id": 100228}
    )
    new_id = run_resp.json()["calc_run_id"]

    list_resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "calc_run_id": new_id, "page_size": 1},
    )
    assert list_resp.json()["total"] == 48


async def test_calc_run_suggest_qty_satisfies_formula(client: AsyncClient) -> None:
    """对一个 P1 SKU,验证 suggest_qty 按规则库存参与口径扣减."""
    run_resp = await client.post(
        "/api/supplyai/calc/run", json={"tenant_id": 100228}
    )
    new_id = run_resp.json()["calc_run_id"]

    list_resp = await client.post(
        "/api/supplyai/skus/list",
        json={
            "tenant_id": 100228,
            "calc_run_id": new_id,
            "priorities": ["p1"],
            "page_size": 50,
        },
    )
    rows = list_resp.json()["rows"]
    assert rows, "至少有一个 P1 SKU"

    for row in rows:
        cov = row.get("coverage_demand")
        stock = row.get("planning_stock")
        if stock is None:
            stock = row.get("fba_available") or 0
        qty = row["suggest_qty"]
        if cov is None:
            continue
        expected = max(0, math.ceil(cov - stock))
        assert qty == expected, (
            f"SKU {row['msku']}: suggest_qty={qty} expected={expected} "
            f"(coverage={cov}, stock={stock})"
        )


async def test_calc_run_default_stock_scope_is_fba_available(
    client: AsyncClient,
) -> None:
    """默认库存参与口径为仅 FBA 可用,可售天数也使用该口径."""
    run_resp = await client.post(
        "/api/supplyai/calc/run", json={"tenant_id": 100228}
    )
    new_id = run_resp.json()["calc_run_id"]

    list_resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "calc_run_id": new_id, "page_size": 10},
    )
    for row in list_resp.json()["rows"]:
        assert row["stock_scope"] == ["fba_available"]
        assert row["planning_stock"] == (row.get("fba_available") or 0)
        daily = row.get("future_daily") or 0
        if daily > 0:
            assert row["sellable_days"] == pytest.approx(
                round(row["planning_stock"] / daily, 2),
                abs=0.02,
            )


async def test_calc_run_risk_level_matches_fba_sellable_days(
    client: AsyncClient,
) -> None:
    """随机抽 SKU 验证 risk_level 与 fba_sellable_days 阈值一致."""
    run_resp = await client.post(
        "/api/supplyai/calc/run", json={"tenant_id": 100228}
    )
    new_id = run_resp.json()["calc_run_id"]

    list_resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "calc_run_id": new_id, "page_size": 48},
    )
    for row in list_resp.json()["rows"]:
        days = row.get("fba_sellable_days")
        prio = row["priority"]
        if days is None:
            assert prio == "safe"
        elif days <= 7:
            assert prio == "p1", f"{row['msku']} days={days} → expected p1"
        elif days <= 15:
            assert prio == "p2"
        elif days <= 30:
            assert prio == "p3"
        else:
            assert prio == "safe"


async def test_calc_run_forecast_daily_average_matches_snapshot(
    client: AsyncClient,
) -> None:
    """快照里 forecast_daily ≈ avg(forecast_qty 序列),误差容忍 ±0.5."""
    run_resp = await client.post(
        "/api/supplyai/calc/run", json={"tenant_id": 100228}
    )
    new_id = run_resp.json()["calc_run_id"]

    list_resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "calc_run_id": new_id, "page_size": 5},
    )
    rows = list_resp.json()["rows"]
    for row in rows:
        if row.get("future_daily") is None:
            continue
        trends = await client.post(
            "/api/supplyai/skus/trends",
            json={
                "tenant_id": 100228,
                "calc_run_id": new_id,
                "listing_id": row["id"],
            },
        )
        forecast_pts = trends.json()["forecast"]
        if not forecast_pts:
            continue
        avg = sum(p["qty"] for p in forecast_pts) / len(forecast_pts)
        assert abs(avg - row["future_daily"]) <= 0.5, (
            f"SKU {row['msku']}: forecast_daily={row['future_daily']} "
            f"avg(series)={avg}"
        )


async def test_calc_run_404_when_no_listings(client: AsyncClient) -> None:
    """租户没有任何 listing 时返回 400 业务错(NO_LISTING)."""
    resp = await client.post(
        "/api/supplyai/calc/run", json={"tenant_id": 999999}
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "NO_LISTINGS"
