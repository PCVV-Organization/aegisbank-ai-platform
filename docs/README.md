# AegisBank AI Platform — Documentation Index & Information Architecture

> **Repository Governance:** `v1.0.2 — Documentation Information Architecture & Evaluation Taxonomy`  
> **Philosophy:** *The LLM interprets and proposes; deterministic identity, policy, authorization, validation, and business rules decide.*  
> **Documentation Framework:** Inspired by **Diátaxis** (Tutorials, How-To Guides, Reference, Explanations) and enterprise banking system governance (OCC SR 11-7 / EBA guidelines).

---

## 1. How to Navigate This Repository

This documentation suite serves three distinct audiences: hiring managers/recruiters reviewing the portfolio, lead architects conducting deep-dive technical evaluations, and engineers auditing the historical construction trail.

To prevent cognitive overload, documentation is partitioned into **Three Navigation Tiers**:

```
docs/
├── [Tier 1: Portfolio Core] ──> Executive architectural defense, STRIDE, runbooks, maturity
├── [Tier 2: Deep Dive]     ──> ADRs, quality matrices, lab performance, master's notes
└── [Tier 3: Audit Trail]   ──> Chronological prompts, early exploratory milestones, charter
```

---

## 2. Tier 1: Portfolio & Interview Core (Essential Assets)

*If you are evaluating AegisBank for a Lead / Senior AI Engineer role, start with these 6 core documents:*

| Document | Primary Focus | Key Engineering Competency |
|---|---|---|
| **[Portfolio Interview Evidence](releases/PORTFOLIO-INTERVIEW-EVIDENCE.md)** | Master defense document for technical interviews | System design trade-offs (Modular Monolith, Outbox, Key Vault boundary), root cause analysis of elusive bugs (`cygrpc` MAX_PATH, *pseudo-tool-call* vulnerability), and behavioral answers. |
| **[Canonical Components](architecture/CANONICAL-COMPONENTS.md)** & **[E2E Final Architecture](architecture/E2E-FINAL-ARCHITECTURE.md)** | End-to-end system design & trust boundaries | Single-agent orchestrator boundary, MCP `stdio` sandboxing, deterministic ownership filters, transactional outbox pattern. |
| **[STRIDE Threat Model](security/V1.0-THREAT-MODEL.md)** | Comprehensive financial AI threat modeling | Spoofing, Tampering, Repudiation, Information Disclosure, Denial of Service, and Elevation of Privilege mitigations for LLM agents. |
| **[Operational Runbooks](operations/runbooks/)** | Production incident response & disaster recovery | 4 actionable runbooks: [Incident Response](operations/runbooks/incident-response.md), [Rollback Procedures](operations/runbooks/rollback.md), [Dependency Outage](operations/runbooks/dependency-outage.md), and [DLQ & HOTL Kill-Switch](operations/runbooks/dlq-and-kill-switch.md). |
| **[Capability Maturity Matrix](requirements/V1.0-MATURITY-MATRIX.md)** | Enterprise requirements verification | Traceability across 4 maturity levels: Foundation, Enterprise Architecture, AI Safety & MLOps, and Operational Hardening. |
| **[AI Evaluation Taxonomy](evaluation/README.md)** & **[Evaluation Catalog](evaluation/EVALUATION-CATALOG.md)** | Scientific evaluation & MLOps evidence | Capability-based evaluation across Intent, Retrieval, Generation, Agent, Safety, System E2E, and Performance with frozen holdouts. |

---

## 3. Tier 2: Technical Deep Dive & Specialized References

*Detailed specifications, architecture decision records, performance benchmarks, and educational references:*

### Architecture & System Design
* **[Architecture Decision Records (ADRs)](architecture/adr/README.md):** 30 append-only decision records documenting architectural choices from SQLite-first to Event Grid, Key Vault boundaries, and local MLOps.
* **[Architecture Integrity Report](architecture/ARCHITECTURE-INTEGRITY-REPORT.md):** Automated architectural linting rules, dependency boundaries, and layer enforcement.
* **[Container Platform Decision](architecture/CONTAINER-PLATFORM-DECISION.md):** Comparative analysis: Azure Container Apps (ACA) vs. Azure Kubernetes Service (AKS).
* **[Cosmos DB Partition Design](architecture/COSMOS-PARTITION-DESIGN.md):** Partition key strategy (`/tenant_id/customer_id`) for multi-tenant banking data.
* **[Redis Cache Policy](architecture/REDIS-CACHE-POLICY.md):** Cache-aside patterns, TTL strategy, and vector index caching.
* **[Event Grid Cloud Design](architecture/EVENT-GRID-CLOUD-DESIGN.md)** & **[Event Grid vs. Service Bus](architecture/EVENT-GRID-VS-SERVICE-BUS.md):** Event-driven reactive push notifications vs. enterprise command brokering.

### Quality, Testing & Performance Evidence
* **[Test Strategy & Pyramid](quality/TEST-STRATEGY.md):** Layered testing across Unit, Integration, Contract, FAST gate, and E2E boundaries.
* **[E2E Journey Matrix](quality/E2E-MATRIX.md):** Verification matrix for the 8 critical banking journeys (Journeys A through H).
* **[Performance Evidence](quality/V1.0-PERFORMANCE-EVIDENCE.md)** & **[SLI/SLO Lab Report](quality/V1.0-SLI-SLO-LAB-REPORT.md):** Local laboratory baseline measurements (p50, p95, p99 latency, error rate) under 25 bounded iterations.
* **[Test Suite Rationalization](quality/TEST-SUITE-RATIONALIZATION.md):** Elimination of test debt (reduced agent suite by 25% while preserving 16 critical security invariants).
* **Runtime Verification Evidence:** [v0.13.1 Functions Host Evidence](quality/V0131-RUNTIME-EVIDENCE.md), [v0.14.0 AppConfig/KeyVault Evidence](quality/V0140-APPCONFIG-IDENTITY-EVIDENCE.md), [v0.15.0 Evaluation Evidence](quality/V0150-EVALUATION-MLOPS-EVIDENCE.md), and [v1.0.0 Release Evidence](releases/V1.0-EVIDENCE.md).

### Security & DevSecOps
* **[DevSecOps Shift-Left Gates](security/DEVSECOPS-GATES.md):** Automated SAST (Bandit), SCA (pip-audit), SBOM generation (CycloneDX), and Secret Scanning.
* **[Container Security Baseline](security/CONTAINER-SECURITY.md):** Non-root user execution, read-only root filesystems, and distroless/minimal base images.
* **[Data Layer Security](security/DATA-LAYER-SECURITY.md):** SQL injection prevention, parameterization, customer-id ownership filtering, and at-rest encryption.
* **[Serverless Security](security/SERVERLESS-SECURITY.md):** Webhook validation handshake, HMAC signature validation, and payload integrity.
* **[Software Bill of Materials (SBOM)](security/sbom.json):** CycloneDX standard machine-readable component inventory.

### Learning, Pedagogy & Master's Notes
* **[Master's Lecture Notes (v0.9)](learning/MASTERS-NOTES.md):** Deep conceptual explanations of OpenTelemetry (Logs, Metrics, Traces), W3C Traceparent propagation, and immutable audit logs.
* **[Master's Notes (v1.0)](learning/V1.0-MASTERS-NOTES.md):** Comprehensive engineering ledger covering the complete platform lifecycle.
* **[Teaching Contract](learning/TEACHING-CONTRACT.md):** Strict educational honesty policy prohibiting inflated claims (`TESTED-LOCAL`, `LOCAL-LAB-PERFORMANCE-BASELINE`, `CLOUD-PENDING`, `PROD-UNPROVEN`, `BLOCKED`).
* **[pgvector Technical Guide](learning/PGVECTOR.md):** HNSW vs. IVFFlat algorithmic trade-offs in PostgreSQL.
* **[Containers & Service Bus](learning/CONTAINERS-SERVICE-BUS.md)** & **[Azure Functions Triggers](learning/AZURE-FUNCTIONS-TRIGGERS-BINDINGS.md):** Cloud integration foundations.
* **[Glossary](learning/GLOSSARY.md):** Standard enterprise AI and banking definitions.

---

## 4. Tier 3: Historical Scaffolding & Construction Audit Trail

*These artifacts represent the historical construction and exploration process. They are preserved for reproducibility and auditability, but are excluded from primary portfolio navigation:*

* **[ChatGPT Prompts Log (000–026)](chatgpt-prompts/):** 28 chronological prompt transcripts recording the incremental engineering directives from bootstrap to v1.0 release.
* **[Early Milestone Experiments](experiments/):** Initial exploration documents ([v0.3 Intent Baseline](experiments/v0.3-intent-classification-baseline.md), [v0.4 RAG Foundation](experiments/v0.4-rag-retrieval-foundation.md), [v0.5 Grounded Generation](experiments/v0.5-grounded-generation-evaluation.md), [v0.6 Native Tool Calling](experiments/v0.6.1-native-tool-calling.md), [v0.7 MCP HITL](experiments/v0.7.0-mcp-hitl.md)). Their findings are consolidated in the canonical evaluation suite.
* **[Project Charter](charter/):** Initial bootstrap scope ([Vision](charter/01-vision.md), [Scope](charter/02-scope.md), [Use Cases](charter/03-use-cases.md), [Non-Goals](charter/04-non-goals.md), [Success Criteria](charter/05-success-criteria.md)).
* **[Career Gap Analysis](career/role-profile-images-and-gap-analysis.md):** Internal personal skills alignment against 2026 Lead AI Engineer job specifications.
* **[Research Notes](research/):** SDK evaluation notes ([PydanticAI](research/pydantic-ai-mcp-integration.md), [MCP Python SDK](research/mcp-python-sdk-hitl-patterns.md)).

---

## 5. Artifact Classification Taxonomy

Every document in `docs/` is classified into one of 11 formal governance categories:

| Purpose Category | Definition | Location Pattern | Examples |
|---|---|---|---|
| `CANONICAL/REFERENCE` | Stable authoritative specifications and references | `docs/architecture/`, `docs/requirements/` | [CANONICAL-COMPONENTS.md](architecture/CANONICAL-COMPONENTS.md), [V1.0-MATURITY-MATRIX.md](requirements/V1.0-MATURITY-MATRIX.md) |
| `ARCHITECTURE/ADR` | Append-only architectural decision records | `docs/architecture/adr/` | [ADR-001](architecture/adr/ADR-001-modular-monolith-first.md) to [ADR-030](architecture/adr/ADR-030-local-ai-evaluation-and-mlops-foundation.md) |
| `EVALUATION-PROTOCOL` | Human-authored evaluation methodologies and taxonomies | `docs/evaluation/` | [docs/evaluation/README.md](evaluation/README.md), [EVALUATION-CATALOG.md](evaluation/EVALUATION-CATALOG.md) |
| `RAW-EVALUATION-EVIDENCE` | Machine-generated evaluation benchmarks and query plans | `docs/evaluation/` (historical), `reports/` | [v012_retrieval_comparison.json](evaluation/v012_retrieval_comparison.json), [v012-pgvector-query-plans.json](evaluation/v012-pgvector-query-plans.json) |
| `QUALITY-GATE` | Executed test strategies, matrices, and runtime evidence | `docs/quality/` | [TEST-STRATEGY.md](quality/TEST-STRATEGY.md), [E2E-MATRIX.md](quality/E2E-MATRIX.md), [V1.0-PERFORMANCE-EVIDENCE.md](quality/V1.0-PERFORMANCE-EVIDENCE.md) |
| `OPERATIONS` | Operational runbooks, procedures, and troubleshooting | `docs/operations/` | [runbooks/incident-response.md](operations/runbooks/incident-response.md), [runbooks/rollback.md](operations/runbooks/rollback.md) |
| `SECURITY` | Threat models, DevSecOps gates, and security baselines | `docs/security/` | [V1.0-THREAT-MODEL.md](security/V1.0-THREAT-MODEL.md), [DEVSECOPS-GATES.md](security/DEVSECOPS-GATES.md) |
| `LEARNING` | Conceptual explanations, didactics, and teaching contracts | `docs/learning/` | [MASTERS-NOTES.md](learning/MASTERS-NOTES.md), [TEACHING-CONTRACT.md](learning/TEACHING-CONTRACT.md) |
| `EXPERIMENT-HISTORY` | Historical exploratory milestones superseded by release code | `docs/experiments/` | [v0.3-intent-classification-baseline.md](experiments/v0.3-intent-classification-baseline.md) |
| `RELEASE/PORTFOLIO` | Published release evidence and interview defense narratives | `docs/releases/` | [PORTFOLIO-INTERVIEW-EVIDENCE.md](releases/PORTFOLIO-INTERVIEW-EVIDENCE.md), [V1.0-EVIDENCE.md](releases/V1.0-EVIDENCE.md) |
| `HISTORICAL-AUDIT` | Immutable chronological construction logs and prompt runs | `docs/chatgpt-prompts/`, `docs/charter/` | [000_PROMPT.md](chatgpt-prompts/000_PROMPT.md) to [026_PROMPT.md](chatgpt-prompts/026_PROMPT.md) |

---

## 6. Document Governance Rules for Future Changes

To maintain clean documentation architecture over time, all future additions must adhere to the following placement rules:

1. **Human-Authored Protocols:** Methodologies, evaluation protocols, and taxonomies must reside in `docs/evaluation/`.
2. **Human-Readable Evidence:** Markdown reports summarizing test or benchmark execution must reside in `docs/quality/` or `docs/releases/`.
3. **Machine-Generated Raw Outputs:** Raw JSON, JSONL, SQLite MLflow runs, or profiling dumps must be generated in `reports/` or `reports/evaluation/`. Historical artifacts already committed in `docs/evaluation/` (`v012_retrieval_comparison.json`, `v012-pgvector-query-plans.json`) must NOT be moved cosmetically to avoid breaking external links and git history.
4. **Append-Only ADRs:** Architecture decisions cannot be edited or deleted once accepted. Changes require a new ADR superseding the previous one.
5. **No True Duplication:** Documentation must reference existing single sources of truth via markdown links rather than duplicating content across files.
