"""Canonical secret provider and Key Vault adapter for AegisBank.

Strictly separated from configuration (:mod:`~aegisbank_agent.configuration.config`):
* Configuration = non-secret application settings (feature flags, timeouts).
* Secrets = sensitive credentials (passwords, private keys, API tokens).

In compliance with banking security principles:
* Secrets are never logged or exposed in audit trails without redaction.
* Real Azure Key Vault access is tagged ``CLOUD-KEYVAULT-PENDING``.
* Local development and testing use :class:`LocalSyntheticSecretProvider`
  (tagged ``LOCAL-SECRETS-COVERED``) with strictly synthetic values.
"""

from __future__ import annotations

import json
import logging
import os
import re
from dataclasses import dataclass, field
from typing import Any, Mapping, Protocol, runtime_checkable

from .environment import EnvironmentSelectionError, resolve_runtime_environment

logger = logging.getLogger(__name__)


class SecretError(RuntimeError):
    """Base exception for secret resolution and provider errors."""


class MissingSecret(SecretError):  # noqa: N818
    """Raised when a requested secret does not exist."""


class SecretAccessDenied(SecretError):  # noqa: N818
    """Raised when access to a secret is denied (RBAC/authentication error)."""


@dataclass(frozen=True, slots=True)
class SecretSource:
    """Audit descriptor of where a secret value was retrieved from."""

    name: str
    vault_url: str | None = None
    version: str | None = None


@runtime_checkable
class SecretProvider(Protocol):
    """Canonical protocol for secret resolution."""

    name: str

    def get(self, name: str, version: str | None = None) -> str: ...

    def get_optional(self, name: str, version: str | None = None) -> str | None: ...

    def require(self, name: str, version: str | None = None) -> str: ...

    def describe(self, name: str) -> SecretSource | None: ...


@dataclass(slots=True)
class LocalSyntheticSecretProvider:
    """In-memory synthetic secret provider for local development and unit tests.

    Tagged: ``LOCAL-SECRETS-COVERED``
    """

    _secrets: dict[str, str] = field(default_factory=dict)
    name: str = "local-synthetic-secrets"

    def __init__(self, secrets: Mapping[str, str] | None = None) -> None:
        self._secrets = dict(secrets or {})
        self.name = "local-synthetic-secrets"

    def set_secret(self, name: str, value: str) -> None:
        """Store a synthetic secret in the local memory store."""
        self._secrets[name] = value

    def get(self, name: str, version: str | None = None) -> str:
        return self.require(name, version=version)

    def get_optional(self, name: str, version: str | None = None) -> str | None:
        if version:
            v_key = f"{name}/{version}"
            if v_key in self._secrets:
                return self._secrets[v_key]
        return self._secrets.get(name)

    def require(self, name: str, version: str | None = None) -> str:
        val = self.get_optional(name, version=version)
        if val is None:
            raise MissingSecret(f"Secret '{name}' not found in {self.name}")
        return val

    def describe(self, name: str) -> SecretSource | None:
        if name not in self._secrets:
            return None
        return SecretSource(name=name, vault_url="local://synthetic")


@dataclass(slots=True)
class AzureKeyVaultSecretProvider:
    """Adapter for Azure Key Vault ``SecretClient`` contract.

    Tagged: ``CLOUD-KEYVAULT-PENDING``
    Real cloud access requires Azure infrastructure, Microsoft Entra ID,
    and RBAC assignment ('Key Vault Secrets User').
    """

    _client: Any = None
    vault_url: str | None = None
    name: str = "azure-key-vault"

    def __init__(
        self,
        client: Any = None,
        vault_url: str | None = None,
        credential: Any = None,
    ) -> None:
        self.name = "azure-key-vault"
        self.vault_url = vault_url
        if client is not None:
            self._client = client
        elif vault_url is not None:
            # Lazy import to keep azure-keyvault-secrets optional at import time
            from azure.keyvault.secrets import SecretClient

            from .identity import resolve_azure_credential

            cred = credential or resolve_azure_credential()
            self._client = SecretClient(vault_url=vault_url, credential=cred)
        else:
            self._client = None

    def get(self, name: str, version: str | None = None) -> str:
        return self.require(name, version=version)

    def get_optional(self, name: str, version: str | None = None) -> str | None:
        try:
            return self.require(name, version=version)
        except MissingSecret:
            return None

    def require(self, name: str, version: str | None = None) -> str:
        if self._client is None:
            raise SecretError("AzureKeyVaultSecretProvider has no active SecretClient configured")
        try:
            secret = (
                self._client.get_secret(name, version=version)
                if version
                else self._client.get_secret(name)
            )
            if hasattr(secret, "value"):
                return str(secret.value)
            return str(secret)
        except Exception as exc:
            exc_type = type(exc).__name__
            exc_str = str(exc).lower()
            if "notfound" in exc_type.lower() or "404" in exc_str or "not found" in exc_str:
                raise MissingSecret(f"Secret '{name}' not found in Key Vault") from exc
            if (
                "authentication" in exc_str
                or "denied" in exc_str
                or "401" in exc_str
                or "403" in exc_str
            ):
                raise SecretAccessDenied(f"Access to secret '{name}' was denied") from exc
            raise SecretError(f"Failed to retrieve secret '{name}': {exc}") from exc

    def describe(self, name: str) -> SecretSource | None:
        return SecretSource(name=name, vault_url=self.vault_url)


class _ResolveDispatcher:
    """Dispatches resolve whether called as a classmethod or instance method."""

    def __get__(self, instance: Any, owner: Any) -> Any:
        if instance is None:

            def _class_resolve(
                reference: str, secret_provider: SecretProvider | None = None
            ) -> str:
                _, secret_name, version = owner.parse_secret_identifier(reference)
                provider = secret_provider or get_default_secret_provider()
                try:
                    return provider.require(secret_name, version=version)
                except TypeError:
                    return provider.require(secret_name)

            return _class_resolve

        def _instance_resolve(reference: str, secret_provider: SecretProvider | None = None) -> str:
            _, secret_name, version = owner.parse_secret_identifier(reference)
            provider = secret_provider or instance.secret_provider or get_default_secret_provider()
            try:
                return provider.require(secret_name, version=version)
            except TypeError:
                return provider.require(secret_name)

            return _instance_resolve

        return _instance_resolve


class KeyVaultReferenceResolver:
    """Resolves Azure App Configuration Key Vault References into actual secret values.

    Pattern:
    App Configuration stores a reference pointing to a Key Vault URI:
    ``{"uri": "https://<vault-name>.vault.azure.net/secrets/<secret-name>"}``
    The application parses the reference and resolves the actual credential
    via an authorized :class:`SecretProvider`.
    """

    URI_PATTERN = re.compile(
        r"https?://(?P<vault>[^/]+)/secrets/(?P<name>[^/]+)(?:/(?P<version>[^/?#]+))?"
    )

    secret_provider: SecretProvider | None = None

    def __init__(self, secret_provider: SecretProvider | None = None) -> None:
        self.secret_provider = secret_provider

    @classmethod
    def parse_secret_identifier(cls, reference: str) -> tuple[str, str, str | None]:
        """Extract (vault_name, secret_name, version) from a Key Vault URI or JSON payload."""
        trimmed = reference.strip()
        uri = trimmed
        if trimmed.startswith("{"):
            try:
                parsed = json.loads(trimmed)
                uri = parsed.get("uri", "")
            except json.JSONDecodeError as exc:
                raise SecretError(f"Malformed Key Vault reference JSON: {reference!r}") from exc

        match = cls.URI_PATTERN.match(uri)
        if not match:
            raise SecretError(f"Invalid Key Vault URI in reference: {reference!r}")

        return match.group("vault"), match.group("name"), match.group("version")

    resolve = _ResolveDispatcher()


_DEFAULT_SECRET_PROVIDER: SecretProvider | None = None


def build_default_secret_provider() -> SecretProvider:
    """Select synthetic local secrets or the Azure Key Vault provider explicitly.

    Staging and production never fall back to synthetic values. The Key Vault
    URL is intentionally bootstrap-only; credentials come from
    ``resolve_azure_credential()`` inside the adapter.
    """
    from .identity import resolve_azure_credential

    environment = resolve_runtime_environment()
    if not environment.is_cloud:
        return LocalSyntheticSecretProvider()
    vault_url = os.getenv("AZURE_KEY_VAULT_URL", "")
    if not vault_url.startswith("https://"):
        raise EnvironmentSelectionError("AZURE_KEY_VAULT_URL must use https in cloud environments")
    cred = resolve_azure_credential(environment)
    return AzureKeyVaultSecretProvider(vault_url=vault_url, credential=cred)


def get_default_secret_provider() -> SecretProvider:
    """Return the process-wide default secret provider."""
    global _DEFAULT_SECRET_PROVIDER
    if _DEFAULT_SECRET_PROVIDER is None:
        _DEFAULT_SECRET_PROVIDER = build_default_secret_provider()
    return _DEFAULT_SECRET_PROVIDER


def set_default_secret_provider(provider: SecretProvider | None) -> None:
    """Set the process-wide default secret provider (testing hook)."""
    global _DEFAULT_SECRET_PROVIDER
    _DEFAULT_SECRET_PROVIDER = provider


def reset_default_secret_provider() -> None:
    """Reset default secret provider to uninitialized state."""
    set_default_secret_provider(None)
