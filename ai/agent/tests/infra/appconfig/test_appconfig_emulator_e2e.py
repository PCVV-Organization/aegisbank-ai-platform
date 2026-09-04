"""Live E2E acceptance tests against Azure App Configuration Emulator container."""

from __future__ import annotations

import json
import urllib.request

import pytest

from aegisbank_agent.configuration.config import (
    AppConfigurationEmulatorProvider,
    MissingConfigurationKey,
    coerce_bool,
    coerce_int,
)
from aegisbank_agent.configuration.secrets import (
    KeyVaultReferenceResolver,
    LocalSyntheticSecretProvider,
)

pytestmark = pytest.mark.infra

EMULATOR_URL = "http://127.0.0.1:8483"


def _has_appconfig_emulator() -> bool:
    """Helper to detect if Azure App Configuration Emulator is healthy."""
    try:
        req = urllib.request.urlopen(f"{EMULATOR_URL}/kv", timeout=1.5)
        return req.status == 200
    except Exception:
        return False


@pytest.mark.skipif(
    not _has_appconfig_emulator(), reason="App Configuration Emulator is not available"
)
def test_appconfig_emulator_kv_lifecycle_and_labels() -> None:
    """Verify live key-value creation, retrieval, labels, and separation across environments."""
    local_provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="local")
    prod_provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="production")

    # Set keys with different labels
    local_provider.set_kv("rag.top_k", "10", label="local")
    prod_provider.set_kv("rag.top_k", "5", label="production")

    local_provider.refresh()
    prod_provider.refresh()

    assert local_provider.get("rag.top_k") == "10"
    assert coerce_int(local_provider.get("rag.top_k"), "rag.top_k") == 10

    assert prod_provider.get("rag.top_k") == "5"
    assert coerce_int(prod_provider.get("rag.top_k"), "rag.top_k") == 5


@pytest.mark.skipif(
    not _has_appconfig_emulator(), reason="App Configuration Emulator is not available"
)
def test_appconfig_emulator_feature_flags() -> None:
    """Verify official feature flag schema storage and retrieval in emulator."""
    provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="local")

    provider.set_feature_flag("agent_write_enabled", enabled=False, label="local")
    provider.refresh()

    raw_ff = provider.get(".appconfig.featureflag/agent_write_enabled")
    assert raw_ff is not None
    ff_data = json.loads(raw_ff)
    assert ff_data["id"] == "agent_write_enabled"
    assert ff_data["enabled"] is False


@pytest.mark.skipif(
    not _has_appconfig_emulator(), reason="App Configuration Emulator is not available"
)
def test_appconfig_emulator_keyvault_reference_resolution() -> None:
    """Verify storing Key Vault reference in App Config and resolving via SecretProvider."""
    config_provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="local")
    secret_provider = LocalSyntheticSecretProvider(
        {
            "db-sa-password": "synthetic-ultra-secure-pass-12345",
        }
    )
    resolver = KeyVaultReferenceResolver(secret_provider=secret_provider)

    # Store Key Vault Reference in App Configuration Emulator
    vault_uri = "https://aegisbank-kv.vault.azure.net/secrets/db-sa-password"
    config_provider.set_keyvault_reference(
        key="db.sa.password.ref",
        vault_uri=vault_uri,
        label="local",
    )
    config_provider.refresh()

    raw_ref = config_provider.get("db.sa.password.ref")
    assert raw_ref is not None

    # Resolution succeeds through SecretProvider
    resolved_secret = resolver.resolve(raw_ref)
    assert resolved_secret == "synthetic-ultra-secure-pass-12345"


@pytest.mark.skipif(
    not _has_appconfig_emulator(), reason="App Configuration Emulator is not available"
)
def test_appconfig_emulator_dynamic_refresh() -> None:
    """Verify runtime dynamic refresh when configuration is modified in emulator."""
    reader_provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="local")
    admin_provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="local")

    admin_provider.set_kv("runtime.test.toggle", "true", label="local")
    reader_provider.refresh()
    assert coerce_bool(reader_provider.get("runtime.test.toggle"), "runtime.test.toggle") is True

    # Mutate value via admin provider in remote store
    admin_provider.set_kv("runtime.test.toggle", "false", label="local")
    # Before reader refresh, reader's cached value remains True
    assert coerce_bool(reader_provider.get("runtime.test.toggle"), "runtime.test.toggle") is True

    # After reader refresh, new value is visible
    reader_provider.refresh()
    assert coerce_bool(reader_provider.get("runtime.test.toggle"), "runtime.test.toggle") is False


@pytest.mark.skipif(
    not _has_appconfig_emulator(), reason="App Configuration Emulator is not available"
)
def test_appconfig_emulator_missing_key_fails_fast() -> None:
    """Verify fail-fast behavior when requiring a non-existent configuration key."""
    provider = AppConfigurationEmulatorProvider(endpoint=EMULATOR_URL, label="local")
    with pytest.raises(MissingConfigurationKey):
        provider.require("non.existent.parameter.aegisbank")
