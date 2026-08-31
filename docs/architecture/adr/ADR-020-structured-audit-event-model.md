# ADR-020: Structured Audit Event Model for Regulatory Non-Repudiation

## Status

Accepted for `v0.9`.

## Context

Operational logs (stdout/JSON logs) are optimized for developer debugging and SRE troubleshooting, and are subject to log rotation, sampling, and retention policies. In contrast, regulated banking AI systems require an immutable, append-oriented audit trail that proves non-repudiation, captures human approvals, and records exact cryptographic argument hashes.

## Decision

1. **Dedicated Append-Only Audit Trail**:
   - Implement `AuditLogger` and structured `AuditEvent` schema distinct from operational logging.
   - Capture key milestone events (`AGENT_RUN_STARTED`, `TOOL_PROPOSED`, `HITL_REQUESTED`, `HITL_APPROVED`, `HITL_REJECTED`, `HITL_EXECUTED`, `SERVICE_REQUEST_CREATED`, `HOTL_KILL_SWITCH_ENGAGED`).
2. **Mandatory Redaction**:
   - Apply automatic redaction filters to prevent raw API keys, passwords, bearer tokens, or sensitive raw customer inputs from entering the audit store.
3. **Correlation Binding**:
   - Every audit record binds `correlation_id`, `trace_id`, `timestamp`, `actor` (`USER`, `AGENT`, `SUPERVISOR`, `SYSTEM`), and structured payload.

## Consequences

### Positive
- Strict chronological, tamper-evident audit history of all state changes and AI proposals.
- Compliance readiness for banking oversight without exposing raw credentials.
- Clear separation between developer logs and compliance records.

### Negative
- Adds storage overhead for capturing security events alongside operational logs.
