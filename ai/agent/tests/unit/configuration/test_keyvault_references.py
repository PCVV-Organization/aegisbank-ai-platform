"""Unit tests for Key Vault Reference resolution and secret provider boundaries."""

from __future__ import annotations

import pytest

from aegisbank_agent.configuration.environment import EnvironmentSelectionError
from aegisbank_agent.configuration.secrets import (
    AzureKeyVaultSecretProvider,
    KeyVaultReferenceResolver,
    LocalSyntheticSecretProvider,
    MissingSecret,
    SecretAccessDenied,
    SecretError,
    build_default_secret_provider,
    get_default_secret_provider,
    reset_default_secret_provider,
    set_default_secret_provider,
)


def test_keyvault_reference_resolver_json_payload() -> None:
    provider = LocalSyntheticSecretProvider({"db-password": "synthetic-password-123"})
    reference_json = '{"uri": "https://aegisbank-kv.vault.azure.net/secrets/db-password"}'
    vault, name, version = KeyVaultReferenceResolver.parse_secret_identifier(reference_json)
    assert vault == "aegisbank-kv.vault.azure.net"
    assert name == "db-password"
    assert version is None

    resolved = KeyVaultReferenceResolver.resolve(reference_json, secret_provider=provider)
    assert resolved == "synthetic-password-123"


def test_keyvault_reference_resolver_raw_versioned_uri() -> None:
    provider = LocalSyntheticSecretProvider({"api-key": "synthetic-key-abc"})
    uri = "https://aegisbank-kv.vault.azure.net/secrets/api-key/7a8b9c0d1e2f"
    vault, name, version = KeyVaultReferenceResolver.parse_secret_identifier(uri)
    assert vault == "aegisbank-kv.vault.azure.net"
    assert name == "api-key"
    assert version == "7a8b9c0d1e2f"

    resolved = KeyVaultReferenceResolver.resolve(uri, secret_provider=provider)
    assert resolved == "synthetic-key-abc"


def test_keyvault_reference_resolver_malformed_formats() -> None:
    with pytest.raises(SecretError, match="Malformed Key Vault reference JSON"):
        KeyVaultReferenceResolver.parse_secret_identifier("{not valid json}")

    with pytest.raises(SecretError, match="Invalid Key Vault URI"):
        KeyVaultReferenceResolver.parse_secret_identifier("https://invalid-uri/not-secrets/test")


def test_keyvault_reference_resolver_missing_secret() -> None:
    provider = LocalSyntheticSecretProvider({"other-secret": "val"})
    ref = '{"uri": "https://aegisbank-kv.vault.azure.net/secrets/non-existent"}'
    with pytest.raises(MissingSecret):
        KeyVaultReferenceResolver.resolve(ref, secret_provider=provider)


def test_azure_keyvault_provider_access_denied_mapping() -> None:
    class MockDeniedClient:
        def get_secret(self, name: str):
            raise RuntimeError("ClientAuthenticationError: 403 Forbidden - Access denied by policy")

    provider = AzureKeyVaultSecretProvider(client=MockDeniedClient())
    with pytest.raises(SecretAccessDenied, match="Access to secret 'restricted' was denied"):
        provider.require("restricted")


def test_azure_keyvault_provider_not_found_mapping() -> None:
    class MockNotFoundClient:
        def get_secret(self, name: str):
            raise RuntimeError("ResourceNotFoundError: 404 Secret not found")

    provider = AzureKeyVaultSecretProvider(client=MockNotFoundClient())
    with pytest.raises(MissingSecret, match="Secret 'unknown' not found in Key Vault"):
        provider.require("unknown")
    assert provider.get_optional("unknown") is None


def test_default_secret_provider_lifecycle() -> None:
    reset_default_secret_provider()
    default_p = get_default_secret_provider()
    assert isinstance(default_p, LocalSyntheticSecretProvider)

    custom_p = LocalSyntheticSecretProvider({"custom": "val"})
    set_default_secret_provider(custom_p)
    assert get_default_secret_provider() is custom_p
    assert get_default_secret_provider().require("custom") == "val"

    reset_default_secret_provider()
    assert get_default_secret_provider() is not custom_p


def test_cloud_secret_provider_fails_closed_without_key_vault(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    monkeypatch.delenv("AZURE_KEY_VAULT_URL", raising=False)
    with pytest.raises(EnvironmentSelectionError, match="AZURE_KEY_VAULT_URL"):
        build_default_secret_provider()


def test_cloud_secret_provider_uses_key_vault_adapter(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://aegisbank.vault.azure.net")
    captured = {}

    def fake_provider(*, vault_url):
        captured["vault_url"] = vault_url
        return LocalSyntheticSecretProvider()

    monkeypatch.setattr(
        "aegisbank_agent.configuration.secrets.AzureKeyVaultSecretProvider", fake_provider
    )
    assert isinstance(build_default_secret_provider(), LocalSyntheticSecretProvider)
    assert captured["vault_url"] == "https://aegisbank.vault.azure.net"
