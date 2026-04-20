"""Test Step 2: cache/manager.py — verify caching works correctly."""

import asyncio
import time

from seo_agent.cache.manager import (
    cached_call,
    async_cached_call,
    clear_cache,
    cache_stats,
    _make_key,
)


# ── Helpers ──────────────────────────────────────────────────────────────

call_count = 0


def expensive_function(x: int, y: int) -> int:
    """Simulates an expensive API call."""
    global call_count
    call_count += 1
    return x + y


async def async_expensive_function(x: int, y: int) -> int:
    """Simulates an expensive async API call."""
    global call_count
    call_count += 1
    return x * y


# ── Tests ────────────────────────────────────────────────────────────────


def setup_function():
    """Reset state before each test."""
    global call_count
    call_count = 0
    clear_cache()


def test_make_key_deterministic():
    """Same inputs produce the same cache key."""
    k1 = _make_key("foo", (1, 2), {"bar": "baz"})
    k2 = _make_key("foo", (1, 2), {"bar": "baz"})
    assert k1 == k2


def test_make_key_different_for_different_inputs():
    k1 = _make_key("foo", (1,), {})
    k2 = _make_key("foo", (2,), {})
    assert k1 != k2


def test_cached_call_caches_result():
    """Second call should return cached result without calling the function again."""
    result1 = cached_call(expensive_function, 3, 4)
    result2 = cached_call(expensive_function, 3, 4)

    assert result1 == 7
    assert result2 == 7
    assert call_count == 1  # Function only called once


def test_cached_call_different_args():
    """Different arguments should result in separate cache entries."""
    r1 = cached_call(expensive_function, 1, 2)
    r2 = cached_call(expensive_function, 3, 4)

    assert r1 == 3
    assert r2 == 7
    assert call_count == 2


def test_async_cached_call():
    """Async caching should work the same way."""

    async def run():
        r1 = await async_cached_call(async_expensive_function, 3, 4)
        r2 = await async_cached_call(async_expensive_function, 3, 4)
        assert r1 == 12
        assert r2 == 12
        assert call_count == 1

    asyncio.run(run())


def test_clear_cache():
    """After clearing, function should be called again."""
    cached_call(expensive_function, 5, 5)
    assert call_count == 1

    clear_cache()

    cached_call(expensive_function, 5, 5)
    assert call_count == 2


def test_cache_stats():
    """Stats should reflect cached entries."""
    clear_cache()
    cached_call(expensive_function, 1, 1)
    cached_call(expensive_function, 2, 2)

    stats = cache_stats()
    assert stats["size"] == 2
    assert "cache_store" in stats["directory"]


def test_cached_call_with_custom_ttl():
    """Custom TTL should not break caching."""
    r = cached_call(expensive_function, 10, 20, ttl_hours=1)
    assert r == 30
    assert call_count == 1
