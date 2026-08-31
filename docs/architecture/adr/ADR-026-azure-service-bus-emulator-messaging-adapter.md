# ADR-026: Azure Service Bus Emulator Messaging Adapter Behind Canonical MessageBus

- **Status:** Accepted
- **Context:**
  In v0.8, AegisBank established the canonical messaging contract `MessageBus` (`publish(topic, message)`) with in-memory `LocalMessageBus`. In v0.11, the platform introduces local enterprise messaging via the official Microsoft Azure Service Bus Emulator over AMQP (port `5672`).
- **Decision:**
  Implement `AzureServiceBusMessageBus` as a concrete adapter implementing `MessageBus` using the official `azure-servicebus` Python SDK. The adapter connects to the emulator queue `service-requests` and maps peek-lock, complete, abandon, and dead-letter settlement semantics without duplicating business rules, idempotency checks, retries, or circuit breakers.
- **Consequences:**
  - **Positive:** Enables AMQP-based enterprise asynchronous communication and settlement testing locally with zero cloud costs.
  - **Positive:** Reuses existing reliability and outbox components (`OutboxProcessor`, `IdempotentConsumer`, `DeadLetterQueue`) under the `DISCOVER BEFORE CREATE` rule.
  - **Negative:** Service Bus Emulator has documented limitations (no Azure AD, no geo-replication, no cloud SLAs).
- **Alternatives Rejected:**
  - Creating a second parallel domain message bus.
  - Using RabbitMQ or Kafka instead of Azure-aligned Service Bus technology.
  - Direct synchronous HTTP calls between Core Banking and event consumers.
