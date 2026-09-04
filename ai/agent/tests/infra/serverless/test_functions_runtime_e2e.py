"""End-to-end integration tests against live Azure Functions runtime container.

Validates that the Event Grid CloudEvent handler executes through the live
Microsoft Azure Functions Host and Python 3.14 worker on port 7071.
Skipped automatically when the live runtime container is not running.
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

import pytest

BASE_URL = "http://127.0.0.1:7071"
MASTER_KEY = "aegisbank-local-master-key"
WEBHOOK_URL = (
    f"{BASE_URL}/runtime/webhooks/eventgrid?functionName=service_request_created&code={MASTER_KEY}"
)
REPO_ROOT = Path(__file__).resolve().parents[5]

pytestmark = pytest.mark.infra


def _is_runtime_available() -> bool:
    try:
        url = f"{BASE_URL}/admin/host/status?code={MASTER_KEY}"
        with urllib.request.urlopen(url, timeout=1.5) as resp:
            return resp.status == 200
    except urllib.error.URLError, OSError, TimeoutError, ValueError:
        return False


def _post_json(url: str, payload: Any, headers: dict[str, str] | None = None) -> tuple[int, Any]:
    req_headers = {"Content-Type": "application/json", **(headers or {})}
    data = json.dumps(payload).encode("utf-8")
    req = urllib.request.Request(url, data=data, headers=req_headers, method="POST")
    try:
        with urllib.request.urlopen(req, timeout=5.0) as resp:
            content = resp.read().decode("utf-8")
            try:
                parsed = json.loads(content) if content else {}
            except json.JSONDecodeError:
                parsed = content
            return resp.status, parsed
    except urllib.error.HTTPError as exc:
        content = exc.read().decode("utf-8")
        try:
            parsed = json.loads(content) if content else {}
        except json.JSONDecodeError:
            parsed = content
        return exc.code, parsed


@pytest.mark.skipif(
    not _is_runtime_available(),
    reason="Azure Functions live runtime container not active on port 7071",
)
def test_live_functions_host_status_is_running() -> None:
    url = f"{BASE_URL}/admin/host/status?code={MASTER_KEY}"
    with urllib.request.urlopen(url, timeout=2.0) as resp:
        assert resp.status == 200
        data = json.loads(resp.read().decode("utf-8"))
        assert data.get("state") == "Running"
        assert "version" in data


@pytest.mark.skipif(
    not _is_runtime_available(),
    reason="Azure Functions live runtime container not active on port 7071",
)
def test_live_event_grid_subscription_handshake() -> None:
    validation_code = "TEST-VALIDATION-CODE-999"
    handshake = [
        {
            "id": "validation-test-e2e",
            "topic": "/subscriptions/test/topics/test",
            "subject": "",
            "data": {"validationCode": validation_code},
            "eventType": "Microsoft.EventGrid.SubscriptionValidationEvent",
            "eventTime": "2026-09-01T22:56:00Z",
            "dataVersion": "1",
        }
    ]
    status, body = _post_json(
        WEBHOOK_URL,
        handshake,
        headers={"aeg-event-type": "SubscriptionValidation"},
    )
    assert status == 200
    assert isinstance(body, dict)
    assert body.get("validationResponse") == validation_code


@pytest.mark.skipif(
    not _is_runtime_available(),
    reason="Azure Functions live runtime container not active on port 7071",
)
def test_live_event_grid_cloudevent_execution_and_idempotency() -> None:
    sample_file = (
        REPO_ROOT
        / "functions"
        / "aegisbank-events"
        / "samples"
        / "service-request-created.cloudevent.json"
    )
    event_payload = json.loads(sample_file.read_text(encoding="utf-8"))
    event_payload["time"] = "2026-09-01T22:56:00Z"
    event_payload["id"] = "EVT-E2E-RUNTIME-001"
    event_payload["correlationid"] = "CORR-E2E-RUNTIME-001"
    event_payload["data"]["service_request_id"] = "SR-E2E-001"

    # Initial dispatch -> expect HTTP 202 Accepted
    status1, _ = _post_json(
        WEBHOOK_URL,
        event_payload,
        headers={"aeg-event-type": "Notification"},
    )
    assert status1 in (200, 202)

    # Replay identical event -> expect idempotent HTTP 202 Accepted
    status2, _ = _post_json(
        WEBHOOK_URL,
        event_payload,
        headers={"aeg-event-type": "Notification"},
    )
    assert status2 in (200, 202)
