# Reliability Component

## Purpose

Owns idempotency, bounded retries, circuit breaking, timeouts, outbox, and messaging adapters. Review consumers and tests before changing it; do not create parallel reliability owners.

## Source navigation

- `__init__.py`
- `azure_servicebus_adapter.py`
- `circuit_breaker.py`
- `idempotency.py`
- `messaging.py`
- `retry.py`
- `timeout.py`
- [Start Here](../../../../../docs/START-HERE.md) and the [directory map](../../../../../docs/DIRECTORY-MAP.md).

## Before changing this component

Identify inputs, outputs, and consumers. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Writes must be idempotent before enabling retries; keep retries bounded to known transient failures. Update tests and documentation with interface changes.

## Limits

Local adapters and tests do not prove cloud broker availability, distributed guarantees, or production resilience. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
