"""Contract tests for Transactional Outbox domain event schemas."""

from __future__ import annotations

import json
from pathlib import Path

import jsonschema
import pytest
from mock_core_banking.persistence.models import OutboxEvent as DbOutboxEvent

from aegisbank_agent.tools.banking_tools import (
    CreateServiceRequestTool,
    create_default_database,
)
from aegisbank_agent.tools.base import AgentContext

pytestmark = pytest.mark.contract


def _load_schema(filename: str) -> dict:
    contracts_dir = Path(__file__).resolve().parents[4] / "contracts"
    schema_path = contracts_dir / filename
    with open(schema_path, "r", encoding="utf-8") as f:
        return json.load(f)


def test_service_request_created_event_matches_contract_schema() -> None:
    db = create_default_database()
    tool = CreateServiceRequestTool(db)
    ctx = AgentContext(session_customer_id="CUST-0001")

    res = tool.execute(
        {
            "category": "LOAN",
            "reason_code": "LOAN_BALANCE_DISPUTE",
            "reason_label": "Saldo o detalle del préstamo",
            "description": "Contract validation service request",
            "idempotency_key": "IDEMP-CONTRACT-001",
        },
        ctx,
    )
    assert res.success is True

    # Retrieve outbox event directly from database
    with db.session() as session:
        db_event = (
            session.query(DbOutboxEvent)
            .filter_by(aggregate_id=res.data["service_request_id"])
            .first()
        )
        assert db_event is not None

        payload_obj = (
            json.loads(db_event.payload) if isinstance(db_event.payload, str) else db_event.payload
        )
        event_dict = {
            "event_id": db_event.event_id,
            "event_type": db_event.event_type,
            "aggregate_type": "ServiceRequest",
            "aggregate_id": db_event.aggregate_id,
            "timestamp": db_event.created_at.isoformat(),
            "payload": payload_obj,
        }

    schema = _load_schema("service-request-created.schema.json")
    jsonschema.validate(instance=event_dict, schema=schema)
