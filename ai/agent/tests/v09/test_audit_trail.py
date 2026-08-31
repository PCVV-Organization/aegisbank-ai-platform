"""Tests for AuditLogger append-only persistence and redaction."""

from __future__ import annotations

from aegisbank_agent.observability.audit import AuditEventType, AuditLogger


def test_audit_logger_records_immutable_events() -> None:
    logger = AuditLogger()
    logger.clear()

    logger.record(
        event_type=AuditEventType.AGENT_RUN_STARTED,
        correlation_id="CORR-AUD-001",
        customer_id="CUST-0001",
        actor="USER",
        payload={"query": "Consulta"},
    )
    e2 = logger.record(
        event_type=AuditEventType.HITL_APPROVED,
        correlation_id="CORR-AUD-001",
        customer_id="CUST-0001",
        actor="USER",
        payload={"approval_id": "APP-001", "secret_token": "token123"},
    )

    events = logger.list_events()
    assert len(events) == 2
    assert events[0].event_type == AuditEventType.AGENT_RUN_STARTED
    assert events[1].event_type == AuditEventType.HITL_APPROVED
    assert events[1].payload["secret_token"] == "[REDACTED]"

    filtered = logger.list_events(correlation_id="CORR-AUD-001")
    assert len(filtered) == 2

    by_type = logger.list_events(event_type=AuditEventType.HITL_APPROVED)
    assert len(by_type) == 1
    assert by_type[0].audit_id == e2.audit_id
