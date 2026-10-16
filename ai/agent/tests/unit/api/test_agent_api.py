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


def test_service_request_feed_uses_verified_identity_and_core_api(monkeypatch) -> None:
    monkeypatch.setenv("AEGISBANK_ENV", "staging")
    monkeypatch.setenv("AEGISBANK_CORE_BANKING_URL", "http://core.test")
    principal = PrincipalContext(customer_id="CUST-0001", authenticated=True, claims={})
    test_app = create_app(auth_provider=AuthenticationProvider(jwt_validator=lambda _: principal))
    client = TestClient(test_app)

    response_body = b'[{"service_request_id":"SR-000007","category":"GENERAL","description":"Consulta","status":"OPEN","created_at":"2026-01-01T00:00:00+00:00"}]'
    fake_response = MagicMock()
    fake_response.read.return_value = response_body
    fake_response.__enter__.return_value = fake_response
    fake_response.__exit__.return_value = False
    with patch("aegisbank_agent.api.urllib.request.urlopen", return_value=fake_response) as open_url:
        response = client.get(
            "/api/v1/me/service-requests",
            headers={"Authorization": "Bearer verified"},
        )

    assert response.status_code == 200
    assert response.json()["items"][0]["service_request_id"] == "SR-000007"
    requested_url = open_url.call_args.args[0].full_url
    assert requested_url.endswith("/api/v1/service-requests/customer/CUST-0001")
    assert "customer_id=" not in requested_url
