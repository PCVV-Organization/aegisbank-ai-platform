"""Unit tests for Manual User-E2E Hardening and Demo Readiness (Milestone v1.0.7)."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import MagicMock, patch

from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.seed import seed_database

from aegisbank_agent.agent import AgentOrchestrator, format_currency
from aegisbank_agent.knowledge_routing import (
    requires_authorized_knowledge,
    requires_write_action,
)
from aegisbank_agent.tools.banking_tools import CreateServiceRequestTool
from aegisbank_agent.tools.base import AgentContext


def test_format_currency_rules() -> None:
    """Validate currency formatting rules: PEN -> S/ (never $), USD -> $, EUR -> €."""
    assert format_currency("1500.50", "PEN") == "S/ 1500.50"
    assert format_currency("1500", "pen") == "S/ 1500.00"
    assert format_currency(2800.0, "PEN") == "S/ 2800.00"
    assert format_currency("100.00", "USD") == "$100.00"
    assert format_currency("50.00", "EUR") == "€50.00"
    assert format_currency("75.00", "BRL") == "75.00 BRL"
    assert format_currency("", "PEN") == ""
    assert format_currency(None, "PEN") == ""


def test_write_action_takes_precedence_over_policy_knowledge() -> None:
    """Complaints with terms like 'comisión' must be treated as write action, not policy query."""
    complaint = "Por favor registra un reclamo formal por cobro indebido de comision en mi prestamo"
    assert requires_write_action(complaint) is True
    assert requires_authorized_knowledge(complaint) is False

    # But pure factual policy inquiry should remain knowledge required
    inquiry = "¿Cuál es la comisión por mora en un crédito personal?"
    assert requires_write_action(inquiry) is False
    assert requires_authorized_knowledge(inquiry) is True


def test_create_service_request_tool_http_boundary() -> None:
    """Verify CreateServiceRequestTool dispatches HTTP POST when URL is set."""
    db = Database("sqlite:///:memory:")
    db.create_schema()
    seed_database(db)
    tool = CreateServiceRequestTool(db)
    context = AgentContext(session_customer_id="CUST-0001")

    fake_response = {
        "service_request_id": "SR-000099",
        "customer_id": "CUST-0001",
        "category": "FEE",
        "description": "Cobro indebido de comision por mantenimiento",
        "status": "OPEN",
        "created_at": "2026-09-22T16:00:00Z",
    }

    mock_resp = MagicMock()
    mock_resp.read.return_value = json.dumps(fake_response).encode("utf-8")
    mock_resp.__enter__.return_value = mock_resp

    def _mock_env(key: str, default: str | None = None) -> str | None:
        if key == "AEGISBANK_CORE_BANKING_URL":
            return "http://127.0.0.1:8015"
        return default

    with (
        patch("os.getenv", side_effect=_mock_env),
        patch("urllib.request.urlopen", return_value=mock_resp) as mock_urlopen,
    ):
        result = tool.execute(
            {
                "category": "FEE",
                "description": "Cobro indebido de comision por mantenimiento",
            },
            context,
        )

        assert result.success is True
        assert result.data["service_request_id"] == "SR-000099"
        assert result.data["category"] == "FEE"
        assert mock_urlopen.called
        req = mock_urlopen.call_args[0][0]
        assert req.get_method() == "POST"
        assert req.full_url == "http://127.0.0.1:8015/api/v1/service-requests"


def test_session_ownership_audit_actor_naming(tmp_path: Path) -> None:
    """Verify foreign session access violation records SESSION_OWNERSHIP as actor."""
    from aegisbank_agent.observability.audit import AuditEventType
    from aegisbank_agent.session_store import SQLiteSessionStore

    store_path = tmp_path / "sessions.db"
    store = SQLiteSessionStore(store_path)
    store.get_or_create("shared-session", "CUST-0001")

    mock_audit = MagicMock()
    orchestrator = AgentOrchestrator(session_store=store, audit_logger=mock_audit)

    result = orchestrator.run("Hola", customer_id="CUST-0002", session_id="shared-session")
    assert result.success is False
    assert result.error == "Session ownership violation"

    assert mock_audit.record.called
    call_kwargs = mock_audit.record.call_args.kwargs
    assert call_kwargs["actor"] == "SESSION_OWNERSHIP"
    assert call_kwargs["event_type"] == AuditEventType.TOOL_DENIED
    assert call_kwargs["payload"]["reason"] == "SESSION_OWNERSHIP_VIOLATION"
