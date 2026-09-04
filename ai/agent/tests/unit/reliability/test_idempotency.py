"""Tests for IdempotencyGuard and idempotency persistence."""

from __future__ import annotations

import pytest
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.models import IdempotencyRecord, ServiceRequest
from sqlalchemy import select

from aegisbank_agent.reliability.idempotency import (
    IdempotencyConflictError,
    IdempotencyGuard,
    canonical_arguments_hash,
)
from aegisbank_agent.tools.banking_tools import CreateServiceRequestTool
from aegisbank_agent.tools.base import AgentContext

pytestmark = pytest.mark.unit


def test_canonical_arguments_hash_deterministic() -> None:
    args1 = {"description": "Cuota duplicada", "category": "INSTALLMENT"}
    args2 = {"category": "INSTALLMENT", "description": "Cuota duplicada"}
    assert canonical_arguments_hash(args1) == canonical_arguments_hash(args2)


def test_idempotent_execution_replays_cached_result(in_memory_db: Database) -> None:
    guard = IdempotencyGuard(in_memory_db)
    counter = {"calls": 0}

    def dummy_write() -> dict[str, str]:
        counter["calls"] += 1
        return {"service_request_id": f"SR-{counter['calls']:06d}", "status": "OPEN"}

    args = {"category": "INSTALLMENT", "description": "Cuota duplicada"}

    # First call: executes operation
    res1, cached1 = guard.execute_idempotent("KEY-123", "CUST-0001", args, dummy_write)
    assert cached1 is False
    assert res1["service_request_id"] == "SR-000001"
    assert counter["calls"] == 1

    # Second call with same key: returns cached result without re-executing
    res2, cached2 = guard.execute_idempotent("KEY-123", "CUST-0001", args, dummy_write)
    assert cached2 is True
    assert res2["service_request_id"] == "SR-000001"
    assert counter["calls"] == 1


def test_idempotent_execution_detects_tampered_args(in_memory_db: Database) -> None:
    guard = IdempotencyGuard(in_memory_db)

    def dummy_write() -> dict[str, str]:
        return {"service_request_id": "SR-000001"}

    orig_args = {"category": "INSTALLMENT", "description": "Cuota duplicada"}
    guard.execute_idempotent("KEY-456", "CUST-0001", orig_args, dummy_write)

    tampered_args = {"category": "INSTALLMENT", "description": "Doble cuota modificada"}
    with pytest.raises(IdempotencyConflictError):
        guard.execute_idempotent("KEY-456", "CUST-0001", tampered_args, dummy_write)


def test_idempotent_execution_detects_customer_mismatch(in_memory_db: Database) -> None:
    guard = IdempotencyGuard(in_memory_db)

    def dummy_write() -> dict[str, str]:
        return {"service_request_id": "SR-000001"}

    args = {"category": "INSTALLMENT", "description": "Cuota duplicada"}
    guard.execute_idempotent("KEY-789", "CUST-0001", args, dummy_write)

    with pytest.raises(IdempotencyConflictError):
        guard.execute_idempotent("KEY-789", "CUST-0002", args, dummy_write)


def test_create_service_request_tool_with_idempotency_key(in_memory_db: Database) -> None:
    tool = CreateServiceRequestTool(in_memory_db)
    context = AgentContext(session_customer_id="CUST-0001")

    # Initial count
    with in_memory_db.session() as session:
        initial_sr_count = len(
            session.scalars(
                select(ServiceRequest).where(ServiceRequest.customer_id == "CUST-0001")
            ).all()
        )
        initial_idemp_count = len(session.scalars(select(IdempotencyRecord)).all())

    # Call 1 with explicit key
    res1 = tool.execute(
        {
            "category": "INSTALLMENT",
            "description": "Reclamo por cuota duplicada",
            "idempotency_key": "IDEMP-KEY-TEST-001",
        },
        context,
    )
    assert res1.success is True
    sr_id_1 = res1.data["service_request_id"]

    # Call 2 with identical key
    res2 = tool.execute(
        {
            "category": "INSTALLMENT",
            "description": "Reclamo por cuota duplicada",
            "idempotency_key": "IDEMP-KEY-TEST-001",
        },
        context,
    )
    assert res2.success is True
    assert res2.data["service_request_id"] == sr_id_1

    # Verify exactly 1 ServiceRequest and 1 IdempotencyRecord were written
    with in_memory_db.session() as session:
        final_sr_count = len(
            session.scalars(
                select(ServiceRequest).where(ServiceRequest.customer_id == "CUST-0001")
            ).all()
        )
        final_idemp_count = len(session.scalars(select(IdempotencyRecord)).all())

    assert final_sr_count == initial_sr_count + 1
    assert final_idemp_count == initial_idemp_count + 1
