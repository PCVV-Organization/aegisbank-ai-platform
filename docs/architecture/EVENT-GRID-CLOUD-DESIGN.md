# Declarative Azure Event Grid Cloud Design (AegisBank)

> **Status:** Design only. This document does not provision or deploy Azure infrastructure. All cloud capabilities below remain unvalidated unless supported by separate, dated execution evidence.

## 1. Azure Event Distribution Topology

```mermaid
graph TD
    Publisher[Mock Core Banking / Outbox Publisher] -->|CloudEvents 1.0 HTTPS POST| Topic[Event Grid Custom Topic:<br/>aegisbank-domain-events]

    subgraph Event Subscriptions and Advanced Filters
        Topic -->|Filter: type=*.created.v1 and subject=service-requests/*| Sub1[Subscription: sub-audit-compliance]
        Topic -->|Filter: type=*.created.v1 and amount > 10000| Sub2[Subscription: sub-high-value-analytics]
    end

    Sub1 -->|Push Delivery / Event Grid Trigger| FunctionApp1[Azure Function: ServiceRequestEventHandler]
    Sub2 -->|Push Delivery / Event Grid Trigger| FunctionApp2[Azure Function: HighValueRiskAnalyzer]

    Sub1 -.->|Max retries exceeded (24h) / HTTP 500| DLQ[Dead-letter container:<br/>eventgrid-deadletter/sub-audit]
```

## 2. Declarative Cloud Resource Design

### 2.1. Event Grid custom topic

- **Name:** `aegisbank-domain-events-topic`
- **Location:** `eastus2` or a secondary region
- **Input schema:** `CloudEventSchemaV1_0`
- **Network isolation:** Private Endpoint in the AegisBank VNet

### 2.2. Canonical subscription: `sub-audit-compliance`

- **Endpoint:** Azure Function `service_request_event_handler`
- **Advanced filters:**
  - Event type: `includedEventTypes = ["com.aegisbank.service-request.created.v1"]`
  - Subject prefix: `subjectBeginsWith = "service-requests/"`
  - Data filter: `NumberIn` or `StringContains` on `data` attributes

### 2.3. Retry policy

- **Maximum delivery attempts:** 30
- **Event time-to-live:** 1440 minutes (24 hours)
- **Retry algorithm:** Exponential backoff managed by Event Grid

### 2.4. Dead-letter destination

- **Storage:** Azure Storage Account (Blob container)
- **Container:** `eventgrid-deadletter/sub-audit-compliance/`
- **Purpose:** Retain events that fail permanently after the retry or TTL limit for forensic review and manual reprocessing.

## 3. Recorded Capability Status

- Declarative subscription and filter design: `EVENTGRID-CLOUD-PENDING`.
- Azure Storage dead-letter destination: `EVENTGRID-DEADLETTER-CLOUD-PENDING`.
- Cloud service retry policies: `EVENTGRID-SERVICE-RETRY-CLOUD-PENDING`.
- Local Azure Functions handler: `LOCAL-FUNCTIONS-COVERED` (recorded claim; verify current test evidence).
