"""Unit tests for the canonical ServiceRequestEventHandler composition."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any

import pytest

REPO_ROOT = Path(__file__).resolve().parents[4]
FUNCTIONS_ROOT = REPO_ROOT / "functions" / "aegisbank-events"
if str(FUNCTIONS_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_ROOT))

from mock_core_banking.persistence.database import Database  # noqa: E402
from service_request_handler import (  # type: ignore[import-not-found]  # noqa: E402
    EventIntegrityError,
    MalformedEventError,
    ServiceRequestEventHandler,
    UnsupportedEventTypeError,
    UnsupportedSchemaVersionError,
    create_default_dependencies,
)

from aegisbank_agent.observability.audit import AuditEventType, get_audit_logger  # noqa: E402
from aegisbank_agent.observability.metrics import OperationalMetrics  # noqa: E402


def _build_event(**overrides: Any) -> dict[str, Any]:
    event: dict[str, Any] = {
        "specversion": "1.0",
        "id": "EVT-HANDLER-001",
        "source": "urn:aegisbank:mock-core-banking",
        "type": "com.aegisbank.service-request.created.v1",
        "subject": "/service-requests/SR-000123",
        "time": "2026-09-01T22:56:00-05:00",
        "datacontenttype": "application/json",
        "dataschema": "urn:aegisbank:contracts:service-request-created:v1",
        "correlationid": "CORR-HANDLER-001",
        "data": {
            "service_request_id": "SR-000123",
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "status": "OPEN",
        },
    }
    event.update(overrides)
    return event


@pytest.fixture
def metrics() -> OperationalMetrics:
    return OperationalMetrics()


@pytest.fixture
def audit():
    logger = get_audit_logger()
    logger.clear()
    return logger


@pytest.fixture
def handler(metrics: OperationalMetrics, audit) -> ServiceRequestEventHandler:
    database = Database("sqlite:///:memory:")
    database.create_schema()
    from aegisbank_agent.reliability.idempotency import IdempotencyGuard

    deps = create_default_dependencies()
    fresh = ServiceRequestEventHandler.__new__(ServiceRequestEventHandler)
    fresh.__dict__["_dependencies"] = type(deps)(
        idempotency=IdempotencyGuard(database),
        audit=audit,
        metrics=metrics,
        logger=deps.logger,
    )
    return fresh


def test_handle_first_event_is_processed(handler: ServiceRequestEventHandler) -> None:
    result = handler.handle_cloud_event(_build_event())
    assert result.status == "PROCESSED"
    assert result.event_id == "EVT-HANDLER-001"
    assert result.correlation_id == "CORR-HANDLER-001"


def test_handle_duplicate_event_is_idempotent(handler: ServiceRequestEventHandler) -> None:
    event = _build_event()
    first = handler.handle_cloud_event(event)
    second = handler.handle_cloud_event(event)
    assert first.status == "PROCESSED"
    assert second.status == "DUPLICATE"
    assert first.event_id == second.event_id
    assert first.processed_at == second.processed_at


def test_handle_replays_audit_replay_event(handler: ServiceRequestEventHandler, audit) -> None:
    event = _build_event(id="EVT-AUDIT-001", correlationid="CORR-AUDIT-001")
    handler.handle_cloud_event(event)
    handler.handle_cloud_event(event)
    replays = audit.list_events(event_type=AuditEventType.IDEMPOTENCY_REPLAY)
    assert len(replays) == 1
    assert replays[0].correlation_id == "CORR-AUDIT-001"


def test_handle_rejects_unknown_event_type(handler: ServiceRequestEventHandler) -> None:
    with pytest.raises(UnsupportedEventTypeError):
        handler.handle_cloud_event(_build_event(type="com.otherbank.event"))


def test_handle_rejects_unknown_specversion(handler: ServiceRequestEventHandler) -> None:
    with pytest.raises(UnsupportedSchemaVersionError):
        handler.handle_cloud_event(_build_event(specversion="2.0"))


def test_handle_rejects_malformed_data(handler: ServiceRequestEventHandler) -> None:
    bad_event = _build_event()
    bad_event["data"] = dict(bad_event["data"], category="PAYMENT")
    with pytest.raises(MalformedEventError):
        handler.handle_cloud_event(bad_event)


def test_handle_rejects_invalid_traceparent(handler: ServiceRequestEventHandler) -> None:
    with pytest.raises(MalformedEventError):
        handler.handle_cloud_event(_build_event(traceparent="not-a-trace"))


def test_handle_rejects_replayed_event_with_different_content(
    handler: ServiceRequestEventHandler,
) -> None:
    handler.handle_cloud_event(_build_event())
    tampered = _build_event(
        data={
            "service_request_id": "SR-000123",
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "status": "OPEN",
        }
    )
    tampered["correlationid"] = "CORR-TAMPER"
    tampered["data"] = dict(tampered["data"], status="REJECTED")
    with pytest.raises(EventIntegrityError):
        handler.handle_cloud_event(tampered)


def test_handler_increments_metrics(handler: ServiceRequestEventHandler, metrics) -> None:
    event = _build_event()
    handler.handle_cloud_event(event)
    handler.handle_cloud_event(event)
    snapshot = metrics.snapshot()
    assert snapshot["counters"]["event_grid_invocation_count"] == 2
    assert snapshot["counters"]["event_grid_processed_count"] == 1
    assert snapshot["counters"]["event_grid_duplicate_count"] == 1


def test_handler_records_latency(handler: ServiceRequestEventHandler, metrics) -> None:
    handler.handle_cloud_event(_build_event())
    snapshot = metrics.snapshot()
    assert snapshot["latencies"]["event_grid_handler_latencies_ms"]["count"] == 1
