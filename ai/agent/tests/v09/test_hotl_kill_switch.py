"""Tests for HOTLSupervisor supervisory kill-switch control."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from mock_core_banking.persistence.database import Database

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.observability.audit import AuditEventType, AuditLogger
from aegisbank_agent.observability.hotl import HOTLSupervisor
from aegisbank_agent.tools.banking_tools import CreateServiceRequestTool
from aegisbank_agent.tools.registry import ToolRegistry


class DummyChoice:
    def __init__(self, message: object):
        self.message = message


class DummyResponse:
    def __init__(self, message: object):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


class DummyToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = arguments


def test_hotl_kill_switch_blocks_write_tools_immediately(in_memory_db: Database) -> None:
    audit = AuditLogger()
    hotl = HOTLSupervisor(audit_logger=audit)
    assert hotl.is_write_allowed is True

    # Engage kill-switch
    hotl.engage_kill_switch("Anomalía detectada en el host transaccional")
    assert hotl.is_write_allowed is False
    assert "Anomalía detectada" in hotl.kill_switch_reason

    # Verify audit event was logged
    audit_events = audit.list_events(event_type=AuditEventType.HOTL_KILL_SWITCH_ENGAGED)
    assert len(audit_events) == 1

    # Setup agent with mocked LLM proposing write tool
    tc = DummyToolCall(
        "call_write_01",
        "create_service_request",
        json.dumps({"category": "LOAN", "description": "Reclamo bloqueado"}),
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="No se pudo procesar la solicitud.")),
    ]

    registry = ToolRegistry([CreateServiceRequestTool(in_memory_db)])
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        hotl_supervisor=hotl,
        audit_logger=audit,
    )

    result = orchestrator.run("Crear reclamo", customer_id="CUST-0001")

    # Assert tool was blocked without asking for HITL approval
    assert len(result.approval_requests) == 0
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].result.success is False
    assert "deshabilitada por supervisión HOTL" in result.tool_calls[0].result.error

    # Restore kill switch
    hotl.disengage_kill_switch()
    assert hotl.is_write_allowed is True
