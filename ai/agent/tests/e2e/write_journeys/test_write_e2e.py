"""End-to-End Acceptance tests for AegisBank v0.8 Reliability + Messaging flow."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.models import IdempotencyRecord, OutboxEvent, ServiceRequest
from sqlalchemy import select

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.hitl import ApprovalStatus, HITLApprovalManager
from aegisbank_agent.reliability.messaging import (
    IdempotentConsumer,
    LocalMessageBus,
    Message,
    OutboxProcessor,
)
from aegisbank_agent.tools.banking_tools import (
    CreateServiceRequestTool,
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.e2e


class DummyChoice:
    def __init__(self, message: object):
        self.message = message


class DummyResponse:
    def __init__(self, message: object):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


class DummyToolCall:
    def __init__(self, id: str, name: str, arguments: str):
        self.id = id
        self.function = MagicMock()
        self.function.name = name
        self.function.arguments = arguments


def test_full_e2e_reliability_messaging_flow_approve(in_memory_db: Database) -> None:
    # 1. Setup Infrastructure
    bus = LocalMessageBus()
    consumed_events: list[Message] = []
    consumer = IdempotentConsumer(consumed_events.append)
    bus.subscribe("ServiceRequestCreated", consumer.handle)

    # 2. Setup Agent with mocked LLM tool proposal
    tc = DummyToolCall(
        "call_101",
        "create_service_request",
        json.dumps(
            {
                "category": "INSTALLMENT",
                "description": "Reclamo formal cuota duplicada",
                "idempotency_key": "IDEMP-E2E-TEST-001",
            }
        ),
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="Su reclamo fue aprobado y registrado exitosamente.")),
    ]

    hitl_mgr = HITLApprovalManager()
    registry = ToolRegistry(
        [
            SearchKnowledgeTool(),
            GetMyLoansTool(in_memory_db),
            GetLoanDetailsTool(in_memory_db),
            GetNextInstallmentTool(in_memory_db),
            CreateServiceRequestTool(in_memory_db),
        ]
    )
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        hitl_manager=hitl_mgr,
        approval_callback=lambda req: True,  # Human APPROVES
    )

    # 3. Execute query through Agent
    result = orchestrator.run(
        "Por favor crea el reclamo de cuota duplicada", customer_id="CUST-0001"
    )
    assert result.success is True
    assert len(result.approval_requests) == 1
    assert result.approval_requests[0].status == ApprovalStatus.EXECUTED

    # 4. Verify Database state: ServiceRequest, IdempotencyRecord, OutboxEvent
    with in_memory_db.session() as session:
        created_sr = session.scalar(
            select(ServiceRequest).where(
                ServiceRequest.description == "Reclamo formal cuota duplicada"
            )
        )
        assert created_sr is not None
        assert created_sr.customer_id == "CUST-0001"

        idemp = session.scalar(
            select(IdempotencyRecord).where(
                IdempotencyRecord.idempotency_key == "IDEMP-E2E-TEST-001"
            )
        )
        assert idemp is not None
        assert idemp.resource_id == created_sr.service_request_id

        outbox = session.scalar(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == created_sr.service_request_id)
        )
        assert outbox is not None
        assert outbox.status == "PENDING"

    # 5. Execute Outbox Processor -> publishes to MessageBus -> IdempotentConsumer
    processor = OutboxProcessor(in_memory_db, bus)
    processed_count = processor.process_pending()
    assert processed_count >= 1

    # 6. Verify Consumer received and processed event
    assert len(consumed_events) == 1
    msg = consumed_events[0]
    assert msg.event_type == "ServiceRequestCreated"
    assert msg.payload["customer_id"] == "CUST-0001"
    assert msg.payload["category"] == "INSTALLMENT"

    # 7. Verify Outbox event status updated to PUBLISHED
    with in_memory_db.session() as session:
        outbox_post = session.scalar(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == created_sr.service_request_id)
        )
        assert outbox_post is not None
        assert outbox_post.status == "PUBLISHED"


def test_full_e2e_reliability_messaging_flow_reject(in_memory_db: Database) -> None:
    bus = LocalMessageBus()
    consumed_events: list[Message] = []
    consumer = IdempotentConsumer(consumed_events.append)
    bus.subscribe("ServiceRequestCreated", consumer.handle)

    with in_memory_db.session() as session:
        initial_sr_count = len(session.scalars(select(ServiceRequest)).all())
        initial_outbox_count = len(session.scalars(select(OutboxEvent)).all())

    tc = DummyToolCall(
        "call_102",
        "create_service_request",
        json.dumps(
            {
                "category": "LOAN",
                "description": "Reclamo rechazado por humano",
                "idempotency_key": "IDEMP-REJECT-001",
            }
        ),
    )
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[tc])),
        DummyResponse(DummyMessage(content="Operación cancelada por el usuario.")),
    ]

    hitl_mgr = HITLApprovalManager()
    registry = ToolRegistry(
        [
            SearchKnowledgeTool(),
            GetMyLoansTool(in_memory_db),
            CreateServiceRequestTool(in_memory_db),
        ]
    )
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        hitl_manager=hitl_mgr,
        approval_callback=lambda req: False,  # Human REJECTS
    )

    result = orchestrator.run("Registrar reclamo", customer_id="CUST-0001")
    assert result.success is True
    assert len(result.approval_requests) == 1
    assert result.approval_requests[0].status == ApprovalStatus.REJECTED

    # Verify zero mutations
    with in_memory_db.session() as session:
        final_sr_count = len(session.scalars(select(ServiceRequest)).all())
        final_outbox_count = len(session.scalars(select(OutboxEvent)).all())

    assert final_sr_count == initial_sr_count
    assert final_outbox_count == initial_outbox_count

    # Outbox processor has nothing to publish
    processor = OutboxProcessor(in_memory_db, bus)
    processed_count = processor.process_pending()
    assert processed_count == 0
    assert len(consumed_events) == 0
