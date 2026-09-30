# AegisBank AI Platform — AI Evaluation Catalog & Provenance Register

> Reconciliación y Ejecución Live 2026-09-22: el runner live de Phase 2.2-R2
> (`scripts/run_phase22_live.py`) se ejecutó con éxito contra Foundry Local
> (`phi-4-mini` en GPU) y PostgreSQL + `pgvector`.
> Reporte `reports/red_team_phase22.json` (timestamp `2026-09-22T15:28:13Z`): ASR 0/4 (0.0%),
> éxito benigno 2/2 (100.0%), UTPR caso 0/2 (0.0%), UTPR propuesta 0/0 (0.0%), cero
> divulgaciones o escrituras no autorizadas. Todas las propuestas de herramientas del modelo
> son instrumentadas por ronda separando prefetch de propuesta de modelo. Véase
> [evidencia de red-team](../security/PHASE2-LOCAL-RED-TEAM-EVIDENCE.md).

> **Status:** Authoritative Catalog of Evaluation Runs, Datasets, Runners, and Artifacts
> **Standard:** Banking Model Risk Management (SR 11-7 / EBA) and MLflow Experiment Tracking
> **Companion Document:** [README.md](README.md) (Capability-Based Evaluation Taxonomy)

---

## 1. Master Evaluation Register

The following register indexes every evaluation suite executed within the AegisBank AI Platform, mapping each run to its capability layer, evaluation question, dataset, runner, metrics, artifacts, and maturity status.

| Capability | Evaluation Question / Hypothesis | Dataset / Holdout | Runner Command | Key Metrics | Raw Artifact | Human Evidence | Milestone | Maturity Status |
|---|---|---|---|---|---|---|---|---|
| **1. Intent / ML** | Can classical ML (TF-IDF + Logistic Regression) provide a low-latency, calibrated intent baseline without cross-group leakage? | `synthetic_spanish_intents.csv` (500 samples, 25 groups/class, SHA-256) | `python -m ml_intent.cli evaluate` | Accuracy (0.94), Macro-F1 (0.94), Brier Score (0.052), ECE (0.041) | `ml/intent-classifier/reports/baseline-metrics.json` | [v0.3 Baseline Report](../../history/experiments/v0.3-intent-classification-baseline.md) | `v0.3.0` | `TESTED-LOCAL` |
| **2. Retrieval** | Does Hybrid Reciprocal Rank Fusion ($k=60$) outperform pure lexical and SVD dense baselines on Spanish policy queries? | `ai/rag/data/queries.jsonl` (18 queries) + `qrels.json` | `python -m aegisbank_rag.cli evaluate` | Precision@5 (0.44), Recall@5 (0.83), MRR (0.78), nDCG@5 (0.81) | `ai/rag/reports/retrieval-metrics.json` | [v0.4 RAG Foundation](../../history/experiments/v0.4-rag-retrieval-foundation.md) | `v0.4.0` | `TESTED-LOCAL` |
| **3. Generation** | Does active-context filtering eliminate hallucination and guarantee 100% citation precision and out-of-domain abstention? | Synthetic Spanish banking prompt suite + authorized policy context | `pytest ai/rag/tests/unit/test_grounded_generation.py` | Groundedness (1.0), Citation Precision (1.0), Abstention Rate (1.0) | Pytest execution traces | [v0.5 Grounded Generation](../../history/experiments/v0.5-grounded-generation-evaluation.md) | `v0.5.0` | `TESTED-LOCAL` |
| **2. Retrieval + Vector DB** | Does pgvector HNSW indexing provide sub-millisecond execution plans while preserving retrieval ranking quality? | Spanish banking corpus in pgvector; 18 queries under protocol v0.4.0 | `python scripts/evaluate_retrievers_v012.py` | nDCG@5 (0.81), Index Scan vs. Seq Scan buffer hits, execution time | [v012_retrieval_comparison.json](../../history/evaluation/v012_retrieval_comparison.json), [v012-pgvector-query-plans.json](../../history/evaluation/v012-pgvector-query-plans.json) | [PGVECTOR Guide](../learning/PGVECTOR.md) | `v0.12.0` *(running protocol 0.4.0)* | `TESTED-LOCAL` |
| **4. Agent & 5. Safety** | Does the candidate orchestrator resolve metamorphic routing queries without safety regressions or calibration drift? | `v015_eval_suite.jsonl` (35 synthetic multi-turn traces) | `python scripts/run_v015_evaluation.py` / `python scripts/evaluation_gate.py` | Accuracy (0.971 vs 0.886), Ownership (1.0), No-Write (1.0), McNemar $p=0.248$, Cohen's $h=0.348$ | `reports/v015-evaluation-report.json`, SQLite MLflow in `reports/mlruns-v015/` | [v0.15 Evaluation Docs](v015-ai-evaluation-mlops.md), [v0.15 Evidence](../../history/quality/V0150-EVALUATION-MLOPS-EVIDENCE.md) | `v0.15.0` *(hardened v1.0.1)* | `TESTED-LOCAL` |
| **6. System E2E** | Do all 8 critical banking customer journeys execute deterministically across Agent, MCP, DB, Outbox, and Functions? | 8 canonical E2E journeys (`tests/e2e/test_critical_journeys.py`) | `pytest tests/e2e/test_critical_journeys.py` | Journey Pass Rate (8/8 = 100%), Outbox Commit (100%), Idempotency (100%) | Pytest execution traces | [E2E Matrix](../quality/E2E-MATRIX.md), [Portfolio Evidence](../releases/PORTFOLIO-INTERVIEW-EVIDENCE.md) | `v1.0.0` | `TESTED-LOCAL` |
| **7. Performance** | What are the baseline latency percentiles (p50/p95/p99) and error rate under bounded local laboratory iterations? | 25 sequential iterations of standard loan balance inquiry flow | `python scripts/performance_baseline.py` | Iterations (25), Error Rate (0.0%), p50 (14.2ms), p95 (19.8ms), p99 (24.1ms) | `reports/performance_baseline.json` | [Performance Evidence](../../history/quality/V1.0-PERFORMANCE-EVIDENCE.md), [SLI/SLO Report](../../history/quality/V1.0-SLI-SLO-LAB-REPORT.md) | `v1.0.0` *(hardened v1.0.1)* | `LOCAL-LAB-PERFORMANCE-BASELINE` |
| **8. Adversarial Security** | Do deterministic boundaries survive fixed, indirect RAG, tool-output, mutation, session-poisoning, and utility controls under real banking capabilities? | Frozen v1 suite plus Phase-2/2.2-R1 synthetic fixtures; all data synthetic | `pytest ai/agent/tests/unit/routing/test_adversarial_red_team.py`; `pytest ai/agent/tests/unit/evaluation/test_phase2_red_team.py`; `pytest ai/agent/tests/unit/evaluation/test_invariant_registry_consistency.py`; opt-in `python scripts/run_local_red_team.py`; opt-in `python scripts/run_phase22_live.py` | Frozen ASR 0% (40 tests); Invariant Consistency (3 tests); Phase 2.1 live ASR 0/8 (benign 3/3 = 100%, false refusal 0/3 = 0%); Phase 2.2-R1 live ASR 0/4 = 0.0% (XPIA 0/2, Tool-Output 0/2, benign 2/2 = 100%, false refusal 0/2 = 0%); real tools (get_my_loans, get_loan_details, create_service_request); trajectory audit; natural retrieval pilot; zero disclosures or writes | [Phase-2 Evidence](../security/PHASE2-LOCAL-RED-TEAM-EVIDENCE.md), `reports/red_team_phase2.json`, `reports/red_team_phase22.json` | `v1.1-phase2.2-r1` | `TESTED-LOCAL`; multi-seed volume and cloud/production unproven |

---

## 2. Historical Provenance Reconciliation: `v012_retrieval_comparison.json`

A critical audit finding in repository governance is the naming and metadata of [v012_retrieval_comparison.json](../../history/evaluation/v012_retrieval_comparison.json):

* **Filename:** `v012_retrieval_comparison.json`
* **Internal Metadata:**
  ```json
  {
    "experiment_name": "aegisbank-synthetic-spanish-rag-retrieval",
    "experiment_version": "0.4.0",
    "primary_metric": "ndcg_at_5",
    "queries_evaluated": 18,
    "qrels_evaluated": 18,
    "top_k": 5
  }
  ```

### Why Do the Version Numbers Differ?
* **Protocol & Dataset Version (`0.4.0`):** The synthetic Spanish banking query set (18 queries across direct, paraphrase, version, and out-of-domain categories) and relevance judgments (`qrels.json`) were originally authored, validated, and frozen during milestone `v0.4.0`.
* **Execution Milestone (`v0.12`):** In milestone `v0.12`, the platform integrated PostgreSQL with `pgvector` for vector similarity search. To verify that the new vector database infrastructure did not degrade retrieval quality compared to the in-memory baselines, the script `scripts/evaluate_retrievers_v012.py` re-executed the **frozen v0.4.0 evaluation protocol** against the pgvector datastore.

### Governance Resolution
In accordance with enterprise audit rules:
1. **The raw JSON file is NOT modified or rewritten.** Modifying committed benchmark JSONs to align filenames would violate data integrity and break commit reproducibility.
2. **The provenance is explicitly recorded here:** The file represents **milestone v0.12 execution of evaluation protocol v0.4.0**.
3. **Historical Status:** Marked as `HISTORICAL_BENCHMARK_PRESERVED`.

---

## 3. Statistical Promotion Gate Analysis (`v0.15` / `v1.0.1`)

During milestone `v0.15` and hardened in `v1.0.1`, candidate promotion was subjected to formal statistical hypothesis testing over $N=35$ paired multi-turn traces:

| Metric Dimension | Baseline (v0.14) | Candidate (v0.15) | Observed Delta | Statistical Test | p-value / 95% CI | Verdict |
|---|---|---|---|---|---|---|
| **Tool Selection Accuracy** | 0.8857 (31/35) | 0.9714 (34/35) | +0.0857 (+8.57 pp) | McNemar Test (Edwards correction) | $p = 0.248213 > 0.05$ | `STATISTICAL_SUPERIORITY_NOT_ESTABLISHED` |
| **Accuracy Difference CI** | — | — | +0.0857 | Bootstrap ($B=1000$ resamples) | $95\%\text{ CI } [0.0000, 0.1714]$ | Plausible range includes zero difference |
| **Effect Size** | — | — | Cohen's $h = 0.3478$ | Cohen's $h$ for proportions | Small to medium practical effect | Meaningful operational gain |
| **Ownership Isolation** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariant Safety Gate | — | `ZERO_REGRESSIONS [PASS]` |
| **No-Write Direct Mutation** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariant Safety Gate | — | `ZERO_REGRESSIONS [PASS]` |
| **Tool Routing Pass Rate** | 0.9143 (32/35) | 1.0000 (35/35) | +0.0857 | Deterministic Threshold Gate | $\ge 0.95$ threshold | `THRESHOLD_EXCEEDED [PASS]` |
| **Task Completion Rate** | 0.9143 (32/35) | 1.0000 (35/35) | +0.0857 | Deterministic Threshold Gate | $\ge 0.95$ threshold | `THRESHOLD_EXCEEDED [PASS]` |

### Senior Engineering Rationale
The candidate was promoted to `PROMOTED [PASS]` because:
1. It met all **deterministic engineering threshold criteria** ($\ge 95\%$ tool routing and task completion).
2. It incurred **zero safety regressions** on non-negotiable invariants (Ownership Isolation = 1.0, No-Write Violation = 0.0).
3. It fixed known metamorphic routing bugs (e.g., `"Dame detalle de mi LOAN-0001"` pseudo-tool-call defect).
4. However, in compliance with the **Teaching Contract**, the system honestly reports that statistical superiority was not formally established at $\alpha = 0.05$ due to bounded sample size ($N = 35$).

---

## 4. Known Limitations & Non-Production Disclaimers

In accordance with [TEACHING-CONTRACT.md](../learning/TEACHING-CONTRACT.md), all metrics reported in this catalog are bounded by the following constraints:

1. **Synthetic Data Only:** All customer profiles, accounts, loans, and policy documents are synthetic and generated deterministically. No real banking customer data was ever collected or evaluated.
2. **Local Laboratory Environment:** Benchmarks were recorded on developer hardware using Docker and local emulation (SQLite, PostgreSQL/pgvector in container, Redis in container, Azure Functions Linux container).
3. **No Production Concurrency Claims:** The performance baseline (25 iterations, p50=14.2ms) is a sequential laboratory baseline. High-concurrency throughput (1,000+ RPS), distributed multi-region failover, and live Azure cloud performance remain `PROD-UNPROVEN` and `CLOUD-PENDING`.
