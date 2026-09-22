"""Redis Cache-Aside Manager for AegisBank RAG and Knowledge Retrieval.

Provides connection pooling, namespaced keys, TTL expiration, single-flight
stampede protection with distributed locks, and graceful failure fallbacks.
"""

from __future__ import annotations

import hashlib
import json
import logging
import os
import time
import uuid
from collections.abc import Callable
from typing import Any, TypeVar

import redis
from redis.exceptions import RedisError

logger = logging.getLogger(__name__)

DEFAULT_REDIS_URL = os.environ.get("REDIS_URL", "redis://127.0.0.1:6379/0")
CACHE_SCHEMA_VERSION = "1.0"

T = TypeVar("T")

# Atomic Lua script for safe distributed lock release
RELEASE_LOCK_LUA = """
if redis.call("get", KEYS[1]) == ARGV[1] then
    return redis.call("del", KEYS[1])
else
    return 0
end
"""


def build_cache_key(namespace: str, version: str, query: str) -> str:
    """Build a deterministic, versioned, namespaced cache key."""
    digest = hashlib.sha256(query.strip().lower().encode("utf-8")).hexdigest()[:16]
    return f"aegisbank:{namespace}:v1:{version}:{digest}"


class RedisCacheManager:
    """Canonical cache-aside manager backed by Redis connection pool."""

    def __init__(
        self,
        redis_url: str = DEFAULT_REDIS_URL,
        *,
        max_connections: int = 10,
        socket_timeout: float = 1.0,
        socket_connect_timeout: float = 1.0,
    ) -> None:
        self.redis_url = redis_url
        self._pool = redis.ConnectionPool.from_url(
            redis_url,
            max_connections=max_connections,
            socket_timeout=socket_timeout,
            socket_connect_timeout=socket_connect_timeout,
            decode_responses=True,
        )
        self._client: redis.Redis = redis.Redis(connection_pool=self._pool)
        self._hits = 0
        self._misses = 0
        self._sets = 0
        self._invalidations = 0
        self._errors = 0

    @property
    def hit_ratio(self) -> float:
        total = self._hits + self._misses
        return self._hits / total if total > 0 else 0.0

    @property
    def metrics(self) -> dict[str, Any]:
        return {
            "cache_hit_count": self._hits,
            "cache_miss_count": self._misses,
            "cache_hit_ratio": round(self.hit_ratio, 4),
            "cache_set_count": self._sets,
            "cache_invalidation_count": self._invalidations,
            "cache_error_count": self._errors,
        }

    def ping(self) -> bool:
        """Check if Redis server is reachable."""
        try:
            return bool(self._client.ping())
        except RedisError:
            self._errors += 1
            return False

    def get(self, key: str) -> Any | None:
        """Retrieve and deserialize value from cache; returns None on MISS or error."""
        try:
            raw = self._client.get(key)
            if raw is None:
                self._misses += 1
                return None

            envelope = json.loads(raw)
            if (
                not isinstance(envelope, dict)
                or envelope.get("schema_version") != CACHE_SCHEMA_VERSION
            ):
                self._misses += 1
                return None

            self._hits += 1
            return envelope.get("data")
        except (RedisError, json.JSONDecodeError, UnicodeDecodeError) as err:
            logger.warning("Redis cache GET failed for key %s: %s", key, err)
            self._errors += 1
            self._misses += 1
            return None

    def set(self, key: str, value: Any, ttl_seconds: int = 300) -> bool:
        """Serialize and store value with TTL; returns False on error."""
        try:
            envelope = {
                "schema_version": CACHE_SCHEMA_VERSION,
                "timestamp_utc": time.time(),
                "ttl_seconds": ttl_seconds,
                "data": value,
            }
            raw = json.dumps(envelope, ensure_ascii=False)
            success = bool(self._client.set(key, raw, ex=ttl_seconds))
            if success:
                self._sets += 1
            return success
        except (RedisError, TypeError) as err:
            logger.warning("Redis cache SET failed for key %s: %s", key, err)
            self._errors += 1
            return False

    def invalidate_key(self, key: str) -> bool:
        """Invalidate a specific cache key."""
        try:
            count = self._client.delete(key)
            if count > 0:
                self._invalidations += 1
            return count > 0
        except RedisError as err:
            logger.warning("Redis cache DELETE failed for key %s: %s", key, err)
            self._errors += 1
            return False

    def invalidate_prefix(self, prefix: str) -> int:
        """Invalidate all keys matching a prefix using non-blocking SCAN iteration."""
        try:
            deleted_count = 0
            cursor = 0
            match_pattern = f"{prefix}*" if not prefix.endswith("*") else prefix
            while True:
                cursor, keys = self._client.scan(cursor=cursor, match=match_pattern, count=100)
                if keys:
                    deleted_count += self._client.delete(*keys)
                if cursor == 0:
                    break
            self._invalidations += deleted_count
            return deleted_count
        except RedisError as err:
            logger.warning("Redis cache invalidate_prefix failed for %s: %s", prefix, err)
            self._errors += 1
            return 0

    def execute_single_flight(
        self,
        key: str,
        loader: Callable[[], T],
        *,
        ttl_seconds: int = 300,
        lock_timeout_seconds: int = 5,
        max_wait_ms: int = 500,
    ) -> T:
        """Cache-aside with single-flight stampede protection using a distributed lock."""
        # 1. Fast path: try cache GET
        cached = self.get(key)
        if cached is not None:
            return cached  # type: ignore[return-value]

        # 2. Try acquiring single-flight lock
        lock_key = f"aegisbank:lock:{key}"
        token = str(uuid.uuid4())
        acquired = False
        try:
            acquired = bool(self._client.set(lock_key, token, nx=True, ex=lock_timeout_seconds))
        except RedisError:
            # If lock acquisition fails due to Redis issue, proceed to direct load
            pass

        if acquired:
            try:
                # Execute source loader
                result = loader()
                self.set(key, result, ttl_seconds=ttl_seconds)
                return result
            finally:
                # Safe atomic lock release
                try:
                    self._client.eval(RELEASE_LOCK_LUA, 1, lock_key, token)  # type: ignore[no-untyped-call]
                except RedisError:
                    pass

        # 3. Another process holds the lock; wait with short backoff then re-read cache
        start_time = time.perf_counter()
        while (time.perf_counter() - start_time) * 1000.0 < max_wait_ms:
            time.sleep(0.02)
            cached = self.get(key)
            if cached is not None:
                return cached  # type: ignore[return-value]

        # 4. Fallback: if timeout reached and still no cache, execute loader directly
        result = loader()
        self.set(key, result, ttl_seconds=ttl_seconds)
        return result
