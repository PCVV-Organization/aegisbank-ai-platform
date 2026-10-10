# Event Grid vs. Service Bus in AegisBank (v0.13 Design)

> **Historical milestone context:** `v0.13.0 — Azure Functions + Event Grid Local Serverless Foundation`.
> **Purpose:** Describe the intended separation between Azure Event Grid (serverless event push) and Azure Service Bus (durable brokered messaging). The design uses both; neither replaces the other.
> **Source recency:** The comparison was recorded as reviewed against Microsoft Learn on 2026-09-02. Service capabilities and limits can change; revalidate against current Microsoft documentation before making architecture or deployment decisions.
> **Execution status:** This design does not prove cloud deployment. Check the maturity matrix and current evidence.

## 1. Recorded Service Comparison

| Dimension | Azure Event Grid | Azure Service Bus |
|---|---|---|
| Architectural pattern | Event notification / HTTP push | Brokered queue or topic/subscription |
| Transport | HTTP + CloudEvents 1.0 (recommended in the recorded design) or legacy Event Grid schema | AMQP 1.0 + HTTP |
| Delivery semantics | At-least-once; no ordering guarantee in the recorded comparison | At-least-once; FIFO with sessions; native duplicate detection |
| Consumption | Push to HTTPS webhook | Pull or push with settlement (`complete`, `abandon`, `dead-letter`) |
| Persistence | No persistent queue; retry with exponential backoff until TTL/DLQ | Broker persists messages until completed or expired |
| Retention (recorded) | 1–30 retries, 1–1440 minute TTL; Blob Storage DLQ | Message TTL and broker-integrated DLQ |
| Filtering | Event types, subject prefix/suffix, advanced numeric/string/boolean filters | SQL filters on `application_properties`; correlation filters |
| Typical use | Reactive notifications, fan-out, SaaS integration | Durable commands, workflow coordination, settlement |
| Azure availability | Recorded as GA for Basic/Standard | Recorded as GA for Basic/Standard/Premium |

Revalidate all product limits, tiers, and availability before implementation.

## 2. Intended AegisBank Placement

```text
HITL APPROVED
    ↓
create_service_request
    ↓
SQL transaction: service request + transactional outbox
    ├── OutboxProcessor → LocalMessageBus / Azure Service Bus → durable idempotent consumer + DLQ
    └── CloudEvents mapper → HTTPS Event Grid publish → Azure Function → idempotent audit handler
```

| Responsibility | Intended owner |
|---|---|
| Durable transactional commands (HITL approvals, settlement, command queues) | Service Bus |
| Broker dead-letter queue for poisoned messages | Service Bus DLQ |
| Reactive `ServiceRequestCreated` notification to a serverless function | Event Grid |
| Fire-and-forget projection/audit notifications | Event Grid |
| Managed at-least-once retries for HTTP event delivery | Event Grid (verify current limits) |
| Strict FIFO ordering and sessions | Service Bus |
| High fan-out to multiple filtered subscribers | Event Grid topic |

## 3. Selection Guide

| Requirement | Prefer |
|---|---|
| Strict ordering per `aggregate_id` | Service Bus sessions |
| Handler-controlled settlement (`complete` / `abandon` / `dead-letter`) | Service Bus |
| Native HTTPS push without coupling to a broker SDK | Event Grid |
| Multiple subscriptions with independent filters | Event Grid topic |
| Cloud-managed delivery retry | Event Grid |
| SaaS/system-topic integration (for example, `Microsoft.Storage.BlobCreated`) | Event Grid |
| Durable message storage for days | Service Bus |
| Broker-integrated dead-letter semantics | Service Bus |
| Messages larger than the recorded 1 MB Event Grid limit | Service Bus; verify current limits |

## 4. Recorded AegisBank Maturity

| Capability | Recorded local status | Cloud status |
|---|---|---|
| Service Bus Emulator (AMQP) | `LAB-COVERED` (v0.11) | `CLOUD-PENDING` |
| `AzureServiceBusMessageBus` adapter | `LAB-COVERED` (v0.11) | Same adapter with Entra token is intended |
| Event Grid service emulation | `EVENT_GRID_SERVICE_EMULATED = NO` | No official emulator was recorded; service runtime is cloud-hosted |
| Local Event Grid handler (Azure Functions v2) | `EVENT_GRID_HANDLER_LOCAL = COVERED` (v0.13) | Function App deployment is not evidenced here |
| CloudEvents 1.0 envelope | `LAB-COVERED` (v0.13; strict schema) | Same envelope intended in cloud |

These are historical status statements, not fresh test results.

## 5. Why Service Bus Is Not Replaced

1. Service Bus supports sessions/FIFO, native duplicate detection, and manual settlement; Event Grid does not provide the same ordering/settlement contract.
2. Service Bus has a broker-integrated DLQ; the recorded Event Grid design uses Blob Storage and requires additional processing.
3. Service Bus supports sessions and transactions; the recorded Event Grid model is at-least-once without broker settlement.
4. `ServiceRequestCreated` has two intended consumers: reactive fan-out through Event Grid and durable command processing through Service Bus.

## 6. Recorded Design Decision

The design retains both transports and treats the transactional outbox as the publication source. An `OutboxProcessor` routes events by `event_type`:

- **Event Grid** → Azure Function for a thin, idempotent, auditable reactive handler.
- **Service Bus** → existing durable consumers, with no intended replacement.

Do not add parallel handlers, buses, outboxes, audit loggers, or metrics frameworks without reviewing [canonical components](CANONICAL-COMPONENTS.md) and documenting a justified architecture change. Verify this design against the current source before implementation.
