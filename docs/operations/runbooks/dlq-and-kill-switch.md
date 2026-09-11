# DLQ and HOTL Kill-Switch Runbook

1. Engage `HOTLSupervisor` before investigating a suspected unsafe WRITE path.
2. Inspect DLQ event IDs, error classes, attempt counts, and payload digests.
3. Do not manually edit or replay a message with a changed payload.
4. Correct the cause, run focused reliability and ownership tests, and replay
   only through the canonical idempotent consumer.
5. Disengage the kill-switch only after an explicit operator decision and a
   clean quality gate.
