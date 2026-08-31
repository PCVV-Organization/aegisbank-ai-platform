# ADR-015: Mandatory Human-in-the-Loop (HITL) Authorization for Banking Writes

## Status

Accepted for `v0.7`.

## Context

Autonomous AI agents must not execute state-changing or financial operations without human oversight. Even low-risk operations (such as filing a customer service request or claim) can trigger workflow changes, operational costs, or state mutations. Relying on model self-restraint or prompt instructions alone is insufficient against prompt injection, hallucination, or tool parameter manipulation.

In alignment with Microsoft AI-103 governance guidelines and the permanent project rules of AegisBank, all write operations require explicit human authorization before execution on the underlying transactional system.

## Decision

1. **State Machine (`ApprovalRequest`)**:
   - Every proposal by the LLM to invoke a write tool (`create_service_request`) creates an immutable `ApprovalRequest` record with status `PENDING`.
   - The approval state lifecycle enforces the transitions:
     `PENDING` -> `APPROVED` -> `EXECUTED`, or `PENDING` -> `REJECTED`.

2. **Explicit User Interaction**:
   - The CLI/UI displays the exact normalized tool name, category, description, and authenticated customer ID.
   - Requires explicit affirmative confirmation (`Approve? [y/N]`).
   - Default choice is `DENY`.

3. **Integrity and Anti-Tampering Safeguards**:
   - The approval is cryptographically bound to the canonical JSON serialization of the proposed arguments (`argument_hash`).
   - If arguments change post-approval, the request is immediately transitioned to `REJECTED` and execution is blocked.
   - Once an approval reaches `EXECUTED`, replay attempts are strictly rejected.
   - An approval created for customer $A$ cannot be authorized or executed by customer $B$.

4. **Zero Auto-Approval / Language Inference**:
   - Approval cannot be inferred from the model's text generation.
   - The Core Banking write endpoint (`POST /api/v1/service-requests`) is only invoked when `ApprovalRequest.status == APPROVED`.

## Consequences

### Positive
- Guarantees 100% human oversight for all state-changing actions.
- Immune to prompt injection or model hallucination attempting unauthorized database writes.
- Complete audit trail with timestamps, reviewer identity, and execution results.

### Negative
- Synchronous human oversight pauses automated multi-turn execution until user review is provided.
