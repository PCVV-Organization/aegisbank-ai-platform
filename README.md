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

**Current milestone:** `v0.3.0 - ML/NLP Intent Classification Baseline` (COMPLETE)

| Version | Milestone | Status |
| --- | --- | --- |
| `v0.1` | Project Charter + Local Tooling | COMPLETE |
| `v0.2` | Core Banking Mock | COMPLETE |
| `v0.3` | ML/NLP Intent Classification Baseline | COMPLETE |
| `v0.4` | RAG | NOT STARTED |
| `v0.5` | Agent + read-only tools | NOT STARTED |
| `v0.6` | MCP + HITL | NOT STARTED |
| `v0.7` | Reliability + Messaging | NOT STARTED |
| `v0.8` | Quality + Evaluations | NOT STARTED |
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

## Repository Structure

```text
aegisbank-ai-platform/
|-- README.md               # this document
|-- .gitignore
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

1. Open `v0.4 - RAG` only after explicit approval. Do not start a new milestone
   automatically.
2. Review the seven ADRs. None of them commits the project to a specific
   implementation outside its declared milestone.
3. Record any requested scope change before implementation begins.

No Docker, Azure, RAG, model, agent, MCP server of our own, HITL workflow,
messaging, retry policy, or circuit breaker has been implemented beyond
`v0.3`.

## Reference Baseline

The charter uses official sources as design references, not as claims of
certification or compliance. The source baseline was checked on 2026-08-20:

- [Microsoft AI-103 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103)
- [Microsoft AI-200 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200)
- [MCP tools specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Peru D.S. N.° 115-2025-PCM](https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
