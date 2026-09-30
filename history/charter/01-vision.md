# 01 - Vision

| Field | Value |
| --- | --- |
| Project | AegisBank AI Platform |
| Milestone | `v0.1.0 - Project Charter` |
| Status | Ready for review |
| Last reviewed | 2026-08-20 |

## Problem

Many generative AI demonstrations prove only that a model can produce a plausible
response. They do not prove that the response is grounded in authorized evidence,
that a tool call is allowed, that a write cannot be duplicated, that failures are
contained, or that an operator can reconstruct what happened.

At the same time, building a complete bank, an early fleet of microservices, or a
multi-agent system would obscure those engineering lessons behind unnecessary
business scope and infrastructure complexity.

AegisBank addresses both problems with one bounded laboratory: a fictitious
banking context that is small enough to finish and rigorous enough to exercise
enterprise AI engineering practices.

## Vision

Create a secure agentic banking AI laboratory in which every answer, data access,
and proposed action is grounded, policy-controlled, observable, testable, and
reconstructable.

The system will eventually provide one assistant, **Aegis**, that can:

- answer fictitious banking product questions from authorized and versioned sources;
- read data belonging to a synthetic customer through constrained tools;
- draft a fictitious service request or complaint;
- execute that write only after explicit human approval and deterministic authorization;
- abstain when evidence, authorization, or dependency health is insufficient;
- produce audit and telemetry evidence without indiscriminate sensitive-data capture.

## Objective

Design, build, evaluate, secure, deploy, and observe a fictitious banking platform
based on generative AI and a single agent. The platform must demonstrate RAG, MCP
tool use, HITL and HOTL controls, resilient APIs, auditability, automated quality
gates, and a local-to-Azure delivery path using exclusively synthetic data.

The project has two equal outcomes:

1. A working, evidence-based engineering artifact suitable for technical review.
2. A structured laboratory for applying AI, ML, NLP, research, MLOps, backend,
   cloud, security, and operations competencies.

## Fictitious Users

| User | Need | Boundary |
| --- | --- | --- |
| Synthetic customer | Ask product questions, inspect a simulated loan, and request help | Has no relationship to a real person or account |
| Human approver | Review, approve, reject, or amend a proposed write | Approval does not replace deterministic authorization |
| Operator | Inspect health, traces, alerts, and audit events; disable unsafe execution paths | HOTL capability may begin as operational controls rather than a custom dashboard |
| AI/ML engineer | Build and compare retrieval, classification, generation, and agent behavior | Uses versioned synthetic datasets and measurable experiments |
| Backend/cloud engineer | Productize APIs, persistence, messaging, resilience, identity, and telemetry | Proceeds local first and creates no paid resource without approval |
| Security/compliance reviewer | Trace controls to risks and reference frameworks | Reviews an educational system, not a regulated-bank attestation |
| Portfolio reviewer/interviewer | Evaluate decisions, trade-offs, tests, and measured results | Sees evidence, not unsupported capability claims |

## Educational Value

| Learning area | Planned evidence |
| --- | --- |
| AI foundations | Explicit decomposition into classification, retrieval, ranking, generation, decision, and action |
| Machine Learning | Reproducible TF-IDF and Logistic Regression intent-classification baseline |
| NLP and Transformers | Intent detection, embeddings, semantic retrieval, chunking, reranking, and a justified small-model comparison |
| Research | Controlled comparison of traditional ML, a small Transformer, and an LLM classifier |
| MLOps/LLMOps | Versioned datasets, experiments, prompts, models, evaluations, gates, deployment, and monitoring |
| AI-103 alignment | Foundry-oriented generative AI, RAG, agent workflows, tools, evaluations, guardrails, oversight, and tracing |
| AI-200 alignment | Backend lifecycle, containers, data services, vector workloads, messaging, secrets, identity, monitoring, and distributed observability |
| Enterprise banking engineering | Deterministic authorization, HITL writes, idempotency, bounded retry, circuit breaker, audit, contracts, and E2E evidence |

This mapping is a study and portfolio plan. It is not a statement that the project
or its contributors hold a certification.

## Portfolio Value

The repository should allow a reviewer to answer the following from committed
evidence rather than a live demonstration alone:

- What business problem is solved, and what is intentionally excluded?
- Which claims are grounded in a source, a test, a metric, or an ADR?
- Why is one agent sufficient, and what evidence would justify another?
- How is a write prevented before approval and authorization?
- How are duplicate effects, transient failures, persistent failures, and partial
  failures handled?
- Can one execution be reconstructed without exposing unnecessary sensitive data?
- How were RAG, agent, and ML alternatives evaluated?
- What changed between local execution, containers, CI, and Azure?

## Design Principles

1. **Synthetic by construction.** Real personal, account, card, credential, and transaction data is prohibited.
2. **Small business scope, serious engineering.** Implement only the use cases needed to demonstrate the controls.
3. **Local first.** Prove behavior locally before Docker, CI, or cloud deployment.
4. **Monolith first.** Use a modular monolith until lifecycle, scale, ownership, security, or isolation evidence justifies extraction.
5. **Single-agent first.** One governed agent must be evaluated and observable before any multi-agent experiment.
6. **Deterministic authority.** Identity, policy, authorization, validation, and business rules authorize; the LLM never does.
7. **Human control over writes.** Every state-changing operation in `v1.0` requires explicit HITL approval.
8. **Ground or abstain.** A fluent answer without sufficient authorized evidence is a failure, not a feature.
9. **Defense in depth.** Input, output, retrieval, tool, action, identity, and infrastructure controls are separate layers.
10. **Reliable effects.** Idempotency precedes retry; retry and circuit breaker solve different failure modes.
11. **Observable without oversharing.** Trace decisions and effects while minimizing and redacting sensitive content.
12. **Evidence before claims.** A capability is complete only when its required validation has actually run.
13. **Technology must earn its place.** Every addition must resolve a requirement, reduce a risk, or demonstrate a defined competency.
14. **Stop at the boundary.** `v1.0` completion triggers stabilization, not automatic feature expansion.

## Governance Position

AegisBank is a fictitious educational project and is not affiliated with Mibanco,
Microsoft, the SBS, the Peruvian government, or any financial institution. It
must not claim legal or regulatory compliance, production readiness for banking,
or official alignment/certification.

The D.S. N.° 115-2025-PCM approved the regulation of Peru's Law N.° 31814. Official
PCM guidance identifies management of critical banking assets and credit
evaluation among high-risk AI uses and describes human-supervision duties for
high-risk private-sector systems. AegisBank excludes real banking operations and
credit decisions, but adopts human oversight, audit, privacy, and risk management
as design requirements and learning objectives.

NIST AI RMF 1.0 is used as a voluntary risk-management reference through its
`GOVERN`, `MAP`, `MEASURE`, and `MANAGE` functions. NIST states that AI RMF 1.0 is
under revision as of this charter review, so future compliance documentation must
record the exact version consulted.

## Official Reference Baseline

Checked on 2026-08-20:

- [AI-103 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-103)
- [AI-200 study guide](https://learn.microsoft.com/en-us/credentials/certifications/resources/study-guides/ai-200)
- [MCP tools specification, 2025-11-25](https://modelcontextprotocol.io/specification/2025-11-25/server/tools)
- [Azure Retry pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/retry)
- [Azure Circuit Breaker pattern](https://learn.microsoft.com/en-us/azure/architecture/patterns/circuit-breaker)
- [D.S. N.° 115-2025-PCM](https://www.gob.pe/institucion/pcm/normas-legales/7133522-115-2025-pcm)
- [PCM classification of AI uses](https://www.gob.pe/110225-clasificacion-de-la-ia-en-el-peru)
- [PCM obligations for public and private entities](https://www.gob.pe/110229-obligaciones-especificas-de-las-entidades-publicas-y-privadas-en-el-uso-de-la-inteligencia-artificial)
- [Peru Law N.° 29733, Personal Data Protection](https://www.gob.pe/institucion/anpd/normas-legales/2018427-29733-2011)
- [D.S. N.° 016-2024-JUS, regulation of Law N.° 29733](https://www.gob.pe/institucion/anpd/normas-legales/6554453-16-2024-jus)
- [NIST AI Risk Management Framework](https://www.nist.gov/itl/ai-risk-management-framework)
