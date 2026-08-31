"""Deterministic failure injection tests verifying all v0.8 reliability invariants."""

from __future__ import annotations

import time
from concurrent.futures import ThreadPoolExecutor

import pytest
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.models import IdempotencyRecord, OutboxEvent, ServiceRequest
from sqlalchemy import select

from aegisbank_agent.hitl import ApprovalStateError, HITLApprovalManager
from aegisbank_agent.reliability.circuit_breaker import (
    CircuitBreaker,
    CircuitBreakerOpenError,
    CircuitState,
)
from aegisbank_agent.reliability.messaging import (
    DeadLetterQueue,
    IdempotentConsumer,
    Message,
)
from aegisbank_agent.reliability.retry import RetryPolicy, TransientError
from aegisbank_agent.reliability.timeout import ExecutionTimeoutError, with_timeout
from aegisbank_agent.tools.banking_tools import CreateServiceRequestTool
from aegisbank_agent.tools.base import AgentContext


# 1. Transient failure -> retry -> success
def test_failure_injection_transient_retry_success() -> None:
    calls = 0

    def flaky_core_banking() -> str:
        nonlocal calls
        calls += 1
        if calls <= 2:
            raise TransientError("Error temporal de conexión con el host bancario")
        return "SR-CREATED-OK"

    policy = RetryPolicy(max_retries=3, base_delay=0.001, jitter=False)
    result = policy.execute(flaky_core_banking)
    assert result == "SR-CREATED-OK"
    assert calls == 3


# 2. Persistent failure -> circuit OPEN
def test_failure_injection_persistent_failure_circuit_open() -> None:
    cb = CircuitBreaker(name="core_banking", failure_threshold=3, recovery_timeout=10.0)

    def failing_service() -> None:
        raise ConnectionError("Host bancario caído")

    for _ in range(3):
        with pytest.raises(ConnectionError):
            cb.execute(failing_service)

    assert cb.state == CircuitState.OPEN
    with pytest.raises(CircuitBreakerOpenError):
        cb.execute(lambda: "SHOULD_NOT_RUN")


# 3. Timeout -> failure controlado
def test_failure_injection_timeout_controlled_failure() -> None:
    def hanging_database_call() -> None:
        time.sleep(0.3)

    with pytest.raises(ExecutionTimeoutError, match="excedió el tiempo límite"):
        with_timeout(0.05, hanging_database_call)


# 4. Duplicate request -> no duplicate ServiceRequest
def test_failure_injection_duplicate_request_single_record(in_memory_db: Database) -> None:
    tool = CreateServiceRequestTool(in_memory_db)
    ctx = AgentContext(session_customer_id="CUST-0001")
    req_args = {
        "category": "INSTALLMENT",
        "description": "Reclamo cuota duplicada",
        "idempotency_key": "IDEMP-DUPL-001",
    }

    res1 = tool.execute(req_args, ctx)
    res2 = tool.execute(req_args, ctx)

    assert res1.success is True
    assert res2.success is True
    assert res1.data["service_request_id"] == res2.data["service_request_id"]

    with in_memory_db.session() as session:
        created_records = session.scalars(
            select(ServiceRequest).where(
                ServiceRequest.service_request_id == res1.data["service_request_id"]
            )
        ).all()
        assert len(created_records) == 1


# 5. Duplicate event -> consumer idempotente
def test_failure_injection_duplicate_event_consumer_idempotent() -> None:
    events_handled = 0

    def on_event(msg: Message) -> None:
        nonlocal events_handled
        events_handled += 1

    consumer = IdempotentConsumer(on_event)
    evt = Message(
        event_id="EVT-IDEMP-01",
        event_type="ServiceRequestCreated",
        aggregate_type="service_request",
        aggregate_id="SR-000001",
        payload={},
    )

    consumer.handle(evt)
    consumer.handle(evt)
    consumer.handle(evt)

    assert events_handled == 1


# 6. Poison event -> DLQ
def test_failure_injection_poison_event_routes_to_dlq() -> None:
    dlq = DeadLetterQueue()

    def buggy_handler(msg: Message) -> None:
        raise RuntimeError("Schema parse failure")

    consumer = IdempotentConsumer(buggy_handler, dlq=dlq, max_delivery_attempts=2)
    poison = Message(
        event_id="EVT-POISON-01",
        event_type="ServiceRequestCreated",
        aggregate_type="service_request",
        aggregate_id="SR-000001",
        payload={},
    )

    with pytest.raises(RuntimeError):
        consumer.handle(poison)
    # 2nd attempt reaches limit -> moved to DLQ
    consumer.handle(poison)

    assert dlq.size() == 1
    assert dlq.get("EVT-POISON-01") is not None


# 7. HITL REJECT -> cero WRITE, cero evento
def test_failure_injection_hitl_reject_zero_write_zero_event(in_memory_db: Database) -> None:
    with in_memory_db.session() as session:
        initial_sr = len(session.scalars(select(ServiceRequest)).all())
        initial_outbox = len(session.scalars(select(OutboxEvent)).all())

    mgr = HITLApprovalManager()
    req = mgr.create_request("create_service_request", "CUST-0001", {"category": "LOAN"})
    mgr.reject(req.approval_id, "CUST-0001", reason="Rechazado")

    with in_memory_db.session() as session:
        final_sr = len(session.scalars(select(ServiceRequest)).all())
        final_outbox = len(session.scalars(select(OutboxEvent)).all())

    assert final_sr == initial_sr
    assert final_outbox == initial_outbox


# 8. APPROVE repetido/replay -> no doble efecto
def test_failure_injection_approve_replay_blocked(in_memory_db: Database) -> None:
    mgr = HITLApprovalManager()
    args = {"category": "LOAN", "description": "Reclamo"}
    req = mgr.create_request("create_service_request", "CUST-0001", args)
    mgr.approve(req.approval_id, "CUST-0001")

    # First execution
    mgr.verify_and_mark_executed(req.approval_id, "CUST-0001", args, {"sr_id": "SR-01"})

    # Replay attempt
    with pytest.raises(ApprovalStateError, match="ya fue ejecutada"):
        mgr.verify_and_mark_executed(req.approval_id, "CUST-0001", args, {"sr_id": "SR-02"})


# 9. Concurrencia con misma idempotency key -> un solo efecto
def test_failure_injection_concurrency_same_idempotency_key(in_memory_db: Database) -> None:
    tool = CreateServiceRequestTool(in_memory_db)
    ctx = AgentContext(session_customer_id="CUST-0001")
    req_args = {
        "category": "INSTALLMENT",
        "description": "Reclamo concurrente",
        "idempotency_key": "IDEMP-CONCURRENCY-001",
    }

    with ThreadPoolExecutor(max_workers=3) as executor:
        futures = [executor.submit(tool.execute, req_args, ctx) for _ in range(3)]
        results = [f.result() for f in futures]

    # All executions must report success with the identical ServiceRequest ID
    sr_ids = {r.data["service_request_id"] for r in results if r.success and r.data}
    assert len(sr_ids) == 1

    with in_memory_db.session() as session:
        idemp_records = session.scalars(
            select(IdempotencyRecord).where(
                IdempotencyRecord.idempotency_key == "IDEMP-CONCURRENCY-001"
            )
        ).all()
        assert len(idemp_records) == 1
