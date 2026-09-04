"""Contract tests validating Cosmos DB item schema compliance against JSON Schema draft 2020-12."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest

pytestmark = pytest.mark.contract


CONTRACTS_DIR = Path(__file__).resolve().parents[4] / "contracts"
COSMOS_SCHEMA_PATH = CONTRACTS_DIR / "cosmos-event-item.schema.json"


@pytest.fixture
def cosmos_schema() -> dict:
    assert COSMOS_SCHEMA_PATH.exists(), f"Schema not found: {COSMOS_SCHEMA_PATH}"
    return json.loads(COSMOS_SCHEMA_PATH.read_text(encoding="utf-8"))


def test_cosmos_contract_valid_payload(cosmos_schema: dict) -> None:
    """Verify standard Cosmos event item conforms to the schema contract."""
    payload = {
        "id": "evt_20260901_001_a1b2c3d4",
        "customer_id": "CUST-001",
        "schema_version": "1.0",
        "event_type": "service_request_logged",
        "correlation_id": "corr-f9a8b7c6",
        "timestamp_utc": "2026-09-01T03:00:00Z",
        "payload": {
            "request_id": "SR-2026-0001",
            "request_type": "account_limit_increase",
            "status": "pending_approval",
        },
        "metadata": {
            "channel": "ai_agent_mcp",
            "agent_version": "0.7.0",
        },
        "ttl": 2592000,
    }
    # Should validate without raising ValidationError
    jsonschema.validate(instance=payload, schema=cosmos_schema)


def test_cosmos_contract_missing_partition_key_fails(cosmos_schema: dict) -> None:
    """Verify payload without required customer_id partition key is rejected."""
    payload = {
        "id": "evt_invalid_001",
        # missing customer_id
        "schema_version": "1.0",
        "event_type": "service_request_logged",
        "correlation_id": "corr-f9a8b7c6",
        "timestamp_utc": "2026-09-01T03:00:00Z",
        "payload": {},
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=payload, schema=cosmos_schema)


def test_cosmos_contract_invalid_schema_version_fails(cosmos_schema: dict) -> None:
    """Verify invalid schema_version format is rejected."""
    payload = {
        "id": "evt_invalid_002",
        "customer_id": "CUST-001",
        "schema_version": "v1_invalid",
        "event_type": "service_request_logged",
        "correlation_id": "corr-f9a8b7c6",
        "timestamp_utc": "2026-09-01T03:00:00Z",
        "payload": {},
    }
    with pytest.raises(jsonschema.ValidationError):
        jsonschema.validate(instance=payload, schema=cosmos_schema)
