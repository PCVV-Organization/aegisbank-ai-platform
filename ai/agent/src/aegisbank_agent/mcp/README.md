# Application MCP Adapter

## Purpose

Adapts the application to the Model Context Protocol (MCP). Review consumers and tests before changing it; do not create a parallel MCP boundary.

## Source navigation

- `__init__.py`
- `server.py`
- [Start Here](../../../../../docs/START-HERE.md)
- [Directory map](../../../../../docs/DIRECTORY-MAP.md)

## Before changing this component

Identify inputs, outputs, and consumers. Review [canonical components](../../../../../docs/architecture/CANONICAL-COMPONENTS.md), use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../../../AGENTS.md), and run relevant checks from the [test strategy](../../../../../docs/quality/TEST-STRATEGY.md). Update tests and documentation with interface changes.

## Limits

This adapter is an application integration, not proof of a production MCP deployment or security certification. See the dated [local baseline record](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical evidence and blockers.
