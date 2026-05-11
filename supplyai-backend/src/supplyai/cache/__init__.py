"""缓存抽象 — 本地内存 / 生产 Redis."""
from supplyai.cache.factory import get_cache_client
from supplyai.cache.interface import CacheClient

__all__ = ["CacheClient", "get_cache_client"]
