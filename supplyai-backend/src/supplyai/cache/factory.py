"""缓存工厂 — 按配置返回对应实现."""
from __future__ import annotations

from functools import lru_cache

from supplyai.cache.in_memory import InMemoryCache
from supplyai.cache.interface import CacheClient
from supplyai.config import settings


@lru_cache(maxsize=1)
def get_cache_client() -> CacheClient:
    """返回单例缓存客户端 — 进程级共享。

    Phase 4 启用 Redis 时增加分支:
        if settings.cache_backend == "redis":
            from supplyai.cache.redis_cache import RedisCache
            return RedisCache(settings.redis_url)
    """
    if settings.cache_backend == "redis":
        # Phase 4 实现
        raise NotImplementedError("Redis cache backend 将在 Phase 4 启用")

    return InMemoryCache(
        maxsize=10_000,
        default_ttl=settings.cache_default_ttl,
    )
