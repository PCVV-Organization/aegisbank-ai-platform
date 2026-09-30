"""Unit coverage for cloud identity paths without Azure network access."""

from __future__ import annotations

from aegisbank_agent.cosmos import CosmosRepository
from aegisbank_agent.reliability.azure_servicebus_adapter import AzureServiceBusMessageBus


def test_service_bus_uses_injected_managed_identity_path(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    captured = {}

    class Client:
        def __init__(self, **kwargs):
            captured.update(kwargs)

    monkeypatch.setattr(
        "aegisbank_agent.reliability.azure_servicebus_adapter.ServiceBusClient", Client
    )
    credential = object()
    adapter = AzureServiceBusMessageBus(
        fully_qualified_namespace="aegisbank.servicebus.windows.net",
        credential=credential,
    )
    assert adapter.connection_string is None
    assert adapter._get_client() is not None
    assert captured == {
        "fully_qualified_namespace": "aegisbank.servicebus.windows.net",
        "credential": credential,
    }


def test_cosmos_uses_injected_credential_in_cloud(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    credential = object()
    captured = {}

    class Client:
        def __init__(self, endpoint, credential):
            captured["endpoint"] = endpoint
            captured["credential"] = credential

    monkeypatch.setattr("aegisbank_agent.cosmos.CosmosClient", Client)
    repository = CosmosRepository(
        endpoint="https://aegisbank.documents.azure.com:443/",
        credential=credential,
    )
    assert repository._get_client() is not None
    assert captured["credential"] is credential


def test_service_bus_rejects_a_client_without_a_connection_target(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "local")
    monkeypatch.delenv("AEGISBANK_SERVICEBUS_NAMESPACE", raising=False)
    monkeypatch.delenv("AEGISBANK_SERVICEBUS_CONN_STR", raising=False)

    adapter = AzureServiceBusMessageBus(connection_string="")
    adapter.connection_string = None

    import pytest

    with pytest.raises(RuntimeError, match="requires either"):
        adapter._get_client()
