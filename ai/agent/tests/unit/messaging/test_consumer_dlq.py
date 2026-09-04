"""Tests for IdempotentConsumer deduplication and Dead-Letter Queue (DLQ) routing."""

from __future__ import annotations

import pytest

from aegisbank_agent.reliability.messaging import (
    DeadLetterQueue,
    IdempotentConsumer,
    Message,
)

pytestmark = pytest.mark.unit


def test_idempotent_consumer_executes_once_on_duplicate_deliveries() -> None:
    processed_count = 0

    def business_handler(msg: Message) -> None:
        nonlocal processed_count
        processed_count += 1

    consumer = IdempotentConsumer(business_handler)
    msg = Message(
        event_id="EVT-001",
        event_type="ServiceRequestCreated",
        aggregate_type="service_request",
        aggregate_id="SR-000001",
        payload={"category": "LOAN", "description": "Consulta"},
    )

    # 1st delivery
    ok1 = consumer.handle(msg)
    assert ok1 is True
    assert processed_count == 1
    assert len(consumer.processed_messages) == 1

    # 2nd delivery (duplicate event_id)
    ok2 = consumer.handle(msg)
    assert ok2 is True
    assert processed_count == 1  # Not executed again


def test_poison_message_routes_to_dlq_after_max_attempts() -> None:
    dlq = DeadLetterQueue()
    attempts_called = 0

    def failing_handler(msg: Message) -> None:
        nonlocal attempts_called
        attempts_called += 1
        raise ValueError("Payload con formato corrupto irrecuperable")

    consumer = IdempotentConsumer(
        handler=failing_handler,
        dlq=dlq,
        max_delivery_attempts=3,
    )

    poison_msg = Message(
        event_id="EVT-POISON-999",
        event_type="ServiceRequestCreated",
        aggregate_type="service_request",
        aggregate_id="SR-999999",
        payload={"corrupt": True},
    )

    # Attempt 1 -> re-raises
    with pytest.raises(ValueError):
        consumer.handle(poison_msg)
    assert dlq.size() == 0

    # Attempt 2 -> re-raises
    with pytest.raises(ValueError):
        consumer.handle(poison_msg)
    assert dlq.size() == 0

    # Attempt 3 (Max reached) -> caught and moved to DLQ, returns False
    ok3 = consumer.handle(poison_msg)
    assert ok3 is False
    assert dlq.size() == 1

    dead_letter = dlq.get("EVT-POISON-999")
    assert dead_letter is not None
    assert dead_letter.attempts == 3
    assert "Payload con formato corrupto" in dead_letter.failure_reason
    assert dead_letter.message.event_id == "EVT-POISON-999"
