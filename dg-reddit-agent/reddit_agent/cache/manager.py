"""Caching layer — diskcache-backed memoization for expensive API calls."""

import hashlib
import json
import logging
from typing import Any, Callable

import diskcache

from reddit_agent.config import settings

logger = logging.getLogger(__name__)

_cache: diskcache.Cache | None = None


def _get_cache() -> diskcache.Cache:
    """Lazy-init the cache backend."""
    global _cache
    if _cache is not None:
        return _cache

    _cache = diskcache.Cache("./cache_store")
    return _cache


def _make_key(fn_name: str, args: tuple, kwargs: dict) -> str:
    """Create a deterministic cache key from function name + arguments."""
    raw = json.dumps(
        {"fn": fn_name, "args": args, "kwargs": kwargs},
        sort_keys=True,
        default=str,
    )
    return hashlib.md5(raw.encode()).hexdigest()


def cached_call(fn: Callable, *args: Any, ttl_hours: int | None = None, **kwargs: Any) -> Any:
    """Call fn with caching. Returns cached result if available, otherwise calls fn and caches."""
    if ttl_hours is None:
        ttl_hours = settings.cache_ttl_hours

    cache = _get_cache()
    key = _make_key(fn.__name__, args, kwargs)

    if key in cache:
        logger.debug("Cache HIT for %s(%s)", fn.__name__, key[:8])
        return cache[key]

    logger.debug("Cache MISS for %s(%s) — calling function", fn.__name__, key[:8])
    result = fn(*args, **kwargs)
    cache.set(key, result, expire=ttl_hours * 3600)
    return result


def clear_cache() -> None:
    """Clear all cached data."""
    cache = _get_cache()
    cache.clear()
    logger.info("Cache cleared")
