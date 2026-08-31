# ADR-023: Contract-First Compatibility Protection

- Status: Accepted
- Date: 2026-08-31

## Context

Independent changes to Core Banking, tool schemas and events can compile while breaking
the consumer that depends on their fields or methods.

## Decision

Keep deterministic contracts for Core Banking OpenAPI, the tool registry and the
`ServiceRequestCreated` boundary. Contract tests must fail on removed required fields,
unexpected WRITE tools or incompatible event payload changes.

## Consequences

Snapshots and explicit assertions are preferred over a heavy contract framework for this
local educational monolith. Versioning remains necessary before a distributed boundary.
