"""Acceptance tests that drive the Function App through its registered bindings."""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any
from unittest.mock import MagicMock

import pytest

REPO_ROOT = Path(__file__).resolve().parents[5]
FUNCTIONS_ROOT = REPO_ROOT / "functions" / "aegisbank-events"
if str(FUNCTIONS_ROOT) not in sys.path:
    sys.path.insert(0, str(FUNCTIONS_ROOT))

import azure.functions as func  # noqa: E402
from function_app import (  # type: ignore[import-not-found]  # noqa: E402
    app,
    service_request_created,
)

pytestmark = pytest.mark.infra


def _sdk_event(**overrides: Any) -> MagicMock:
    payload = {
        "service_request_id": "SR-9001",
        "customer_id": "CUST-9001",
        "category": "GENERAL",
        "status": "OPEN",
    }
    event = MagicMock(spec=func.CloudEvent)
    event.id = overrides.get("id", "EVT-FUNCTION-001")
    event.source = overrides.get("source", "urn:aegisbank:mock-core-banking")
    event.type = overrides.get("type", "com.aegisbank.service-request.created.v1")
    event.subject = overrides.get("subject", "/service-requests/SR-9001")
    event.time = overrides.get("time", "2026-09-01T22:00:00-05:00")
    event.datacontenttype = overrides.get("datacontenttype", "application/json")
    event.dataschema = overrides.get(
        "dataschema", "urn:aegisbank:contracts:service-request-created:v1"
    )
    event.specversion = overrides.get("specversion", "1.0")
    event.correlationid = overrides.get("correlationid", "CORR-FUNCTION-001")
    event.traceparent = overrides.get("traceparent", None)
    event.data = payload if not overrides else {**payload, **overrides.get("data_overrides", {})}
    event.get_json.return_value = event.data
    event.to_dict.return_value = {
        "id": event.id,
        "source": event.source,
        "type": event.type,
        "specversion": event.specversion,
        "subject": event.subject,
        "time": event.time,
        "datacontenttype": event.datacontenttype,
        "dataschema": event.dataschema,
        "data": event.data,
        "extension_attrs": {"correlationid": event.correlationid, "traceparent": event.traceparent},
    }
    return event


def test_function_app_declares_event_grid_trigger() -> None:
    function_names = {fn.get_function_name() for fn in app.get_functions()}
    assert "service_request_created" in function_names


def test_event_grid_trigger_processes_cloudevent_payload() -> None:
    event = _sdk_event()
    service_request_created(event)


def test_event_grid_trigger_acknowledges_malformed_payload_gracefully() -> None:
    payload = {
        "specversion": "1.0",
        "id": "EVT-BAD-001",
        "source": "urn:aegisbank:mock-core-banking",
        "type": "com.otherbank.event",
        "subject": "/service-requests/SR-9999",
        "time": "2026-09-01T22:00:00-05:00",
        "datacontenttype": "application/json",
        "dataschema": "urn:aegisbank:contracts:service-request-created:v1",
        "correlationid": "CORR-BAD-001",
        "data": {
            "service_request_id": "SR-9999",
            "customer_id": "CUST-0001",
            "category": "GENERAL",
            "status": "OPEN",
        },
    }
    with pytest.raises(Exception):
        service_request_created(payload)


def test_event_grid_trigger_is_idempotent_across_invocations() -> None:
    event = _sdk_event(id="EVT-IDEMP-001", correlationid="CORR-IDEMP-001")
    service_request_created(event)
    service_request_created(event)
