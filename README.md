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

**Current milestone:** `v0.1.0 - Project Charter + Local Tooling`

`v0.1` covers the project charter plus the local OpenCode tooling required to
develop the project incrementally. No AI functionality has been implemented.

| Version | Milestone | Status |
| --- | --- | --- |
| `v0.1` | Project Charter + Local Tooling | COMPLETE |
| `v0.2` | Core Banking Mock | PROPOSED — code in working tree, awaiting explicit approval before commit |
| `v0.3` | ML/NLP Baseline | NOT STARTED |
| `v0.4` | RAG | NOT STARTED |
| `v0.5` | Agent and read-only tools | NOT STARTED |
| `v0.6` | MCP and HITL | NOT STARTED |
| `v0.7` | Reliability and Messaging | NOT STARTED |
| `v0.8` | Quality and Evaluations | NOT STARTED |
| `v0.9` | Azure Deployment | NOT STARTED |
| `v1.0` | Enterprise Hardening | NOT STARTED |
| `v1.1` | AKS experiment | Optional after `v1.0` |
| `v1.2` | Multi-agent experiment | Optional after `v1.0` |

## What `v0.1` Includes

- Five charter documents defining the product boundary (`docs/charter/`).
- `AGENTS.md` repository operating rules and milestone workflow.
- Bootstrap-manifest and contract schemas (`contracts/`).
- Knowledge scaffold (`docs/architecture/adr/`, `docs/research/`).
- OpenCode-native local tooling wired in `opencode.json`:
  - 4 MCP servers (`sequential-thinking`, `filesystem`, `git`, `everything`).
  - 1 declared LSP (`pyright`, local install); Red Hat `yaml-ls` auto-installs.
  - Retrieval policy adopted via `.ai-env/retrieval-policy.json`.

A working `services/mock-core-banking/` directory exists in the working tree
from an earlier autonomous session and is **not yet committed**. It claims to
include 82 passing tests, ruff-clean, valid OpenAPI 0.2.0. Review and an
explicit approval are required before any `v0.2` commit. Until then,
`v0.2` is **PROPOSED**, not COMPLETE.

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

## Architecture Decisions

- [ADR-001](docs/architecture/adr/ADR-001-modular-monolith-first.md) — Modular monolith first.
- [ADR-002](docs/architecture/adr/ADR-002-local-sqlite-before-postgresql.md) — Local SQLite before PostgreSQL.
- [ADR-003](docs/architecture/adr/ADR-003-agent-sdk-pydantic-ai.md) — Agent SDK choice (v0.5): pydantic-ai.
- [ADR-004](docs/architecture/adr/ADR-004-vector-store-chromadb-in-process.md) — Vector store choice (v0.4): chromadb in-process.

## Repository Structure

```text
aegisbank-ai-platform/
|-- README.md
|-- AGENTS.md
|-- .gitignore
|-- .opencode/            # MCP / LSP local installs (npm)
|-- .ai-env/              # Retrieval policy adopted from OpenCode
|-- .intelligence/        # Pre-existing project knowledge scaffold
|-- contracts/            # JSON Schema files
|-- docs/
|   |-- charter/          # v0.1 charter (5 docs)
|   |-- architecture/adr/ # Architecture Decision Records
|   `-- research/         # Library / pattern research notes
|-- opencode.json         # OpenCode-native config (MCP, LSP, instructions)
`-- tui.json              # TUI-only overrides (theme)
```

## How To Continue

1. Run the OpenCode launcher to confirm wiring:
   ```powershell
   pwsh "$env:USERPROFILE\.config\opencode\scripts\opencode-launcher.ps1" `
        -Profile minimax-plus `
        -TargetDir $PWD `
        -PrintRouting -DryRun
   ```
2. Review the four ADRs. None of them commits the project to a specific
   implementation outside its milestone.
3. Decide whether to approve the uncommitted `v0.2` proposal (see
   "What `v0.1` Includes" above). Do not start `v0.3` automatically.
4. Record any requested scope change before implementation begins.
5. Start `v0.3 - ML/NLP Baseline` only after explicit approval.

No Docker, Azure, RAG, model, agent, MCP server of our own, HITL workflow,
messaging, retry policy, or circuit breaker has been implemented.

## Reference Baseline

The charter uses official sources as design references, not as claims of
certification or compliance. The source baseline was checked on 2026-08-20:

- [Microsoft AI-103 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103)
- [Microsoft AI-200 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200)
- [MCP tools specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Peru D.S. N.° 115-2025-PCM](https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
