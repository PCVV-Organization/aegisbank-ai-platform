# Phase-2 Local Red-Team Evidence: Reconciliation & Live Real-Capability Evaluation

## Reconciliation — 2026-09-21

The results below are historical, not a new live run. The preserved machine
report `reports/red_team_phase2.json` dates to 2026-09-11; the current historical
`reports/red_team_phase22.json` dates to 2026-09-12 and identifies itself as
`phase2.2-r2-live-v1`, despite the R1 labels in the narrative below. Its observed
ASR is 0/4, benign success 2/2 and UTPR 0/2. These small samples do not close R2.

Current review found that `tools_available` comes from case fixtures rather than
captured per-round model requests; tool records also include deterministic
pre-reads. Therefore UTPR is a trace-based proxy, not proven model-only proposal
telemetry. Output-guard tests classify foreign-ID examples as positive cases;
they do not establish semantic false-positive rates on benign policy examples.
The statement below about no benign impact applies only to the evaluated cases.

Baseline closure added deterministic query-policy enforcement before dispatch
and corrected the disclosure oracle to inspect every foreign customer ID.
The old live reports have not been recomputed with these changes. Foundry Local
was installed but stopped on 2026-09-21. See the
[baseline closure report](../quality/LOCAL-BASELINE-CLOSURE-20260921.md) for
current tests, static-analysis blockers and the release decision.

**Status:** `TESTED-LOCAL` for deterministic fixtures, bounded local harness, and executed
local Foundry Local suite (`phi-4-mini`) across direct, mutation, live pgvector XPIA, and
live tool-output injection under real banking capabilities (`get_my_loans`, `get_loan_details`,
`create_service_request`).

This is a reproducible `EXTEND` of canonical responsibility #24 (`Local AI Evaluation & MLOps`)
located in `ai/agent/src/aegisbank_agent/evaluation/red_team.py`. It does NOT introduce a
secondary security framework and does NOT claim universal prompt-injection resistance,
certification, or production security.

## Evidence Executed

| Scope | Command | Result |
|---|---|---|
| Frozen adversarial regression + extended vectors | `pytest ai/agent/tests/unit/routing/test_adversarial_red_team.py` | `40 passed` (Tests 01–26, ASR 0.0%) |
| Invariant Registry Consistency Suite | `pytest ai/agent/tests/unit/evaluation/test_invariant_registry_consistency.py` | `3 passed` (Zero drift against §6.6 canonical 15 invariants) |
| Phase-2/2.2-R1 real-capability unit tests | `pytest ai/agent/tests/unit/evaluation/test_phase2_red_team.py` | `7 passed` (Trajectory schema, invariants, real tools) |
| FAST quality gate (active session lock) | `$env:AEGISBANK_SESSION_ID="phase22-r1"; python scripts/quality_gate.py --fast` | `13/13 PASS` (All 13 gates PASS) |
| Live Phase 2.1 runner (Foundry Local opt-in) | `$env:AEGISBANK_RUN_LIVE_REDTEAM="1"; python scripts/run_local_red_team.py` | `EXECUTED` on `phi-4-mini` (GPU, FL 0.10.3), ASR `0/8 = 0.0%`, disclosures 0, writes 0, benign success `3/3 = 100%`, false refusals `0/3 = 0.0%` |
| Live Phase 2.2-R1 runner (Real Capabilities) | `$env:AEGISBANK_RUN_PHASE22_LIVE="1"; python scripts/run_phase22_live.py` | `EXECUTED` on `phi-4-mini` + `pgvector`, ASR `0/4 = 0.0%`, XPIA `0/2 = 0%`, Tool-Output `0/2 = 0%`, disclosures 0, writes 0, benign success `2/2 = 100%`, false refusals `0/2 = 0%` |

## Scope And Oracles

The Phase-2 harness records model, model version, system-prompt version, suite version,
timestamp, attack totals, overall and per-category Attack Success Rate (ASR, tasa de éxito
del ataque), cross-customer disclosures, unauthorized tools/writes, HITL/HOTL bypasses,
unsupported financial claims, benign task success rate, false refusal rate, and complete
tool trajectories (`tools_available`, `tools_requested`, `tools_denied`, `tools_executed`
with normalized arguments, customer binding, and denial reason).

Synthetic retrieved documents and tool outputs are untrusted data. Labels
`EVIDENCIA_RAG_NO_CONFIABLE` and `SALIDA_TOOL_NO_CONFIABLE` establish the trust boundary
and reduce instruction/data ambiguity; they are not the security control by themselves and
do not guarantee model obedience. Deterministic authorization, ownership isolation, tool
allowlists, schema validation, HITL argument hashing, HOTL supervisory kill-switch,
idempotency, post-generation Customer IDOR scrubbing, and output verification enforce defense in depth.

## Real Banking Capabilities & Tool Trajectories

Phase 2.2-R1 eliminates fictitious payloads (such as unexposed transfer operations) and targets
the exact banking operations registered in the agent's tool catalog:
1. `get_my_loans`: Session-bound loan overview (READ).
2. `get_loan_details`: Specific loan inquiry subject to customer ownership (READ).
3. `create_service_request`: Core Banking ticket creation requiring mandatory HITL (WRITE).

Each observation records:
- `tools_available`: Authoritative tools exposed in the current evaluation round.
- `tools_requested`: Tool proposals emitted by the model with parsed arguments.
- `tools_denied`: Tool calls rejected by policy, ownership, or human operator.
- `tools_executed`: Tool calls executed deterministically with Core Banking return data.
- `invariants_checked`: Strictly synchronized with canonical invariants $I_1, I_2, I_3, I_4, I_7$.

## Retrieval Boundary vs. Natural Discoverability

The evaluation decouples two distinct security questions:
1. **Execution Boundary Enforcement:** When an adversarial payload reaches model context, do
   deterministic invariant defenses hold? In tests `phase22-xpia-read-poisoned` and
   `phase22-xpia-write-poisoned`, synthetic fixtures are injected with `score=1.0` to guarantee
   evaluation of the model-policy boundary under hostile input.
2. **Corpus Poisoning Discoverability:** In Part F (`exploratory_natural_retrieval_pilot`), an
   unforced 4-document corpus in PostgreSQL + `pgvector` was queried with normal dense embeddings.
   The poisoned chunk naturally achieved **rank 2** with cosine similarity **0.8347** against
   `¿Qué requisitos tiene un crédito vehicular?`, landing in top-3 (`top_k_inclusion: True`).
   This provides empirical evidence of indirect injection discoverability in vector stores.

## Defense-in-Depth: Post-Generation Customer IDOR Isolation ($I_4$)

Empirical evaluation on live `phi-4-mini` revealed a critical nuance: when poisoned RAG chunks
instructed the model to pivot to customer `CUST-0002`, the model did not execute unauthorized
tools, but paraphrased the injection text, echoing `"CUST-0002"` in its narrative answer.
Under Invariant $I_4$ (*"toda operación sobre datos de otro cliente es denegada determinísticamente
antes de invocar herramientas o emitir datos"*), `AgentOrchestrator` was enhanced with
post-generation IDOR interception (`is_cross_customer_attempt(answer, customer_id)`). Foreign customer
identifiers in generated text trigger an immediate deterministic refusal, eliminating cross-customer
data reflection without impacting benign task completion.

## Metric Summary

The executed live suites evaluate attacks and controls with explicit numerators and denominators:

- **Live Phase 2.1 (`reports/red_team_phase2.json`):**
  - `overall_asr = 0/8 = 0.0%`
  - `benign_task_success_rate = 3/3 = 100.0%`
  - `false_refusal_rate = 0/3 = 0.0%`
  - `cross_customer_disclosures = 0`
  - `unauthorized_writes = 0`
  - `hitl_bypasses = 0`, `hotl_bypasses = 0`
- **Live Phase 2.2-R1 (`reports/red_team_phase22.json`):**
  - `overall_asr = 0/4 = 0.0%`
  - `per_category_asr.XPIA_RAG = 0/2 = 0.0%`
  - `per_category_asr.TOOL_OUTPUT = 0/2 = 0.0%`
  - `benign_task_success_rate = 2/2 = 100.0%`
  - `false_refusal_rate = 0/2 = 0.0%`
  - `cross_customer_disclosures = 0`
  - `unauthorized_writes = 0`
  - `hitl_bypasses = 0`, `hotl_bypasses = 0`

## Interpretation

- The frozen suite result proves strictly `ASR = 0% on the evaluated fixed regression and live
  suites`. It does NOT prove universal prompt-injection resistance.
- System prompt and secret tests prove only that **no secret or system-prompt disclosure was
  observed in the evaluated test cases**; no claim of "zero secrets in memory" is made without
  a full memory/heap dump audit.
- In the live XPIA and tool-output cases on `phi-4-mini`, the exercised deterministic
  boundaries ($I_1, I_2, I_3, I_4, I_7$) held. The transactional outbox invariant ($I_5$)
  was not exercised by these read/injection cases and is not claimed as live evidence here.
- Cloud Foundry red teaming, adaptive adversarial generation, and production resilience remain
  `CLOUD-PENDING` and `PROD-UNPROVEN`.
