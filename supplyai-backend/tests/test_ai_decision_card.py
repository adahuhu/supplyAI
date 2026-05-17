from __future__ import annotations

import pytest
from httpx import ASGITransport, AsyncClient

from supplyai.main import app


@pytest.mark.asyncio
async def test_decision_card_rule_impact_uses_backend_calc_snapshot() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/supplyai/ai/decision-card",
            json={
                "tenant_id": 100228,
                "scenario": "rule_impact",
                "context": {"listing_id": 1000003, "target_safety_days": 21},
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "backend"
    assert body["calc_run_id"]
    card = body["card"]
    assert card["type"] == "rule_impact"
    assert card["source"] == "backend"
    assert card["scope"] == "sku"
    assert card["rows"][0]["msku"] == "MS40060"
    assert card["rows"][0]["targetSafeDays"] == 21


@pytest.mark.asyncio
async def test_decision_card_plan_comparison_binds_listing_id() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/supplyai/ai/decision-card",
            json={
                "tenant_id": 100228,
                "scenario": "plan_comparison",
                "context": {"listing_id": 1000003, "qty_target": 100},
            },
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "backend"
    assert body["calc_run_id"]
    card = body["card"]
    if body["status"] == "partial":
        assert "物流方式" in card["message"]
    else:
        assert card["type"] == "plan_comparison"
        assert card["source"] == "backend"
        assert card["scope"] == "sku"
        assert card["sku"]["msku"] == "MS40060"
        assert card["actionItems"][0]["qty"] == 100


@pytest.mark.asyncio
async def test_decision_card_risk_queue_uses_backend_rows() -> None:
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/supplyai/ai/decision-card",
            json={"tenant_id": 100228, "scenario": "risk_queue", "context": {"limit": 10}},
        )

    assert resp.status_code == 200
    body = resp.json()
    assert body["source"] == "backend"
    card = body["card"]
    assert card["type"] == "risk_queue"
    assert card["source"] == "backend"
    assert card["rows"]
    assert card["rows"][0]["listingId"]
