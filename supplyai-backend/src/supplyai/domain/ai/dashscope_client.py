"""DashScope 客户端 — 通过 OpenAI 兼容模式接 Qwen3.6-plus.

DashScope 端点: https://dashscope.aliyuncs.com/compatible-mode/v1
认证: Bearer <DASHSCOPE_API_KEY>
请求/响应与 OpenAI ChatCompletion 一致,支持 tools / tool_calls。
"""
from __future__ import annotations

import json
from typing import Any, AsyncIterator

import httpx

from supplyai.domain.ai.client import (
    ChatMessage,
    ChatResponse,
    StreamDelta,
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
        enable_thinking: bool = False,
    ) -> None:
        if not api_key:
            raise ValueError("DashScope api_key 未配置 (settings.dashscope_api_key)")
        self._api_key = api_key
        self._model = model
        self._base_url = base_url.rstrip("/")
        self._timeout = timeout
        self._verify_ssl = verify_ssl
        self._enable_thinking = enable_thinking
        self._http = http_client  # 测试时可注入

    async def chat(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> ChatResponse:
        body = self._build_body(messages, tools, max_tokens, temperature, stream=False)
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

    def _build_body(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None,
        max_tokens: int,
        temperature: float,
        *,
        stream: bool,
    ) -> dict[str, Any]:
        body: dict[str, Any] = {
            "model": self._model,
            "messages": [self._serialize_message(m) for m in messages],
            "max_tokens": max_tokens,
            "temperature": temperature,
        }
        if stream:
            body["stream"] = True
        # Qwen3.x 默认开启 reasoning_content;关掉以消除 30-60s 首字延迟。
        # 通过 extra_body 透传:OpenAI 兼容协议本来没有这个字段,DashScope 自定义接受。
        if not self._enable_thinking:
            body["enable_thinking"] = False
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
        return body

    async def chat_stream(
        self,
        messages: list[ChatMessage],
        tools: list[ToolDef] | None = None,
        max_tokens: int = 1024,
        temperature: float = 0.2,
    ) -> AsyncIterator[StreamDelta]:
        """流式 chat — yield delta token,结尾 yield 一个 finish_reason 非空的 delta.

        tool_calls 分支:Qwen 在 stream=true 下会按片段下发 tool_calls.function.arguments,
        我们在内部累积成完整 JSON,只在 finish_reason='tool_calls' 时整体下发。
        """
        body = self._build_body(messages, tools, max_tokens, temperature, stream=True)

        owns_http = self._http is None
        client = self._http or httpx.AsyncClient(
            timeout=self._timeout,
            verify=self._verify_ssl,
        )

        # 累积工具调用 — index → {id, name, args_buf}
        tc_buf: dict[int, dict[str, Any]] = {}

        try:
            async with client.stream(
                "POST",
                f"{self._base_url}/chat/completions",
                json=body,
                headers={"Authorization": f"Bearer {self._api_key}"},
            ) as resp:
                resp.raise_for_status()
                async for line in resp.aiter_lines():
                    if not line or not line.startswith("data:"):
                        continue
                    payload = line[5:].strip()
                    if payload == "[DONE]":
                        break
                    try:
                        chunk = json.loads(payload)
                    except json.JSONDecodeError:
                        continue
                    choice = (chunk.get("choices") or [{}])[0]
                    delta = choice.get("delta") or {}
                    finish_reason = choice.get("finish_reason")

                    # 内容增量 + reasoning(thinking)增量
                    text = delta.get("content") or ""
                    reasoning = delta.get("reasoning_content") or ""

                    # 工具调用累积(OpenAI 兼容协议:tool_calls 是数组,index 标识同一个调用)
                    for tc in delta.get("tool_calls") or []:
                        idx = tc.get("index", 0)
                        buf = tc_buf.setdefault(idx, {"id": "", "name": "", "args_buf": ""})
                        if tc.get("id"):
                            buf["id"] = tc["id"]
                        fn = tc.get("function") or {}
                        if fn.get("name"):
                            buf["name"] = fn["name"]
                        if fn.get("arguments"):
                            buf["args_buf"] += fn["arguments"]

                    # 一帧可能 reasoning 和 content 同时非空(切换点),都吐出来
                    if not finish_reason and (text or reasoning):
                        yield StreamDelta(text=text, reasoning_text=reasoning)

                    if finish_reason:
                        # 结束:打包累积的 tool_calls(如有),返一个 final delta
                        tool_calls: list[ToolCall] = []
                        if tc_buf:
                            for idx in sorted(tc_buf.keys()):
                                buf = tc_buf[idx]
                                tool_calls.append(ToolCall(
                                    id=buf["id"] or f"call_{idx}",
                                    name=buf["name"],
                                    arguments=_parse_args(buf["args_buf"]),
                                ))
                        yield StreamDelta(
                            text=text,
                            reasoning_text=reasoning,
                            tool_calls=tool_calls,
                            finish_reason=finish_reason,
                        )
                        break
        finally:
            if owns_http:
                await client.aclose()

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
