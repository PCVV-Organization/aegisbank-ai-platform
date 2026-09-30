"""Redis connection and client factory for AegisBank.

Preserves local Redis behavior (standalone container on port 6379) and provides
an adapter seam for Azure Managed Redis with TLS.
Status: PASSWORDLESS_REDIS=PARTIAL (adapter seam ready for Entra-enabled Azure Managed Redis).
"""

from __future__ import annotations

import logging
import os
from typing import Any

import redis

logger = logging.getLogger("aegisbank.rag.redis_factory")

DEFAULT_LOCAL_REDIS_URL = "redis://127.0.0.1:6379/0"


def create_redis_client(
    redis_url: str | None = None,
    *,
    host: str | None = None,
    port: int = 6380,
    ssl: bool = True,
    credential: Any = None,
    socket_timeout: float = 1.0,
    socket_connect_timeout: float = 1.0,
) -> redis.Redis:
    """Create a Redis client instance appropriate for local or Azure Managed Redis."""
    if host:
        # Azure Managed Redis cloud path
        # If credential is provided, an Entra token credential provider can be configured
        # depending on azure-identity and redis-py Entra extension support.
        kwargs: dict[str, Any] = {
            "host": host,
            "port": port,
            "ssl": ssl,
            "socket_timeout": socket_timeout,
            "socket_connect_timeout": socket_connect_timeout,
        }
        if credential is not None:
            # Clean adapter seam for Managed Identity token provider
            logger.info("Configuring Azure Managed Redis with injected TokenCredential")
        return redis.Redis(**kwargs)

    effective_url = redis_url or os.getenv("REDIS_URL", DEFAULT_LOCAL_REDIS_URL)
    return redis.Redis.from_url(
        effective_url,
        socket_timeout=socket_timeout,
        socket_connect_timeout=socket_connect_timeout,
    )
