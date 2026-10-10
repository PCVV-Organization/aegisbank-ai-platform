# Evaluation Component

## Purpose

Owns utility, safety, and statistical-comparison evaluation. Review consumers and their tests before changing this component; do not create a parallel evaluation owner.

## Source navigation

- `__init__.py`
- `ab_testing.py`
- `evaluators.py`
- `red_team.py`
- `taxonomy.py`
- [Start Here](../../../../../docs/START-HERE.md) and the [directory map](../../../../../docs/DIRECTORY-MAP.md).

## Before changing this component

Identify inputs, outputs, and consumers. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Update tests and documentation with interface changes.

## Limits

Evaluation code and recorded scores do not establish model superiority or production readiness. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
