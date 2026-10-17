"""Contract and CloudEvents 1.0 validation tests for AegisBank."""

from __future__ import annotations

import json
import sys
from pathlib import Path
from typing import Any

import jsonschema
import pytest
from jsonschema import Draft202012Validator

REPO_ROOT = Path(__file__).resolve().parents[5]
CONTRACTS_DIR = REPO_ROOT / "contracts"
CLOUDEVENT_SCHEMA = CONTRACTS_DIR / "cloudevents" / "service-request-created-v1.schema.json"
DOMAIN_SCHEMA = CONTRACTS_DIR / "service-request-created.schema.json"

FUNCTIONS_ROOT = REPO_ROOT / "functions" / "aegisbank-events"
if str(FUNCTIONS_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_ROOT))

from cloud_event import (  # type: ignore[import-not-found]  # noqa: E402
    CLOUD_EVENT_DATA_SCHEMA,
    CLOUD_EVENT_SOURCE,
    CLOUD_EVENT_SPEC_VERSION,
    CLOUD_EVENT_TYPE,
    CloudEventValidationError,
    map_service_request_created,
    validate_cloud_event,
)

pytestmark = pytest.mark.contract


@pytest.fixture
def cloudevents_schema() -> dict[str, Any]:
    return json.loads(CLOUDEVENT_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture
def domain_schema() -> dict[str, Any]:
    return json.loads(DOMAIN_SCHEMA.read_text(encoding="utf-8"))


@pytest.fixture
def canonical_outbox_event() -> dict[str, Any]:
    return {
        "event_id": "EVT-SR-000123",
        "event_type": "ServiceRequestCreated",
        "aggregate_type": "ServiceRequest",
        "aggregate_id": "SR-000123",
        "timestamp": "2026-09-01T22:56:00-05:00",
        "payload": {
            "service_request_id": "SR-000123",
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "reason_code": "GENERAL_OTHER",
            "reason_label": "Otro motivo",
            "description": "Solicitud de consulta general",
            "status": "OPEN",
            "created_at": "2026-09-01T22:55:50-05:00",
        },
    }


@pytest.fixture
def canonical_cloud_event() -> dict[str, Any]:
    return {
        "specversion": CLOUD_EVENT_SPEC_VERSION,
        "id": "EVT-SR-000123",
        "source": CLOUD_EVENT_SOURCE,
        "type": CLOUD_EVENT_TYPE,
        "subject": "/service-requests/SR-000123",
        "time": "2026-09-01T22:56:00-05:00",
        "datacontenttype": "application/json",
        "dataschema": CLOUD_EVENT_DATA_SCHEMA,
        "correlationid": "CORR-V013-LOCAL-001",
        "traceparent": "00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
        "data": {
            "service_request_id": "SR-000123",
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "reason_code": "GENERAL_OTHER",
            "reason_label": "Otro motivo",
            "status": "OPEN",
        },
    }


def test_cloud_event_schema_is_valid_draft_2020_12(cloudevents_schema: dict[str, Any]) -> None:
    Draft202012Validator.check_schema(cloudevents_schema)


def test_canonical_cloud_event_passes_schema(
    cloudevents_schema: dict[str, Any], canonical_cloud_event: dict[str, Any]
) -> None:
    jsonschema.validate(instance=canonical_cloud_event, schema=cloudevents_schema)


def test_validate_cloud_event_rejects_unknown_type(
    cloudevents_schema: dict[str, Any], canonical_cloud_event: dict[str, Any]
) -> None:
    invalid = dict(canonical_cloud_event, type="com.otherbank.event")
    with pytest.raises(CloudEventValidationError):
        validate_cloud_event(invalid)


def test_validate_cloud_event_rejects_unknown_specversion(
    cloudevents_schema: dict[str, Any], canonical_cloud_event: dict[str, Any]
) -> None:
    invalid = dict(canonical_cloud_event, specversion="2.0")
    with pytest.raises(CloudEventValidationError):
        validate_cloud_event(invalid)


def test_validate_cloud_event_rejects_unknown_category(
    cloudevents_schema: dict[str, Any], canonical_cloud_event: dict[str, Any]
) -> None:
    invalid_data = dict(canonical_cloud_event["data"], category="PAYMENT")
    invalid = dict(canonical_cloud_event, data=invalid_data)
    with pytest.raises(CloudEventValidationError):
        validate_cloud_event(invalid)


def test_validate_cloud_event_rejects_extra_data_field(
    cloudevents_schema: dict[str, Any], canonical_cloud_event: dict[str, Any]
) -> None:
    invalid_data = dict(canonical_cloud_event["data"], amount=10.0)
    invalid = dict(canonical_cloud_event, data=invalid_data)
    with pytest.raises(CloudEventValidationError):
        validate_cloud_event(invalid)


def test_validate_cloud_event_rejects_invalid_traceparent(
    cloudevents_schema: dict[str, Any], canonical_cloud_event: dict[str, Any]
) -> None:
    invalid = dict(canonical_cloud_event, traceparent="not-a-traceparent")
    with pytest.raises(CloudEventValidationError):
        validate_cloud_event(invalid)


def test_map_service_request_created_minimizes_data_fields(
    canonical_outbox_event: dict[str, Any],
) -> None:
    cloud_event = map_service_request_created(
        canonical_outbox_event, correlation_id="CORR-V013-LOCAL-001"
    )
    assert cloud_event["type"] == CLOUD_EVENT_TYPE
    assert cloud_event["specversion"] == CLOUD_EVENT_SPEC_VERSION
    assert cloud_event["source"] == CLOUD_EVENT_SOURCE
    assert cloud_event["dataschema"] == CLOUD_EVENT_DATA_SCHEMA
    assert cloud_event["subject"] == "/service-requests/SR-000123"
    assert set(cloud_event["data"].keys()) == {
        "service_request_id",
        "customer_id",
        "category",
        "reason_code",
        "reason_label",
        "status",
    }
    assert "description" not in cloud_event["data"]
    assert "created_at" not in cloud_event["data"]


def test_map_service_request_created_preserves_traceparent(
    canonical_outbox_event: dict[str, Any],
) -> None:
    cloud_event = map_service_request_created(
        canonical_outbox_event,
        correlation_id="CORR-V013-LOCAL-002",
        traceparent="00-4bf92f3577b34da6a3ce929d0e0e4736-00f067aa0ba902b7-01",
    )
    assert cloud_event["traceparent"].startswith("00-4bf92f3577b34da6a3ce929d0e0e4736-")


def test_map_service_request_created_rejects_invalid_domain(
    canonical_outbox_event: dict[str, Any],
) -> None:
    bad_event = dict(canonical_outbox_event)
    bad_payload = dict(canonical_outbox_event["payload"])
    bad_payload["status"] = "UNKNOWN_STATE"
    bad_event["payload"] = bad_payload
    with pytest.raises(CloudEventValidationError):
        map_service_request_created(bad_event, correlation_id="CORR-X")
