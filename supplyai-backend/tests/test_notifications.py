from __future__ import annotations

from datetime import date

import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_dingtalk_preview_returns_boss_daily_report(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/notifications/dingtalk/preview",
        json={
            "tenant_id": 100228,
            "role": "boss",
            "detail_url": "https://example.com/SupplyAI.html",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "boss"
    assert body["title"] == f"SupplyAI 每日经营简报｜{date.today().isoformat()}"
    assert body["dingtalk_payload"]["msgtype"] == "actionCard"
    assert body["markdown"].startswith("## 🔎 SupplyAI 每日经营简报")
    assert "核心经营速览" in body["markdown"]
    assert "今日风险概览" in body["markdown"]
    assert "近 7 天畅销 SKU Top 3" in body["markdown"]
    assert "优先处理 SKU" not in body["markdown"]
    assert "操作建议" not in body["markdown"]
    assert "一句话总结" in body["markdown"]
    assert body["report"]["top_skus"]
    assert body["report"]["top_skus"][0]["store_name"]
    assert body["report"]["focus_skus"][0]["store_name"]
    assert "| 指标 | 数值 | 状态 |" not in body["markdown"]
    assert "商品:" in body["markdown"]
    assert "可售天数:" not in body["markdown"]
    assert "建议采购量" not in body["markdown"]
    assert "预计采购金额" not in body["markdown"]
    assert "需要我帮你" not in body["markdown"]
    assert "短期（今天-7天）" in body["markdown"]
    assert "中期（1-4周）" in body["markdown"]
    assert "长期（1-3月）" in body["markdown"]
    assert body["markdown"].count("近 7 天销量:") == 3
    assert body["markdown"].count("查看分析工作台") == 0
    assert body["dingtalk_payload"]["actionCard"]["singleTitle"] == "了解详情"
    assert "ai=1" in body["dingtalk_payload"]["actionCard"]["singleURL"]
    assert body["report"]["risk"]["risk_sku_count"] >= body["report"]["risk"]["p1_count"]


@pytest.mark.asyncio
async def test_dingtalk_preview_operator_scope_is_filtered(client: AsyncClient) -> None:
    filters = await client.post(
        "/api/supplyai/dashboard/filters",
        json={"tenant_id": 100228},
    )
    assert filters.status_code == 200
    owners = filters.json()["owners"]
    assert owners
    owner = owners[0]["value"]

    resp = await client.post(
        "/api/supplyai/notifications/dingtalk/preview",
        json={
            "tenant_id": 100228,
            "role": "operator",
            "owners": [owner],
            "target_name": owner,
            "detail_url": "https://example.com/SupplyAI.html?page=list",
        },
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["role"] == "operator"
    assert owner in body["report"]["scope_label"]
    assert "page=list" in body["detail_url"]
    assert "ai=1" in body["detail_url"]


@pytest.mark.asyncio
async def test_dingtalk_send_without_webhook_is_simulated(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/notifications/dingtalk/send",
        json={"tenant_id": 100228, "role": "boss"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "simulated"
    assert body["provider_response"]["simulated"] is True


@pytest.mark.asyncio
async def test_dingtalk_card_svg_renders_report_card(client: AsyncClient) -> None:
    resp = await client.get(
        "/api/supplyai/notifications/dingtalk/card.svg",
        params={"tenant_id": 100228, "role": "boss"},
    )

    assert resp.status_code == 200
    assert resp.headers["content-type"].startswith("image/svg+xml")
    assert "<svg" in resp.text
    assert "SupplyAI 每日经营简报" in resp.text
    assert "近 7 天畅销 SKU" in resp.text
