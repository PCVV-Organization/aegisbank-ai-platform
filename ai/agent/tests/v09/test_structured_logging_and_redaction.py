"""Tests for StructuredLogger and automatic secret/PII redaction."""

from __future__ import annotations

from aegisbank_agent.observability.context import ObservabilityContext
from aegisbank_agent.observability.logging import RedactionFilter, StructuredLogger


def test_redaction_filter_masks_credentials_and_tokens() -> None:
    raw_payload = {
        "api_key": "sk-1234567890abcdef1234567890",
        "user_password": "SuperSecretPassword123!",
        "auth_token": "bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9",
        "customer_id": "CUST-0001",
        "nested": {
            "secret_access_key": "SECRET123",
            "safe_description": "Consulta de saldo regular",
        },
    }

    cleaned = RedactionFilter.redact_dict(raw_payload)

    assert cleaned["api_key"] == "[REDACTED]"
    assert cleaned["user_password"] == "[REDACTED]"
    assert cleaned["auth_token"] == "[REDACTED]"
    assert cleaned["customer_id"] == "CUST-0001"
    assert cleaned["nested"]["secret_access_key"] == "[REDACTED]"
    assert cleaned["nested"]["safe_description"] == "Consulta de saldo regular"


def test_structured_logger_emits_json_with_correlation_context() -> None:
    logger = StructuredLogger(name="test.logger")
    logger.clear()

    ctx = ObservabilityContext(
        correlation_id="CORR-TEST-999",
        session_id="SESS-001",
        customer_id="CUST-0001",
    )

    entry = logger.info(
        "tool_executed",
        context=ctx,
        tool_name="get_my_loans",
        execution_status="SUCCESS",
        latency_ms=25.4,
        extra={"api_key": "sk-leak-attempt", "records_returned": 2},
    )

    assert entry["event_name"] == "tool_executed"
    assert entry["correlation_id"] == "CORR-TEST-999"
    assert entry["tool_name"] == "get_my_loans"
    assert entry["latency_ms"] == 25.4
    assert entry["details"]["api_key"] == "[REDACTED]"
    assert entry["details"]["records_returned"] == 2
    assert len(logger.emitted_logs) == 1
