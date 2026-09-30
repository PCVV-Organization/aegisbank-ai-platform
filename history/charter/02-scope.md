# 02 - Scope

| Field | Value |
| --- | --- |
| Project | AegisBank AI Platform |
| Milestone | `v0.1.0 - Project Charter` |
| Status | Ready for review |
| Delivery boundary | `v1.0 - Enterprise Hardening` |

## Scope Statement

`v1.0` will deliver one local-first, Azure-targeted, fictitious banking AI
laboratory. One assistant will answer questions from authorized knowledge, read
synthetic customer information through constrained tools, and create one kind of
state-changing record, a service request or complaint, only after explicit human
approval and deterministic authorization.

The destination includes enterprise controls and evidence, not the breadth of a
real bank. The detailed exclusions in [04 - Non-goals](04-non-goals.md) are part
of this boundary.

## In Scope For v1.0

### Controlled business capabilities

- One conversational assistant named **Aegis**.
- Product and policy questions answered through RAG from a fictitious, authorized,
  versioned corpus.
- Citations to the evidence used for supported answers.
- Abstention when evidence is absent, insufficient, unauthorized, obsolete, or unavailable.
- Read-only lookup of a synthetic customer's installment and simulated loan data.
- Drafting, approval, and creation of one fictitious service request or complaint.
- Explicit rejection, amendment, expiration, or cancellation of a proposed write.
- Operator controls sufficient to inspect and suspend risky behavior without
  requiring a complex custom dashboard.

### AI and ML capabilities

- Versioned prompts with objective, expected format, restrictions, tests, and rollback identity.
- Input, output, retrieval, and action/tool guardrails.
- Retrieval ingestion, chunking, embeddings, vector search, ranking or reranking,
  source lifecycle metadata, and grounded generation.
- One governed agent with read tools first and one HITL-protected write tool later.
- MCP as the planned tool boundary, with explicit schemas and least-privilege authorization.
- RAG evaluation that separates retrieval quality from generation quality.
- Agent evaluation for intent, task adherence/completion, tool selection, tool
  input, tool success, output use, policy compliance, and HITL compliance.
- A reproducible intent-classification baseline using TF-IDF and Logistic Regression.
- An experimental comparison against a small Transformer and an LLM classifier
  only after hypotheses, datasets, and evaluation methods are defined.
- Dataset, prompt, experiment, metric, artifact, and model versioning appropriate
  to the implemented maturity level, with MLflow introduced only when useful.

### Backend, reliability, and data

- Python, FastAPI, Pydantic, SQLAlchemy, PostgreSQL, and pytest as preferred core technologies.
- A modular monolith as the initial deployable architecture.
- REST APIs and explicit OpenAPI contracts.
- Synthetic, deterministic, reproducible fixtures and datasets.
- Validation, policy, authorization, and business rules outside the LLM.
- `Idempotency-Key` support for every write, preventing duplicate business effects.
- Bounded retries with backoff, and jitter where appropriate, only for classified transient failures.
- Circuit breakers for persistent dependency failures, with `CLOSED`, `OPEN`, and `HALF_OPEN` behavior.
- Correlation and trace identifiers propagated across API, agent, MCP, data,
  messaging, audit, and telemetry boundaries.
- Structured audit events with data minimization and redaction.
- Messaging introduced when the service-request flow needs decoupling, using
  `ServiceRequestCreated` as the first domain event and Azure Service Bus as the cloud target.

### Quality, security, and operations

- Unit, integration, contract, end-to-end, and AI evaluation test layers.
- Contract checks for OpenAPI and MCP tool schemas; Pact only if a real consumer/provider need emerges.
- CI gates for formatting/linting, type checks, tests, security checks,
  relevant AI evaluations, and builds when each toolchain exists.
- Docker packaging after local behavior is proven.
- OpenTelemetry-based logs, metrics, and distributed traces with sensitive-data controls.
- Application Insights/Azure Monitor as the future cloud observability target.
- Threat modeling, control mapping, incident-oriented auditability, and dependency review.
- Secret management through local placeholders first and Azure Key Vault/managed identity later.
- No real secret in Git and no paid Azure deployment without explicit approval.

### Cloud and documentation

- Local execution before container and cloud work.
- Azure Container Registry and Azure Container Apps as the first deployment path.
- Azure AI/Foundry services, Azure AI Search, Azure Database for PostgreSQL,
  Azure Service Bus, Key Vault, managed identity, and Azure Monitor only in their
  authorized milestones and where the final design justifies them.
- Infrastructure as code using Bicep after the deployable architecture is stable.
- Architecture diagrams, ADRs, runbooks, research reports, model/evaluation cards,
  threat model, and a compliance control matrix as later milestone artifacts.
- AKS only as optional post-`v1.0` work, not as a `v1.0` dependency.

## v1.0 Boundary

The `v1.0` product boundary contains exactly three user-facing capability groups:

1. **Knowledge:** answer supported product/policy questions and abstain otherwise.
2. **Read:** retrieve an authorized synthetic customer's installment and loan information.
3. **Write:** create one fictitious service request/complaint after HITL approval.

New financial operations, channels, autonomous decisions, agent roles, or cloud
platforms are outside the boundary even if the architecture could support them.

`v1.0` is complete only when the criteria in
[05 - Success criteria](05-success-criteria.md) have objective evidence. At that
point the project stops feature development and enters stabilization and review.

## Out Of Scope

The following categories are excluded from `v1.0`:

- Any integration, identity, customer, account, or transaction from a real bank.
- Transfers, payments, disbursements, card processing, or movement of real or simulated funds.
- Automated credit approval, production credit scoring, fraud adjudication, or consequential financial decisions.
- Biometric processing, a mobile application, or an initial real WhatsApp integration.
- Production operation for a regulated institution or a claim of legal compliance.
- Multiple cloud providers, blockchain audit, Kafka, an in-house LLM, or large-model fine-tuning.
- Early microservices, early AKS, or multi-agent orchestration before `v1.0`.
- A complete bank, complete core banking platform, or high-fidelity clone of one.

## Constraints

| Constraint | Consequence |
| --- | --- |
| Workspace | Project writes remain inside `C:\aegisbank-ai-platform` |
| Data | Only synthetic, non-identifiable, reproducible data may enter source, tests, logs, prompts, or telemetry |
| Authorization | An LLM output is never an authorization decision |
| Human oversight | Every write requires explicit, action-bound HITL approval |
| Architecture | Modular monolith and one agent are defaults until evidence supports change |
| Delivery | Local, then Docker, CI, and Azure; phases cannot be skipped by convenience |
| Cost | No resource that may incur Azure cost is created without explicit approval |
| Security | Secrets stay outside Git; logging and tracing minimize sensitive content |
| Evidence | Completion requires executed validation, not an expectation that behavior works |
| Sources | Current official documentation is preferred for changing SDK, service, protocol, and legal claims |
| Scope | Each technology must resolve a requirement, reduce a risk, or demonstrate a defined competency |

## Roadmap And Phase Gates

| Version | Deliverable | Entry condition | Exit evidence |
| --- | --- | --- | --- |
| `v0.1` | Project Charter | Approved project concept | Five charter documents, root governance, validation, local commit when possible |
| `v0.2` | Core Banking Mock | Explicit approval of `v0.1` | Local API, persistence, synthetic fixtures, domain tests |
| `v0.3` | ML/NLP Baseline | Stable intent labels and dataset contract | Reproducible baseline, metrics, error analysis |
| `v0.4` | RAG | Authorized corpus and source lifecycle defined | Retrieval/generation pipeline, citations, abstention, baseline evals |
| `v0.5` | Agent and read tools | RAG and read API contracts stable | Single agent, constrained read tools, agent eval baseline |
| `v0.6` | MCP and HITL | Read tool path secure and observable | MCP boundary, approval state machine, protected complaint write |
| `v0.7` | Reliability and Messaging | Idempotent write semantics proven | Retry classification, circuit breaker, event flow, failure tests |
| `v0.8` | Quality and Evaluations | Major execution paths stable | Full test taxonomy, contract/E2E suites, enforceable eval gates |
| `v0.9` | Azure Deployment | Local, Docker, and CI gates pass | Authorized Azure deployment, identity, secrets, telemetry, IaC evidence |
| `v1.0` | Enterprise Hardening | All functional components integrated | Threat model, control matrix, observability, docs, portfolio evidence, DoD pass |
| `v1.1` | AKS experiment | `v1.0` complete and AKS hypothesis approved | Optional comparative deployment evidence |
| `v1.2` | Multi-agent experiment | `v1.0` complete and single-agent limitation proven | Optional controlled experiment, not default architecture |

No later phase may be used to hide a failed exit criterion from an earlier phase.

## Future Dependencies And Admission Criteria

These are planned candidates, not dependencies installed or selected by `v0.1`:

| Candidate | Earliest phase | Admit only when |
| --- | --- | --- |
| FastAPI/Pydantic/SQLAlchemy/PostgreSQL | `v0.2` | Domain/API/persistence design and supported versions are verified |
| scikit-learn | `v0.3` | Intent dataset, labels, split policy, and baseline experiment are specified |
| Microsoft Foundry model and embedding SDKs | `v0.4` | Local abstraction, model access, cost, safety, and evaluation plan are approved |
| Azure AI Search | `v0.4` or `v0.9` | Corpus and retrieval requirements justify managed vector/search capabilities |
| MCP SDK | `v0.5`/`v0.6` | Current official protocol/SDK contract and authorization boundary are verified |
| MLflow | `v0.3` or later | Experiment volume and reproducibility needs exceed simple tracked artifacts |
| PyTorch/Transformers | Research phase | A documented hypothesis justifies a small-model experiment |
| Azure Service Bus | `v0.7`/`v0.9` | Asynchronous decoupling and delivery semantics are defined |
| OpenTelemetry | First distributed boundary | Required spans, attributes, propagation, retention, and redaction are defined |
| Docker/GitHub Actions | After local baseline | Reproducible commands and gates already pass locally |
| Bicep/Azure services | `v0.9` | Cloud design, budget, identity, security, and deployment approval exist |

No candidate is mandatory merely because it appears in this table.

## Scope Change Control

A scope change must be recorded before implementation and answer:

1. Which approved requirement cannot be met without the change?
2. Which concrete risk is reduced, or which defined competency is demonstrated?
3. Why is the existing simpler design insufficient?
4. What new security, cost, operational, testing, and schedule burden is introduced?
5. Which charter, ADR, success criterion, and roadmap gate must change?

If those questions do not have evidence-based answers, the proposal remains out of scope.
