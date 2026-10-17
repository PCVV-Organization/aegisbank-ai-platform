"""Thin Event Grid handler composed from AegisBank canonical components."""

from __future__ import annotations

import os
import threading
import time
from collections.abc import Mapping
from dataclasses import dataclass
from datetime import datetime, timezone
from typing import Any

from aegisbank_agent.observability.audit import (
    AuditEventType,
    AuditLogger,
    get_audit_logger,
)
from aegisbank_agent.observability.context import ObservabilityContext
from aegisbank_agent.observability.logging import StructuredLogger, get_logger
from aegisbank_agent.observability.metrics import OperationalMetrics, get_metrics
from aegisbank_agent.observability.tracer import (
    get_current_trace_and_span_id,
    get_tracer,
)
from aegisbank_agent.reliability.idempotency import (
    IdempotencyConflictError,
    IdempotencyGuard,
)
from cloud_event import (
    CLOUD_EVENT_SPEC_VERSION,
    CLOUD_EVENT_TYPE,
    CloudEventValidationError,
    cloud_event_from_sdk,
    validate_cloud_event,
)
from mock_core_banking.persistence.database import Database
from opentelemetry import trace
from opentelemetry.trace import NonRecordingSpan, SpanContext, TraceFlags, TraceState


class PermanentEventError(ValueError):
    """Base class for events that cannot succeed without changing their content."""


class MalformedEventError(PermanentEventError):
    """Raised when the CloudEvent envelope or data violates its contract."""


class UnsupportedEventTypeError(PermanentEventError):
    """Raised when no handler exists for the versioned event type."""


class UnsupportedSchemaVersionError(PermanentEventError):
    """Raised when the CloudEvents specification version is unsupported."""


class EventIntegrityError(PermanentEventError):
    """Raised when an event ID is replayed with different content."""


@dataclass(frozen=True)
class EventProcessingResult:
    """Observable result of one handler invocation."""

    event_id: str
    status: str
    correlation_id: str
    trace_id: str
    processed_at: str
    latency_ms: float


@dataclass(frozen=True)
class HandlerDependencies:
    """Composition boundary for canonical reliability and observability services."""

    idempotency: IdempotencyGuard
    audit: AuditLogger
    metrics: OperationalMetrics
    logger: StructuredLogger


_DEFAULT_DEPENDENCIES: HandlerDependencies | None = None
_DEFAULT_DEPENDENCIES_LOCK = threading.Lock()


def create_default_dependencies() -> HandlerDependencies:
    """Create warm-instance local dependencies without persistent business state."""
    global _DEFAULT_DEPENDENCIES
    with _DEFAULT_DEPENDENCIES_LOCK:
        if _DEFAULT_DEPENDENCIES is None:
            database_url = os.getenv(
                "AEGISBANK_FUNCTION_IDEMPOTENCY_DATABASE_URL", "sqlite:///:memory:"
            )
            database = Database(database_url)
            database.create_schema()
            _DEFAULT_DEPENDENCIES = HandlerDependencies(
                idempotency=IdempotencyGuard(database),
                audit=get_audit_logger(),
                metrics=get_metrics(),
                logger=get_logger("aegisbank.functions.events"),
            )
    return _DEFAULT_DEPENDENCIES


def _remote_parent_context(traceparent: str | None) -> Any | None:
    if traceparent is None:
        return None

    _, trace_id_hex, span_id_hex, flags_hex = traceparent.split("-", maxsplit=3)
    span_context = SpanContext(
        trace_id=int(trace_id_hex, 16),
        span_id=int(span_id_hex, 16),
        is_remote=True,
        trace_flags=TraceFlags(int(flags_hex, 16)),
        trace_state=TraceState(),
    )
    if not span_context.is_valid:
        raise MalformedEventError(
            "CloudEvent traceparent contains an invalid trace or span ID"
        )
    return trace.set_span_in_context(NonRecordingSpan(span_context))


class ServiceRequestEventHandler:
    """Validate and process ``ServiceRequestCreated`` exactly once per local store."""

    def __init__(self, dependencies: HandlerDependencies | None = None) -> None:
        self._dependencies = dependencies or create_default_dependencies()

    @property
    def dependencies(self) -> HandlerDependencies:
        return self._dependencies

    def handle_cloud_event(
        self, raw_event: Mapping[str, Any] | Any
    ) -> EventProcessingResult:
        started_at = time.perf_counter()
        deps = self._dependencies
        deps.metrics.increment("request_count")
        deps.metrics.increment("event_grid_invocation_count")

        try:
            event = (
                dict(raw_event)
                if isinstance(raw_event, Mapping)
                else cloud_event_from_sdk(raw_event)
            )
            # Accept pre-reason legacy events during the contract migration.
            # New producers always emit the required canonical fields.
            data = dict(event.get("data", {}))
            data.setdefault("reason_code", "GENERAL_OTHER")
            data.setdefault("reason_label", "Otro motivo")
            event["data"] = data
            self._validate_supported_event(event)
        except (CloudEventValidationError, PermanentEventError) as exc:
            self._record_rejection(exc, started_at)
            raise

        event_id = event["id"]
        data = event["data"]
        correlation_id = event["correlationid"]
        customer_id = data["customer_id"]
        parent_context = _remote_parent_context(event.get("traceparent"))
        tracer = get_tracer("aegisbank.functions.events")

        try:
            with tracer.start_as_current_span(
                "functions.event_grid.service_request_created",
                context=parent_context,
                attributes={
                    "messaging.system": "azure_event_grid",
                    "messaging.message.id": event_id,
                    "messaging.operation": "process",
                    "aegisbank.correlation_id": correlation_id,
                    "aegisbank.event.type": event["type"],
                },
            ):
                context = ObservabilityContext(
                    correlation_id=correlation_id,
                    session_id="azure-functions-local",
                    customer_id=customer_id,
                )
                result_data, replayed = deps.idempotency.execute_idempotent(
                    idempotency_key=f"event-grid:{event_id}",
                    customer_id=customer_id,
                    arguments=event,
                    operation=lambda: self._process_once(event, context),
                    resource_id_extractor=lambda result: result["service_request_id"],
                )

                if replayed:
                    deps.metrics.increment("event_grid_duplicate_count")
                    trace_id, _ = get_current_trace_and_span_id()
                    deps.audit.record(
                        AuditEventType.IDEMPOTENCY_REPLAY,
                        correlation_id=correlation_id,
                        trace_id=trace_id,
                        customer_id=customer_id,
                        actor="AZURE_FUNCTION_EVENT_HANDLER",
                        payload={"event_id": event_id, "source": event["source"]},
                    )
                    deps.logger.info(
                        "event_grid_duplicate",
                        context=context,
                        execution_status="DUPLICATE",
                        extra={"event_id": event_id, "event_type": event["type"]},
                    )

                trace_id, _ = get_current_trace_and_span_id()
                latency_ms = self._record_latency(started_at)
                return EventProcessingResult(
                    event_id=event_id,
                    status="DUPLICATE" if replayed else "PROCESSED",
                    correlation_id=correlation_id,
                    trace_id=trace_id,
                    processed_at=result_data["processed_at"],
                    latency_ms=latency_ms,
                )
        except IdempotencyConflictError as exc:
            deps.metrics.increment("request_error_count")
            deps.metrics.increment("event_grid_rejected_count")
            latency_ms = self._record_latency(started_at)
            trace_id, _ = get_current_trace_and_span_id()
            deps.audit.record(
                AuditEventType.IDEMPOTENCY_CONFLICT,
                correlation_id=correlation_id,
                trace_id=trace_id,
                customer_id=customer_id,
                actor="AZURE_FUNCTION_EVENT_HANDLER",
                payload={"event_id": event_id, "reason": "EVENT_ID_CONTENT_MISMATCH"},
            )
            deps.logger.error(
                "event_grid_integrity_conflict",
                context=ObservabilityContext(
                    correlation_id=correlation_id,
                    session_id="azure-functions-local",
                    customer_id=customer_id,
                ),
                execution_status="REJECTED",
                latency_ms=latency_ms,
                error_code="EVENT_ID_CONTENT_MISMATCH",
                extra={"event_id": event_id},
            )
            raise EventIntegrityError(
                "Event ID was replayed with different content"
            ) from exc

    @staticmethod
    def _validate_supported_event(event: Mapping[str, Any]) -> None:
        if event.get("specversion") != CLOUD_EVENT_SPEC_VERSION:
            raise UnsupportedSchemaVersionError(
                f"Unsupported CloudEvents specversion: {event.get('specversion')!r}"
            )
        if event.get("type") != CLOUD_EVENT_TYPE:
            raise UnsupportedEventTypeError(
                f"Unsupported event type: {event.get('type')!r}"
            )
        try:
            validate_cloud_event(event)
        except CloudEventValidationError as exc:
            raise MalformedEventError(str(exc)) from exc

    def _process_once(
        self,
        event: Mapping[str, Any],
        context: ObservabilityContext,
    ) -> dict[str, str]:
        deps = self._dependencies
        data = event["data"]
        trace_id, _ = get_current_trace_and_span_id()
        processed_at = datetime.now(timezone.utc).isoformat()

        deps.audit.record(
            AuditEventType.SERVICE_REQUEST_CREATED,
            correlation_id=event["correlationid"],
            trace_id=trace_id,
            customer_id=data["customer_id"],
            actor="AZURE_FUNCTION_EVENT_HANDLER",
            payload={
                "event_id": event["id"],
                "event_type": event["type"],
                "source": event["source"],
                "service_request_id": data["service_request_id"],
                "category": data["category"],
                "status": data["status"],
            },
        )
        deps.metrics.increment("event_grid_processed_count")
        deps.logger.info(
            "service_request_created_event_processed",
            context=context,
            execution_status="SUCCESS",
            extra={
                "event_id": event["id"],
                "event_type": event["type"],
                "service_request_id": data["service_request_id"],
                "category": data["category"],
                "status": data["status"],
            },
        )
        return {
            "event_id": event["id"],
            "service_request_id": data["service_request_id"],
            "processed_at": processed_at,
        }

    def _record_rejection(self, exc: Exception, started_at: float) -> None:
        deps = self._dependencies
        deps.metrics.increment("request_error_count")
        deps.metrics.increment("event_grid_rejected_count")
        latency_ms = self._record_latency(started_at)
        deps.logger.error(
            "event_grid_contract_rejected",
            context=ObservabilityContext(
                correlation_id="UNTRUSTED_EVENT",
                session_id="azure-functions-local",
            ),
            execution_status="REJECTED",
            latency_ms=latency_ms,
            error_code=type(exc).__name__,
        )

    def _record_latency(self, started_at: float) -> float:
        latency_ms = round((time.perf_counter() - started_at) * 1000.0, 3)
        self._dependencies.metrics.record_latency(
            "event_grid_handler_latencies_ms", latency_ms
        )
        return latency_ms
