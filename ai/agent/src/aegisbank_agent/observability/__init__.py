"""Observability, AgentOps, structured audit, and HOTL supervision for AegisBank."""

from __future__ import annotations

from .agentops import AgentOpsSummary
from .audit import AuditEvent, AuditEventType, AuditLogger, get_audit_logger
from .context import ObservabilityContext
from .hotl import HOTLSupervisor, get_hotl_supervisor
from .logging import RedactionFilter, StructuredLogger, get_logger
from .metrics import OperationalMetrics, get_metrics
from .telemetry import Observability, create_observability, redact
from .tracer import (
    get_current_trace_and_span_id,
    get_memory_exporter,
    get_tracer,
    setup_tracer,
    trace_span,
)

__all__ = [
    "AgentOpsSummary",
    "AuditEvent",
    "AuditEventType",
    "AuditLogger",
    "HOTLSupervisor",
    "Observability",
    "ObservabilityContext",
    "OperationalMetrics",
    "RedactionFilter",
    "StructuredLogger",
    "create_observability",
    "get_audit_logger",
    "get_current_trace_and_span_id",
    "get_hotl_supervisor",
    "get_logger",
    "get_memory_exporter",
    "get_metrics",
    "get_tracer",
    "redact",
    "setup_tracer",
    "trace_span",
]
