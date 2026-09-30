"""Typed runtime-environment selection and cloud safety guards.

This module is deliberately independent from configuration and secret providers so
those providers can use it during their own bootstrap.  It contains no network
calls and never logs configuration values.
"""

from __future__ import annotations

from enum import StrEnum
from typing import Mapping
from urllib.parse import urlparse


class EnvironmentSelectionError(RuntimeError):
    """Raised when a runtime environment is absent, unknown, or unsafe."""


class RuntimeEnvironment(StrEnum):
    """Supported logical environments for the application runtime."""

    LOCAL = "local"
    TEST = "test"
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"

    @property
    def is_cloud(self) -> bool:
        return self in {self.STAGING, self.PRODUCTION}


_LEGACY_LOCAL_ALIASES = {
    "container": RuntimeEnvironment.LOCAL,
    "kubernetes-local": RuntimeEnvironment.LOCAL,
}


def resolve_runtime_environment(values: Mapping[str, str] | None = None) -> RuntimeEnvironment:
    """Return the explicit logical environment, rejecting unknown values.

    ``container`` and ``kubernetes-local`` are retained as documented local
    compatibility aliases for the existing Compose and Kubernetes manifests.
    They are never treated as cloud environments.
    """
    import os

    source = os.environ if values is None else values
    raw = source.get("AEGISBANK_ENV", RuntimeEnvironment.LOCAL.value).strip().lower()
    if raw in _LEGACY_LOCAL_ALIASES:
        return _LEGACY_LOCAL_ALIASES[raw]
    try:
        return RuntimeEnvironment(raw)
    except ValueError as exc:
        allowed = ", ".join(item.value for item in RuntimeEnvironment)
        raise EnvironmentSelectionError(
            f"AEGISBANK_ENV must be one of: {allowed}; received an unsupported value"
        ) from exc


def is_local_endpoint(value: str | None) -> bool:
    """Identify explicit loopback endpoints without imposing an HTTPS-only policy."""
    if not value:
        return False
    parsed = urlparse(value)
    host = (parsed.hostname or "").lower()
    return host in {"localhost", "127.0.0.1", "::1", "0.0.0.0"}


def _is_enabled(value: str | None) -> bool:
    return (value or "").strip().lower() in {"1", "true", "yes", "on"}


_LOCAL_ONLY_KEYS = (
    "AEGISBANK_APPCONFIG_EMULATOR_URL",
    "AEGISBANK_FOUNDRY_LOCAL_BASE_URL",
    "AEGISBANK_CORE_BANKING_URL",
    "CORE_BANKING_URL",
    "COSMOS_ENDPOINT",
    "REDIS_URL",
    "AEGISBANK_PGVECTOR_URL",
)

_KNOWN_EMULATOR_KEYS = {
    "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw==",
}


def load_local_dotenv(base_dir: str | None = None) -> bool:
    """Load a developer .env.local file for a local workflow only.

    CRITICAL INVARIANT:
    In cloud environments (staging or production), this function is an absolute NO-OP
    and NEVER loads any developer dotenv file.
    """
    from pathlib import Path

    env = resolve_runtime_environment()
    if env.is_cloud:
        return False

    search_root = Path(base_dir) if base_dir else Path.cwd()
    candidates = [search_root / ".env.local"]
    for candidate in candidates:
        if candidate.is_file():
            try:
                from dotenv import load_dotenv

                load_dotenv(candidate, override=False)
                return True
            except ImportError:
                pass
    return False


def validate_runtime_configuration(
    environment: RuntimeEnvironment,
    values: Mapping[str, str] | None = None,
) -> None:
    """Fail closed for cloud selections that still point at local infrastructure.

    The error identifies only unsafe keys. It never includes a value because a
    connection string or endpoint can itself be sensitive operational metadata.
    """
    import os

    if not environment.is_cloud:
        return
    source = os.environ if values is None else values
    problems: list[str] = []

    if _is_enabled(source.get("AEGISBANK_USE_APPCONFIG_EMULATOR")):
        problems.append("AEGISBANK_USE_APPCONFIG_EMULATOR")

    connection_string = source.get("AEGISBANK_SERVICEBUS_CONN_STR", "")
    lowered_conn = connection_string.lower()
    if (
        "usedevelopmentemulator=true" in lowered_conn
        or "sb://127.0.0.1" in lowered_conn
        or "sb://localhost" in lowered_conn
    ):
        problems.append("AEGISBANK_SERVICEBUS_CONN_STR")

    for key in _LOCAL_ONLY_KEYS:
        val = source.get(key)
        if val and is_local_endpoint(val):
            problems.append(key)

    cosmos_key = source.get("COSMOS_KEY", "")
    if cosmos_key and cosmos_key in _KNOWN_EMULATOR_KEYS:
        problems.append("COSMOS_KEY")

    cosmos_endpoint = source.get("COSMOS_ENDPOINT", "")
    if cosmos_endpoint and (":8081" in cosmos_endpoint or is_local_endpoint(cosmos_endpoint)):
        problems.append("COSMOS_ENDPOINT")

    pg_url = source.get("AEGISBANK_PGVECTOR_URL", "")
    if pg_url and ("aegis_password" in pg_url or is_local_endpoint(pg_url)):
        problems.append("AEGISBANK_PGVECTOR_URL")

    if source.get("AEGISBANK_DATABASE_URL"):
        problems.append("AEGISBANK_DATABASE_URL")

    if _is_enabled(source.get("TEST_AUTH_BYPASS")) or _is_enabled(
        source.get("AEGISBANK_TEST_AUTH_BYPASS")
    ):
        problems.append("TEST_AUTH_BYPASS")

    if environment is RuntimeEnvironment.PRODUCTION:
        if _is_enabled(source.get("DEBUG")) or _is_enabled(source.get("AEGISBANK_DEBUG")):
            problems.append("DEBUG")

        appconfig_ep = source.get("AZURE_APPCONFIG_ENDPOINT", "")
        if not appconfig_ep or not appconfig_ep.startswith("https://"):
            problems.append("AZURE_APPCONFIG_ENDPOINT")

        kv_url = source.get("AZURE_KEY_VAULT_URL", "")
        if not kv_url or not kv_url.startswith("https://"):
            problems.append("AZURE_KEY_VAULT_URL")
    else:
        appconfig_ep = source.get("AZURE_APPCONFIG_ENDPOINT", "")
        if appconfig_ep and not appconfig_ep.startswith("https://"):
            problems.append("AZURE_APPCONFIG_ENDPOINT")

        kv_url = source.get("AZURE_KEY_VAULT_URL", "")
        if kv_url and not kv_url.startswith("https://"):
            problems.append("AZURE_KEY_VAULT_URL")

    if problems:
        raise EnvironmentSelectionError(
            "Cloud environment rejects local, emulator, or missing bootstrap settings: "
            + ", ".join(sorted(set(problems)))
        )
