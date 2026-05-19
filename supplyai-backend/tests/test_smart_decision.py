"""SmartDecisionService 测试 — 分类 + 卡片 + 解释 + 退化."""
from __future__ import annotations

import asyncio
from unittest.mock import AsyncMock

import pytest

from supplyai.domain.ai.client import ChatMessage, ChatResponse
from supplyai.schemas.ai import ChatRequestMessage, SmartDecisionRequest
from supplyai.services.smart_decision_service import (
    SmartDecisionService,
    _extract_rule_impact_context,
)

TENANT = 100228


def _make_req(text: str) -> SmartDecisionRequest:
    return SmartDecisionRequest(
        tenant_id=TENANT,
        messages=[ChatRequestMessage(role="user", content=text)],
    )


class TestClassify:
    """两级分类:正则优先,LLM 兜底."""

    def test_regex_hits_risk_queue(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("哪些SKU必须补货")
        assert scenario == "risk_queue"
        assert method == "regex"

    def test_regex_hits_sales_leaders(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("我哪些产品的销量最好，应该重点推哪些SKU呢")
        assert scenario == "sales_leaders"
        assert method == "regex"

    def test_regex_hits_holiday(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("大促要备哪些货")
        assert scenario == "holiday_readiness"
        assert method == "regex"

    def test_regex_hits_plan_comparison(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("海运和空运对比")
        assert scenario == "plan_comparison"
        assert method == "regex"

    def test_regex_hits_rule_impact(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("安全天数改成21天")
        assert scenario == "rule_impact"
        assert method == "regex"

    def test_extract_rule_impact_target_days_from_followup(self):
        assert _extract_rule_impact_context("安全天数再改成15天呢") == {
            "target_safety_days": 15
        }
        assert _extract_rule_impact_context("调到18天看看") == {
            "target_safety_days": 18
        }

    def test_regex_hits_single_sku(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("挑一个高风险SKU")
        assert scenario == "single_sku_replenishment"
        assert method == "regex"

    def test_regex_misses(self):
        svc = SmartDecisionService.__new__(SmartDecisionService)
        scenario, method = svc._classify_regex("哪些货快卖完了")
        assert scenario is None

    @pytest.mark.asyncio
    async def test_llm_classify_returns_scenario(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = ChatResponse(content="risk_queue", finish_reason="stop")
        svc = SmartDecisionService.__new__(SmartDecisionService)
        svc._ai_client = mock_client
        scenario, method = await svc._classify_llm("哪些货快卖完了")
        assert scenario == "risk_queue"
        assert method == "llm"

    @pytest.mark.asyncio
    async def test_llm_classify_returns_none(self):
        mock_client = AsyncMock()
        mock_client.chat.return_value = ChatResponse(content="none", finish_reason="stop")
        svc = SmartDecisionService.__new__(SmartDecisionService)
        svc._ai_client = mock_client
        scenario, method = await svc._classify_llm("你好")
        assert scenario is None

    @pytest.mark.asyncio
    async def test_llm_classify_timeout_returns_none(self):
        mock_client = AsyncMock()
        mock_client.chat.side_effect = asyncio.TimeoutError()
        svc = SmartDecisionService.__new__(SmartDecisionService)
        svc._ai_client = mock_client
        scenario, method = await svc._classify_llm("哪些货快卖完了")
        assert scenario is None


class TestStream:
    """完整流式编排:分类 → 卡片 → 解释 → done."""

    @pytest.mark.asyncio
    async def test_regex_hit_with_explain(self, client):
        req = _make_req("哪些SKU必须补货?按紧急度排序")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "classify" in types
        assert "card" in types
        assert "done" in types
        classify_ev = next(e for e in events if e["type"] == "classify")
        assert classify_ev["scenario"] == "risk_queue"
        assert classify_ev["method"] == "regex"
        card_ev = next(e for e in events if e["type"] == "card")
        assert card_ev["card"]["type"] == "risk_queue"
        assert "summary" in card_ev
        assert len(card_ev["summary"]) > 20

    @pytest.mark.asyncio
    async def test_card_explain_off(self, client, monkeypatch):
        monkeypatch.setattr("supplyai.services.smart_decision_service.settings.card_explain", False)
        req = _make_req("风险队列")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "classify" in types
        assert "card" in types
        assert "done" in types
        assert "delta" not in types

    @pytest.mark.asyncio
    async def test_no_scenario_falls_through_to_chat(self, client):
        req = _make_req("你好,请自我介绍")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "classify" not in types
        assert "card" not in types
        assert "delta" in types
        assert "done" in types

    @pytest.mark.asyncio
    async def test_card_summary_in_history_enables_followup(self, client):
        req = SmartDecisionRequest(
            tenant_id=TENANT,
            messages=[
                ChatRequestMessage(role="user", content="风险队列"),
                ChatRequestMessage(role="assistant", content="风险队列: P1=12个, Top SKU: MS40060(p1)"),
                ChatRequestMessage(role="user", content="第一个为什么是P1"),
            ],
        )
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        events = _parse_sse(resp.text)
        types = [e["type"] for e in events]
        assert "delta" in types
        assert "done" in types

    @pytest.mark.asyncio
    async def test_sales_leaders_returns_sku_recommendations(self, client, monkeypatch):
        monkeypatch.setattr("supplyai.services.smart_decision_service.settings.card_explain", False)
        req = _make_req("我哪些产品的销量最好，应该重点推哪些SKU呢")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        classify_ev = next(e for e in events if e["type"] == "classify")
        assert classify_ev["scenario"] == "sales_leaders"
        card_ev = next(e for e in events if e["type"] == "card")
        card = card_ev["card"]
        assert card["type"] == "sales_leaders"
        assert card["rows"]
        first = card["rows"][0]
        assert first["msku"]
        assert first["sales7d"] >= 0
        assert first["reasons"]
        assert first["recommendation"]

    @pytest.mark.asyncio
    async def test_rule_impact_uses_target_days_from_user_text(self, client, monkeypatch):
        monkeypatch.setattr("supplyai.services.smart_decision_service.settings.card_explain", False)
        req = _make_req("安全天数再改成15天呢")
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        card_ev = next(e for e in events if e["type"] == "card")
        card = card_ev["card"]
        assert card["type"] == "rule_impact"
        assert card["targetSafeDays"] == 15
        assert card["rows"]
        assert all(row["targetSafeDays"] == 15 for row in card["rows"])

    @pytest.mark.asyncio
    async def test_sku_followup_ai_503_uses_local_snapshot_fallback(self, client, monkeypatch):
        """外部模型 503 时,SKU 页追问应返回本地快照结论,不能把原始报错透给用户."""

        class BrokenAiClient:
            async def chat(self, messages: list[ChatMessage], **kwargs):  # noqa: ANN003
                raise RuntimeError("503 Service Unavailable")

            async def chat_stream(self, messages: list[ChatMessage], **kwargs):  # noqa: ANN003
                raise RuntimeError("503 Service Unavailable")
                yield  # pragma: no cover

        import supplyai.api.v1.ai as ai_api

        monkeypatch.setattr(ai_api, "get_ai_client", lambda: BrokenAiClient())
        req = SmartDecisionRequest(
            tenant_id=TENANT,
            messages=[ChatRequestMessage(role="user", content="这个SKU下次备货是什么时候")],
            context={
                "current_page": "sku",
                "sku": {"listing_id": 1000003, "msku": "MS40619"},
            },
        )
        resp = await client.post(
            "/api/supplyai/ai/smart-decision/stream",
            json=req.model_dump(),
        )
        assert resp.status_code == 200
        events = _parse_sse(resp.text)
        assert not [e for e in events if e["type"] == "error"]
        full_text = "".join(e.get("text", "") for e in events if e["type"] == "delta")
        assert "503" not in full_text
        assert "建议采购" in full_text
        assert "可售天数" in full_text
        done = next(e for e in events if e["type"] == "done")
        assert done.get("status") == "degraded"


def _parse_sse(text: str) -> list[dict]:
    """解析 SSE 文本为 event list."""
    import json
    events = []
    for line in text.strip().split("\n"):
        line = line.strip()
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events
