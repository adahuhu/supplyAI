"""DashScopeClient — 走 Qwen3.6-plus OpenAI 兼容模式.

测试不打外部网络,用 httpx.MockTransport 隔离。
"""
from __future__ import annotations

import json
from typing import Any

import httpx
import pytest

from supplyai.domain.ai.client import ChatMessage, ToolDef
from supplyai.domain.ai.dashscope_client import DashScopeClient


def _resp(payload: dict[str, Any]) -> httpx.Response:
    return httpx.Response(200, json=payload)


def _make_client(handler) -> DashScopeClient:
    transport = httpx.MockTransport(handler)
    http = httpx.AsyncClient(transport=transport)
    return DashScopeClient(api_key="sk-test", model="qwen3.6-plus", http_client=http)


async def test_chat_text_only() -> None:
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["url"] = str(req.url)
        captured["auth"] = req.headers.get("authorization")
        captured["body"] = json.loads(req.content)
        return _resp({
            "choices": [{
                "finish_reason": "stop",
                "message": {"role": "assistant", "content": "你好世界"},
            }],
        })

    cli = _make_client(handler)
    out = await cli.chat(messages=[ChatMessage(role="user", content="ping")])

    assert out.content == "你好世界"
    assert out.finish_reason == "stop"
    assert out.tool_calls == []
    # 请求格式校验
    assert "/chat/completions" in captured["url"]
    assert captured["auth"] == "Bearer sk-test"
    assert captured["body"]["model"] == "qwen3.6-plus"
    assert captured["body"]["messages"] == [{"role": "user", "content": "ping"}]


async def test_chat_with_tool_calls() -> None:
    """模型决定调工具时,response.tool_calls 解析为结构化对象."""
    def handler(req: httpx.Request) -> httpx.Response:
        return _resp({
            "choices": [{
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [
                        {
                            "id": "call_1",
                            "type": "function",
                            "function": {
                                "name": "query_stockout_risk",
                                "arguments": '{"tenant_id": 100228, "limit": 5}',
                            },
                        }
                    ],
                },
            }],
        })

    cli = _make_client(handler)
    out = await cli.chat(
        messages=[ChatMessage(role="user", content="哪些 SKU 紧急?")],
        tools=[ToolDef(
            name="query_stockout_risk",
            description="查询风险队列",
            parameters={"type": "object", "properties": {"tenant_id": {"type": "integer"}}},
        )],
    )
    assert out.finish_reason == "tool_calls"
    assert len(out.tool_calls) == 1
    tc = out.tool_calls[0]
    assert tc.id == "call_1"
    assert tc.name == "query_stockout_risk"
    assert tc.arguments == {"tenant_id": 100228, "limit": 5}


async def test_chat_includes_tools_in_request_body() -> None:
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(req.content)
        return _resp({
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "ok"}}],
        })

    cli = _make_client(handler)
    await cli.chat(
        messages=[ChatMessage(role="user", content="x")],
        tools=[ToolDef(
            name="query_sku_detail",
            description="查 SKU 详情",
            parameters={"type": "object", "properties": {"listing_id": {"type": "integer"}}},
        )],
    )
    tools = captured["body"]["tools"]
    assert len(tools) == 1
    assert tools[0]["type"] == "function"
    assert tools[0]["function"]["name"] == "query_sku_detail"
    assert tools[0]["function"]["parameters"]["properties"]["listing_id"]["type"] == "integer"


async def test_serialize_tool_message_with_tool_call_id() -> None:
    """工具结果回传给模型时,tool_call_id 必须落到请求体."""
    captured = {}

    def handler(req: httpx.Request) -> httpx.Response:
        captured["body"] = json.loads(req.content)
        return _resp({
            "choices": [{"finish_reason": "stop", "message": {"role": "assistant", "content": "done"}}],
        })

    cli = _make_client(handler)
    await cli.chat(messages=[
        ChatMessage(role="user", content="问"),
        ChatMessage(role="assistant", content=""),
        ChatMessage(role="tool", content='{"result":1}', tool_call_id="call_1"),
    ])
    msgs = captured["body"]["messages"]
    assert msgs[2]["role"] == "tool"
    assert msgs[2]["tool_call_id"] == "call_1"
    assert msgs[2]["content"] == '{"result":1}'


async def test_missing_api_key_raises() -> None:
    with pytest.raises(ValueError, match="api[_ ]?key"):
        DashScopeClient(api_key="")


async def test_http_error_propagates() -> None:
    def handler(req: httpx.Request) -> httpx.Response:
        return httpx.Response(401, json={"error": "auth"})

    cli = _make_client(handler)
    with pytest.raises(httpx.HTTPStatusError):
        await cli.chat(messages=[ChatMessage(role="user", content="ping")])


async def test_tool_arguments_already_dict() -> None:
    """有些 SDK 已经把 arguments 解析成 dict,不要重复 parse 失败."""
    def handler(req: httpx.Request) -> httpx.Response:
        return _resp({
            "choices": [{
                "finish_reason": "tool_calls",
                "message": {
                    "role": "assistant",
                    "content": "",
                    "tool_calls": [{
                        "id": "call_x",
                        "type": "function",
                        "function": {
                            "name": "f",
                            "arguments": {"already": "dict"},
                        },
                    }],
                },
            }],
        })
    cli = _make_client(handler)
    out = await cli.chat(messages=[ChatMessage(role="user", content="x")])
    assert out.tool_calls[0].arguments == {"already": "dict"}
