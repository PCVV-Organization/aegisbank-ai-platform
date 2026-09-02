# ADR-028: Local Serverless Event-Driven Foundation with Azure Functions Python v2 and CloudEvents 1.0

- **Status:** Accepted
- **Milestone:** `v0.13.0 — Azure Functions + Event Grid Local Serverless Foundation`
- **Context:**
  AegisBank already exposes an asynchronous, durable messaging contract through the canonical `MessageBus` (`v0.8`) and its Azure Service Bus Emulator adapter (`v0.11`). That path is a *brokered queue* optimised for command-style work, durable settlement, sessions, and dead-letter queues. The `ServiceRequestCreated` domain event published by the canonical Transactional Outbox is currently routed exclusively through that broker.

  Microsoft AI-200 (`Designing and Implementing a Microsoft Azure AI Solution`, study guide reviewed `2026-09-02`) explicitly requires understanding of **Azure Event Grid** ("Implement event-driven workflows by using Azure Event Grid, including filters, custom events, and retries") and **Azure Functions** ("Build serverless APIs, including implementing triggers and bindings"). CloudEvents `1.0` is the format officially recommended by Azure Event Grid.

  The `ServiceRequestCreated` domain event already meets the prerequisites for a push-based, fan-out, event-notification pattern: it is immutable, idempotent-by-construction (`event_id`), and emitted exactly once per database commit. Therefore, we add an *additional*, *non-replacing* serverless notification path while preserving the canonical outbox + broker for command-style work.
- **Decision:**
  1. Add `functions/aegisbank-events/` as a Python v2 Azure Functions project (`function_app.py`, `host.json`, `local.settings.example.json`, `requirements.txt`) executed locally with **Azure Functions Core Tools v4 (`func@4.14.0`)**.
  2. Use the Python v2 decorator model with `azure.functions.CloudEvent` as the trigger input (`@app.event_grid_trigger(arg_name="event")`) and a single function `service_request_created`. Azure Functions CLI v5 is preview-only and is *not* used.
  3. Map `ServiceRequestCreated` to the canonical CloudEvents `1.0` envelope at `contracts/cloudevents/service-request-created-v1.schema.json`:
     - `id` = `domain_event.event_id`
     - `source` = `urn:aegisbank:mock-core-banking`
     - `type` = `com.aegisbank.service-request.created.v1`
     - `subject` = `/service-requests/{aggregate_id}`
     - `dataschema` = `urn:aegisbank:contracts:service-request-created:v1`
     - `data` = the **minimal** projection of `payload` containing only `service_request_id`, `customer_id`, `category`, `status` (no `description`, no PII, no secrets).
     - Extension attributes: `correlationid` (mandatory), `traceparent` (optional W3C trace context).
  4. Reuse the existing canonical components instead of duplicating:
     - `IdempotencyGuard` (`ai/agent/src/aegisbank_agent/reliability/idempotency.py`) — keyed by `event-grid:{event_id}` for exactly-once delivery.
     - `AuditLogger` + `AuditEventType.{SERVICE_REQUEST_CREATED, IDEMPOTENCY_REPLAY, IDEMPOTENCY_CONFLICT}` — append-only regulatory trail.
     - `OperationalMetrics` — counters `event_grid_invocation_count`, `event_grid_processed_count`, `event_grid_duplicate_count`, `event_grid_rejected_count`, `request_count`, `request_error_count` plus latency histogram `event_grid_handler_latencies_ms`.
     - `StructuredLogger` — JSON logs with redaction filter.
     - `ObservabilityContext` — binds `correlation_id` / `session_id` / `customer_id` to the local span.
     - `get_tracer` — OpenTelemetry trace with the incoming `traceparent` (when present) used as the remote parent span.
  5. The handler is **stateless**: function instances hold no business state. Local idempotency uses an in-memory SQLite database configured via `AEGISBANK_FUNCTION_IDEMPOTENCY_DATABASE_URL` (defaults to `sqlite:///:memory:`). **No persistent state is added to Core Banking.**
  6. **Event Grid emulator status:** Microsoft does **not** publish a complete official local Event Grid emulator. Therefore, the handler is exercised through:
     - direct invocation of `handle_cloud_event()` in unit tests,
     - the registered `service_request_created` function binding in host acceptance tests,
     - `func start` + `POST http://localhost:7071/admin/functions/service_request_created` for manual smoke runs.
     Cloud Grid *service* emulation is `NO`; CloudEvents *handler* coverage is `COVERED`.
  7. **No Azurite is required** for the Event Grid trigger; the function does not use storage-backed triggers. Storage accounts are not added to `deploy/local/docker-compose.yml` for this milestone.
  8. The canonical messaging path (`LocalMessageBus` / `OutboxProcessor` / `AzureServiceBusMessageBus`) is **not replaced**. Event Grid is added as an additional consumer fan-out path. Service Bus continues to own command/work queues, durable messaging and DLQ semantics for the same event.
- **Consequences:**
  - **Positive:** Adds an Azure Functions + Event Grid foundation that maps directly to AI-200 learning objectives without duplicating reliability, audit, metrics, tracing or logging logic.
  - **Positive:** Preserves `DISCOVER BEFORE CREATE` — zero new true duplication (verified by `tests/serverless/` + existing canonical catalog).
  - **Positive:** CloudEvents strict envelope validation (`Draft202012Validator`) blocks malformed or non-canonical events at the boundary.
  - **Negative:** Local-only `func start` does not exercise Event Grid delivery; an external push (tunnel or in-cluster gateway) is needed for a true end-to-end exercise. This is documented as `EVENT_GRID_SERVICE_EMULATED = NO` and remains `CLOUD-PENDING`.
  - **Negative:** The CloudEvents extension attributes (`correlationid`, `traceparent`) are not part of the CloudEvents core spec; they are valid extension attributes per CNCF guidance but a strict CloudEvents-only consumer might ignore them. The handler treats them as mandatory business context, not as core CloudEvents semantics.
- **Alternatives Rejected:**
  - **Using Event Grid proprietary schema instead of CloudEvents 1.0.** Microsoft explicitly recommends CloudEvents `1.0` for new implementations; the proprietary schema is documented as "no major improvements will be made".
  - **Building a second `MessageBus` for CloudEvents.** Would duplicate reliability, dedupe, and observability components. Rejected under `DISCOVER BEFORE CREATE`.
  - **Hosting the Function App in Docker Compose with Azurite for storage-backed triggers.** Out of scope for `v0.13` and not required by the Event Grid trigger.
  - **Running the Function App with Azure Functions Core Tools v5.** v5 is preview-only and explicitly lacks Java/PowerShell support; not safe as the local baseline.
  - **Adopting the deprecated `function.json` (Python v1) programming model.** v1 is "legacy"; v2 is the recommended model for new Python apps.
