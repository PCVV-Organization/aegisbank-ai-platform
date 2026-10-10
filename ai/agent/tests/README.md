# Agent Test Suite Guide

## Test layers

- `unit/` isolates individual component behavior.
- `integration/` exercises connected components in process.
- `contracts/` verifies tool, event, and persistence interfaces.
- `e2e/` exercises complete read and explicitly approved-write journeys.
- `infra/` contains opt-in tests requiring specific services or emulators.

`conftest.py` provides synthetic fixtures. Do not add overlapping suites without a clear gap, and never report `SKIP` as `PASS`.

## Navigation

- [Start Here](../../../docs/START-HERE.md)
- [Directory map](../../../docs/DIRECTORY-MAP.md)
- [Canonical components](../../../docs/architecture/CANONICAL-COMPONENTS.md)
- [Test strategy](../../../docs/quality/TEST-STRATEGY.md)

## Before changing tests

Identify the behavior and layer being tested. Use synthetic data, acquire SessionGuard as required by [AGENTS.md](../../../AGENTS.md), and run the narrow relevant suite before broader validation. When an interface changes, update tests and documentation together.

## Evidence limits

Test configuration is not execution evidence. Record the exact command, date, and result; consult the dated [local baseline record](../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md) for historical results and blockers.
