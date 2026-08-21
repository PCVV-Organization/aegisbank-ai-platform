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

Pending (no ADR yet — flagged here to ensure they don't get lost):

- LSP choice for PowerShell (deferred; upstream distribution gone).
- Eval framework choice for v0.8 (promptfoo vs custom harness).
- Bicep module layout for v0.9.
- Secrets management in CI / Azure for v0.9 (OIDC vs federated).