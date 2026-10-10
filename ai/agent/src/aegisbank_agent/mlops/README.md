# MLOps Component

## Purpose

Owns experiment tracking and drift detection. Review consumers and tests before changing it; do not create a parallel experiment or drift owner.

## Source navigation

- `__init__.py`
- `drift.py`
- `tracker.py`
- [Start Here](../../../../../docs/START-HERE.md)
- [Directory map](../../../../../docs/DIRECTORY-MAP.md)

## Before changing this component

Identify inputs, outputs, and consumers. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Update tests and documentation with interface changes.

## Limits

Local experiment tracking or drift checks do not prove cloud monitoring or production model quality. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
