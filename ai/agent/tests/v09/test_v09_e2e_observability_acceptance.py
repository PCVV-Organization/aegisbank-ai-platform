"""End-to-End Acceptance test for v0.9 Observability, AgentOps, and Audit trail."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

from mock_core_banking.persistence.database import Database

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.observability.agentops import AgentOpsSummary
from aegisbank_agent.observability.audit import AuditEventType, AuditLogger
from aegisbank_agent.observability.hotl import HOTLSupervisor
from aegisbank_agent.observability.logging import StructuredLogger
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.observability.tracer import get_memory_exporter, setup_tracer
from aegisbank_agent.tools.banking_tools import CreateServiceRequestTool, GetMyLoansTool
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


def test_v09_e2e_observability_full_pipeline(in_memory_db: Database) -> None:
    # 1. Setup Observability Stack
    setup_tracer()
    exporter = get_memory_exporter()
    exporter.clear()

    metrics = OperationalMetrics()
    logger = StructuredLogger(name="aegisbank.test")
    audit = AuditLogger()
    hotl = HOTLSupervisor(audit_logger=audit)

    # 2. Setup Agent with Mocked LLM tool calls
    tc_read = DummyToolCall("tc_01", "get_my_loans", json.dumps({}))
    tc_write = DummyToolCall(
        "tc_02",
        "create_service_request",
        json.dumps(
            {
                "category": "INSTALLMENT",
                "description": "Reclamo cuota E2E",
                "idempotency_key": "IDEMP-V09-E2E",
            }
        ),
    )

    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc_read])),
        DummyResponse(DummyMessage(tool_calls=[tc_write])),
        DummyResponse(DummyMessage(content="Su reclamo ha sido creado exitosamente.")),
    ]

    registry = ToolRegistry(
        [
            GetMyLoansTool(in_memory_db),
            CreateServiceRequestTool(in_memory_db),
        ]
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        hitl_manager=HITLApprovalManager(),
        approval_callback=lambda req: True,  # Approve
        hotl_supervisor=hotl,
        metrics=metrics,
        structured_logger=logger,
        audit_logger=audit,
    )

    # 3. Run Agent with custom correlation ID
    custom_corr_id = "CORR-E2E-ACCEPTANCE-001"
    result = orchestrator.run(
        "Consulta mis préstamos y crea un reclamo",
        customer_id="CUST-0001",
        correlation_id=custom_corr_id,
    )

    assert result.success is True
    assert result.correlation_id == custom_corr_id

    # 4. Verify OpenTelemetry Spans
    spans = exporter.get_finished_spans()
    span_names = [s.name for s in spans]
    assert "agent.run" in span_names
    assert "llm.chat" in span_names
    assert "tool.get_my_loans" in span_names
    assert "tool.create_service_request" in span_names

    # 5. Verify Structured Logs
    logs = logger.emitted_logs
    assert len(logs) >= 2
    assert all(log["correlation_id"] == custom_corr_id for log in logs)

    # 6. Verify Audit Trail
    audit_events = audit.list_events(correlation_id=custom_corr_id)
    event_types = [e.event_type for e in audit_events]
    assert AuditEventType.AGENT_RUN_STARTED in event_types
    assert AuditEventType.TOOL_PROPOSED in event_types
    assert AuditEventType.HITL_REQUESTED in event_types
    assert AuditEventType.HITL_APPROVED in event_types
    assert AuditEventType.HITL_EXECUTED in event_types
    assert AuditEventType.AGENT_RUN_COMPLETED in event_types

    # 7. Verify Operational Metrics and AgentOps Summary
    summary = AgentOpsSummary(metrics=metrics, audit_logger=audit)
    report = summary.generate_report()
    assert report["total_requests"] == 1
    assert report["error_rate_pct"] == 0.0
    assert report["hitl_approval_rate_pct"] == 100.0
    assert report["status"] == "HEALTHY"
