# AegisBank AI Platform

An educational and portfolio laboratory for building safer banking AI with
Python and synthetic data. Aegis can retrieve documentation and query simulated
banking data, then propose service requests for explicit human approval. The
LLM interprets and proposes; deterministic identity, authorization, and
business rules decide what may execute.

**Understand it in five minutes:** read the [project brief](docs/PROJECT-BRIEF.md),
then [one request from start to finish](docs/START-HERE.md).
**Working with an LLM:** start with [README.LLM.md](README.LLM.md) and retrieve
only the guide and source relevant to the task.

## What you can explore

- Read a synthetic customer's loans, balances, or next installment through
  tools restricted to that customer's session.
- Ask document questions and receive retrieved citations or an abstention when
  available evidence cannot support an answer.
- Propose a service request, reject or approve it explicitly, and inspect
  idempotency, audit records, and event delivery.
- Study local model inference, RAG, security controls, and evaluation separately.

The classical intent classifier in `ml/` is an independent experiment; the
agent's semantic routing uses bounded LLM tool proposals and deterministic policy.

## Project status

**Status reviewed: 2026-10-11.** The application is published at
[PCVV-Organization/aegisbank-ai-platform](https://github.com/PCVV-Organization/aegisbank-ai-platform)
on `master`. The latest recorded local FAST quality gate passed **13/13 on
2026-10-10**; the associated corrections are in
[commit a7e4506](https://github.com/PCVV-Organization/aegisbank-ai-platform/commit/a7e4506bbecb462f0af6ad39af75723cba2de2a3).
This is dated local evidence, not cloud acceptance or a fresh full-infrastructure run.

The earlier **v1.0.8 local baseline (2026-09-22)** records broader synthetic
tests, Docker reproducibility, and human rejection/approval journeys. Consult
the [maturity matrix](docs/requirements/V1.0-MATURITY-MATRIX.md) and the owning
dated reports for their scope, skips, and historical blockers.

| Area | Evidence boundary |
|---|---|
| Local application | Recorded FAST gate passed; infrastructure and live-model journeys have separate checks. |
| GitHub Actions | Workflows are configured; successful remote runs must be verified in Actions. |
| Azure staging | Deployment contracts and adapters exist; cloud execution and acceptance remain pending. |
| Production | Unproven; this remains a synthetic educational laboratory. |

## Start here

This application has its own Git repository. The outer `ai-env` repository
contains development tooling and instructions. See
[repository boundaries](docs/engineering/REPOSITORY-BOUNDARIES.md).

| Need | Entry point |
|---|---|
| Compact project overview | [Project brief](docs/PROJECT-BRIEF.md) |
| LLM and agent context | [README.LLM.md](README.LLM.md), [AGENTS.md](AGENTS.md) |
| Concise navigation | [llms.txt](llms.txt) |
| Machine-readable file inventory | [project-index.json](project-index.json) |
| Documentation portal | [docs/README.md](docs/README.md) |
| Architecture and ownership | [Canonical components](docs/architecture/CANONICAL-COMPONENTS.md), [E2E flow](docs/architecture/E2E-FINAL-ARCHITECTURE.md) |
| Portfolio demonstration | [Portfolio evidence](docs/releases/PORTFOLIO-INTERVIEW-EVIDENCE.md) |
| Quality and evidence limits | [Test strategy](docs/quality/TEST-STRATEGY.md), [evaluation](docs/evaluation/README.md) |
| Contribute or organize documentation | [CONTRIBUTING.md](CONTRIBUTING.md), [documentation standard](docs/engineering/DOCUMENTATION-STANDARD.md) |

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

For example, “When is my next installment?” lets the model propose a bounded
read tool; that tool still checks the customer's ownership. “Create a service
request” requires a separate human approval before the transaction can commit.
The [onboarding walkthrough](docs/START-HERE.md) explains each boundary.

## Local development

Run commands from this directory, which contains `ai/`, `services/`, and
`scripts/`. If you opened the outer workspace, first enter
`aegisbank-ai-platform/`.

For a fresh clone with Python 3.14, start the synthetic banking API:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e "services/mock-core-banking[dev]"
.venv\Scripts\python.exe -m uvicorn mock_core_banking.main:app `
  --app-dir services/mock-core-banking/src --host 127.0.0.1 --port 8001
```

Open [the local API explorer](http://127.0.0.1:8001/docs) after startup. This
path uses local SQLite and synthetic seed data. For the model-backed assistant,
continue with the [agent guide](ai/agent/README.md) and
[Foundry Local configuration](docs/operations/LOCAL-ENVIRONMENT-CONFIGURATION.md).
See the [Core Banking guide](services/mock-core-banking/README.md) for API tests
and configuration.

1. Read the [development instructions](AGENTS.md) and check Git status.
2. Follow the relevant component README. Dependencies are declared in its
   `pyproject.toml`.
   The application components require Python 3.14. Use the component's documented
   environment and run command. Configure local variables using the
   [environment guide](docs/operations/LOCAL-ENVIRONMENT-CONFIGURATION.md).
3. To check documentation navigation only, use Python:

```powershell
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
git diff --check
```

For static type validation, use the [Pyright guide](docs/quality/PYRIGHT-VALIDATION.md)
with the tooling available in your environment. For application changes, consult the test
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

The root `README.md` is the canonical GitHub landing page. GitHub automation is
documented in [.github/CI-GUIDE.md](.github/CI-GUIDE.md) so it does not shadow
this introduction. Maintained guides are in English and follow the
[documentation standard](docs/engineering/DOCUMENTATION-STANDARD.md).
