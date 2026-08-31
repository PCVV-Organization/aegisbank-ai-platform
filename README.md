# AegisBank AI Platform

> Educational and portfolio laboratory designed to demonstrate secure agentic
> banking AI with Python, Microsoft Foundry, RAG, MCP, human oversight, resilient
> cloud architecture, MLOps, and Azure.

## What It Is

AegisBank AI Platform is an educational and portfolio laboratory for designing,
building, evaluating, securing, and operating a fictitious banking AI platform.
Its future assistant, **Aegis**, will answer questions from authorized knowledge,
read synthetic customer information through controlled tools, and propose a
low-risk write action that requires explicit human approval.

The project is deliberately small in business scope and rigorous in engineering
scope. It exists to demonstrate grounded generation, deterministic authorization,
human oversight, reliability, auditability, testing, and observability without
pretending to reproduce a complete bank.

## What It Is Not

- It is not a bank, a core banking product, or production financial software.
- It is not affiliated with Mibanco, Microsoft, the SBS, or any financial institution.
- It does not use real customers, identifiers, accounts, cards, credentials, or transactions.
- It does not make real credit decisions or execute transfers, payments, or disbursements.
- It does not claim legal, regulatory, security, or NIST certification or compliance.

All project data must be synthetic and reproducible.

## Current Status

**Current milestone:** `v0.8.0 — Reliability + Messaging Foundation` (`COMPLETE`)

| Version | Milestone | Status |
| --- | --- | --- |
| `v0.1` | Project Charter + Local Tooling | COMPLETE |
| `v0.2` | Core Banking Mock | COMPLETE |
| `v0.3` | ML/NLP Intent Classification Baseline | COMPLETE |
| `v0.4` | RAG Retrieval & Evaluation Foundation | COMPLETE |
| `v0.5` | Grounded Generation & LLM Evaluation | COMPLETE |
| `v0.6` | Single Agent + Read-Only Function Tools | COMPLETE |
| `v0.7` | MCP + HITL | COMPLETE |
| `v0.8` | Reliability + Messaging Foundation | COMPLETE |
| `v0.9` | Azure Deployment | NOT STARTED |
| `v1.0` | Enterprise Hardening | NOT STARTED |
| `v1.1` | AKS experiment | Optional after `v1.0` |
| `v1.2` | Multi-agent experiment | Optional after `v1.0` |

## What `v0.3` Includes

- Deterministic synthetic Spanish banking intent dataset (500 records, 25
  template groups per class, group-aware train/holdout split, SHA-256
  fingerprint).
- TF-IDF plus Logistic Regression baseline (`ml/intent-classifier/`).
- Stratified-group cross-validation with zero group leakage across folds.
- Trivial `DummyClassifier` floor for comparison.
- Reproducible CLI (`generate`, `validate`, `evaluate`, `predict`) and a
  frozen holdout evaluation report (`reports/baseline-metrics.json`,
  `reports/baseline-report.md`).
- 17 unit tests covering dataset invariants, pipeline configuration,
  cross-validation behaviour, and reproducibility (97 deterministic
  metrics checks).
- Two architecture decision records: `ADR-006` (classical ML baseline) and
  `ADR-007` (group-aware synthetic evaluation).

## What `v0.4` Includes

- Synthetic Spanish banking corpus with versioned metadata
  (`document_id`, `version`, `effective_from`, `effective_to`, `status`,
  `source`) under `ai/rag/data/corpus/`.
- Deterministic chunking into `chk__{document_id}__{version}__c{idx}_{digest}`
  chunk IDs (`ai/rag/src/aegisbank_rag/chunking.py`).
- Three retrievers behind a common `Retriever` interface:
  `LexicalRetriever` (TF-IDF), `DenseLocalRetriever` (TF-IDF + TruncatedSVD
  LSA, **not** equivalent to Azure AI Search embeddings), and
  `HybridRRFRetriever` (Reciprocal Rank Fusion with frozen `k = 60`).
- Synthetic query set plus qrels covering direct, paraphrase, version, and
  out-of-domain categories (`ai/rag/data/queries.jsonl`,
  `ai/rag/data/qrels.json`).
- Offline evaluation that computes Precision@5, Recall@5, MRR@5, and
  nDCG@5 for every method and persists the report to
  `ai/rag/reports/retrieval-report.md` and the metrics to
  `ai/rag/reports/retrieval-metrics.json`.
- CLI with `index`, `search`, and `evaluate` subcommands.
- 36 unit tests covering corpus invariants, chunking, lexical and dense
  retrievers, RRF fusion, metrics, evaluation, citation metadata, and
  reproducibility.
- Two architecture decision records: `ADR-008` (local retrieval before
  Azure AI Search) and `ADR-009` (hybrid retrieval with RRF).

## What `v0.5` Includes

- Provider-neutral `LLMProvider` and strict structured-answer contract under
  `ai/rag/src/aegisbank_rag/`.
- Deterministic active-only context construction preserving document, version,
  chunk, and source provenance.
- Central prompt `rag-answer-v001`, citation allow-list validation, no-context
  abstention, and untrusted-context instruction defenses.
- Separate prompt-development and held-out generation-evaluation datasets,
  including direct, multi-chunk, version, insufficient, out-of-domain, and
  suspicious-context cases.
- Deterministic generation metric harness and contract tests.
- Foundry Local `0.10.3` baseline using `phi-4-mini` and six held-out cases;
  metrics are recorded under `ai/rag/reports/` without production thresholds.
- Two architecture decision records: `ADR-010` (provider-neutral LLM boundary)
  and `ADR-011` (grounded generation citation validation).

## What `v0.6` Includes

- Single-agent orchestrator (`ai/agent/`) with multi-turn loop and round limits.
- Strict read-only tool allowlist: `search_knowledge`, `get_my_loans`,
  `get_loan_details`, `get_next_installment`.
- Deterministic customer ownership validation preventing cross-customer access.
- Canonical agent system prompt `agent-system-v001`.
- Complete test coverage across schemas, registry, tools, ownership, and evaluation.
- Foundry Local `0.10.3` live local baseline recorded in `ai/agent/reports/`.
- Two architecture decision records: `ADR-012` (single-agent read-only first)
  and `ADR-013` (deterministic tool authorization boundary).

## What `v0.7` Includes

- Local Model Context Protocol (MCP) server boundary (`ai/agent/src/aegisbank_agent/mcp/`)
  using the official Python `mcp>=2.1.1` SDK over `stdio` transport (Protocol `2026-07-28`).
- Informative tool annotations metadata (`readOnlyHint=True` for read tools;
  `readOnlyHint=False`, `destructiveHint=False` for write tool).
- Single, low-risk state-changing WRITE operation: `create_service_request`.
- Mandatory Human-in-the-Loop (HITL) approval state machine (`ApprovalRequest`
  with states `PENDING`, `APPROVED`, `REJECTED`, `EXECUTED`).
- Cryptographic argument hash binding and tampering detection post-approval.
- Replay prevention for executed approvals and customer boundary isolation.
- Interactive CLI human oversight prompt with default `DENY` behavior.
- Complete acceptance test suite with 10 explicit security and workflow invariants.
- Two architecture decision records: `ADR-014` (local MCP boundary using stdio)
  and `ADR-015` (mandatory HITL for banking writes).

## What `v0.8` Includes

- Deterministic Idempotency Guard (`IdempotencyGuard` + `idempotency_records` table)
  with SHA-256 argument canonicalization, cached result playback, and conflict detection.
- Bounded Exponential Backoff Retry Policy (`RetryPolicy`) with full jitter,
  strictly scoped to transient recoverable errors (zero retries on validation, auth,
  HITL rejects, and idempotency conflicts).
- 3-State Finite State Machine Circuit Breaker (`CircuitBreaker` with `CLOSED`, `OPEN`,
  `HALF_OPEN`) to prevent cascading dependency failure.
- Strict bounded execution timeouts (`with_timeout`).
- Transactional Outbox Pattern (`OutboxRepository` + `outbox_events` table) persisting
  the `ServiceRequestCreated` domain event within the same atomic database transaction.
- Agnostic Message Bus Abstraction (`LocalMessageBus` and `OutboxProcessor`).
- Idempotent Event Consumer (`IdempotentConsumer`) with Dead-Letter Queue (`DeadLetterQueue`)
  routing for persistently failing poison messages.
- Deterministic 9-scenario failure injection test suite and full E2E acceptance tests.
- Three architecture decision records: `ADR-016` (idempotent writes before retries),
  `ADR-017` (transactional outbox + messaging abstraction), and `ADR-018` (circuit breaker policy).

## Project Rules

- Local first: local execution, then Docker, CI, and only then Azure.
- Synthetic data only; real personal or financial data is prohibited.
- One agent and a modular monolith until evidence justifies more complexity.
- The LLM may interpret and propose, but it never authorizes an operation.
- Every state-changing operation requires HITL approval in `v1.0`.
- Unsupported answers must abstain rather than fabricate evidence.
- No paid Azure resource may be created without explicit authorization.
- A technology enters the project only when it resolves a requirement, reduces
  a risk, or demonstrates a defined competency.

## Charter

The approved product boundary is defined by these documents:

- [Vision](docs/charter/01-vision.md)
- [Scope](docs/charter/02-scope.md)
- [Use cases](docs/charter/03-use-cases.md)
- [Non-goals](docs/charter/04-non-goals.md)
- [Success criteria](docs/charter/05-success-criteria.md)

## Architecture Decisions

- [ADR-001](docs/architecture/adr/ADR-001-modular-monolith-first.md) — Modular monolith first.
- [ADR-002](docs/architecture/adr/ADR-002-local-sqlite-before-postgresql.md) — Local SQLite before PostgreSQL.
- [ADR-003](docs/architecture/adr/ADR-003-agent-sdk-pydantic-ai.md) — Agent SDK choice (v0.5): pydantic-ai.
- [ADR-004](docs/architecture/adr/ADR-004-vector-store-chromadb-in-process.md) — Vector store choice (v0.4): chromadb in-process.
- [ADR-005](docs/architecture/adr/ADR-005-deferred-tooling-evaluation.md) — Deferred tooling evaluation.
- [ADR-006](docs/architecture/adr/ADR-006-classical-ml-intent-baseline.md) — Classical ML baseline for v0.3 (TF-IDF + Logistic Regression).
- [ADR-007](docs/architecture/adr/ADR-007-group-aware-synthetic-evaluation.md) — Group-aware synthetic evaluation for v0.3 (`template_group_id`).
- [ADR-008](docs/architecture/adr/ADR-008-local-retrieval-before-azure-ai-search.md) — Local retrieval foundation before Azure AI Search (v0.4).
- [ADR-009](docs/architecture/adr/ADR-009-hybrid-retrieval-with-rrf.md) — Hybrid retrieval with Reciprocal Rank Fusion (`k=60`) for v0.4.
- [ADR-010](docs/architecture/adr/ADR-010-provider-agnostic-llm-boundary.md) — Provider-agnostic LLM boundary for v0.5.
- [ADR-011](docs/architecture/adr/ADR-011-grounded-generation-citation-validation.md) — Grounded generation with citation validation for v0.5.
- [ADR-012](docs/architecture/adr/ADR-012-single-agent-orchestrator-read-only-tools.md) — Single-agent orchestrator with read-only tools for v0.6.
- [ADR-013](docs/architecture/adr/ADR-013-deterministic-tool-authorization-boundary.md) — Deterministic tool authorization and ownership boundary for v0.6.
- [ADR-014](docs/architecture/adr/ADR-014-local-mcp-boundary-stdio.md) — Local MCP boundary using stdio transport for v0.7.
- [ADR-015](docs/architecture/adr/ADR-015-mandatory-hitl-for-banking-writes.md) — Mandatory HITL for banking writes for v0.7.

## Repository Structure

```text
aegisbank-ai-platform/
|-- README.md               # this document
|-- .gitignore
|-- ai/
|   |-- agent/              # v0.6/v0.7 agent orchestrator, MCP server & HITL
|   `-- rag/                # v0.4 retrieval & v0.5 generation baseline
|-- contracts/              # JSON Schema files
|-- docs/
|   |-- charter/            # v0.1 charter (5 docs)
|   |-- architecture/adr/   # Architecture Decision Records
|   |-- chatgpt-prompts/    # Milestone bootstrap prompts
|   |-- experiments/        # Reproducible experiment reports
|   `-- research/           # Library / pattern research notes
|-- ml/
|   `-- intent-classifier/  # v0.3 ML baseline (Python package)
`-- services/
    `-- mock-core-banking/  # v0.2 Core Banking Mock (FastAPI)
```

OpenCode runtime configuration (MCP servers, LSP servers, agent/permission
boundaries, slash commands, retrieval policy, intelligence layer) is managed
by the OpenCode AI-ENV wrapper at the parent directory level. The project
itself remains a pure code-and-documentation repository.

## How To Continue

1. Start `v0.8 - Quality + Evaluations` only after explicit approval. Do not
   start a new milestone automatically.
2. Review the fifteen ADRs. None of them commits the project to a specific
   implementation outside its declared milestone.
3. Record any requested scope change before implementation begins.
4. Use the [role-profile learning map](docs/career/role-profile-images-and-gap-analysis.md)
   to study terminology, evidence, and remaining gaps against Microsoft AI-103
   and AI-200. It transcribes the supplied role-profile images without claiming
   certification or production readiness.

No Docker, Azure, complex multi-agent flows, or paid cloud services have been
implemented.

## Reference Baseline

The charter uses official sources as design references, not as claims of
certification or compliance. The source baseline was checked on 2026-08-30:

- [Microsoft AI-103 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103)
- [Microsoft AI-200 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200)
- [MCP tools specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Peru D.S. N.° 115-2025-PCM](https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
