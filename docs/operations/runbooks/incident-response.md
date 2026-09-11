# Incident Response Runbook

1. Record the correlation ID, trace ID, timestamp, component, and minimized
   error summary. Do not copy secrets or unrestricted customer payloads.
2. Check health, OTel spans, structured logs, operational metrics, and audit
   events in that order.
3. If a WRITE path is suspect, engage the canonical `HOTLSupervisor` kill-switch.
4. If messaging is suspect, stop the consumer, inspect the outbox and DLQ, and
   preserve event IDs for idempotent replay.
5. Classify the event as `BLOCKED`, `RECOVERED`, or `CLOUD-PENDING`; do not call
   it production impact without production evidence.
6. Run the relevant focused test and the quality gate before releasing the
   kill-switch.
