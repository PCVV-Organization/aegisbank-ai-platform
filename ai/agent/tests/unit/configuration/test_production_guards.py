"""Unit tests for production fail-closed guards, dotenv restrictions, and cloud boundaries."""

from __future__ import annotations

import os
from pathlib import Path

import pytest

from aegisbank_agent.configuration.config import (
    AppConfigurationCloudProvider,
    ConfigurationError,
    MissingConfigurationKey,
    build_default_provider,
)
from aegisbank_agent.configuration.environment import (
    EnvironmentSelectionError,
    RuntimeEnvironment,
    load_local_dotenv,
    resolve_runtime_environment,
    validate_runtime_configuration,
)
from aegisbank_agent.configuration.secrets import (
    AzureKeyVaultSecretProvider,
    LocalSyntheticSecretProvider,
    build_default_secret_provider,
)


def test_runtime_environment_unknown_value_fails_closed() -> None:
    with pytest.raises(EnvironmentSelectionError, match="must be one of"):
        resolve_runtime_environment({"AEGISBANK_ENV": "unknown-cloud"})


def test_runtime_environment_legacy_aliases_resolve_to_local() -> None:
    assert resolve_runtime_environment({"AEGISBANK_ENV": "container"}) is RuntimeEnvironment.LOCAL
    assert (
        resolve_runtime_environment({"AEGISBANK_ENV": "kubernetes-local"})
        is RuntimeEnvironment.LOCAL
    )


def test_load_local_dotenv_in_cloud_is_noop(monkeypatch, tmp_path: Path) -> None:
    """Proves that .env or .env.local is NEVER loaded in staging or production."""
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    fake_env = tmp_path / ".env.local"
    fake_env.write_text("LEAKED_SECRET_TEST=forbidden_in_prod\n", encoding="utf-8")

    monkeypatch.delenv("LEAKED_SECRET_TEST", raising=False)
    loaded = load_local_dotenv(str(tmp_path))

    assert loaded is False
    assert "LEAKED_SECRET_TEST" not in os.environ


def test_validate_runtime_configuration_passes_valid_staging() -> None:
    valid_staging = {
        "AEGISBANK_ENV": "staging",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank-staging.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank-staging.vault.azure.net/",
    }
    # Should not raise
    validate_runtime_configuration(RuntimeEnvironment.STAGING, valid_staging)


def test_validate_runtime_configuration_rejects_emulators_in_cloud() -> None:
    bad_values = {
        "AEGISBANK_ENV": "production",
        "AEGISBANK_USE_APPCONFIG_EMULATOR": "true",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.PRODUCTION, bad_values)
    assert "AEGISBANK_USE_APPCONFIG_EMULATOR" in str(exc_info.value)


def test_validate_runtime_configuration_rejects_servicebus_emulator() -> None:
    bad_values = {
        "AEGISBANK_ENV": "staging",
        "AEGISBANK_SERVICEBUS_CONN_STR": "Endpoint=sb://127.0.0.1;UseDevelopmentEmulator=true;",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.STAGING, bad_values)
    assert "AEGISBANK_SERVICEBUS_CONN_STR" in str(exc_info.value)


def test_validate_runtime_configuration_rejects_cosmos_emulator_key() -> None:
    bad_values = {
        "AEGISBANK_ENV": "staging",
        "COSMOS_KEY": (
            "C2y6yDjf5/R+ob0N8A7Cgv30VRDJIWEHLM+4QDU5DE2nQ9nDuVTqobD4b8mGGyPMbIZnqyMsEcaGQy67XIw/Jw=="
        ),
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.STAGING, bad_values)
    assert "COSMOS_KEY" in str(exc_info.value)
    # Ensure raw key is NOT printed in the exception
    assert "C2y6yDjf5" not in str(exc_info.value)


def test_validate_runtime_configuration_rejects_loopback_postgres() -> None:
    bad_values = {
        "AEGISBANK_ENV": "production",
        "AEGISBANK_PGVECTOR_URL": "postgresql://aegis_user:aegis_password@localhost:5432/aegis_rag",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.PRODUCTION, bad_values)
    assert "AEGISBANK_PGVECTOR_URL" in str(exc_info.value)
    assert "aegis_password" not in str(exc_info.value)


def test_validate_runtime_configuration_rejects_debug_in_production() -> None:
    bad_values = {
        "AEGISBANK_ENV": "production",
        "DEBUG": "true",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.PRODUCTION, bad_values)
    assert "DEBUG" in str(exc_info.value)


def test_validate_runtime_configuration_rejects_auth_bypass_in_cloud() -> None:
    bad_values = {
        "AEGISBANK_ENV": "staging",
        "TEST_AUTH_BYPASS": "1",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.STAGING, bad_values)
    assert "TEST_AUTH_BYPASS" in str(exc_info.value)


def test_validate_runtime_configuration_rejects_missing_production_vault() -> None:
    bad_values = {
        "AEGISBANK_ENV": "production",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.PRODUCTION, bad_values)
    assert "AZURE_KEY_VAULT_URL" in str(exc_info.value)


def test_cloud_secret_provider_cannot_use_synthetic_provider(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    monkeypatch.setenv("AZURE_KEY_VAULT_URL", "https://aegisbank.vault.azure.net/")

    provider = build_default_secret_provider()
    assert isinstance(provider, AzureKeyVaultSecretProvider)
    assert not isinstance(provider, LocalSyntheticSecretProvider)


def test_cloud_config_provider_fails_closed_missing_endpoint(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    monkeypatch.delenv("AZURE_APPCONFIG_ENDPOINT", raising=False)

    with pytest.raises(MissingConfigurationKey):
        build_default_provider()


def test_cloud_config_provider_rejects_http_in_cloud() -> None:
    with pytest.raises(ConfigurationError, match="must use https"):
        AppConfigurationCloudProvider(
            endpoint="http://insecure-appconfig.azconfig.io",
            _label="production",
        )
