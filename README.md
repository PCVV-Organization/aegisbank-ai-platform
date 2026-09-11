# AegisBank AI Platform

> Educational and portfolio laboratory designed to demonstrate secure agentic
> banking AI with Python, Microsoft Foundry, RAG, MCP, human oversight, resilient
> cloud architecture, MLOps, and Azure.

---

## 1. What It Is

AegisBank AI Platform is an educational and portfolio laboratory for designing,
building, evaluating, securing, and operating a fictitious banking AI platform.
Its assistant, **Aegis**, answers questions from authorized knowledge,
reads synthetic customer information through controlled tools, and proposes
low-risk write actions requiring explicit human approval.

The project demonstrates grounded generation, deterministic authorization,
human oversight, reliability, auditability, testing, and observability without
pretending to reproduce a complete bank.

### What It Is Not
- It is not a bank, a core banking product, or production financial software.
- It is not affiliated with Mibanco, Microsoft, the SBS, or any financial institution.
- It does not use real customers, identifiers, accounts, cards, credentials, or transactions.
- It does not make real credit decisions or execute transfers, payments, or disbursements.
- It does not claim legal, regulatory, security, or NIST certification or compliance.

All project data is strictly synthetic and reproducible.

---

## 2. Current Status & Release Target

**Current Release:** `v1.0.2 — Documentation Information Architecture & Evaluation Taxonomy`
**Base Technical Development:** Frozen at `v1.0.1` (`668c0b2`, evidence integrity corrective).
**Philosophy:** *The LLM interprets and proposes; deterministic identity, policy, authorization, validation, and business rules decide.*

---

## 3. Portfolio & Technical Architecture Portal

All platform documentation is governed and organized under the master documentation portal:

👉 **[Master Documentation Portal & Information Architecture (docs/README.md)](docs/README.md)**

### Tier 1: Core Portfolio Assets (Start Here)

For hiring managers, lead architects, and technical interviewers, these 6 core documents demonstrate system design rigor, security modeling, and operational maturity:

| Area | Primary Document | Core Competency Demonstrated |
|---|---|---|
| **Architectural Defense** | **[Portfolio Interview Evidence](docs/releases/PORTFOLIO-INTERVIEW-EVIDENCE.md)** | System design trade-offs (Modular Monolith, Outbox, Key Vault reference boundary), root cause analyses (`cygrpc` Win32 MAX_PATH, *pseudo-tool-call* vulnerability), and behavioral answers. |
| **System Architecture** | **[Canonical Components](docs/architecture/CANONICAL-COMPONENTS.md)** & **[E2E Final Architecture](docs/architecture/E2E-FINAL-ARCHITECTURE.md)** | Trust boundaries, single-agent orchestrator, MCP `stdio` sandboxing, deterministic customer-id ownership filtering, and transactional outbox. |
| **Banking AI Security** | **[STRIDE Threat Model](docs/security/V1.0-THREAT-MODEL.md)** | Formal STRIDE threat analysis covering indirect prompt injection, IDOR cross-customer attacks, replay attacks, and PII sanitization. |
| **Operations & Resilience** | **[Operational Runbooks](docs/operations/runbooks/)** | 4 actionable disaster-recovery runbooks: [Incident Response](docs/operations/runbooks/incident-response.md), [Rollback](docs/operations/runbooks/rollback.md), [Dependency Outage](docs/operations/runbooks/dependency-outage.md), and [DLQ & Kill-Switch](docs/operations/runbooks/dlq-and-kill-switch.md). |
| **Enterprise Requirements** | **[Capability Maturity Matrix](docs/requirements/V1.0-MATURITY-MATRIX.md)** | Traceability across 4 enterprise maturity tiers: Foundation, Enterprise Architecture, AI Safety & MLOps, and Operational Hardening. |
| **Scientific AI Evaluation** | **[AI Evaluation Taxonomy](docs/evaluation/README.md)** & **[Evaluation Catalog](docs/evaluation/EVALUATION-CATALOG.md)** | Capability-centric evaluation across Intent, Retrieval, Generation, Agent, Safety, System E2E, and Performance with frozen holdouts and provenance reconciliation. |

---

## 4. Key Permanent Principles

1. **Deterministic Authority:** The LLM may interpret and propose; deterministic identity, policy, authorization, validation, and business rules decide.
2. **Mandatory HITL:** Every state-changing write operation requires explicit Human-in-the-Loop approval before persistence.
3. **Fail-Safe Abstention:** Unsupported answers must abstain rather than fabricate evidence.
4. **Outbox Before Retries:** Writes must be transactional and idempotent before any message retry policy is enabled.
5. **Context Propagation:** W3C `traceparent` correlation identifiers are propagated across every execution boundary.
6. **No Fake Production Claims:** Local demonstrations remain honestly designated as `TESTED-LOCAL`, `LOCAL-LAB-PERFORMANCE-BASELINE`, `CLOUD-PENDING`, or `PROD-UNPROVEN` (see [Teaching Contract](docs/learning/TEACHING-CONTRACT.md)).

---

## 5. Repository Structure

```text
aegisbank-ai-platform/
├── README.md                           # Platform landing page (this document)
├── .gitignore
├── ai/
│   ├── agent/                          # Agent orchestrator, MCP stdio server & HITL state machine
│   └── rag/                            # Retrieval (TF-IDF, SVD, pgvector HNSW) & Grounded Generation
├── contracts/                          # JSON Schemas (OpenAPI, CloudEvents, Outbox domain events)
├── docs/                               # Master documentation suite (see docs/README.md)
│   ├── architecture/                   # Canonical components, E2E architecture & 30 append-only ADRs
│   ├── evaluation/                     # Capability-based AI evaluation taxonomy & master catalog
│   ├── operations/                     # Production operational runbooks & Kubernetes troubleshooting
│   ├── quality/                        # Test strategy, E2E journey matrix & performance evidence
│   ├── releases/                       # Portfolio interview evidence & release verification
│   ├── requirements/                   # Enterprise capability maturity matrix
│   ├── security/                       # STRIDE threat model, DevSecOps gates, SBOM & security policies
│   ├── learning/                       # Master's notes, didactic guides & Teaching Contract
│   ├── experiments/                    # Early milestone exploration history (v0.3 - v0.7)
│   └── chatgpt-prompts/                # Chronological construction prompt audit log (000 - 026)
├── functions/
│   └── aegisbank-events/               # Azure Functions Python v2 worker (Event Grid / CloudEvents)
├── ml/
│   └── intent-classifier/              # Classical ML intent baseline (TF-IDF + Logistic Regression)
├── services/
│   └── mock-core-banking/              # FastAPI core banking mock (Accounts, Loans, Cards, Outbox)
└── scripts/                            # Unified quality gate, session guard, performance & evaluation CLI
```

---

## 6. Quick Start & Verification

### Local Environment Setup
```powershell
# Activate Python 3.14 virtual environment
.\.venv\Scripts\Activate.ps1

# Run FAST Quality Gate (all 13 automated checks)
python scripts/quality_gate.py --fast
```

### Run an Agent Inquiry via CLI
```powershell
# Read-only loan balance inquiry
python -m aegisbank_agent.cli run "Dame detalle de mi prestamo LOAN-0001" --customer-id CUST-0001
```

For full setup, architecture deep-dives, and interview presentation notes, see [docs/README.md](docs/README.md).
