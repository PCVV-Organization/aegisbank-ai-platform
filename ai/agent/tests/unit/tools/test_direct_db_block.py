"""Unit tests verifying that Agent direct database access is blocked in cloud environments."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aegisbank_agent.configuration.environment import RuntimeEnvironment
from aegisbank_agent.tools.banking_tools import create_default_database
from aegisbank_agent.tools.core_banking_client import (
    CoreBankingHttpClient,
    EntraServiceAuthHandler,
)


def test_create_default_database_allowed_in_local(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    monkeypatch.delenv("AEGISBANK_DATABASE_URL", raising=False)
    db = create_default_database()
    assert db is not None


def test_create_default_database_blocked_in_staging(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    monkeypatch.setenv("AEGISBANK_DATABASE_URL", "sqlite:////app/data/aegisbank.db")
    with patch(
        "aegisbank_agent.configuration.environment.resolve_runtime_environment",
        return_value=RuntimeEnvironment.STAGING,
    ):
        with pytest.raises(RuntimeError, match="Direct Core Banking database access is prohibited"):
            create_default_database()


def test_create_default_database_blocked_in_production(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    monkeypatch.setenv("AEGISBANK_DATABASE_URL", "sqlite:////app/data/aegisbank.db")
    with patch(
        "aegisbank_agent.configuration.environment.resolve_runtime_environment",
        return_value=RuntimeEnvironment.PRODUCTION,
    ):
        with pytest.raises(RuntimeError, match="Direct Core Banking database access is prohibited"):
            create_default_database()


def test_core_banking_client_service_auth_header() -> None:
    token_provider = MagicMock()
    token_mock = MagicMock()
    token_mock.token = "fake-entra-service-token"
    token_provider.get_token.return_value = token_mock

    auth_handler = EntraServiceAuthHandler(
        audience="api://mock-core-banking/.default",
        credential=token_provider,
    )
    headers = auth_handler.get_auth_headers()
    assert headers["Authorization"] == "Bearer fake-entra-service-token"

    client = CoreBankingHttpClient(
        base_url="http://mock-core-banking:8000",
        auth_handler=auth_handler,
    )
    with patch("urllib.request.urlopen") as mock_urlopen:
        mock_resp = MagicMock()
        mock_resp.read.return_value = b'{"success": true}'
        mock_urlopen.return_value.__enter__.return_value = mock_resp

        result = client.post("/api/v1/accounts", {"account_id": "ACC-01"})
        assert result == {"success": True}
        req = mock_urlopen.call_args[0][0]
        assert req.headers["Authorization"] == "Bearer fake-entra-service-token"
        assert req.headers["Content-type"] == "application/json"
