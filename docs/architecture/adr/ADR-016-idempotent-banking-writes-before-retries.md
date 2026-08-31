# ADR-016: Idempotent Banking Writes Before Retries

## Status

Accepted for `v0.8`.

## Context

Autonomous agents, clients, and middleware operating over distributed networks inevitably encounter network timeouts, connection drops, and service delays. If a write operation (such as creating a customer service request) is retried without idempotency guarantees, partial network failures (where the server received and committed the request, but the response was lost) will result in duplicate database records.

In accordance with core banking architectural principles and Microsoft AI-200 resiliency patterns, writes must be protected by deterministic idempotency before any automated retry mechanism is enabled.

## Decision

1. **Idempotency Key Specification**:
   - The banking write operation (`create_service_request`) accepts an optional `Idempotency-Key` string.
   - When provided, the `IdempotencyGuard` verifies the key in persistent storage (`idempotency_records` table).
2. **Canonical Argument Hashing**:
   - The SHA-256 hash of the canonical JSON representation of normalized arguments is computed and stored.
   - If a request arrives with an existing key and identical hash: the cached response is immediately returned (`cached=True`) without re-executing database mutations.
   - If a request arrives with an existing key but differing arguments or customer ID: an `IdempotencyConflictError` is raised immediately.
3. **Prerequisite for Retries**:
   - No automated retry policy shall be executed against write operations unless guarded by an idempotency key.

## Consequences

### Positive
- Zero duplicate service requests created across network disconnects, browser refreshes, or retry loops.
- Deterministic response playback.
- Safe integration with downstream automated retry policies.

### Negative
- Requires maintaining an idempotency persistence table and indexing overhead.
