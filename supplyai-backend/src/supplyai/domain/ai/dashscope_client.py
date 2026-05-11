"""DashScope 客户端 — 通过 OpenAI 兼容模式接 Qwen3.6-plus.

DashScope 端点: https://dashscope.aliyuncs.com/compatible-mode/v1
认证: Bearer <DASHSCOPE_API_KEY>
请求/响应与 OpenAI ChatCompletion 一致,支持 tools / tool_calls。
"""
from __future__ import annotations

import json
from typing import Any

import httpx

from supplyai.domain.ai.client import (
    ChatMessage,
    ChatResponse,
    ToolCall,
    ToolDef,
)

DASHSCOPE_BASE_URL = "https://dashscope.aliyuncs.com/compatible-mode/v1"


class DashScopeClient:
    """Qwen3.6-plus 客户端 (OpenAI 兼容)."""

    def __init__(
        self,
        api_key: str,
        model: str = "qwen3.6-plus",
        base_url: str = DASHSCOPE_BASE_URL,
        http_client: httpx.AsyncClient | None = None,
        timeout: float = 60.0,
        verify_ssl: bool = True,
    ) -> None:
        if not api_key:
            raise ValueError("DashScope api_key 未配置 (settings.dashscope_api_key)")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._http = http_client  # 测试时可注入

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> ChatResponse:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [self._serialize_message(m) for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if tools:
            body["tools"] = [
                {
                    "type": "function",
                    "function": {
                        "name": t.name,
                        "description": t.description,
                        "parameters": t.parameters,
                    },
                }
                for t in tools
            ]

        owns_http = self._http is None
        client = self._http or httpx.AsyncClient(
            timeout=self._timeout,
            verify=self._verify_ssl,
        )
        try:
            resp = await client.post(
                f"{self._base_url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}"},
            )
            resp.raise_for_status()
            data = resp.json()
        finally:
            if owns_http:
                await client.aclose()

        return self._parse_response(data)

    @staticmethod
    def _serialize_message(m: ChatMessage) -> dict[str, Any]:
        d: dict[str, Any] = {"role": m.role, "content": m.content}
        if m.tool_call_id:
            d["tool_call_id"] = m.tool_call_id
        return d

    @staticmethod
    def _parse_response(data: dict[str, Any]) -> ChatResponse:
        choice = (data.get("choices") or [{}])[0]
        msg = choice.get("message") or {}
        content = msg.get("content") or ""
        finish_reason = choice.get("finish_reason") or "stop"
        tool_calls_raw = msg.get("tool_calls") or []
        tool_calls = [
            ToolCall(
                id=tc.get("id") or "",
                name=(tc.get("function") or {}).get("name") or "",
                arguments=_parse_args((tc.get("function") or {}).get("arguments")),
            )
            for tc in tool_calls_raw
        ]
        return ChatResponse(
            content=content,
            tool_calls=tool_calls,
            finish_reason=finish_reason,
        )


def _parse_args(raw: Any) -> dict[str, Any]:
    """tool call 的 arguments 在 OpenAI 协议是 JSON 字符串,有些 SDK 已解析为 dict."""
    if isinstance(raw, dict):
        return raw
    if not raw:
        return {}
    try:
        return json.loads(raw)
    except (json.JSONDecodeError, TypeError):
        return {}
