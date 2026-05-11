"""CacheClient Protocol — 隔离本地 / 生产实现."""
from __future__ import annotations

from typing import Any, Protocol


class CacheClient(Protocol):
    """缓存抽象接口.

    本地实现:`InMemoryCache`(进程内 LRU)
    生产实现:`RedisCache`(Phase 4 启用)

    所有方法 async,即便 in-memory 实现也用 async 保证业务代码 0 修改。
    """

    async def get(self, key: str) -> Any | None: ...

    async def set(self, key: str, value: Any, ttl: int | None = None) -> None: ...

    async def delete(self, key: str) -> None: ...

    async def invalidate_pattern(self, pattern: str) -> None:
        """批量失效 — pattern 用 fnmatch 风格(`*`、`?`)。"""
        ...
