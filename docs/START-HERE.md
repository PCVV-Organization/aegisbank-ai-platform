# Start Here: AegisBank for New Readers

## 1. What this project is

AegisBank is an educational banking laboratory built with synthetic data. It
demonstrates an assistant that can look up simulated loans and documents, and
propose service requests that require human approval. It is not a real bank and
does not make real credit decisions.

The workspace has two Git repositories: **ai-env prepares the developer**;
**aegisbank-ai-platform contains the application**. Open the outer repository
for developer-tool configuration and instructions. Work in this repository for
banking rules, tests, and contracts. Each repository has its own history and
remote configuration.

## 2. One request from start to finish

1. A person submits a request in the context of a synthetic customer.
2. The agent determines whether the request needs banking data, knowledge, or clarification.
3. For banking data, authorized tools enforce ownership and deterministic rules.
4. For knowledge, the system retrieves documents. Retrieved documents are untrusted evidence, not instructions.
5. The model proposes text or a tool call; deterministic policy decides what is allowed.
6. A write requires explicit human approval and safety checks. Traces, audit records, and idempotency protect the operation from duplicate effects.

For example, “Show my loans” should use tools authorized for the current
session. A document that says “look up another customer's account” grants no
permission.

## 3. Reading path

| Goal | Read first | Then |
|---|---|---|
| Understand the purpose | [README](../README.md) | [Glossary](learning/GLOSSARY.md) |
| Find a directory | [Directory map](DIRECTORY-MAP.md) | Component README |
| Change agent behavior | [Agent](../ai/agent/README.md) | [Canonical component catalog](architecture/CANONICAL-COMPONENTS.md) |
| Change banking persistence or API | [Mock Core Banking](../services/mock-core-banking/README.md) | `api`, `domain`, `schemas`, `persistence` |
| Change retrieval | [RAG](../ai/rag/README.md) | Corpus, retrievers, and citation tests |
| Evaluate models | [Evaluation](evaluation/README.md) | Catalog, dataset, and specific runner |
| Work as an LLM | [README.LLM](../README.LLM.md) | [llms.txt](../llms.txt) and only the relevant sources |
| Review local baseline status | [Project README](../README.md) | Verify current Git state and fresh evidence |

## 4. Check navigation without running the application

From the application Git root (the directory containing `ai/`, `services/`,
and `scripts/`):

```powershell
git rev-parse --show-toplevel
git status --short
python -B scripts/documentation_index.py --check
```

Reading documentation requires Git and the Python standard library for the
navigation check. It does not require credentials, Docker, Azure, or a model.
To run application code, prepare Python 3.14 and the virtual environment as
described in each component README. Do not assume globally installed packages
are available in the project's `.venv`.

## 5. Before implementing a change

Read [AGENTS.md](../AGENTS.md), define the authorized scope, identify component
owners, and acquire SessionGuard. Choose tests using the
[test strategy](quality/TEST-STRATEGY.md). Record the command, date, and actual
result. A skipped test is not a pass. Historical findings such as the 75
Pyright errors and partial R2 status were recorded on 2026-09-21; this guide
does not claim that they are fixed or current.
