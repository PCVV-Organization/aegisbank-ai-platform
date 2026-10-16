"""Comprehensive End-to-End (E2E) regression test suite for critical AegisBank journeys."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.hitl import ApprovalStatus, HITLApprovalManager
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.hotl import HOTLSupervisor
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.reliability.circuit_breaker import CircuitBreaker, CircuitBreakerOpenError
from aegisbank_agent.reliability.messaging import (
    DeadLetterQueue,
    IdempotentConsumer,
    LocalMessageBus,
    Message,
    OutboxProcessor,
)
from aegisbank_agent.reliability.retry import RetryPolicy
from aegisbank_agent.tools.banking_tools import (
    CreateServiceRequestTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.e2e


class _Response:
    def __init__(self, message: object):
        self.choices = [type("Choice", (), {"message": message})()]


class _Message:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


def _call(name: str, arguments: dict[str, str]) -> object:
    function = type("Function", (), {"name": name, "arguments": json.dumps(arguments)})()
    return type("ToolCall", (), {"id": "E2E-CALL-001", "function": function})()


# Journey A: Single-step READ account
def test_journey_a_read_account_policy_routes_real_tool() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _Response(
        _Message(content="Estos son tus préstamos sintéticos.")
    )
    registry = ToolRegistry([GetMyLoansTool(create_default_database())])

    result = AgentOrchestrator(client=client, registry=registry).run(
        "¿Cuáles son mis préstamos activos?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert [record.tool_name for record in result.tool_calls] == ["get_my_loans"]
    assert result.tool_calls[0].result.data["customer_id"] == "CUST-0001"


# Journey B: Multi-step READ account + next installment
def test_journey_b_multistep_read_routes_next_installment() -> None:
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[_call("get_next_installment", {"loan_id": "LOAN-0002"})])),
        _Response(_Message(content="La cuota fue consultada en Core Banking.")),
    ]
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetNextInstallmentTool(db)])

    result = AgentOrchestrator(client=client, registry=registry).run(
        "¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert [record.tool_name for record in result.tool_calls] == [
        "get_my_loans",
        "get_next_installment",
        "get_next_installment",
    ]
    assert result.tool_calls[-1].result.success is True


# Journey C: RAG knowledge available with grounding
def test_journey_c_rag_knowledge_available_with_grounding() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = _Response(
        _Message(content="El crédito personal permite plazos de 6 a 60 meses según la política.")
    )
    registry = ToolRegistry([SearchKnowledgeTool()])

    result = AgentOrchestrator(client=client, registry=registry).run(
        "¿Cuáles son los plazos de un crédito personal?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert result.tool_calls[0].result.success is True
    assert len(result.tool_calls[0].result.data.get("hits", [])) > 0


# Journey D: RAG knowledge gap with explicit abstention
def test_journey_d_rag_knowledge_gap_abstains_before_generation() -> None:
    client = MagicMock()
    metrics = OperationalMetrics()
    registry = ToolRegistry([SearchKnowledgeTool()])

    result = AgentOrchestrator(client=client, registry=registry, metrics=metrics).run(
        "¿Cuál es el plazo máximo para un crédito vehicular?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert "No encuentro información suficiente" in result.answer
    assert metrics.get_counter("knowledge_abstention_count") == 1


# Journey E: WRITE with HITL REJECT (zero side effects)
def test_journey_e_write_hitl_reject_zero_side_effects() -> None:
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), CreateServiceRequestTool(db)])
    hitl_mgr = HITLApprovalManager()

    tc_write = _call(
        "create_service_request",
        {
            "category": "LOAN",
            "description": "Solicitud que será rechazada",
            "idempotency_key": "IDEMP-E2E-REJECT",
        },
    )
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[tc_write])),
        _Response(_Message(content="Operación cancelada.")),
    ]

    orchestrator = AgentOrchestrator(
        client=client,
        registry=registry,
        hitl_manager=hitl_mgr,
        approval_callback=lambda req: False,  # Human says REJECT
    )

    result = orchestrator.run("Crea un reclamo formal", customer_id="CUST-0001")

    assert len(result.approval_requests) == 1
    assert result.approval_requests[0].status == ApprovalStatus.REJECTED
    # Assert zero side-effects in database
    with db.session() as session:
        from mock_core_banking.persistence.models import ServiceRequest  # noqa: E402

        sr = (
            session.query(ServiceRequest)
            .filter_by(description="Solicitud que será rechazada")
            .first()
        )
        assert sr is None


# Journey F: WRITE with HITL APPROVE (idempotent write + outbox + consumer)
def test_journey_f_write_hitl_approve_idempotent_outbox_consumer() -> None:
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), CreateServiceRequestTool(db)])
    hitl_mgr = HITLApprovalManager()
    bus = LocalMessageBus()
    consumed_events: list[Message] = []

    consumer = IdempotentConsumer(handler=lambda event: consumed_events.append(event))
    bus.subscribe("ServiceRequestCreated", consumer.handle)

    tc_write = _call(
        "create_service_request",
        {
            "category": "LOAN",
            "description": "Solicitud aprobada E2E",
            "idempotency_key": "IDEMP-E2E-APPROVE-001",
        },
    )
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[tc_write])),
        _Response(_Message(content="Solicitud creada exitosamente.")),
    ]

    orchestrator = AgentOrchestrator(
        client=client,
        registry=registry,
        hitl_manager=hitl_mgr,
        approval_callback=lambda req: True,  # Human says APPROVE
    )

    result = orchestrator.run("Crea una solicitud formal", customer_id="CUST-0001")

    assert result.success is True
    assert len(result.approval_requests) == 1
    assert result.approval_requests[0].status in (ApprovalStatus.APPROVED, ApprovalStatus.EXECUTED)

    # Process outbox events to bus and verify consumer processing
    processor = OutboxProcessor(db, bus)
    processed_count = processor.process_pending()
    assert processed_count >= 1
    assert len(consumed_events) >= 1
    assert consumed_events[0].event_type == "ServiceRequestCreated"


# Journey G: HOTL supervisory kill-switch engagement
def test_journey_g_hotl_kill_switch_blocks_write() -> None:
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), CreateServiceRequestTool(db)])
    audit = AuditLogger()
    hotl = HOTLSupervisor(audit_logger=audit)
    hotl.engage_kill_switch(reason="Emergencia de seguridad operativa")

    tc_write = _call(
        "create_service_request",
        {
            "category": "LOAN",
            "description": "Solicitud bloqueada por HOTL",
            "idempotency_key": "IDEMP-E2E-HOTL",
        },
    )
    client = MagicMock()
    client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[tc_write])),
        _Response(_Message(content="No se pudo procesar la solicitud.")),
    ]

    orchestrator = AgentOrchestrator(
        client=client,
        registry=registry,
        hotl_supervisor=hotl,
    )

    result = orchestrator.run("Crear solicitud urgente", customer_id="CUST-0001")

    assert result.tool_calls[0].result.success is False
    assert "HOTL" in result.tool_calls[0].result.error


# Journey H: Reliability (retries, circuit breaker, DLQ)
def test_journey_h_reliability_retries_circuit_breaker_dlq() -> None:
    # 1. Transient failure -> retry -> success
    attempts = 0

    def transient_fn() -> str:
        nonlocal attempts
        attempts += 1
        if attempts < 3:
            raise ConnectionError("Transient network failure")
        return "SUCCESS_RETRY"

    policy = RetryPolicy(max_retries=3, base_delay=0.01, max_delay=0.05, jitter=False)
    assert policy.execute(transient_fn) == "SUCCESS_RETRY"
    assert attempts == 3

    # 2. Persistent failure -> circuit breaker OPEN
    cb = CircuitBreaker(failure_threshold=2, recovery_timeout=0.1)

    def failing_fn() -> None:
        raise ValueError("Downstream service crashed")

    for _ in range(2):
        with pytest.raises(ValueError):
            cb.execute(failing_fn)

    assert cb.state.value == "OPEN"
    with pytest.raises(CircuitBreakerOpenError):
        cb.execute(failing_fn)

    # 3. Poison event -> DLQ
    dlq = DeadLetterQueue()

    poison_event = Message(
        event_id="EVT-POISON-001",
        event_type="CorruptedPayloadEvent",
        aggregate_type="ServiceRequest",
        aggregate_id="SR-999999",
        payload={"corrupted": True},
    )

    def crashing_handler(event: Message) -> None:
        raise RuntimeError("Deserialization failed for poison pill")

    consumer = IdempotentConsumer(handler=crashing_handler, dlq=dlq, max_delivery_attempts=2)
    with pytest.raises(RuntimeError):
        consumer.handle(poison_event)  # Attempt 1 -> re-raises for broker retry

    res = consumer.handle(poison_event)  # Attempt 2 -> routes to DLQ and returns False
    assert res is False

    # Verify poison event is safely routed to DLQ
    dead_letters = dlq.list_records()
    assert any(dl.message.event_id == "EVT-POISON-001" for dl in dead_letters)
