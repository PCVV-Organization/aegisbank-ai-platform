# ADR-017: Transactional Outbox Pattern and Messaging Abstraction

## Status

Accepted for `v0.8`.

## Context

Publishing domain events (such as `ServiceRequestCreated`) directly to an external message bus inside a business transaction introduces the classic *dual-write problem*:
- If the database commits but the message bus fails or times out, the event is lost.
- If the message bus receives the event but the database transaction rolls back, phantom events are processed downstream.

Distributed two-phase commit (2PC / XA transactions) introduces severe performance bottlenecks and is unsupported across modern cloud messaging brokers like Azure Service Bus.

## Decision

1. **Transactional Outbox Pattern**:
   - The `ServiceRequestRepository.create()` method writes the `ServiceRequest` entity and an `OutboxEvent` record within the **same atomic database transaction**.
   - Outbox records start with `status = "PENDING"`.
2. **Asynchronous Outbox Processor**:
   - An independent worker (`OutboxProcessor`) reads pending events, publishes them to the decoupled `MessageBus`, and updates the status to `"PUBLISHED"`.
3. **Agnostic Message Bus Abstraction**:
   - The application depends on an abstract `MessageBus` / `EventPublisher` interface.
   - Milestone `v0.8` uses an in-process / SQLite `LocalMessageBus`.
   - Future cloud milestones (e.g. `v0.9` / `v0.11`) can substitute this with Azure Service Bus Topics/Subscriptions without changing business logic.

## Consequences

### Positive
- Guaranteed at-least-once event publication without distributed transactions.
- Zero dual-write inconsistencies or phantom events.
- Complete audit log of all emitted business events in the `outbox_events` table.

### Negative
- Consumers must be idempotent to handle potential at-least-once message deliveries.
