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

**Current milestone:** `v0.1.0 - Project Charter`

The repository currently contains governance and scope documentation only. No
banking API, model, RAG pipeline, agent, MCP server, cloud resource, or deployable
application has been implemented.

| Version | Milestone | Status |
| --- | --- | --- |
| `v0.1` | Project Charter | Charter ready; review pending |
| `v0.2` | Core Banking Mock | Planned; requires approval |
| `v0.3` | ML/NLP Baseline | Planned |
| `v0.4` | RAG | Planned |
| `v0.5` | Agent and read-only tools | Planned |
| `v0.6` | MCP and HITL | Planned |
| `v0.7` | Reliability and Messaging | Planned |
| `v0.8` | Quality and Evaluations | Planned |
| `v0.9` | Azure Deployment | Planned |
| `v1.0` | Enterprise Hardening | Planned |
| `v1.1` | AKS experiment | Optional after `v1.0` |
| `v1.2` | Multi-agent experiment | Optional after `v1.0` |

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
- [Repository operating rules](AGENTS.md)

## Initial Structure

```text
aegisbank-ai-platform/
|-- README.md
|-- AGENTS.md
|-- .gitignore
|-- docs/
|   `-- charter/
|       |-- 01-vision.md
|       |-- 02-scope.md
|       |-- 03-use-cases.md
|       |-- 04-non-goals.md
|       `-- 05-success-criteria.md
|-- .intelligence/        # Pre-existing project knowledge scaffold
|-- .opencode/            # Pre-existing local OpenCode support files
|-- contracts/            # Pre-existing OpenCode support schemas
`-- opencode.json          # Pre-existing OpenCode bootstrap config
```

## How To Continue

1. Read and review the five charter documents.
2. Record any requested scope change before implementation begins.
3. Start `v0.2 - Core Banking Mock` only after explicit approval.
4. Implement and validate only that milestone; do not advance automatically.

There are no application dependencies or runtime commands in `v0.1.0`.

## Reference Baseline

The charter uses official sources as design references, not as claims of
certification or compliance. The source baseline was checked on 2026-08-20:

- [Microsoft AI-103 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103)
- [Microsoft AI-200 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200)
- [MCP tools specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Peru D.S. N.° 115-2025-PCM](https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
