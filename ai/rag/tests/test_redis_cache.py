"""Acceptance and unit tests for Redis Cache-Aside Manager (v0.12.2).

Verifies cache lifecycle (MISS->LOAD->SET->HIT), TTL expiration, invalidation by key and prefix,
stale data prevention on version bump, single-flight stampede protection, and failure fallback.
"""

from __future__ import annotations

import concurrent.futures
import time
from typing import Any

import pytest
import redis

from aegisbank_rag.cache import (
    DEFAULT_REDIS_URL,
    RedisCacheManager,
    build_cache_key,
)


def _is_redis_running() -> bool:
    try:
        r = redis.Redis.from_url(DEFAULT_REDIS_URL, socket_timeout=0.5)
        return bool(r.ping())
    except Exception:
        return False


pytestmark = pytest.mark.skipif(
    not _is_redis_running(),
    reason="Redis server is not running on 127.0.0.1:6379",
)


@pytest.fixture
def cache_mgr() -> RedisCacheManager:
    mgr = RedisCacheManager()
    mgr.invalidate_prefix("aegisbank:test:")
    return mgr


def test_cache_aside_lifecycle_miss_load_set_hit(cache_mgr: RedisCacheManager) -> None:
    """Demonstrate classic cache-aside flow: MISS -> Load -> SET -> HIT."""
    key = "aegisbank:test:rag:v1:query_001"
    load_count = 0

    def mock_loader() -> dict[str, Any]:
        nonlocal load_count
        load_count += 1
        return {"policy": "Credito Personal", "max_term": 60}

    # 1. First execution: MISS -> runs loader -> SET
    result1 = cache_mgr.execute_single_flight(key, mock_loader, ttl_seconds=60)
    assert result1 == {"policy": "Credito Personal", "max_term": 60}
    assert load_count == 1

    # 2. Second execution: HIT -> returns cached value without loader execution
    result2 = cache_mgr.execute_single_flight(key, mock_loader, ttl_seconds=60)
    assert result2 == {"policy": "Credito Personal", "max_term": 60}
    assert load_count == 1  # Loader not called again

    # Check metrics
    assert cache_mgr.metrics["cache_hit_count"] >= 1
    assert cache_mgr.metrics["cache_miss_count"] >= 1
    assert cache_mgr.metrics["cache_hit_ratio"] > 0.0


def test_cache_ttl_expiration(cache_mgr: RedisCacheManager) -> None:
    """Verify key automatically expires after TTL seconds."""
    key = "aegisbank:test:rag:v1:short_ttl"
    cache_mgr.set(key, {"temp_data": "expires_soon"}, ttl_seconds=1)

    # Immediate read: HIT
    assert cache_mgr.get(key) == {"temp_data": "expires_soon"}

    # Wait for TTL expiry
    time.sleep(1.2)

    # Post-expiry read: MISS
    assert cache_mgr.get(key) is None


def test_cache_invalidation_by_key_and_prefix(cache_mgr: RedisCacheManager) -> None:
    """Verify explicit invalidation by single key and by namespace prefix."""
    key1 = "aegisbank:test:docs:v1:doc1"
    key2 = "aegisbank:test:docs:v1:doc2"
    key3 = "aegisbank:test:other:v1:item1"

    cache_mgr.set(key1, {"doc": 1}, ttl_seconds=60)
    cache_mgr.set(key2, {"doc": 2}, ttl_seconds=60)
    cache_mgr.set(key3, {"other": 1}, ttl_seconds=60)

    # Invalidate single key
    assert cache_mgr.invalidate_key(key1) is True
    assert cache_mgr.get(key1) is None
    assert cache_mgr.get(key2) == {"doc": 2}

    # Invalidate by prefix
    deleted = cache_mgr.invalidate_prefix("aegisbank:test:docs:v1:")
    assert deleted >= 1
    assert cache_mgr.get(key2) is None
    assert cache_mgr.get(key3) == {"other": 1}


def test_cache_version_bump_prevents_stale_data(cache_mgr: RedisCacheManager) -> None:
    """Verify version bump in cache key prevents serving stale data from previous corpus."""
    query = "¿Cuál es la tasa de interés?"
    key_v1 = build_cache_key("rag", "v1.0", query)
    key_v2 = build_cache_key("rag", "v2.0", query)

    assert key_v1 != key_v2

    # Populate v1.0
    cache_mgr.set(key_v1, {"rate": "15.5%"}, ttl_seconds=60)

    # Query with active corpus v2.0 -> MISS -> fresh load
    assert cache_mgr.get(key_v2) is None


def test_cache_stampede_single_flight_protection(cache_mgr: RedisCacheManager) -> None:
    """Simulate concurrent requests to missing key; verify loader executes once."""
    key = "aegisbank:test:stampede:key_1"
    load_count = 0

    def slow_loader() -> dict[str, str]:
        nonlocal load_count
        load_count += 1
        time.sleep(0.1)  # Simulate expensive database/retrieval query
        return {"data": "expensive_result"}

    # Execute 10 concurrent requests
    with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
        futures = [
            executor.submit(
                cache_mgr.execute_single_flight,
                key,
                slow_loader,
                ttl_seconds=60,
            )
            for _ in range(10)
        ]
        results = [f.result() for f in futures]

    # All threads receive the valid data
    for res in results:
        assert res == {"data": "expensive_result"}

    # Loader executed only once despite 10 concurrent callers
    assert load_count == 1


def test_cache_failure_fallback_graceful_degradation() -> None:
    """Verify application continues working via source fallback when Redis is unreachable."""
    # Connect to offline Redis port
    offline_mgr = RedisCacheManager(
        redis_url="redis://127.0.0.1:9999/0",
        socket_timeout=0.1,
        socket_connect_timeout=0.1,
    )
    assert offline_mgr.ping() is False

    load_called = False

    def fallback_loader() -> str:
        nonlocal load_called
        load_called = True
        return "fallback_canonical_data"

    # Single-flight should gracefully execute loader without crashing
    result = offline_mgr.execute_single_flight("aegisbank:test:fallback", fallback_loader)
    assert result == "fallback_canonical_data"
    assert load_called is True
    assert offline_mgr.metrics["cache_error_count"] > 0
