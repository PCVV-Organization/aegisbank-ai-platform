# ADR-023: Contract-First Compatibility and Tool Schema Protection

## Context

In banking and enterprise AI architectures, services and agents communicate across strict interfaces: REST APIs, Model Context Protocol (MCP) tool registrations, and transactional event streams. If an API path changes, a required parameter is omitted, or an unauthorized WRITE tool is accidentally exposed, catastrophic runtime failures or unauthorized mutations can occur.

## Decision

Enforce Contract-First verification across three key interfaces:

1. **Core Banking OpenAPI Contract:** OpenAPI 3.1 schema validation verifying that all public endpoints, path parameters, and response models (`LoanResponse`, `InstallmentResponse`, `ServiceRequestResponse`) remain backwards-compatible and strictly enforce that `/api/v1/service-requests` is the only exposed WRITE route.
2. **MCP Tool Registry Contract:** Validate all exposed MCP tool definitions, descriptions, input JSON schemas, and read-only vs write annotations, failing automatically if unauthorized tools or mutation capabilities are registered.
3. **Transactional Outbox Event Contract:** Validate domain event payloads (e.g. `ServiceRequestCreated`) against versioned JSON Schema specifications (`contracts/service-request-created.schema.json`).

## Consequences

### Positive
- Detects API and tool breakage before runtime deployment.
- Prevents accidental exposure of state-changing operations without explicit HITL approval mechanisms.
- Supports independent evolution of backend services and agent orchestrators.

### Negative / Trade-offs
- Schema files in `contracts/` must be versioned and updated intentionally when APIs evolve.
