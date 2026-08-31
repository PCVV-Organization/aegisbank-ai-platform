"""Structured, append-oriented audit log for critical banking security and transaction events."""

from __future__ import annotations

import threading
import uuid
from dataclasses import asdict, dataclass
from datetime import datetime, timezone
from enum import Enum
from typing import Any

from .logging import RedactionFilter


class AuditEventType(str, Enum):
    AGENT_RUN_STARTED = "AGENT_RUN_STARTED"
    AGENT_RUN_COMPLETED = "AGENT_RUN_COMPLETED"
    TOOL_PROPOSED = "TOOL_PROPOSED"
    TOOL_EXECUTED = "TOOL_EXECUTED"
    TOOL_DENIED = "TOOL_DENIED"
    HITL_REQUESTED = "HITL_REQUESTED"
    HITL_APPROVED = "HITL_APPROVED"
    HITL_REJECTED = "HITL_REJECTED"
    HITL_EXECUTED = "HITL_EXECUTED"
    SERVICE_REQUEST_CREATED = "SERVICE_REQUEST_CREATED"
    IDEMPOTENCY_REPLAY = "IDEMPOTENCY_REPLAY"
    IDEMPOTENCY_CONFLICT = "IDEMPOTENCY_CONFLICT"
    RETRY_PERFORMED = "RETRY_PERFORMED"
    CIRCUIT_STATE_CHANGED = "CIRCUIT_STATE_CHANGED"
    MESSAGE_DEAD_LETTERED = "MESSAGE_DEAD_LETTERED"
    HOTL_KILL_SWITCH_ENGAGED = "HOTL_KILL_SWITCH_ENGAGED"
    HOTL_KILL_SWITCH_DISENGAGED = "HOTL_KILL_SWITCH_DISENGAGED"


@dataclass(frozen=True)
class AuditEvent:
    """Immutable audit trail entry."""

    audit_id: str
    timestamp: str
    event_type: AuditEventType
    correlation_id: str
    trace_id: str
    customer_id: str
    actor: str
    payload: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        d = asdict(self)
        d["event_type"] = self.event_type.value
        return d


class AuditLogger:
    """Thread-safe, append-oriented audit logger preserving non-repudiation."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._trail: list[AuditEvent] = []

    def record(
        self,
        event_type: AuditEventType,
        correlation_id: str,
        trace_id: str = "0" * 32,
        customer_id: str = "",
        actor: str = "SYSTEM",
        payload: dict[str, Any] | None = None,
    ) -> AuditEvent:
        """Record an immutable audit event with automatic secret redaction."""
        now = datetime.now(timezone.utc).isoformat()
        audit_id = f"AUD-{uuid.uuid4().hex[:12].upper()}"
        clean_payload = RedactionFilter.redact_dict(payload or {})

        event = AuditEvent(
            audit_id=audit_id,
            timestamp=now,
            event_type=event_type,
            correlation_id=correlation_id,
            trace_id=trace_id,
            customer_id=customer_id,
            actor=actor,
            payload=clean_payload,
        )

        with self._lock:
            self._trail.append(event)

        return event

    def list_events(
        self,
        correlation_id: str | None = None,
        event_type: AuditEventType | None = None,
    ) -> list[AuditEvent]:
        """Query audit trail records with optional filtering."""
        with self._lock:
            records = list(self._trail)

        if correlation_id:
            records = [r for r in records if r.correlation_id == correlation_id]
        if event_type:
            records = [r for r in records if r.event_type == event_type]

        return records

    def clear(self) -> None:
        """Clear audit trail (for test isolation)."""
        with self._lock:
            self._trail.clear()


_GLOBAL_AUDIT = AuditLogger()


def get_audit_logger() -> AuditLogger:
    """Retrieve global audit logger instance."""
    return _GLOBAL_AUDIT
