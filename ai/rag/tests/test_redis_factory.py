"""Unit tests for Redis connection and client factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from aegisbank_rag.redis_factory import create_redis_client


def test_create_redis_client_local_url() -> None:
    with patch("redis.Redis.from_url") as mock_from_url:
        mock_client = MagicMock()
        mock_from_url.return_value = mock_client

        client = create_redis_client("redis://127.0.0.1:6379/0")
        assert client is mock_client
        mock_from_url.assert_called_once_with(
            "redis://127.0.0.1:6379/0",
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )


def test_create_redis_client_azure_host() -> None:
    with patch("redis.Redis") as mock_redis_cls:
        mock_client = MagicMock()
        mock_redis_cls.return_value = mock_client

        mock_credential = MagicMock()
        client = create_redis_client(
            host="aegisbank-cache.redis.cache.windows.net",
            port=6380,
            ssl=True,
            credential=mock_credential,
        )
        assert client is mock_client
        mock_redis_cls.assert_called_once_with(
            host="aegisbank-cache.redis.cache.windows.net",
            port=6380,
            ssl=True,
            socket_timeout=1.0,
            socket_connect_timeout=1.0,
        )
