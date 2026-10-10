# Observability Component

## Purpose

Owns traces, metrics, audit events, and human-on-the-loop (HOTL) supervision. Review consumers and tests before changing it; do not create parallel telemetry, audit, or supervision owners.

## Source navigation

- `__init__.py`, `agentops.py`, `audit.py`, `context.py`, `hotl.py`
- `logging.py`, `metrics.py`, `telemetry.py`, `tracer.py`
- [Start Here](../../../../../docs/START-HERE.md)
- [Directory map](../../../../../docs/DIRECTORY-MAP.md)

## Before changing this component

Identify inputs, outputs, and consumers. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Minimize and redact sensitive information in telemetry. Update tests and documentation with interface changes.

## Limits

Local telemetry does not prove a cloud exporter, complete audit durability, or certification. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
