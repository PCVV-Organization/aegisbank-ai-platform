"""Local message bus, Outbox processor, Idempotent Consumer, and Dead-Letter Queue (DLQ)."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Callable

from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.repositories import OutboxRepository


@dataclass(frozen=True)
class Message:
    """Canonical domain event message representation."""

    event_id: str
    event_type: str
    aggregate_type: str
    aggregate_id: str
    payload: dict[str, Any]
    created_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


@dataclass
class DeadLetterRecord:
    """Record of a poison message routed to the Dead-Letter Queue."""

    message: Message
    failure_reason: str
    attempts: int
    failed_at: datetime = field(default_factory=lambda: datetime.now(timezone.utc))


class DeadLetterQueue:
    """Local Dead-Letter Queue storage for failed poison messages."""

    def __init__(self) -> None:
        self._records: dict[str, DeadLetterRecord] = {}

    def push(self, message: Message, failure_reason: str, attempts: int) -> DeadLetterRecord:
        record = DeadLetterRecord(
            message=message,
            failure_reason=failure_reason,
            attempts=attempts,
        )
        self._records[message.event_id] = record
        return record

    def list_records(self) -> list[DeadLetterRecord]:
        return list(self._records.values())

    def get(self, event_id: str) -> DeadLetterRecord | None:
        return self._records.get(event_id)

    def size(self) -> int:
        return len(self._records)


class LocalMessageBus:
    """In-process message broker supporting topic pub/sub subscriptions."""

    def __init__(self) -> None:
        self._subscribers: dict[str, list[Callable[[Message], None]]] = {}
        self._published_messages: list[Message] = []

    def subscribe(self, topic: str, handler: Callable[[Message], None]) -> None:
        if topic not in self._subscribers:
            self._subscribers[topic] = []
        self._subscribers[topic].append(handler)

    def publish(self, topic: str, message: Message) -> None:
        self._published_messages.append(message)
        handlers = self._subscribers.get(topic, [])
        for handler in handlers:
            handler(message)

    @property
    def published_history(self) -> list[Message]:
        return list(self._published_messages)


class OutboxProcessor:
    """Background processor that polls pending outbox events and publishes them to the bus."""

    def __init__(self, database: Database, message_bus: LocalMessageBus) -> None:
        self._database = database
        self._bus = message_bus

    def process_pending(self, limit: int = 50) -> int:
        """Fetch pending outbox events, publish to message bus, and mark as PUBLISHED."""
        processed_count = 0
        with self._database.session() as session:
            repo = OutboxRepository(session)
            pending_events = repo.list_pending(limit=limit)

            for event in pending_events:
                try:
                    payload_dict = (
                        json.loads(event.payload)
                        if isinstance(event.payload, str)
                        else event.payload
                    )
                except Exception:
                    payload_dict = {"raw": event.payload}

                msg = Message(
                    event_id=event.event_id,
                    event_type=event.event_type,
                    aggregate_type=event.aggregate_type,
                    aggregate_id=event.aggregate_id,
                    payload=payload_dict,
                    created_at=event.created_at,
                )

                # Publish to message bus topic (both specific and wildcard)
                self._bus.publish(event.event_type, msg)
                self._bus.publish(f"{event.aggregate_type}.events", msg)

                repo.mark_published(event.event_id)
                processed_count += 1

            session.commit()

        return processed_count


class IdempotentConsumer:
    """Consumer that guarantees at-most-once execution per event_id with Dead-Letter routing."""

    def __init__(
        self,
        handler: Callable[[Message], None],
        dlq: DeadLetterQueue | None = None,
        max_delivery_attempts: int = 3,
    ) -> None:
        self._handler = handler
        self._dlq = dlq or DeadLetterQueue()
        self._max_delivery_attempts = max_delivery_attempts
        self._processed_event_ids: set[str] = set()
        self._attempt_counters: dict[str, int] = {}
        self._successfully_processed_messages: list[Message] = []

    @property
    def dlq(self) -> DeadLetterQueue:
        return self._dlq

    @property
    def processed_messages(self) -> list[Message]:
        return list(self._successfully_processed_messages)

    def handle(self, message: Message) -> bool:
        """Handle incoming event idempotently.

        Returns:
            bool: True if executed or already processed, False if routed to DLQ.
        """
        # 1. Deduplication check
        if message.event_id in self._processed_event_ids:
            # Already processed -> acknowledge immediately without re-executing
            return True

        # 2. Attempt counter tracking
        current_attempts = self._attempt_counters.get(message.event_id, 0) + 1
        self._attempt_counters[message.event_id] = current_attempts

        # 3. Execution attempt
        try:
            self._handler(message)
            self._processed_event_ids.add(message.event_id)
            self._successfully_processed_messages.append(message)
            return True
        except Exception as exc:
            if current_attempts >= self._max_delivery_attempts:
                # Max attempts reached -> route to Dead-Letter Queue (DLQ)
                self._dlq.push(
                    message=message,
                    failure_reason=str(exc),
                    attempts=current_attempts,
                )
                return False
            # Still within attempt threshold -> re-raise for retry mechanism
            raise exc
