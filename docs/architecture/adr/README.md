# Architecture Decision Records

This directory captures durable decisions for the AegisBank AI Platform.
Each ADR is immutable once accepted; superseded decisions are linked from
the new ADR.

Index:

- [ADR-001](./ADR-001-modular-monolith-first.md) — Modular monolith first
  (v0.2 architectural shape).
- [ADR-002](./ADR-002-local-sqlite-before-postgresql.md) — Local SQLite
  before PostgreSQL (v0.2 datastore choice).
- [ADR-003](./ADR-003-agent-sdk-pydantic-ai.md) — Agent SDK choice for v0.5
  (pydantic-ai).
- [ADR-004](./ADR-004-vector-store-chromadb-in-process.md) — Vector store
  integration strategy for v0.4 (chromadb in-process).
- [ADR-005](./ADR-005-deferred-tooling-evaluation.md) — Evaluation of
  deferred local-tooling items (docker LSP, PowerShell LSP, context7, custom
  Aegis skills, codebase-memory, pydantic-ai, chromadb).
- [ADR-006](./ADR-006-classical-ml-intent-baseline.md) — Classical ML intent
  baseline for v0.3 (TF-IDF plus Logistic Regression).
- [ADR-007](./ADR-007-group-aware-synthetic-evaluation.md) — Group-aware
  synthetic evaluation for v0.3 (`template_group_id`).
- [ADR-008](./ADR-008-local-retrieval-before-azure-ai-search.md) — Local
  retrieval foundation before any Azure AI Search deployment (v0.4).
- [ADR-009](./ADR-009-hybrid-retrieval-with-rrf.md) — Hybrid retrieval via
  Reciprocal Rank Fusion for v0.4 (`k = 60` frozen).
- [ADR-010](./ADR-010-provider-agnostic-llm-boundary.md) — Provider-neutral
  LLM request boundary for grounded generation (v0.5).
- [ADR-011](./ADR-011-grounded-generation-citation-validation.md) — Grounded
  generation with active-context and citation validation (v0.5).
- [ADR-012](./ADR-012-single-agent-orchestrator-read-only-tools.md) — Single
  agent orchestrator with read-only function tools (v0.6).
- [ADR-013](./ADR-013-deterministic-tool-authorization-boundary.md) — Deterministic
  tool authorization and ownership boundary (v0.6).
- [ADR-014](./ADR-014-local-mcp-boundary-stdio.md) — Local Model Context
  Protocol (MCP) boundary using stdio transport (v0.7).
- [ADR-015](./ADR-015-mandatory-hitl-for-banking-writes.md) — Mandatory
  Human-in-the-Loop (HITL) authorization for banking writes (v0.7).
- [ADR-016](./ADR-016-idempotent-banking-writes-before-retries.md) — Idempotent
  banking writes before retries (v0.8).
- [ADR-017](./ADR-017-transactional-outbox-and-messaging-abstraction.md) — Transactional
  Outbox pattern and messaging abstraction (v0.8).
- [ADR-018](./ADR-018-circuit-breaker-policy-for-external-dependencies.md) — Circuit
  breaker policy for external dependencies (v0.8).

Scope note: ADR-003 remains an accepted historical decision, but the current
`v0.5 - Grounded Generation & LLM Evaluation` authorization explicitly
excludes Agent, MCP, HITL, and tools. Its implementation is therefore deferred
and is not part of this milestone.

Pending (no ADR yet — flagged here to ensure they don't get lost):

- LSP choice for PowerShell (deferred; upstream distribution gone).
- Eval framework choice for v0.8 (promptfoo vs custom harness).
- Bicep module layout for v0.9.
- Secrets management in CI / Azure for v0.9 (OIDC vs federated).
