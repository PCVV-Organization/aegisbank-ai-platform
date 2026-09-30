# AegisBank AI Platform — AI Evaluation Taxonomy & Measurement Architecture

> **Architecture Standard:** Capability-Centric Evaluation vs. Milestone Provenance  
> **Target Alignment:** Microsoft AI Foundry / Azure AI Studio Evaluation Frameworks, MLflow Tracking, and Banking Risk Governance (SR 11-7).  
> **Key Catalog:** [EVALUATION-CATALOG.md](EVALUATION-CATALOG.md) (Complete inventory of evaluation runs, holdouts, runners, and artifacts).

---

## 1. Core Principle: Provenance vs. Measurement

A common anti-pattern in emerging AI projects is conflating the **version or milestone** with the **metric** (e.g., claiming *"we evaluate according to v0.12"*).

In AegisBank:
* **A Metric** evaluates a specific mathematical or behavioral dimension of an AI capability (e.g., *nDCG@5* for retrieval ranking, *Brier score* for probability calibration, *Ownership Isolation Rate* for multi-tenant safety).
* **A Version/Milestone (`v0.x`, `v1.x`)** designates **experiment provenance**: the point in time, git commit, runtime environment, and dataset snapshot where a specific benchmark run was executed and recorded.

Milestone numbers never substitute for scientific measurement definitions.

---

## 2. Capability-Based Evaluation Taxonomy

Following the evaluation taxonomy standard of Microsoft AI Foundry and MLflow, AegisBank decomposes system measurement into **7 orthogonal capability layers**:

```
                              AI EVALUATION TAXONOMY
                                         │
 ┌───────────────┬───────────────┬───────┴───────┬───────────────┬───────────────┐
 │               │               │               │               │               │
 ▼               ▼               ▼               ▼               ▼               ▼
1. Intent/ML    2. Retrieval    3. Generation   4. Agent        5. Safety       6. System E2E  &  7. Performance
- Accuracy      - Precision@K   - Groundedness  - Intent Res.   - Ownership     - 8 Journeys      - p50/p95/p99
- Macro-F1      - Recall@K      - Relevance     - Tool Select.  - HITL State    - Outbox/DLQ      - Error Rate
- Brier Score   - MRR           - Citations     - Input Acc.    - No-Write      - Replay Guard    - Concurrency
- ECE           - nDCG@K        - Abstention    - Task Compl.   - Idempotency
```

---

### Layer 1: Intent Classification & Machine Learning Foundations
* **Evaluates:** Classical NLP and discriminatory classification before delegating to generative models.
* **Core Metrics:**
  - **Accuracy & Macro-F1:** Balanced evaluation across classes without majority-class distortion.
  - **Brier Score (Multiclass):** Mean squared difference between predicted probability vectors and one-hot ground truth labels.
  - **Expected Calibration Error (ECE):** Agreement between model confidence bins and empirical accuracy.
  - **Data/Prediction Drift (PSI):** Population Stability Index across categorical intent distributions (10 bins).
* **Primary Provenance:** `v0.3` ([v0.3-intent-classification-baseline.md](../../history/experiments/v0.3-intent-classification-baseline.md)).

### Layer 2: Retrieval (Information Retrieval / RAG Knowledge Search)
* **Evaluates:** The ability to retrieve authorized policy chunks given natural language queries in Spanish banking domain.
* **Core Metrics:**
  - **Precision@K & Recall@K:** Proportion of retrieved chunks that are relevant, and proportion of total relevant chunks successfully found.
  - **Mean Reciprocal Rank (MRR):** Reciprocal rank of the first relevant chunk ($1/\text{rank}_1$).
  - **Normalized Discounted Cumulative Gain (nDCG@K):** Graded relevance ranking quality with logarithmic position discounting.
  - **Query Execution Cost:** Database query plans (`EXPLAIN ANALYZE`), shared buffer hits, and latency comparisons (HNSW vs. IVFFlat in pgvector).
* **Primary Provenance:** `v0.4` (TF-IDF vs. SVD vs. RRF) and `v0.12` ([v012_retrieval_comparison.json](../../history/evaluation/v012_retrieval_comparison.json), [v012-pgvector-query-plans.json](../../history/evaluation/v012-pgvector-query-plans.json)).

### Layer 3: Grounded Generation & Citation Integrity
* **Evaluates:** Generative response synthesis strictly from active retrieved context without external hallucination.
* **Core Metrics:**
  - **Groundedness / Faithfulness:** Percentage of claims in the generated answer supported by active retrieved context.
  - **Relevance:** Semantic alignment of the answer with the user's intent.
  - **Citation Precision & Recall:** Exactness of referenced chunk digests (`chk__<doc>__<ver>__c<idx>_<hash>`).
  - **Abstention Rate on Unanswerable Queries:** Deterministic refusal when retrieved context lacks relevant information (*I do not know*).
* **Primary Provenance:** `v0.5` ([v0.5-grounded-generation-evaluation.md](../../history/experiments/v0.5-grounded-generation-evaluation.md)).

### Layer 4: Agent Multi-Turn Trajectories & Tool Execution
* **Evaluates:** Orchestrator decision-making, tool routing, argument synthesis, and goal completion across conversation turns.
* **Core Metrics:**
  - **Intent Resolution Rate:** Correct routing to Core Banking, RAG Knowledge, or Abstention paths.
  - **Tool Selection Accuracy:** Precision and recall in selecting the correct tool from the registered MCP catalog.
  - **Tool Input Accuracy:** Exact parameter schema compliance (e.g., extracting `loan_id="LOAN-0001"` without hallucinating parameters).
  - **Tool Output Utilization:** Whether the model incorporated tool execution results into the final customer response.
  - **Tool Call Success Rate:** Percentage of tool executions that returned success without exception or schema error.
  - **Task Completion:** Successful multi-turn resolution of the user's ultimate request.
* **Primary Provenance:** `v0.6` ([v0.6.1-native-tool-calling.md](../../history/experiments/v0.6.1-native-tool-calling.md)) and `v0.15` ([v015-ai-evaluation-mlops.md](v015-ai-evaluation-mlops.md)).

### Layer 5: Safety & Regulatory Invariants
* **Evaluates:** Deterministic enforcement of banking risk boundaries and security controls.
* **Core Metrics:**
  - **Ownership Isolation Rate (100% invariant):** Rejection of any tool call attempting cross-customer access (`customer_id` mismatch).
  - **No-Write Direct Mutation Rate (0% invariant):** Verification that the agent NEVER executes direct state mutations on write endpoints; all writes must produce an `ApprovalRequest` proposal.
  - **HITL State Machine Compliance:** Correct lifecycle progression (`PENDING` $\rightarrow$ `APPROVED` $\rightarrow$ `EXECUTED` or `REJECTED`).
  - **Idempotency Replay Protection:** Re-submitting the same proposal digest or CloudEvent message must return cached/duplicate status without duplicate DB mutation.
  - **HOTL Kill-Switch Responsiveness:** Immediate blocking of all write proposals when the master supervisor flag is tripped.
* **Primary Provenance:** `v0.7` ([v0.7.0-mcp-hitl.md](../../history/experiments/v0.7.0-mcp-hitl.md)), `v0.15` ([v015-ai-evaluation-mlops.md](v015-ai-evaluation-mlops.md)), and `v1.0` ([V1.0-THREAT-MODEL.md](../security/V1.0-THREAT-MODEL.md)).

### Layer 6: System End-to-End (E2E) Integration
* **Evaluates:** Holistic behavior across the complete distributed stack: Agent $\rightarrow$ MCP Tools $\rightarrow$ Core Banking DB $\rightarrow$ Outbox $\rightarrow$ Functions Host / Event Grid $\rightarrow$ OpenTelemetry.
* **Core Metrics:**
  - **8 Critical Banking Journeys Pass Rate (100%):** Journeys A through H covering inquiries, payments, disputes, out-of-domain queries, and tamper attacks.
  - **Distributed Context Preservation:** 100% propagation of W3C `traceparent` across process and container boundaries.
  - **Audit Log Completeness:** Non-repudiation event generation with PII redaction and cryptographic digest validation.
* **Primary Provenance:** `v1.0` ([E2E-MATRIX.md](../quality/E2E-MATRIX.md), [PORTFOLIO-INTERVIEW-EVIDENCE.md](../releases/PORTFOLIO-INTERVIEW-EVIDENCE.md)).

### Layer 7: Operational Performance & Error Budgets
* **Evaluates:** Execution latency, concurrency limits, resource consumption, and reliability under load.
* **Core Metrics:**
  - **Latency Percentiles (p50, p95, p99):** Wall-clock duration per end-to-end journey.
  - **Failure & Error Rates:** Percentage of requests returning HTTP 5xx or unhandled exceptions.
  - **SLI/SLO Compliance:** Comparison against lab target service levels.
* **Primary Provenance:** `v1.0` ([V1.0-PERFORMANCE-EVIDENCE.md](../../history/quality/V1.0-PERFORMANCE-EVIDENCE.md), [V1.0-SLI-SLO-LAB-REPORT.md](../../history/quality/V1.0-SLI-SLO-LAB-REPORT.md)).

---

## 3. Milestone Mapping (Provenance Matrix)

How platform development milestones map to the capability layers:

| Milestone | Target Capability Layer | Primary Artifact | Runner Command |
|---|---|---|---|
| `v0.3` | **1. Intent / ML** | `ml/intent-classifier/reports/baseline-metrics.json` | `python -m ml_intent.cli evaluate` |
| `v0.4` | **2. Retrieval (Lexical/RRF)** | `ai/rag/reports/retrieval-metrics.json` | `python -m aegisbank_rag.cli evaluate` |
| `v0.5` | **3. Generation (Groundedness)** | `history/experiments/v0.5-grounded-generation-evaluation.md` | Deterministic suite |
| `v0.12` | **2. Retrieval + Vector Indexing** | [v012_retrieval_comparison.json](../../history/evaluation/v012_retrieval_comparison.json), [v012-pgvector-query-plans.json](../../history/evaluation/v012-pgvector-query-plans.json) | `python scripts/evaluate_retrievers_v012.py` |
| `v0.15` | **4. Agent + 5. Safety + MLOps** | [v015-ai-evaluation-mlops.md](v015-ai-evaluation-mlops.md), `reports/v015-evaluation-report.json` | `python scripts/evaluation_gate.py` |
| `v1.0` | **6. System E2E + 7. Performance** | [V1.0-PERFORMANCE-EVIDENCE.md](../../history/quality/V1.0-PERFORMANCE-EVIDENCE.md), [E2E-MATRIX.md](../quality/E2E-MATRIX.md) | `python scripts/performance_baseline.py` |

---

## 4. Statistical Rigor in Candidate Promotion

In enterprise MLOps, observed gains must be tested for statistical validity before promoting a candidate:

1. **Paired Statistical Test:** When evaluating candidate vs. baseline accuracy over identical synthetic queries, we apply **McNemar's test** with Edwards continuity correction.
2. **Bootstrap Confidence Intervals:** 95% confidence intervals are computed via $B = 1000$ bootstrap resamples to assess estimation uncertainty.
3. **Effect Size (Cohen's $h$):** Reports practical effect magnitude for difference between proportions.
4. **Safety Regressions Override Gains:** Even if a candidate achieves higher aggregate accuracy, **any regression** in Ownership Isolation or No-Write Safety triggers an immediate hard gate rejection (`FAIL`).

For full details and individual run parameters, see [EVALUATION-CATALOG.md](EVALUATION-CATALOG.md).
