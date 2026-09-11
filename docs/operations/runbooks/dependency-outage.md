# Dependency Outage Runbook

1. Confirm the dependency failure with timeout and circuit-breaker telemetry.
2. Allow only bounded retries for known transient failures.
3. Keep the circuit open for persistent failures and return a safe response or
   RAG abstention; never fabricate banking data.
4. For messaging, leave the transactional outbox pending and route poisoned
   messages to the DLQ.
5. Recover the dependency, verify health, replay only idempotent events, and
   document the observed recovery evidence.
