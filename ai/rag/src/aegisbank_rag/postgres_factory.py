"""PostgreSQL / pgvector connection factory supporting local and Entra passwordless paths.

In local mode, connections use standard DSN / connection strings.
In Azure mode (Azure Database for PostgreSQL Flexible Server), connections use
dynamically acquired Microsoft Entra ID access tokens with TLS enforced.
Tokens are acquired just-in-time per connection or pool refresh and NEVER stored permanently.
"""

from __future__ import annotations

import logging
import os
from typing import Any

import psycopg
from pgvector.psycopg import register_vector

logger = logging.getLogger("aegisbank.rag.postgres_factory")


def get_postgres_connection(
    connection_string: str | None = None,
    *,
    host: str | None = None,
    dbname: str | None = None,
    user: str | None = None,
    password: str | None = None,
    port: int = 5432,
    credential: Any = None,
    use_entra_auth: bool = False,
    sslmode: str = "prefer",
) -> psycopg.Connection:
    """Establish a psycopg connection with pgvector registration and optional Entra auth."""
    if use_entra_auth or (credential is not None and not password):
        if not host or not dbname or not user:
            raise ValueError(
                "host, dbname, and user are required for Entra-authenticated PostgreSQL"
            )

        if credential is None:
            env = os.getenv("AEGISBANK_ENV", "").strip().lower()
            if env in {"production", "staging"}:
                from azure.identity import ManagedIdentityCredential

                client_id = os.getenv("AZURE_CLIENT_ID")
                credential = (
                    ManagedIdentityCredential(client_id=client_id)
                    if client_id
                    else ManagedIdentityCredential()
                )
            else:
                from azure.identity import DefaultAzureCredential

                credential = DefaultAzureCredential()

        token = credential.get_token("https://ossrdbms-aad.database.windows.net/.default")
        conn = psycopg.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=token.token,
            port=port,
            sslmode="require",
        )
        register_vector(conn)
        return conn

    effective_dsn = connection_string or os.getenv("AEGISBANK_PGVECTOR_URL")
    if effective_dsn:
        conn = psycopg.connect(effective_dsn)
        register_vector(conn)
        return conn

    if host and dbname:
        conn = psycopg.connect(
            host=host,
            dbname=dbname,
            user=user,
            password=password,
            port=port,
            sslmode=sslmode,
        )
        register_vector(conn)
        return conn

    raise RuntimeError("PostgreSQL configuration requires either connection_string or host/dbname")
