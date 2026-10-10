# Configuration Component

## Purpose

Owns application configuration and the secret boundary. Review consumers and their tests before changing this component; do not create a parallel configuration owner.

## Source navigation

- `__init__.py`
- `config.py`
- `secrets.py`
- [Start Here](../../../../../docs/START-HERE.md) explains the application workflow.
- [Directory map](../../../../../docs/DIRECTORY-MAP.md) describes repository areas.

## Before changing this component

Identify inputs, outputs, and consumers. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, and acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md). Run the relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Update tests and documentation in the same change when an interface changes.

## Limits

This guide describes repository responsibilities; it is not certification or evidence of live execution. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
