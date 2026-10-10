# Architecture Integrity and Code-Duplication Report

> **Historical milestone:** v0.10.1 — Architecture Integrity + Cross-Session Coordination.
> **Recorded tool:** Pylint 4.0.8 (`R0801` / `duplicate-code`).
> **Recorded scores:** 9.98/10; zero findings classified as true business-logic duplication.
>
> This is a dated analysis snapshot, not a current scan. The scores and line references must not be reported as current without rerunning the checks.

## 1. Recorded Pylint R0801 Findings

| ID | Modules | Lines in recorded scan | Detected similarity | Classification | Recorded decision |
|---|---|---:|---|---|---|
| `DUP-001` | `aegisbank_rag.generation_evaluation` vs. `aegisbank_rag.retriever` | 139–150 / 67–78 | Mapping/instantiation of `RetrievalHit` dataclass fields. | `INTENTIONAL_SCHEMA_SIMILARITY` | Keep: separate generation-evaluation and live-retrieval domains map to the same canonical contract. |
| `DUP-002` | `aegisbank_rag.dense_local` vs. `aegisbank_rag.lexical` | 61–70 / 42–51 | Sort by `cosine_similarity` and filter chunks with score > 0.0. | `INTENTIONAL_SCHEMA_SIMILARITY` | Keep: independent lexical and dense engines; abstraction was judged to add unnecessary coupling. |
| `DUP-003` | `aegisbank_intent_classifier.constants` vs. `aegisbank_rag.lexical` | 45–55 / 13–24 | `TfidfVectorizer` hyperparameter dictionary (`ngram_range`, `min_df`, `norm`). | `INTENTIONAL_SCHEMA_SIMILARITY` | Keep: classifier and RAG packages use separate contracts; the classifier's synthetic v0.3 dataset contract was recorded as frozen. |
| `DUP-004` | `aegisbank_rag.evaluation` vs. `aegisbank_rag.generation_evaluation` | 225–235 / 383–393 | Markdown report header rendering. | `TEST_FIXTURE_SIMILARITY` | Keep separate formatting for retrieval evaluation and generated-answer evaluation. |
| `DUP-005` | `aegisbank_rag.evaluation` vs. `aegisbank_rag.generation_evaluation` | 218–224 / 376–382 | Indented JSON serialization of evaluation metrics. | `TEST_FIXTURE_SIMILARITY` | Keep standard artifact writing local; a shared helper was judged to reduce cohesion. |
| `DUP-006` | `aegisbank_rag.context` vs. `aegisbank_rag.generation_evaluation` | 14–19 / 78–83 | Dataclass fields (`document_id`, `version`, `chunk_id`, `source`, `status`). | `INTENTIONAL_SCHEMA_SIMILARITY` | Keep canonical citation-context attributes. |

## 2. Recorded Architecture-Drift Review

| Responsibility | Canonical implementation | Recorded decision | Recorded evidence |
|---|---|---|---|
| Agent orchestration | `AgentOrchestrator` (`ai/agent/src/aegisbank_agent/agent.py`) | `REUSE`; keep one source of truth. | No parallel orchestrator found in that scan. |
| Tool registry | `ToolRegistry` (`ai/agent/src/aegisbank_agent/tools/registry.py`) | `REUSE`; central registry. | Exports OpenAI and MCP schemas without ad hoc dictionaries. |
| Routing policy | `requires_account_data` / `requires_banking_read` | `REUSE`; retain deterministic rules. | Separated from stochastic inference in the recorded review. |
| HITL | `HITLApprovalManager` (`ai/agent/src/aegisbank_agent/hitl.py`) | `REUSE`; one manager. | No `HumanApprovalService` duplicate was found in that scan. |
| MCP boundary | `AegisBank Local MCP` (`ai/agent/src/aegisbank_agent/mcp_boundary.py`) | `REUSE`; retain stdio transport. | Report recorded `mcp==2.1.1`, protocol `2026-07-28`. |
| Reliability | `RetryPolicy`, `CircuitBreaker`, `IdempotencyGuard` | `REUSE`; keep the `reliability` module. | Reported as reused by Core Banking and tool calls. |
| Messaging/outbox/DLQ | `LocalMessageBus`, `OutboxProcessor`, `IdempotentConsumer` | `REUSE`; retain decoupled abstraction. | No direct connections outside the broker abstraction were reported. |
| Observability/audit | `StructuredLogger`, `AuditLogger`, `TracerProvider`, `HOTLSupervisor` | `REUSE`; keep the `observability` module. | Central redaction and WORM logging were reported. |

## 3. Recorded Conclusion

- True duplications: **0**.
- Intentional schema similarities: **4**.
- Test-fixture similarities: **2**.
- Refactors required by that scan: **0**.

These findings describe the v0.10.1 scan only. Inspect current source and rerun the relevant static analysis before using them to justify present-day architecture decisions.
