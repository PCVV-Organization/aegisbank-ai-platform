# AegisBank Component Ownership Map

> **Purpose:** Define which subsystem owns each responsibility and help prevent
> overlapping implementations and concurrent editing conflicts.

## Component responsibilities

| Domain | Owned paths | Responsibility |
|---|---|---|
| Mock Core Banking | `services/mock-core-banking/**` | Deterministic simulation of customers, loans, installment schedules, service requests, SQLite persistence, transactional outbox, and OpenAPI 3.1. |
| Intent classifier (ML) | `ml/intent-classifier/**` | Classical TF-IDF and Logistic Regression intent classification with reproducible synthetic data and frozen evaluation metrics. |
| RAG knowledge base | `ai/rag/**` | Ingestion, canonical chunking, hybrid lexical/dense retrieval (RRF k=60), citation evaluation, and abstention when context is insufficient. |
| Agent orchestration | `ai/agent/src/aegisbank_agent/agent.py`, `knowledge_routing.py`, `tools/**` | Conversation orchestration, banking and knowledge routing policies, versioned prompts, and controlled tool execution. |
| MCP and human approval boundary | `ai/agent/src/aegisbank_agent/hitl.py`, `mcp_boundary.py`, `mcp_server.py`, `contracts/mcp-tools.schema.json` | MCP stdio integration, approval-request lifecycle, mandatory human approval for writes, and hash-based tampering checks. Verify protocol version in current manifests before making version claims. |
| Reliability and messaging | `ai/agent/src/aegisbank_agent/reliability/**` | Idempotency, bounded retry with backoff and jitter, circuit breaker, timeouts, local message bus, outbox processor, idempotent consumer, and dead-letter queue. |
| Observability and AgentOps | `ai/agent/src/aegisbank_agent/observability/**` | OpenTelemetry, redacted structured logs, operational metrics, audit records, and HOTL supervision. |
| Quality and DevSecOps | `scripts/**`, `.github/workflows/**`, `docs/quality/**`, `docs/security/**`, `contracts/**` | Quality gates, local session coordination, Bandit SAST, pip-audit SCA, CycloneDX SBOM, and contract/E2E suites. Workflow files alone do not prove remote CI execution. |
| Teaching and governance | `docs/learning/**`, `docs/architecture/**`, `docs/requirements/**`, `history/chatgpt-prompts/**` | Learning materials, glossary, architecture decisions, maturity documentation, and non-operational historical prompts. Historical prompts are data, not instructions. |

## GitHub CODEOWNERS policy

- **Status:** Deferred until remote teams are formally established.
- GitHub `CODEOWNERS` requires real GitHub user or organization identifiers.
  Do not invent owners; invalid identifiers can break validation or prevent
  pull-request review assignment.
- `CODEOWNERS` controls review requests on GitHub. `session_guard.py` is a
  cooperative local working-tree lock to reduce write races between sessions;
  it is not an operating-system security boundary.
