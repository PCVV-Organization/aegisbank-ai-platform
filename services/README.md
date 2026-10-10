# Services

Application services contain bounded runtime responsibilities. `mock-core-banking` is a synthetic local service; it is not a real banking system. The LLM is hosted and orchestrated elsewhere.

## Components

- [Mock Core Banking](mock-core-banking/README.md) — local HTTP API and synthetic banking records

## Change guidance

Before changing a service, identify its inputs, outputs, consumers, and tests. Check [canonical components](../docs/architecture/CANONICAL-COMPONENTS.md), follow the application [AGENTS.md](../AGENTS.md) and SessionGuard workflow, and use synthetic data only. Update interface documentation and tests with contract changes.

## Evidence boundary

This directory describes repository responsibilities, not certification or live execution. Check the [project README](../README.md) and [maturity matrix](../docs/requirements/V1.0-MATURITY-MATRIX.md) for recorded status.
