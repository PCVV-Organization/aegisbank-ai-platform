# Application Tool Registry and Implementations

## Purpose

Owns registration and execution of banking and knowledge tools. Tools expose bounded application capabilities; deterministic identity, ownership, validation, and policy checks—not the LLM—authorize operations.

## Source navigation

- `banking_tools.py`
- `base.py`
- `knowledge_tools.py`
- `registry.py`
- [Start Here](../../../../../docs/START-HERE.md)
- [Directory map](../../../../../docs/DIRECTORY-MAP.md)

## Before changing a tool

Identify inputs, outputs, callers, and side effects. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). State-changing operations require explicit human approval. Update tool contracts, tests, and documentation in the same change.

## Limits

Tool registration does not itself authorize execution or prove a live integration. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
