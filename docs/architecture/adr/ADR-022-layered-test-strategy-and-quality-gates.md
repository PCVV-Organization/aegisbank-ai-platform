# ADR-022: Layered Test Strategy and Deterministic Quality Gates

## Context

AegisBank AI Platform has evolved through multiple milestones introducing ML classification, RAG retrieval, native tool calling, MCP boundaries, HITL approval, reliability resilience (idempotency, retries, circuit breakers, DLQ), and OpenTelemetry observability. Without a formalized, layered test strategy and quality gate pipeline, regression risks and testing debt increase as new capabilities land.

## Decision

Adopt a formal Test Pyramid and deterministic Quality Gate pipeline:

1. **Unit Tests (Base):** Fast, isolated tests for pure functions, math, validation, and policy classification (e.g. `test_money.py`, `test_validation.py`, `test_dataset.py`).
2. **Integration Tests (Middle):** Verify package-level interactions with in-memory SQLite and local mocks without external cloud dependencies (e.g. `services/mock-core-banking/tests/integration`).
3. **Contract Tests (Boundary Protection):** Verify stable OpenAPI schemas, MCP tool definitions, and Outbox event JSON schemas to prevent breaking API changes.
4. **End-to-End (E2E) Journey Tests (Peak):** Validate complete user flows across the full stack (READ account, multi-step loan queries, RAG grounded responses, RAG abstentions, HITL WRITE approvals/rejections, HOTL kill-switch, and reliability fallbacks).
5. **Quality Gate Pipeline:** A unified deterministic entrypoint (`scripts/quality_gate.py`) running static linting, formatting, bytecode compilation, unit/integration/contract/E2E tests, SAST, SCA, and secret scanning in sequential order.

## Consequences

### Positive
- Prevents regression of fixed defects (such as the v0.9.2 tool routing gap).
- Ensures fast feedback during local development while strictly guarding release readiness.
- Aligns with Microsoft Well-Architected Framework testing guidance and Mibanco 2026 QA requirements.

### Negative / Trade-offs
- E2E tests require maintaining mocked components and realistic synthetic test fixtures.
- Pipeline execution time increases, requiring test execution parallelization or selective gating where appropriate.
