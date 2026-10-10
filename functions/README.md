# Functions

Event-driven functions handle asynchronous work outside the interactive request path. Event processing does not replace deterministic authorization or required human approval (HITL).

## Components

- [AegisBank Events](aegisbank-events/README.md) — CloudEvents-triggered local/laboratory processing

## Change guidance

Treat event schemas and delivery behavior as contracts. Update producer and consumer tests when changing envelopes or handling. Use synthetic data only, and verify current implementation and status against the project [README](../README.md) and [canonical components](../docs/architecture/CANONICAL-COMPONENTS.md).
