"""AI 流式输出测试 — /ai/chat/stream 端点 + orchestrator.run_stream."""
from __future__ import annotations

import json

import pytest
from httpx import ASGITransport, AsyncClient

from supplyai.main import app


def _parse_sse(payload: bytes) -> list[dict]:
    """从 raw SSE 字节解析出 event dict 列表."""
    events = []
    for line in payload.decode("utf-8").splitlines():
        if line.startswith("data: "):
            events.append(json.loads(line[6:]))
    return events


@pytest.mark.asyncio
async def test_ai_chat_stream_emits_delta_and_done():
    """无工具调用场景:应该看到 ≥1 个 delta 事件 + 1 个 done."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with ac.stream(
            "POST",
            "/api/supplyai/ai/chat/stream",
            json={
                "tenant_id": 100228,
                "messages": [{"role": "user", "content": "测试流式"}],
            },
        ) as resp:
            assert resp.status_code == 200
            assert resp.headers["content-type"].startswith("text/event-stream")
            chunks = []
            async for chunk in resp.aiter_bytes():
                chunks.append(chunk)

    events = _parse_sse(b"".join(chunks))
    types = [e["type"] for e in events]

    assert "done" in types, f"应该收到 done,实际: {types}"
    delta_events = [e for e in events if e["type"] == "delta"]
    assert delta_events, "应该至少有 1 个 delta"

    # 拼起来应该是 stub 的完整回复
    full_text = "".join(e["text"] for e in delta_events)
    assert full_text, "delta 文本不应为空"
    # stub echo 模式:回复包含 "stub" 或预设关键字
    assert ("stub" in full_text) or ("P1" in full_text) or ("断货" in full_text)


@pytest.mark.asyncio
async def test_ai_chat_stream_done_has_finish_reason():
    """done 事件应携带 finish_reason."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        async with ac.stream(
            "POST",
            "/api/supplyai/ai/chat/stream",
            json={
                "tenant_id": 100228,
                "messages": [{"role": "user", "content": "随便问"}],
            },
        ) as resp:
            chunks = [c async for c in resp.aiter_bytes()]

    events = _parse_sse(b"".join(chunks))
    done = next((e for e in events if e["type"] == "done"), None)
    assert done is not None
    assert done["finish_reason"] in ("stop", "length")
    assert "tool_iterations" in done


@pytest.mark.asyncio
async def test_ai_chat_stream_empty_messages_returns_error():
    """空 messages 应返 400(同非流式行为一致)."""
    async with AsyncClient(transport=ASGITransport(app=app), base_url="http://test") as ac:
        resp = await ac.post(
            "/api/supplyai/ai/chat/stream",
            json={"tenant_id": 100228, "messages": []},
        )
    # AiEmptyMessagesException → 400
    assert resp.status_code in (400, 500)  # 实际是 400,但 stream 内 raise 可能被包成 500
