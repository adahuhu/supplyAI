"""AI 客户端工厂 — 当前仅 DashScope (Qwen3.6-plus, OpenAI 兼容).

未配置 API key 时直接抛错,不再降级到任何 mock。
"""
from __future__ import annotations

from functools import lru_cache

from supplyai.config import settings
from supplyai.domain.ai.client import AiClient
from supplyai.domain.ai.dashscope_client import DashScopeClient


class AiClientNotConfigured(RuntimeError):
    """AI 客户端配置缺失;不允许任何降级到 mock 的兜底."""


@lru_cache(maxsize=1)
def get_ai_client() -> AiClient:
    if settings.ai_provider != "dashscope":
        raise AiClientNotConfigured(
            f"不支持的 AI provider: {settings.ai_provider!r}。当前仅支持 dashscope。"
        )
    if not settings.dashscope_api_key:
        raise AiClientNotConfigured(
            "AI provider=dashscope 但未配置 SUPPLY_DASH_API_KEY (或 DASHSCOPE_API_KEY)。"
        )
    return DashScopeClient(
        api_key=settings.dashscope_api_key,
        model=settings.ai_model,
        base_url=settings.dashscope_base_url,
        verify_ssl=settings.dashscope_verify_ssl,
    )


def reset_ai_client_cache() -> None:
    """测试 / 配置变更后强制下次 get_ai_client 重新构造."""
    get_ai_client.cache_clear()
