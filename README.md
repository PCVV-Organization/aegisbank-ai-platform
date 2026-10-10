# AegisBank AI Platform

An educational and portfolio laboratory for building safer banking AI with
Python and synthetic data. Aegis can retrieve documentation and query simulated
banking data, then propose service requests for explicit human approval. The
LLM interprets and proposes; deterministic identity, authorization, and
business rules decide what may execute.

## Project status

**Documented local baseline: v1.0.8 (2026-09-22).** The recorded evidence reports
FAST gate 13/13; 488 tests passed and none skipped; Pyright reported zero errors
and warnings across Agent, RAG, ML, and Core Banking. Isolated Docker
reproducibility and interactive user journeys for both rejecting and approving
a service request were recorded. These are dated local results, not fresh
validation of the current checkout.

Known limits: remote CI is `CI-CONFIGURED / RUNNER-PENDING`; Azure and other
cloud execution are `CLOUD-PENDING`; production is `PROD-UNPROVEN`. The manual
composite query documented in the evidence was a single prefetched read, not a
true multi-step journey. The `v1.0.7` tag remains an earlier historical
milestone.

## Start here

This application has its own Git repository. The outer `ai-env` repository
contains development tooling and instructions. See
[repository boundaries](docs/engineering/REPOSITORY-BOUNDARIES.md).

| Need | Entry point |
|---|---|
| LLM and agent context | [README.LLM.md](README.LLM.md), [AGENTS.md](AGENTS.md) |
| Concise navigation | [llms.txt](llms.txt) |
| Machine-readable file inventory | [project-index.json](project-index.json) |
| Documentation portal | [docs/README.md](docs/README.md) |
| Architecture and ownership | [Canonical components](docs/architecture/CANONICAL-COMPONENTS.md), [E2E flow](docs/architecture/E2E-FINAL-ARCHITECTURE.md) |
| Portfolio demonstration | [Portfolio evidence](docs/releases/PORTFOLIO-INTERVIEW-EVIDENCE.md) |
| Quality and evidence limits | [Test strategy](docs/quality/TEST-STRATEGY.md), [evaluation](docs/evaluation/README.md) |

## Components

| Path | Responsibility |
|---|---|
| [services/mock-core-banking](services/mock-core-banking/README.md) | FastAPI mock, synthetic data, loans, installments, service requests, and persistence. |
| [ml/intent-classifier](ml/intent-classifier/README.md) | Independent classical ML experiment for intent classification. |
| [ai/rag](ai/rag/README.md) | Document retrieval and grounded generation; pgvector and Redis adapters. |
| [ai/agent](ai/agent/README.md) | One application agent, tools, sessions, MCP, human approval, and safety controls. |
| [functions/aegisbank-events](functions/aegisbank-events/) | Event processing with Azure Functions. |
| [contracts](contracts/) | JSON Schema contracts for integration boundaries. |
| [deploy](deploy/) | Local container configuration and Kubernetes manifests; their presence does not prove deployment. |
| [scripts](scripts/README.md) | Quality checks, evaluations, session coordination, and documentation maintenance. |

RAG means Retrieval-Augmented Generation: retrieve evidence before generating
an answer. MCP (Model Context Protocol) connects tools to the agent. HITL
(Human-in-the-Loop) requires human approval for state changes. See the
[glossary](docs/learning/GLOSSARY.md).

## Main flow

```text
Query -> deterministic identity and policy -> knowledge or tools
      -> grounded answer or abstention -> traces and audit

Proposed write -> explicit human approval -> safety controls
               -> idempotent operation + transaction + outbox
               -> event processing or dead-letter queue
```

The documented baseline includes customer ownership protections, persistent
session state, and controls against making account claims without using
authorized tools. Design documents and local test evidence have different
scopes; see the [capability maturity matrix](docs/requirements/V1.0-MATURITY-MATRIX.md).

## Local development

Run commands from this directory, which contains `ai/`, `services/`, and
`scripts/`. If you opened the outer workspace, first enter
`aegisbank-ai-platform/`.

1. Read the [development instructions](AGENTS.md) and check Git status.
2. Follow the relevant component README. Dependencies are declared in its
   `pyproject.toml`.
3. To check documentation navigation only, use Python:

```powershell
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
git diff --check
```

For the canonical static contract across the four application roots, run:

```powershell
node ..\.agents\node_modules\.pnpm\pyright@1.1.413\node_modules\pyright\index.js `
  --pythonpath .venv\Scripts\python.exe --outputjson
```

See the [Pyright guide](docs/quality/PYRIGHT-VALIDATION.md) for scope,
environment, and limitations. For application changes, consult the test
strategy and `python scripts/quality_gate.py --help`. Some checks require the
application environment and can write reports; read their documented effects
before running them. A documented command is not evidence that it has run.

## Permanent boundaries

- Use synthetic, reproducible data only.
- Keep one application agent in a modular monolith.
- Require explicit human approval and deterministic authorization for writes.
- Do not add real payments, transfers, or credit decisions.
- Azure and paid resources require explicit approval.
- Do not claim certification, compliance, or production readiness.

## Documentation maintenance

Use [documentation maintenance](docs/engineering/DOCUMENTATION-MAINTENANCE.md)
to regenerate indexes and distinguish current guidance from historical
evidence. The [documentation reorganization record](history/quality/DOCUMENTATION-REORGANIZATION-20260915.md)
describes that specific historical change.

For onboarding, read [Start Here](docs/START-HERE.md), then consult the
[directory map](docs/DIRECTORY-MAP.md) or the curated [expanded LLM context](llms-full.txt).
The indexes are generated; do not copy the entire repository into a prompt.
When paths, interfaces, or evidence change, update the owning guide and
regenerate its derived navigation.
