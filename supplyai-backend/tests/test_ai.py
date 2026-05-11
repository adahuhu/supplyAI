"""AI 端点测试 — POST /ai/explain + /ai/chat."""
from __future__ import annotations

from httpx import AsyncClient


async def _pick_listing_id(client: AsyncClient) -> int:
    resp = await client.post(
        "/api/supplyai/skus/list",
        json={"tenant_id": 100228, "page_size": 1},
    )
    return resp.json()["rows"][0]["id"]


async def test_ai_explain_returns_text(client: AsyncClient) -> None:
    listing_id = await _pick_listing_id(client)
    resp = await client.post(
        "/api/supplyai/ai/explain",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    assert resp.status_code == 200, resp.text
    data = resp.json()
    assert "explanation" in data
    assert isinstance(data["explanation"], str)
    assert len(data["explanation"]) > 0


async def test_ai_explain_includes_context(client: AsyncClient) -> None:
    """返回的 context 必须含 SKU 关键字段(用于前端附在 explain 卡片)."""
    listing_id = await _pick_listing_id(client)
    resp = await client.post(
        "/api/supplyai/ai/explain",
        json={"tenant_id": 100228, "listing_id": listing_id},
    )
    data = resp.json()
    ctx = data["context"]
    assert "msku" in ctx
    assert "priority" in ctx
    assert "suggest_qty" in ctx


async def test_ai_explain_404_unknown_sku(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/ai/explain",
        json={"tenant_id": 100228, "listing_id": 99999999},
    )
    assert resp.status_code == 404
    assert resp.json()["detail"]["code"] == "SKU_NOT_FOUND"


async def test_ai_chat_returns_assistant_message(client: AsyncClient) -> None:
    """简单对话 — 用户问"风险",mock 返回风险摘要."""
    resp = await client.post(
        "/api/supplyai/ai/chat",
        json={
            "tenant_id": 100228,
            "messages": [{"role": "user", "content": "当前供应链风险如何"}],
        },
    )
    assert resp.status_code == 200
    data = resp.json()
    assert data["role"] == "assistant"
    assert isinstance(data["content"], str)
    assert len(data["content"]) > 0


async def test_ai_chat_rejects_empty_messages(client: AsyncClient) -> None:
    resp = await client.post(
        "/api/supplyai/ai/chat",
        json={"tenant_id": 100228, "messages": []},
    )
    assert resp.status_code == 400
    assert resp.json()["detail"]["code"] == "AI_EMPTY_MESSAGES"


async def test_ai_chat_truncates_history_beyond_limit(client: AsyncClient) -> None:
    """超过 ai_history_turns 时只保留最近 N 轮(behavior 体现在不报错)."""
    long_msgs = [
        {"role": "user", "content": f"q{i}"}
        for i in range(20)
    ]
    resp = await client.post(
        "/api/supplyai/ai/chat",
        json={"tenant_id": 100228, "messages": long_msgs},
    )
    assert resp.status_code == 200
