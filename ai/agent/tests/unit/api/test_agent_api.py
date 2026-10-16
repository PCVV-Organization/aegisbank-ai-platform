"""Unit tests for Agent Hosted HTTP API, health probes, and cloud authentication boundary."""

from __future__ import annotations

from unittest.mock import MagicMock, patch

from starlette.testclient import TestClient

from aegisbank_agent.api import AuthenticationProvider, PrincipalContext, app, create_app
from aegisbank_agent.configuration.environment import RuntimeEnvironment


def test_agent_api_health_live() -> None:
    client = TestClient(app)
    response = client.get("/health/live")
    assert response.status_code == 200
    assert response.json()["status"] == "alive"


def test_agent_api_health_ready_local() -> None:
    client = TestClient(app)
    response = client.get("/health/ready")
    assert response.status_code == 200
    assert response.json()["status"] == "ready"


def test_agent_api_openapi_schema() -> None:
    client = TestClient(app)
    response = client.get("/openapi.json")
    assert response.status_code == 200
    data = response.json()
    assert "paths" in data
    assert "/health/live" in data["paths"]
    assert "/health/ready" in data["paths"]
    assert "/api/v1/agent/run" in data["paths"]


def test_agent_api_run_local_success(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "local")

    mock_result = MagicMock()
    mock_result.answer = "El saldo de tu cuenta es S/ 1,500.00."
    mock_result.customer_id = "CUST-0001"
    mock_result.rounds = 1
    mock_result.tool_calls = []

    mock_orch = MagicMock()
    mock_orch.run.return_value = mock_result
    test_app = create_app(orchestrator=mock_orch)
    client = TestClient(test_app)

    response = client.post(
        "/api/v1/agent/run",
        json={
            "query": "Consultar saldo",
            "customer_id": "CUST-0001",
        },
    )
    assert response.status_code == 200
    data = response.json()
    assert data["answer"] == "El saldo de tu cuenta es S/ 1,500.00."
    assert data["customer_id"] == "CUST-0001"
    assert data["rounds"] == 1


def test_agent_api_run_cloud_requires_auth(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    client = TestClient(app)

    with patch(
        "aegisbank_agent.api.resolve_runtime_environment",
        return_value=RuntimeEnvironment.STAGING,
    ):
        response = client.post(
            "/api/v1/agent/run",
            json={
                "query": "Consultar saldo",
                "customer_id": "CUST-0001",
            },
        )
        assert response.status_code == 401
        assert "Bearer token missing" in response.json()["detail"]


def test_agent_api_run_cloud_rejects_unconfigured_jwt_validation(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    monkeypatch.delenv("AEGISBANK_ENTRA_TENANT_ID", raising=False)
    monkeypatch.delenv("AEGISBANK_ENTRA_AUDIENCE", raising=False)

    test_app = create_app(orchestrator=MagicMock())
    client = TestClient(test_app)

    with patch(
        "aegisbank_agent.api.resolve_runtime_environment",
        return_value=RuntimeEnvironment.PRODUCTION,
    ):
        response = client.post(
            "/api/v1/agent/run",
            json={"query": "Consultar saldo", "customer_id": "CUST-9999"},
            headers={"Authorization": "Bearer arbitrary-value"},
        )
        assert response.status_code == 503
        assert "JWT verification is not configured" in response.json()["detail"]


def test_agent_api_run_cloud_uses_verified_token_identity(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")

    mock_result = MagicMock()
    mock_result.answer = "Información verificada."
    mock_result.customer_id = "CUST-0001"
    mock_result.rounds = 1
    mock_result.tool_calls = []

    mock_orch = MagicMock()
    mock_orch.run.return_value = mock_result
    verified_principal = PrincipalContext(
        customer_id="CUST-0001",
        authenticated=True,
        claims={"auth_type": "entra-jwt", "subject": "synthetic-subject"},
    )
    auth_provider = AuthenticationProvider(jwt_validator=lambda _token: verified_principal)
    test_app = create_app(orchestrator=mock_orch, auth_provider=auth_provider)
    client = TestClient(test_app)

    with patch(
        "aegisbank_agent.api.resolve_runtime_environment",
        return_value=RuntimeEnvironment.PRODUCTION,
    ):
        response = client.post(
            "/api/v1/agent/run",
            json={
                "query": "Consultar saldo",
                "customer_id": "CUST-9999",
            },
            headers={"Authorization": "Bearer fake-verified-jwt-token"},
        )
        assert response.status_code == 200
        data = response.json()
        assert data["answer"] == "Información verificada."
        assert data["customer_id"] == "CUST-0001"
        mock_orch.run.assert_called_once()
        assert mock_orch.run.call_args.kwargs["customer_id"] == "CUST-0001"


def test_agent_api_run_returns_safe_degraded_response_on_orchestrator_failure(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    mock_orch = MagicMock()
    mock_orch.run.side_effect = RuntimeError("provider unavailable")
    verified_principal = PrincipalContext(
        customer_id="CUST-0001",
        authenticated=True,
        claims={"auth_type": "entra-jwt", "subject": "synthetic-subject"},
    )
    auth_provider = AuthenticationProvider(jwt_validator=lambda _token: verified_principal)
    test_app = create_app(orchestrator=mock_orch, auth_provider=auth_provider)
    client = TestClient(test_app)

    with patch(
        "aegisbank_agent.api.resolve_runtime_environment",
        return_value=RuntimeEnvironment.STAGING,
    ):
        response = client.post(
            "/api/v1/agent/run",
            json={"query": "Consultar saldo", "session_id": "session-123"},
            headers={"Authorization": "Bearer verified-token"},
        )

    assert response.status_code == 200
    assert response.json()["execution_mode"] == "cloud-fallback"
    assert "No pudimos completar" in response.json()["answer"]
    assert response.json()["session_id"] == "session-123"


def test_agent_api_run_rejects_fallback_in_production(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "production")
    mock_orch = MagicMock()
    mock_orch.run.side_effect = RuntimeError("provider unavailable")
    verified_principal = PrincipalContext(
        customer_id="CUST-0001",
        authenticated=True,
        claims={"auth_type": "entra-jwt", "subject": "synthetic-subject"},
    )
    auth_provider = AuthenticationProvider(jwt_validator=lambda _token: verified_principal)
    test_app = create_app(orchestrator=mock_orch, auth_provider=auth_provider)
    client = TestClient(test_app)

    with patch(
        "aegisbank_agent.api.resolve_runtime_environment",
        return_value=RuntimeEnvironment.PRODUCTION,
    ):
        response = client.post(
            "/api/v1/agent/run",
            json={"query": "Consultar saldo", "session_id": "session-123"},
            headers={"Authorization": "Bearer verified-token"},
        )

    assert response.status_code == 503
    assert "no fallback" in response.json()["detail"]


def test_conversation_history_dependency_failure_degrades_to_empty_result(monkeypatch) -> None:
    monkeypatch.setenv("CONVERSATION_PERSISTENCE_ENABLED", "true")
    verified_principal = PrincipalContext(
        customer_id="CUST-0001",
        authenticated=True,
        claims={"auth_type": "entra-jwt", "subject": "synthetic-subject"},
    )
    auth_provider = AuthenticationProvider(jwt_validator=lambda _token: verified_principal)

    class BrokenConversationStore:
        def list_sessions(self, _customer_id: str):
            raise RuntimeError("cosmos unavailable")

        def get_session(self, _customer_id: str, _session_id: str):
            raise RuntimeError("cosmos unavailable")

    with patch("aegisbank_agent.api.ConversationStore", return_value=BrokenConversationStore()):
        test_app = create_app(orchestrator=MagicMock(), auth_provider=auth_provider)
    client = TestClient(test_app)

    assert (
        client.get(
            "/api/v1/conversations", headers={"Authorization": "Bearer verified-token"}
        ).json()
        == []
    )
    assert (
        client.get(
            "/api/v1/conversations/session-123",
            headers={"Authorization": "Bearer verified-token"},
        ).json()
        == []
    )
