"""AI 客户端工厂 — 支持 dashscope / openai 兼容接口."""
from __future__ import annotations

from functools import lru_cache

from supplyai.config import settings
from supplyai.domain.ai.client import AiClient
from supplyai.domain.ai.dashscope_client import DashScopeClient

_SUPPORTED_PROVIDERS = {"dashscope", "openai"}


class AiClientNotConfigured(RuntimeError):
    """AI 客户端配置缺失;不允许任何降级到 mock 的兜底."""


@lru_cache(maxsize=1)
def get_ai_client() -> AiClient:
    provider = (settings.ai_provider or "dashscope").lower()
    if provider not in _SUPPORTED_PROVIDERS:
        raise AiClientNotConfigured(
            f"不支持的 AI provider: {provider!r}。支持: {sorted(_SUPPORTED_PROVIDERS)}"
        )
    if not settings.dashscope_api_key:
        raise AiClientNotConfigured(
            f"AI provider={provider!r} 但未配置 SUPPLY_DASH_API_KEY。"
        )
    enable_thinking = settings.dashscope_enable_thinking if provider == "dashscope" else False
    return DashScopeClient(
        api_key=settings.dashscope_api_key,
        model=settings.ai_model,
        base_url=settings.dashscope_base_url,
        verify_ssl=settings.dashscope_verify_ssl,
        enable_thinking=enable_thinking,
        provider=provider,
    )


def reset_ai_client_cache() -> None:
    """测试 / 配置变更后强制下次 get_ai_client 重新构造."""
    get_ai_client.cache_clear()
