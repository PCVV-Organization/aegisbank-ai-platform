# ADR-019: OpenTelemetry as Vendor-Neutral Observability Standard

## Status

Accepted for `v0.9`.

## Context

AI agent systems require distributed tracing across complex call chains (user requests, model completions, tool calls, human approvals, database writes, outbox events, and consumer pipelines). Proprietary telemetry SDKs tie the architecture to specific cloud vendors (e.g., Azure Application Insights or AWS CloudWatch) prematurely.

In accordance with Microsoft AI-200 recommendations and permanent project rules (local first, vendor neutral), an open, portable telemetry abstraction is necessary.

## Decision

1. **OpenTelemetry SDK Adoption**:
   - Adopt the official CNCF OpenTelemetry Python standard (`opentelemetry-api` and `opentelemetry-sdk`).
   - Instrument hierarchical spans for all core agent activities (`agent.run`, `llm.chat`, `tool.execute`, `hitl.approval`, `outbox.publish`, `consumer.handle`).
2. **Local In-Memory / Development Exporter**:
   - Configure `InMemorySpanExporter` for local testing and inspection without cloud overhead or external network calls.
   - Future cloud milestones (`v0.11+`) can seamlessly reconfigure the exporter to Azure Monitor without altering agent business logic.
3. **Correlation & Trace ID Propagation**:
   - Maintain application-level `correlation_id` alongside OTel 128-bit `trace_id` across logs, spans, and audit records.

## Consequences

### Positive
- Zero cloud lock-in; vendor-neutral instrumentation.
- Complete span hierarchy and latency breakdown across every execution phase.
- Seamless forward compatibility with Azure Monitor and Prometheus.

### Negative
- Requires maintaining span context across asynchronous and multi-threaded boundaries.
