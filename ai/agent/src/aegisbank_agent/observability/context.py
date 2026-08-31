"""Observability context holding correlation ID and tracing metadata."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from typing import Any

from .tracer import get_current_trace_and_span_id


@dataclass
class ObservabilityContext:
    """Carries business correlation and distributed tracing context."""

    correlation_id: str = field(default_factory=lambda: f"CORR-{uuid.uuid4().hex[:12].upper()}")
    session_id: str = "default_session"
    customer_id: str = ""

    @property
    def trace_id(self) -> str:
        trace_id, _ = get_current_trace_and_span_id()
        return trace_id

    @property
    def span_id(self) -> str:
        _, span_id = get_current_trace_and_span_id()
        return span_id

    def to_dict(self) -> dict[str, Any]:
        return {
            "correlation_id": self.correlation_id,
            "session_id": self.session_id,
            "customer_id": self.customer_id,
            "trace_id": self.trace_id,
            "span_id": self.span_id,
        }
