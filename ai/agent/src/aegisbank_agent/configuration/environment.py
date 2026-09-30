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


def validate_runtime_configuration(
    environment: RuntimeEnvironment,
    values: Mapping[str, str] | None = None,
) -> None:
    """Fail closed for cloud selections that still point at local infrastructure.

    The error identifies only unsafe keys.  It never includes a value because a
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
    if "usedevelopmentemulator=true" in connection_string.lower():
        problems.append("AEGISBANK_SERVICEBUS_CONN_STR")
    for key in _LOCAL_ONLY_KEYS:
        if is_local_endpoint(source.get(key)):
            problems.append(key)
    if environment is RuntimeEnvironment.PRODUCTION and not source.get("AZURE_APPCONFIG_ENDPOINT"):
        problems.append("AZURE_APPCONFIG_ENDPOINT")
    if problems:
        raise EnvironmentSelectionError(
            "Cloud environment rejects local, emulator, or missing bootstrap settings: "
            + ", ".join(sorted(set(problems)))
        )
