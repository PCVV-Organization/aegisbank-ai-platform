# Architecture Decision Records (ADRs)

This directory captures durable, append-only architectural decisions for the AegisBank AI Platform.
Following Microsoft Azure Well-Architected Framework and enterprise governance best practices:
* **ADRs are Append-Only:** An accepted decision is never rewritten or deleted to "clean up" history.
* **Superseding Decisions:** When an architectural choice evolves, a new ADR is authored that explicitly references and supersedes the previous record.
* **Historical Immutability:** Historical ADR files remain byte-exact to preserve git commit integrity and auditability.

---

## 1. Master ADR Index

| ADR | Title | Scope Milestone | Status | Key Focus |
|---|---|---|---|---|
| [ADR-001](./ADR-001-modular-monolith-first.md) | Modular monolith first | `v0.2` | Accepted | Decoupled modular packages before microservices |
| [ADR-002](./ADR-002-local-sqlite-before-postgresql.md) | Local SQLite before PostgreSQL | `v0.2` | Accepted | Deterministic in-memory/file datastore for initial local dev |
| [ADR-003](./ADR-003-agent-sdk-pydantic-ai.md) | Agent SDK choice (pydantic-ai) | `v0.5` | Accepted | Evaluated SDK choice for agent orchestrator |
| [ADR-004](./ADR-004-vector-store-chromadb-in-process.md) | Vector store integration strategy | `v0.4` | Accepted | ChromaDB in-process evaluation |
| [ADR-005](./ADR-005-deferred-tooling-evaluation.md) | Evaluation of deferred local-tooling items | `v0.1` | Accepted | Deferred LSP and MCP tooling matrix |
| [ADR-006](./ADR-006-classical-ml-intent-baseline.md) | Classical ML intent baseline | `v0.3` | Accepted | TF-IDF + Logistic Regression baseline |
| [ADR-007](./ADR-007-group-aware-synthetic-evaluation.md) | Group-aware synthetic evaluation | `v0.3` | Accepted | Prevent data leakage across template groups |
| [ADR-008](./ADR-008-local-retrieval-before-azure-ai-search.md) | Local retrieval before Azure AI Search | `v0.4` | Accepted | Local reproducible retrieval foundation |
| [ADR-009](./ADR-009-hybrid-retrieval-with-rrf.md) | Hybrid retrieval via Reciprocal Rank Fusion | `v0.4` | Accepted | RRF with frozen $k = 60$ |
| [ADR-010](./ADR-010-provider-agnostic-llm-boundary.md) | Provider-neutral LLM request boundary | `v0.5` | Accepted | Decoupled LLM provider interface |
| [ADR-011](./ADR-011-grounded-generation-citation-validation.md) | Grounded generation with citation validation | `v0.5` | Accepted | Active-context filtering and citation digests |
| [ADR-012](./ADR-012-single-agent-orchestrator-read-only-tools.md) | Single agent orchestrator with read-only tools | `v0.6` | Accepted | Controlled tool calling boundary |
| [ADR-013](./ADR-013-deterministic-tool-authorization-boundary.md) | Deterministic tool authorization & ownership | `v0.6` | Accepted | Customer ID isolation policy filter |
| [ADR-014](./ADR-014-local-mcp-boundary-stdio.md) | Local Model Context Protocol via stdio | `v0.7` | Accepted | Process-isolated MCP tool server |
| [ADR-015](./ADR-015-mandatory-hitl-for-banking-writes.md) | Mandatory Human-in-the-Loop for banking writes | `v0.7` | Accepted | State machine for approval proposals |
| [ADR-016](./ADR-016-idempotent-banking-writes-before-retries.md) | Idempotent banking writes before retries | `v0.8` | Accepted | Idempotency key replay protection |
| [ADR-017](./ADR-017-transactional-outbox-and-messaging-abstraction.md) | Transactional Outbox pattern | `v0.8` | Accepted | Dual-Write hazard prevention |
| [ADR-018](./ADR-018-circuit-breaker-policy-for-external-dependencies.md) | Circuit breaker policy for external dependencies | `v0.8` | Accepted | Resilient failure boundaries |
| [ADR-019](./ADR-019-opentelemetry-vendor-neutral-observability.md) | OpenTelemetry vendor-neutral observability | `v0.9` | Accepted | W3C traceparent propagation |
| [ADR-020](./ADR-020-structured-audit-event-model.md) | Structured audit event model | `v0.9` | Accepted | Non-repudiation audit logging |
| [ADR-021](./ADR-021-hotl-supervisory-kill-switch-for-writes.md) | Human-on-the-Loop supervisory kill-switch | `v0.9` | Accepted | Master supervisor kill-switch |
| [ADR-022](./ADR-022-layered-test-strategy-and-quality-gates.md) | Layered test strategy and quality gates | `v0.10` | Accepted | FAST gate, integration, and E2E separation |
| [ADR-023](./ADR-023-contract-first-compatibility-protection.md) | Contract-first compatibility protection | `v0.10` | Accepted | OpenAPI, tool schema, and outbox event contracts |
| [ADR-024](./ADR-024-ci-security-gates-before-deployment.md) | CI security gates before deployment | `v0.10` | Accepted | SAST (Bandit), SCA, SBOM, and Secret Scanning |
| [ADR-025](./ADR-025-local-containers-and-service-bus-adapter.md) | Local Containers and Service Bus Adapter | `v0.11` | Accepted | Containerized service bus emulation |
| [ADR-026](./ADR-026-azure-service-bus-emulator-messaging-adapter.md) | Azure Service Bus Emulator Messaging Adapter | `v0.11` | Accepted | Service Bus integration behind canonical bus |
| [ADR-027](./ADR-027-container-platform-decision-container-apps-vs-aks.md) | Container Platform: ACA First vs. AKS Deferred | `v0.11` | Accepted | Azure Container Apps selected for initial cloud |
| [ADR-028](./ADR-028-azure-functions-event-grid-local-serverless-foundation.md) | Local Serverless with Functions & CloudEvents | `v0.13` | Accepted | Python v2 worker & CloudEvents 1.0 webhook |
| [ADR-029](./ADR-029-configuration-secrets-identity-boundary.md) | Configuration, secrets & identity boundary | `v0.14` | Accepted | App Configuration + Key Vault reference boundary |
| [ADR-030](./ADR-030-local-ai-evaluation-and-mlops-foundation.md) | Local AI evaluation and MLOps foundation | `v0.15` | Accepted | Statistical candidate evaluation & promotion gates |

---

## 2. ADR Governance & Structural Audit Register

In compliance with repository governance (`v1.0.2`), an automated structural audit was conducted across all ADR files to verify standard sections (`Status`, `Context`, `Decision`, `Consequences`). In alignment with the **append-only rule**, observed discrepancies are recorded here rather than rewriting accepted files:

### Canonical records
ADR-023 and ADR-024 each have one accepted canonical record. The former
companion drafts were consolidated into those records during the documentation
cleanup; Git history preserves their original text.

### Structural Gaps Noted in Early Records
* **ADR-005:** Structured as an evaluation matrix rather than standard Context/Decision/Consequences sections; retained for historical accuracy.
* **ADR-022:** Contains Context, Decision, and Consequences sections; lacks explicit `- Status: Accepted` frontmatter line. Formally recognized as Accepted.
* **ADR-025, ADR-026, ADR-027, ADR-028:** Structured with narrative headings (`Context & Problem`, `Architectural Decision`, `Consequences & Trade-offs`) and formal status blocks. Formally recognized as Accepted.

---

## 3. Pending Architectural Areas (Future Cloud Roadmap)

The following items are deferred to future cloud milestones (post-`v1.0`):
1. **AKS Deployment Architecture:** Dedicated cluster topology if multi-agent microservices are introduced (post-v1.0).
2. **Cloud Managed Identity (Entra ID Workload Identity):** Production federation between Container Apps and Azure Key Vault/Cosmos DB.
3. **Multi-Region Disaster Recovery:** Active-passive failover for Cosmos DB and Service Bus geo-replication.
