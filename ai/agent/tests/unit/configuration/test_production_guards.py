"""Unit tests for production fail-closed guards, dotenv restrictions, and cloud boundaries."""

from __future__ import annotations

import os
import sys
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


def test_load_local_dotenv_upward_discovery(monkeypatch, tmp_path: Path) -> None:
    """Find the nearest .env.local without crossing the repository boundary."""
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    parent_dir = tmp_path / "repo"
    sub_dir = parent_dir / "ai" / "agent"
    sub_dir.mkdir(parents=True)
    (parent_dir / ".git").mkdir()
    fake_env = parent_dir / ".env.local"
    fake_env.write_text("UPWARD_DISCOVERY_TEST=found_in_parent\n", encoding="utf-8")

    monkeypatch.chdir(sub_dir)
    monkeypatch.delenv("UPWARD_DISCOVERY_TEST", raising=False)
    loaded = load_local_dotenv()

    assert loaded is True
    assert os.environ.get("UPWARD_DISCOVERY_TEST") == "found_in_parent"


def test_load_local_dotenv_without_git_boundary_stays_in_cwd(monkeypatch, tmp_path: Path) -> None:
    """Do not discover an unrelated parent dotenv outside a Git checkout."""
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    parent_dir = tmp_path / "unrelated-parent"
    working_dir = parent_dir / "nested"
    working_dir.mkdir(parents=True)
    (parent_dir / ".env.local").write_text(
        "OUTSIDE_GIT_DOTENV_TEST=must_not_load\n", encoding="utf-8"
    )
    monkeypatch.chdir(working_dir)
    monkeypatch.delenv("OUTSIDE_GIT_DOTENV_TEST", raising=False)

    loaded = load_local_dotenv()

    assert loaded is False
    assert "OUTSIDE_GIT_DOTENV_TEST" not in os.environ


def test_load_local_dotenv_merges_nearest_to_root(monkeypatch, tmp_path: Path) -> None:
    """Nearest values win while the root file supplies variables not overridden."""
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    repo_root = tmp_path / "repo"
    nested_dir = repo_root / "ai" / "agent"
    nested_dir.mkdir(parents=True)
    (repo_root / ".git").mkdir()
    (repo_root / ".env.local").write_text(
        "DOTENV_NEAREST_TEST=root\nDOTENV_ROOT_ONLY_TEST=root\n", encoding="utf-8"
    )
    (nested_dir / ".env.local").write_text("DOTENV_NEAREST_TEST=nested\n", encoding="utf-8")

    monkeypatch.chdir(nested_dir)
    monkeypatch.delenv("DOTENV_NEAREST_TEST", raising=False)
    monkeypatch.delenv("DOTENV_ROOT_ONLY_TEST", raising=False)

    loaded = load_local_dotenv()

    assert loaded is True
    assert os.environ["DOTENV_NEAREST_TEST"] == "nested"
    assert os.environ["DOTENV_ROOT_ONLY_TEST"] == "root"


def test_load_local_dotenv_prefers_process_environment(monkeypatch, tmp_path: Path) -> None:
    """Existing shell values take precedence over local dotenv values."""
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    fake_env = tmp_path / ".env.local"
    fake_env.write_text(
        "DOTENV_PRECEDENCE_TEST=from_file\nDOTENV_FILE_ONLY_TEST=from_file\n",
        encoding="utf-8",
    )
    monkeypatch.setenv("DOTENV_PRECEDENCE_TEST", "from_process")
    monkeypatch.delenv("DOTENV_FILE_ONLY_TEST", raising=False)

    loaded = load_local_dotenv(str(tmp_path))

    assert loaded is True
    assert os.environ["DOTENV_PRECEDENCE_TEST"] == "from_process"
    assert os.environ["DOTENV_FILE_ONLY_TEST"] == "from_file"


def test_load_local_dotenv_does_not_read_plain_dotenv(monkeypatch, tmp_path: Path) -> None:
    """Only the explicit .env.local filename is eligible for application loading."""
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    (tmp_path / ".env").write_text("PLAIN_DOTENV_TEST=wrong_file\n", encoding="utf-8")
    (tmp_path / ".env.local").write_text("LOCAL_DOTENV_TEST=selected_file\n", encoding="utf-8")
    monkeypatch.delenv("PLAIN_DOTENV_TEST", raising=False)
    monkeypatch.delenv("LOCAL_DOTENV_TEST", raising=False)

    loaded = load_local_dotenv(str(tmp_path))

    assert loaded is True
    assert "PLAIN_DOTENV_TEST" not in os.environ
    assert os.environ["LOCAL_DOTENV_TEST"] == "selected_file"


def test_load_local_dotenv_reports_missing_dependency(monkeypatch, tmp_path: Path) -> None:
    """Do not silently ignore an existing local file when python-dotenv is absent."""
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    (tmp_path / ".env.local").write_text("DOTENV_DEPENDENCY_TEST=value\n", encoding="utf-8")
    monkeypatch.setitem(sys.modules, "dotenv", None)

    with pytest.raises(RuntimeError, match="python-dotenv is required"):
        load_local_dotenv(str(tmp_path))


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


def test_validate_runtime_configuration_rejects_direct_database_url_in_cloud() -> None:
    bad_values = {
        "AEGISBANK_ENV": "staging",
        "AEGISBANK_DATABASE_URL": "sqlite:////app/data/aegisbank.db",
        "AZURE_APPCONFIG_ENDPOINT": "https://aegisbank.azconfig.io",
        "AZURE_KEY_VAULT_URL": "https://aegisbank.vault.azure.net/",
    }
    with pytest.raises(EnvironmentSelectionError) as exc_info:
        validate_runtime_configuration(RuntimeEnvironment.STAGING, bad_values)
    assert "AEGISBANK_DATABASE_URL" in str(exc_info.value)
