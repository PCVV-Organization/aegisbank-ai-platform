"""Vendor-neutral local traces, structured logs, metrics, and audit events."""

from __future__ import annotations

import json
import time
import uuid
from contextlib import contextmanager
from contextvars import ContextVar
from datetime import datetime, timezone
from typing import Any, Iterator

from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.repositories import AuditEventRepository
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

_correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")
_SENSITIVE_KEYS = {"api_key", "authorization", "password", "prompt", "token", "secret"}


def redact(value: Any) -> Any:
    """Recursively remove secrets and raw prompts from telemetry payloads."""
    if isinstance(value, dict):
        return {
            key: "[REDACTED]" if key.lower() in _SENSITIVE_KEYS else redact(item)
            for key, item in value.items()
        }
    if isinstance(value, list):
        return [redact(item) for item in value]
    return value


class Observability:
    """Per-run local telemetry collector suitable for tests and development."""

    def __init__(self, database: Database | None = None) -> None:
        provider = TracerProvider()
        self.span_exporter = InMemorySpanExporter()
        provider.add_span_processor(SimpleSpanProcessor(self.span_exporter))
        self.tracer = provider.get_tracer("aegisbank.agent", "0.9.0")
        self.database = database
        self.logs: list[dict[str, Any]] = []
        self.metrics: dict[str, int | float] = {}
        self.correlation_id = f"CORR-{uuid.uuid4().hex[:12].upper()}"
        self.session_id = f"SESSION-{uuid.uuid4().hex[:12].upper()}"

    @property
    def trace_id(self) -> str:
        current = trace.get_current_span()
        return format(current.get_span_context().trace_id, "032x") if current else ""

    @contextmanager
    def span(self, name: str, **attributes: Any) -> Iterator[Any]:
        safe_attributes = redact(attributes)
        with self.tracer.start_as_current_span(name, attributes=safe_attributes) as span:
            span.set_attribute("aegisbank.correlation_id", self.correlation_id)
            yield span

    def log(self, event_name: str, *, level: str = "INFO", **fields: Any) -> None:
        record = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": level,
            "event_name": event_name,
            "correlation_id": self.correlation_id,
            "trace_id": self.trace_id,
            "session_id": self.session_id,
            **redact(fields),
        }
        self.logs.append(record)

    def increment(self, name: str, value: int = 1) -> None:
        self.metrics[name] = self.metrics.get(name, 0) + value

    def observe_latency(self, name: str, started_at: float) -> float:
        latency_ms = round((time.perf_counter() - started_at) * 1000, 3)
        self.metrics[name] = latency_ms
        return latency_ms

    def audit(self, event_name: str, *, database: Database | None = None, **fields: Any) -> None:
        self.log(event_name, **fields)
        db = database or self.database
        if db is None:
            return
        safe = redact(fields)
        with db.session() as session:
            AuditEventRepository(session).append(
                event_id=f"AUD-{uuid.uuid4().hex[:16].upper()}",
                event_name=event_name,
                correlation_id=self.correlation_id,
                trace_id=self.trace_id,
                session_id=self.session_id,
                synthetic_customer_id=safe.get("synthetic_customer_id"),
                tool_name=safe.get("tool_name"),
                approval_status=safe.get("approval_status"),
                execution_status=safe.get("execution_status"),
                latency_ms=safe.get("latency_ms"),
                error_code=safe.get("error_code"),
                details_json=json.dumps(safe, ensure_ascii=False),
                created_at=datetime.now(timezone.utc),
            )
            session.commit()

    def finished_spans(self) -> list[Any]:
        return self.span_exporter.get_finished_spans()


def create_observability(database: Database | None = None) -> Observability:
    return Observability(database)
