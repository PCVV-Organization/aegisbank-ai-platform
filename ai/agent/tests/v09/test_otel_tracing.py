"""Tests for OpenTelemetry distributed tracing and span context management."""

from __future__ import annotations

import pytest
from opentelemetry.trace import StatusCode

from aegisbank_agent.observability.tracer import (
    get_current_trace_and_span_id,
    get_memory_exporter,
    setup_tracer,
    trace_span,
)


def test_tracer_setup_and_span_creation() -> None:
    setup_tracer()
    exporter = get_memory_exporter()
    exporter.clear()

    with trace_span("test.parent_span", attributes={"env": "test", "service": "agent"}):
        trace_id, span_id = get_current_trace_and_span_id()
        assert len(trace_id) == 32
        assert len(span_id) == 16
        assert trace_id != "0" * 32
        assert span_id != "0" * 16

        with trace_span("test.child_span", attributes={"step": 1}):
            _, child_span_id = get_current_trace_and_span_id()
            assert child_span_id != span_id

    spans = exporter.get_finished_spans()
    assert len(spans) == 2

    # Verify attributes and hierarchy
    child_span = [s for s in spans if s.name == "test.child_span"][0]
    parent_span = [s for s in spans if s.name == "test.parent_span"][0]

    assert child_span.attributes["step"] == 1
    assert parent_span.attributes["env"] == "test"
    assert child_span.parent.span_id == parent_span.context.span_id
    assert child_span.status.status_code == StatusCode.OK
    assert parent_span.status.status_code == StatusCode.OK


def test_span_records_exception_on_failure() -> None:
    exporter = get_memory_exporter()
    exporter.clear()

    with pytest.raises(ValueError, match="Error forzado de prueba"):
        with trace_span("test.failing_span"):
            raise ValueError("Error forzado de prueba")

    spans = exporter.get_finished_spans()
    assert len(spans) == 1
    failing_span = spans[0]
    assert failing_span.status.status_code == StatusCode.ERROR
    assert "Error forzado de prueba" in failing_span.status.description
