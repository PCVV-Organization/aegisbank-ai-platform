import json
from dataclasses import dataclass
from typing import Any

import pytest

from aegisbank_agent.configuration.config import (
    AppConfigurationCloudProvider,
    AppConfigurationEmulatorProvider,
    EnvironmentConfigurationProvider,
    InvalidConfigurationValue,
    MissingConfigurationKey,
    coerce_bool,
)
from aegisbank_agent.configuration.environment import (
    EnvironmentSelectionError,
    RuntimeEnvironment,
    resolve_runtime_environment,
    validate_runtime_configuration,
)
from aegisbank_agent.configuration.secrets import (
    AzureKeyVaultSecretProvider,
    LocalSyntheticSecretProvider,
    MissingSecret,
)


def test_environment_provider_is_fail_fast(monkeypatch):
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    provider = EnvironmentConfigurationProvider()
    assert provider.require("AEGISBANK_ENV") == "local"
    with pytest.raises(MissingConfigurationKey):
        provider.require("DOES_NOT_EXIST")


def test_emulator_provider_reads_label_and_refreshes(monkeypatch):
    calls = []

    class Response:
        def __enter__(self):
            return self

        def __exit__(self, *args):
            return False

        def read(self):
            return json.dumps({"items": [{"key": "feature.x", "value": "on"}]}).encode()

    def fake_urlopen(request, timeout):
        calls.append(str(request))
        return Response()

    monkeypatch.setattr("urllib.request.urlopen", fake_urlopen)
    provider = AppConfigurationEmulatorProvider(endpoint="http://config", _label="test")
    assert provider.require("feature.x") == "on"
    assert "label=test" in calls[0]
    provider.refresh()
    assert len(calls) == 2


def test_local_secret_provider_is_separate_and_synthetic():
    provider = LocalSyntheticSecretProvider({"synthetic-token": "not-real"})
    assert provider.require("synthetic-token") == "not-real"
    assert provider.get_optional("missing") is None
    with pytest.raises(MissingSecret):
        provider.require("missing")


def test_key_vault_adapter_matches_secret_client_contract():
    @dataclass
    class Secret:
        value: str

    class Client:
        def get_secret(self, name: str) -> Any:
            return Secret("synthetic-key-vault-value")

    assert AzureKeyVaultSecretProvider(Client()).require("api-key") == "synthetic-key-vault-value"


def test_invalid_boolean_fails_fast():
    with pytest.raises(InvalidConfigurationValue):
        coerce_bool("maybe", "enabled")


def test_environment_selection_is_typed_and_keeps_local_manifest_aliases() -> None:
    assert resolve_runtime_environment({"AEGISBANK_ENV": "staging"}) is RuntimeEnvironment.STAGING
    assert resolve_runtime_environment({"AEGISBANK_ENV": "container"}) is RuntimeEnvironment.LOCAL
    with pytest.raises(EnvironmentSelectionError, match="unsupported value"):
        resolve_runtime_environment({"AEGISBANK_ENV": "preview"})


def test_cloud_configuration_rejects_emulator_and_loopback_without_leaking_values() -> None:
    values = {
        "AEGISBANK_USE_APPCONFIG_EMULATOR": "true",
        "COSMOS_ENDPOINT": "http://127.0.0.1:8081",
    }
    with pytest.raises(EnvironmentSelectionError) as error:
        validate_runtime_configuration(RuntimeEnvironment.PRODUCTION, values)
    assert "AEGISBANK_USE_APPCONFIG_EMULATOR" in str(error.value)
    assert "COSMOS_ENDPOINT" in str(error.value)
    assert "127.0.0.1" not in str(error.value)


def test_cloud_provider_uses_injected_mapping_and_refreshes() -> None:
    calls = []

    class MappingProvider(dict):
        def refresh(self) -> None:
            self["AegisBank:Agent:MaxRounds"] = "4"

    def loader() -> MappingProvider:
        calls.append("load")
        return MappingProvider({"AegisBank:Agent:MaxRounds": "3"})

    provider = AppConfigurationCloudProvider(
        endpoint="https://aegisbank.example.azconfig.io",
        _label="staging",
        credential=object(),
        loader=loader,
    )
    assert provider.require("AegisBank:Agent:MaxRounds") == "3"
    provider.refresh()
    assert provider.require("AegisBank:Agent:MaxRounds") == "4"
    assert calls == ["load"]
