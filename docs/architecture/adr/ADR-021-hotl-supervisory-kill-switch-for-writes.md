# ADR-021: Human-on-the-Loop (HOTL) Supervisory Kill-Switch for Writes

## Status

Accepted for `v0.9`.

## Context

While Human-in-the-Loop (HITL) provides microscopic, synchronous approval for individual transactions, enterprise operations require macroscopic, asynchronous control. If operational metrics detect an abnormal spike in error rates, LLM hallucination clusters, or persistent dependency failures, human operators must possess a global mechanism to immediately suspend all write tools without taking down the entire platform or redeploying code.

## Decision

1. **HOTL Supervisory Controller (`HOTLSupervisor`)**:
   - Introduce an asynchronous supervision layer with `is_write_allowed` gate.
   - Operators can engage the kill-switch (`engage_kill_switch(reason)`) or disengage it (`disengage_kill_switch()`).
2. **Deterministic Fast-Fail**:
   - When the kill-switch is engaged, any write tool proposed by the agent is immediately blocked with `TOOL_DENIED` status before reaching the user prompt or Core Banking.
   - Read-only tools (knowledge search, loan balance inquiries) continue to function normally.
3. **Audit and Alert Notification**:
   - All kill-switch state transitions emit `HOTL_KILL_SWITCH_ENGAGED` / `HOTL_KILL_SWITCH_DISENGAGED` audit events.

## Consequences

### Positive
- Instant operational risk mitigation during platform degradation or security anomalies.
- Clear architectural separation between synchronous HITL (transaction approval) and asynchronous HOTL (system capacity control).
- Safe default behavior.

### Negative
- Requires operational monitoring procedures to prevent inadvertent lockouts.
