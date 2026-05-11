"""进程内 LRU 缓存 — 本地默认实现."""
from __future__ import annotations

import fnmatch
from threading import RLock
from typing import Any

from cachetools import TTLCache


class InMemoryCache:
    """进程内 TTL+LRU 缓存.

    适合本地开发 / 单实例部署。无 daemon、无网络。
    切到生产 Redis 时业务代码 0 修改。
    """

    def __init__(self, maxsize: int = 10_000, default_ttl: int = 60) -> None:
        self._cache: TTLCache[str, Any] = TTLCache(maxsize=maxsize, ttl=default_ttl)
        self._lock = RLock()
        self._default_ttl = default_ttl

    async def get(self, key: str) -> Any | None:
        with self._lock:
            return self._cache.get(key)

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None:  # noqa: ARG002
        # cachetools.TTLCache 的 ttl 是统一的;per-key ttl 暂未单独实现
        with self._lock:
            self._cache[key] = value

    async def delete(self, key: str) -> None:
        with self._lock:
            self._cache.pop(key, None)

    async def invalidate_pattern(self, pattern: str) -> None:
        """按 fnmatch 模式批量失效."""
        with self._lock:
            keys_to_delete = [k for k in self._cache if fnmatch.fnmatch(k, pattern)]
            for key in keys_to_delete:
                del self._cache[key]
