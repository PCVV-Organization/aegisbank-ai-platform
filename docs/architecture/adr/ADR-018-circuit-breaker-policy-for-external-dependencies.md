# ADR-018: Circuit Breaker Policy for External Dependencies

## Status

Accepted for `v0.8`.

## Context

When an upstream or downstream service encounters a persistent outage or severe degradation, continued client requests and automated retry loops exhaust connection pools, consume compute resources, and exacerbate the downstream failure.

A distinct fault tolerance mechanism is required to fast-fail traffic and allow degraded services time to recover.

## Decision

1. **Dedicated Circuit Breaker Finite State Machine**:
   - Implement an explicit 3-state `CircuitBreaker` (`CLOSED`, `OPEN`, `HALF_OPEN`).
   - `failure_threshold`: Tripping after $N$ consecutive failures (default: 3).
   - `recovery_timeout`: Cooldown period before entering `HALF_OPEN` (default: 2.0s).
   - `success_threshold`: Probes required in `HALF_OPEN` before restoring `CLOSED` (default: 1).
2. **Decoupled from Retry Logic**:
   - `RetryPolicy` handles short, transient micro-failures on individual operations.
   - `CircuitBreaker` monitors systemic service health across operations.
   - When `OPEN`, the circuit breaker fast-fails immediately with `CircuitBreakerOpenError` without placing load on the failing dependency.

## Consequences

### Positive
- Prevents cascading failures and protects thread/connection resources.
- Provides immediate deterministic error feedback during outages.
- Self-healing via automatic recovery probes in `HALF_OPEN` state.

### Negative
- Requires careful tuning of failure thresholds and cooldown windows to avoid false-positive tripping during transient load spikes.
