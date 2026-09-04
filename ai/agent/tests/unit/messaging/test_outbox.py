"""Tests for Transactional Outbox pattern and message bus publication."""

from __future__ import annotations

import json

import pytest
from mock_core_banking.domain.enums import ServiceRequestCategory
from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.models import OutboxEvent
from mock_core_banking.persistence.repositories import (
    OutboxRepository,
    ServiceRequestRepository,
)
from sqlalchemy import select

from aegisbank_agent.reliability.messaging import (
    LocalMessageBus,
    Message,
    OutboxProcessor,
)

pytestmark = pytest.mark.unit


def test_transactional_outbox_creates_pending_event_atomically(in_memory_db: Database) -> None:
    with in_memory_db.session() as session:
        sr_repo = ServiceRequestRepository(session)
        sr = sr_repo.create(
            customer_id="CUST-0001",
            category=ServiceRequestCategory.INSTALLMENT,
            description="Reclamo sobre cobro de cuota 3",
        )
        session.commit()

        # Verify OutboxEvent was created with status PENDING
        outbox_repo = OutboxRepository(session)
        pending = outbox_repo.list_pending()
        matching = [e for e in pending if e.aggregate_id == sr.service_request_id]
        assert len(matching) == 1

        event = matching[0]
        assert event.event_type == "ServiceRequestCreated"
        assert event.status == "PENDING"
        payload = json.loads(event.payload)
        assert payload["service_request_id"] == sr.service_request_id
        assert payload["customer_id"] == "CUST-0001"
        assert payload["category"] == "INSTALLMENT"


def test_outbox_processor_publishes_to_bus_and_marks_published(in_memory_db: Database) -> None:
    bus = LocalMessageBus()
    received_messages: list[Message] = []
    bus.subscribe("ServiceRequestCreated", received_messages.append)

    with in_memory_db.session() as session:
        sr_repo = ServiceRequestRepository(session)
        sr = sr_repo.create(
            customer_id="CUST-0001",
            category=ServiceRequestCategory.FEE,
            description="Comisión indebida",
        )
        session.commit()

    processor = OutboxProcessor(in_memory_db, bus)
    processed_count = processor.process_pending()
    assert processed_count >= 1

    # Verify bus received message
    matching_msgs = [m for m in received_messages if m.aggregate_id == sr.service_request_id]
    assert len(matching_msgs) == 1
    assert matching_msgs[0].payload["category"] == "FEE"

    # Verify event status is now PUBLISHED in database
    with in_memory_db.session() as session:
        event = session.scalar(
            select(OutboxEvent).where(OutboxEvent.aggregate_id == sr.service_request_id)
        )
        assert event is not None
        assert event.status == "PUBLISHED"
        assert event.published_at is not None
