"""Unit tests for Azure PostgreSQL Flexible Server Entra ID connection factory."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

import pytest

from aegisbank_rag.postgres_factory import get_postgres_connection


def test_postgres_factory_local_dsn() -> None:
    mock_conn = MagicMock()
    with patch("psycopg.connect", return_value=mock_conn) as mock_connect:
        with patch("aegisbank_rag.postgres_factory.register_vector") as mock_reg:
            conn = get_postgres_connection(
                "postgresql://aegisuser:password@localhost:5432/aegisbank_rag"
            )
            assert conn is mock_conn
            mock_connect.assert_called_once_with(
                "postgresql://aegisuser:password@localhost:5432/aegisbank_rag"
            )
            mock_reg.assert_called_once_with(mock_conn)


def test_postgres_factory_entra_token() -> None:
    mock_token = MagicMock()
    mock_token.token = "fake-entra-access-token"

    mock_credential = MagicMock()
    mock_credential.get_token.return_value = mock_token

    mock_conn = MagicMock()
    with patch("psycopg.connect", return_value=mock_conn) as mock_connect:
        with patch("aegisbank_rag.postgres_factory.register_vector") as mock_reg:
            conn = get_postgres_connection(
                host="aegisbank-psql.postgres.database.azure.com",
                port=5432,
                dbname="aegisbank_rag",
                user="aegis_workload_identity",
                credential=mock_credential,
                use_entra_auth=True,
            )
            assert conn is mock_conn
            mock_credential.get_token.assert_called_once_with(
                "https://ossrdbms-aad.database.windows.net/.default"
            )
            mock_connect.assert_called_once_with(
                host="aegisbank-psql.postgres.database.azure.com",
                port=5432,
                dbname="aegisbank_rag",
                user="aegis_workload_identity",
                password="fake-entra-access-token",
                sslmode="require",
            )
            mock_reg.assert_called_once_with(mock_conn)


def test_postgres_factory_requires_configuration() -> None:
    with pytest.raises(RuntimeError, match="requires either connection_string or host/dbname"):
        get_postgres_connection()
