# AegisBank AI Platform — Portfolio Interview Evidence & Architectural Defense (v1.0.0)

> **Role Focus:** Lead / Senior AI Engineer (LLM / Agentic Systems & Enterprise Cloud Integration)  
> **Target Domain:** Tier-1 Banking & Financial Services (e.g., Mibanco, BCP, Credicorp, Microsoft AI Foundry)  
> **Release Target:** `v1.0.0 — Enterprise Hardening, Final E2E & Portfolio Release`  
> **Baseline Commit:** `8393d88` (`fix(v0.15): validate App Configuration URL schemes`)  
> **Philosophy:** *The LLM interprets and proposes; deterministic identity, policy, authorization, validation, and business rules decide.*

---

## 1. Executive Summary & Problem Space

AegisBank AI Platform is a secure, educational banking AI laboratory designed to demonstrate production-grade software engineering and AI systems architecture. In banking, naive LLM implementations—such as connecting LangChain or LlamaIndex directly to internal databases or APIs—fail dramatically due to:

1. **Non-deterministic execution:** LLMs hallucinate tool arguments, invent transaction IDs, and skip validation steps.
2. **Security vulnerabilities:** Prompt injection, cross-customer data leakage, and unauthorized state mutation.
3. **Distributed data inconsistency:** The "Dual-Write" failure mode where a database record is updated but an event publication fails silently.
4. **Uncalibrated AI evaluation:** Teams claiming improvements based on "vibes" or single test prompts rather than statistical hypothesis testing and holdout suites.

AegisBank solves these challenges through a **Modular Monolith** architecture enforcing strict trust boundaries, deterministic policy guards, transactional outbox messaging, formal Human-in-the-Loop (HITL) state machines, and a rigorous scientific evaluation framework.

```text
[ UNTRUSTED USER INPUT ]
           │
           ▼
┌────────────────────────────────────────────────────────────────────────┐
│                      AgentOrchestrator Boundary                        │
│                                                                        │
│  1. Structured Prompting & Entity Extraction (Regex + Allowlist)       │
│  2. Deterministic Ownership Policy (Customer ID Isolation)             │
│  3. Multi-Turn Tool Calling (Native OpenAI/Azure Format & MCP Stdio)   │
│  4. Groundedness & Citation Abstention Gate                            │
└──────────────────┬─────────────────────────────────┬───────────────────┘
                   │                                 │
                   ▼ (READ Operations)               ▼ (WRITE Proposal)
┌──────────────────────────────────────┐  ┌──────────────────────────────┐
│  Core Banking & Knowledge Retrieval  │  │  HITL & HOTL Safety Boundary │
│  - PostgreSQL + pgvector (HNSW)      │  │  - ApprovalRequest State Mach│
│  - Redis Cache & Vector Search       │  │  - SHA-256 Digest Validation │
│  - Ownership-Enforced Tool Adapters  │  │  - Master HOTL Kill-Switch   │
└──────────────────┬───────────────────┘  └──────────────┬───────────────┘
                   │                                     │ (Approved & Unlocked)
                   │                                     ▼
                   │                      ┌──────────────────────────────┐
                   │                      │  Transactional Outbox & Bus  │
                   │                      │  - Atomic SQL Commit         │
                   │                      │  - IdempotencyGuard Replay   │
                   │                      │  - Dead-Letter Queue (DLQ)   │
                   │                      └──────────────┬───────────────┘
                   │                                     │
                   ▼                                     ▼
┌────────────────────────────────────────────────────────────────────────┐
│                       Observability & Audit Trail                      │
│  - W3C Traceparent Context Propagation (OpenTelemetry)                 │
│  - Immutable AuditLogger (Redacted PII / Secret Sanitization)          │
│  - Operational Metrics (p50, p95, p99 Latency & Error Budgets)         │
└────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Architectural Decisions & Technical Trade-offs Defended

### A. Modular Monolith vs. Early Microservices
* **Decision:** Implement AegisBank as a clean, decoupled modular monolith (`ai/agent`, `ai/rag`, `services/mock-core-banking`, `functions/aegisbank-events`) within a unified repository rather than deploying multi-service distributed microservices (AKS/Service Fabric).
* **Defense:** Early microservices in an AI laboratory introduce network latency, distributed transaction complexity (Saga/2PC), brittle testing environments, and operational overhead without adding business value. A modular monolith enforces strict domain boundaries at the module import level (audited by Pylint and architecture gates) while preserving zero-network-overhead in-memory testing and deterministic debugging. When horizontal scaling is required, packages have clear boundaries ready for containerization.

### B. "The LLM Proposes, Deterministic Code Decides"
* **Decision:** The LLM is never given direct write access to any database or external API. The orchestrator intercepts all write attempts and transforms them into an `ApprovalRequest` proposal.
* **Defense:** LLMs are probabilistic token predictors. Entrusting financial state mutation (money transfers, account creations, dispute filing) to an LLM's autonomy violates fundamental banking risk controls (e.g., Basel Committee, OCC regulations, EBA guidelines). In AegisBank, the LLM only formats the proposed payload; deterministic validation, ownership verification, customer session matching, and explicit human sign-off are required before persistence.

### C. Model Context Protocol (MCP) via `stdio`
* **Decision:** Expose enterprise tool calling via Anthropic's Model Context Protocol (MCP standard `2026-07-28`, `mcp==2.1.1`) using `stdio` transport.
* **Defense:** While HTTP/SSE transports exist, `stdio` runs the MCP tool server as an isolated child OS process. This provides strict memory boundary separation, eliminates port conflict issues in containerized local environments, avoids unauthorized network access, and guarantees that tools execute with explicit process-level sandboxing.

### D. Transactional Outbox Pattern before Message Broker Retries
* **Decision:** When a state-changing operation executes (e.g., `create_service_request`), the entity change and the corresponding domain event are written to the database within the **same atomic SQL transaction** (`outbox_events` table).
* **Defense:** Directly publishing events to a message broker (Azure Service Bus, RabbitMQ, Kafka) after writing to the database creates the classic **Dual-Write Hazard**: if the broker is unreachable, the network partitions, or the process crashes between the DB commit and the broker call, the event is permanently lost. The Transactional Outbox pattern guarantees **at-least-once publication** because the event cannot fail to commit if the business record succeeds.

### E. Configuration vs. Secrets Separation
* **Decision:** Decouple operational configuration (Azure App Configuration) from cryptographic secrets (Azure Key Vault) using the **Key Vault Reference** pattern (`@Microsoft.KeyVault(SecretUri=...)`).
* **Defense:** Storing secrets in `.env` files or operating system environment variables risks accidental leakage via process crash dumps, error logs, `/proc` inspection, or web diagnostic endpoints (`/actuator/env`). App Configuration manages operational flags and tunable parameters (e.g., `rag.top_k = 5`) accessible to operators, while sensitive materials (connection strings, signing keys) reside strictly in Key Vault with role-based data-plane authorization (`Key Vault Secrets User`).

---

## 3. Real Bugs Diagnosed & Root Cause Analysis (RCA)

In enterprise engineering, the hallmark of seniority is not writing bug-free code on the first attempt, but diagnosing elusive system anomalies down to OS, runtime, and algorithmic fundamentals.

### Case 1: Windows NT Dynamic Linker Failure on `cygrpc` (`ERROR_FILENAME_EXCED_RANGE`)
* **Symptom:** When attempting to run Azure Functions Core Tools v4 locally on Windows 11 with the Python 3.14 worker, the host crashed during startup with:  
  `ImportError: DLL load failed while importing cygrpc: El nombre del archivo o la extensión es demasiado largo.`
* **Root Cause Analysis:** Using Windows debugging utilities, the failure was traced to Windows NT Status code `0xCE` (`ERROR_FILENAME_EXCED_RANGE` / Win32 Error 206). The Python 3.14 Language Worker dynamically loaded deep nested virtual environment binaries via `LoadLibraryExW`. The combined path length of the gRPC C-extension (`cygrpc.cp314-win_amd64.pyd`) and its DLL search directories exceeded the Win32 `MAX_PATH` limit (260 characters).
* **Architectural Resolution:** Rather than hacking Windows registry keys (`LongPathsEnabled`) or modifying local developer OS settings—which cannot be guaranteed across CI runners or enterprise developer laptops—we adopted **OCI Container Isolation** (`mcr.microsoft.com/azure-functions/python:4-python3.14`). In Linux (`glibc`), dynamic linking via `dlopen` does not suffer from Win32 path limits, providing a reproducible runtime identical to production Azure Container Apps and App Service. We classified Windows native execution honestly as `BLOCKED` while verifying the Linux runtime container E2E.

### Case 2: Metamorphic Routing Loss & The "Pseudo-Tool-Call" Vulnerability
* **Symptom:** In manual conversational testing:
  - Query A: `"Dame detalle de mi prestamo LOAN-0001"` $\rightarrow$ Executed `get_loan_details(loan_id="LOAN-0001")` correctly.
  - Query B: `"Dame detalle de mi LOAN-0001"` $\rightarrow$ Executed **0 tools**, and the LLM output raw text: `get_loan_details(LOAN-0001)`.
* **Root Cause Analysis:** The routing policy relied on a naive lexical keyword search (`if "prestamo" in text or "credito" in text`). Omitting the noun "prestamo" caused `requires_account_data` to evaluate to `False`. The LLM received `tool_choice="auto"` without mandatory allowlisting. Instead of calling the API, the model hallucinated the function invocation signature as plain text (*pseudo-tool-call*), causing an *abstraction leak* to the end user.
* **Architectural Resolution:**
  1. **Canonical Entity Extraction:** Refactored `knowledge_routing.py` to use deterministic regex boundary matching (`\bLOAN-[0-9]{4}\b`), making loan identification orthogonal to conversational syntax.
  2. **Deterministic Short-Circuit:** When an explicit entity is present and the allowlist contains a single read tool, the orchestrator invokes the tool deterministically against the Core Banking API without risking LLM non-determinism.
  3. **Metamorphic Testing Suite:** Built `ai/agent/tests/unit/routing/test_intent_robustness.py` with parameterized metamorphic relations over 7 linguistic variations, asserting that invariant behavior is maintained across all paraphrases.

### Case 3: App Configuration Key Vault Reference URI Parsing Fault
* **Symptom:** When resolving Key Vault references in Azure App Configuration payloads (`{"uri": "https://aegisbank-kv.vault.azure.net/secrets/db-password"}`), local integration tests threw invalid URI format errors.
* **Root Cause Analysis:** The reference resolver assumed standard HTTP URL formatting and failed when optional version suffixes (`/secrets/{name}/{version}`) or trailing slashes were present, resulting in unhandled string slicing exceptions in the secret provider adapter.
* **Architectural Resolution:** Implemented RFC 3986 compliant URI parsing with strict schema validation (`https://`), domain verification (`*.vault.azure.net`), and regex validation of secret identifiers (`^[a-zA-Z0-9-]+$`). Handled versioned and unversioned references gracefully with fallback to default synthetic secret stores in test environments.

---

## 4. Scientific Evaluation & MLOps Governance (v0.15)

Moving beyond subjective qualitative evaluation ("it looks good to me"), AegisBank incorporates a formal evaluation harness (`ml/evaluation`):

| Evaluation Dimension | Metric / Method | Invariant / Target |
|---|---|---|
| **Groundedness** | Token overlap & factual citation alignment | 100% on held-out compliance set |
| **Abstention** | Knowledge gap detection rate | 100% refusal on out-of-domain queries |
| **Ownership Isolation** | Tenant boundary verification | 0% cross-customer data leakage |
| **Tool Calling Accuracy** | Exact match on tool name & arguments | $\ge 95\%$ across test corpus |
| **Calibration Analysis** | Brier Score & Expected Calibration Error (ECE) | Brier $\le 0.15$, monotonic reliability curve |
| **Statistical Rigor** | Two-sample proportion test & Wilson 95% CI | Explicit reporting of p-values; no false claims of significance when $p > 0.05$ |
| **Distribution Drift** | Population Stability Index (PSI) | Tracking Data Drift, Prediction Drift, and Performance Drift |

MLflow (`mlflow==3.16.0`) tracks evaluation runs against local SQLite storage, persisting metrics, parameters, and confusion matrices as verifiable artifacts without external SaaS dependencies.

---

## 5. Laboratory SLI/SLO vs. Production SLA Benchmarks

AegisBank distinguishes between **laboratory measurements** and **production SLAs**:

* **Observed Laboratory Performance (`scripts/performance_baseline.py`, 25 iterations):**
  - `/health/live`: Mean: `1.23 ms`, p50: `1.20 ms`, p95: `1.92 ms`, p99: `4.17 ms`, Error Rate: `0.0%`.
  - `/api/v1/loans/LOAN-0001`: Mean: `2.32 ms`, p50: `2.15 ms`, p95: `3.00 ms`, p99: `7.55 ms`, Error Rate: `0.0%`.
* **Explicit Boundary:** These numbers reflect in-process synthetic execution. They do **not** constitute a production capacity SLA, high-concurrency stress test (>10,000 req/sec), or WAN latency guarantee.

---

## 6. Honest Capability Maturity Matrix (v1.0.0)

| Layer | Component | Status | Verification Evidence |
|---|---|---|---|
| **Agent Core** | Orchestrator, Prompts, Routing | `TESTED-LOCAL` | 248 passed tests in `ai/agent/tests` |
| **Security** | Ownership, Redaction, Threat Model | `TESTED-LOCAL` | Invariant tests, STRIDE threat model |
| **Safety** | HITL State Machine, HOTL Kill-Switch | `TESTED-LOCAL` | `test_mcp_hitl_acceptance.py`, `test_hotl_kill_switch.py` |
| **Reliability** | Idempotency, Retry, Circuit Breaker | `TESTED-LOCAL` | `test_idempotency.py`, `test_circuit_breaker.py` |
| **Messaging** | Transactional Outbox, DLQ | `TESTED-LOCAL` | `test_outbox.py`, `test_consumer_dlq.py` |
| **Data Stores** | PostgreSQL + pgvector, Redis OSS 8 | `TESTED-LOCAL` | Docker Compose, HNSW index tests |
| **Serverless** | Functions Host on Linux Container | `TESTED-LOCAL` | `test_functions_runtime_e2e.py` (v0.13.1) |
| **Serverless** | Functions Host on Windows Native | `BLOCKED` | Diagnosed Win32 `cygrpc` path limit (`ERROR_FILENAME_EXCED_RANGE`) |
| **Cloud Infra** | Azure Key Vault, Entra ID Managed Identity | `CLOUD-PENDING` | Local synthetic mocks verified; no cloud billing |
| **Production** | Multi-region HA, High TPS, Certifications | `PROD-UNPROVEN` | Intentionally excluded from educational lab |

---

## 7. High-Yield Interview Speaking Points & Defense

### Q: "How do you protect your agent against prompt injection and jailbreaking?"
> *"In financial services, prompt filtering alone is insufficient because adversarial prompts evolve constantly. We employ defense-in-depth:  
> First, prompt hardening and system-level boundaries.  
> Second, and most importantly, **deterministic architectural controls**: the LLM operates with read-only tools by default. Even if an attacker completely hijacks the model's output via indirect prompt injection, the model cannot execute a transfer or dispute. Every state-changing action requires an explicit `ApprovalRequest` validated against a cryptographic SHA-256 payload digest, bound to the authenticated customer ID, and requiring out-of-band human sign-off. The attack surface is constrained by code, not prompt compliance."*

### Q: "Why use the Transactional Outbox pattern when Azure Service Bus has built-in duplicate detection?"
> *"Service Bus duplicate detection only works if the message actually reaches the broker. If your application writes to the database and then experiences a network timeout, socket drop, or process crash before publishing to Service Bus, your database state is updated but downstream systems never receive the event.  
> By writing the event to an `outbox_events` table within the same SQL transaction as the business entity, we guarantee atomic persistence. A background publisher or CDC process then drains the outbox to Service Bus with bounded retries. Service Bus handles broker-level deduplication, but the Outbox pattern guarantees the event is never lost at the producer boundary."*

### Q: "How do you know whether an agent prompt or model change is ready for deployment?"
> *"We do not rely on subjective inspection or manual chat testing. We maintain a frozen holdout evaluation suite (`v015_eval_suite.jsonl`) spanning grounded questions, knowledge gaps, and adversarial probes.  
> Our automated evaluation gate runs candidate traces against baseline traces across 10 deterministic dimensions. We compute Wilson confidence intervals, Brier calibration scores, and two-sample proportion tests. If a candidate claims a +5% accuracy increase but the p-value is 0.31, we reject the claim as statistically insignificant random variation. Only models passing zero-regression safety invariant gates are approved."*
