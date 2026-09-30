# 05 - Success Criteria

| Field | Value |
| --- | --- |
| Project | AegisBank AI Platform |
| Milestone | `v0.1.0 - Project Charter` |
| Status | Ready for review |
| Target | Verifiable `v1.0` completion |

## Measurement Rules

AegisBank succeeds through reproducible evidence, not feature count or subjective
demo quality.

- Every criterion must identify its dataset, environment, command/run, artifact, and result.
- Safety invariants can be absolute before a statistical baseline exists.
- Quality, latency, reliability, and cost thresholds that depend on observed data
  remain `TBD after baseline` until the baseline process below is complete.
- Retrieval and generation are evaluated separately before an end-to-end RAG score is interpreted.
- A failed mandatory gate blocks release; it is not waived by a strong aggregate score.
- Planned behavior is never reported as passing behavior.
- Measurements use synthetic data and redact unnecessary content.

## Functional Correctness

| Criterion | Required evidence | v1.0 gate |
| --- | --- | --- |
| UC-001 product answer | E2E cases map material claims to eligible cited documents | Pass all critical cases; quality thresholds approved after baseline |
| UC-002 installment read | API/tool response matches deterministic fixtures and authorization policy | 100% of critical success and denial cases pass |
| UC-003 loan read | API/tool response matches deterministic fixtures without cross-customer disclosure | 100% of critical success and denial cases pass |
| UC-004 complaint write | Approved E2E flow creates one record and returns its stable ID | 100% of critical write-path cases pass |
| UC-005 abstention | Unanswerable/conflicting/obsolete/adversarial cases abstain or clarify correctly | Threshold `TBD after baseline`; zero policy-forced-answer violations |
| UC-006 degraded dependency | Fault-injection cases produce classified retry, circuit, and degraded outcomes | 100% of critical safety cases pass |
| Scope boundary | No transfer, payment, disbursement, credit decision, real-data, or autonomous-write path exists | Zero prohibited paths discovered |

## RAG Quality

### Required measures

- Retrieval relevance and ranked retrieval metrics appropriate to the labeled dataset.
- Recall and precision where ground-truth relevant passages exist.
- Groundedness/faithfulness of generated claims.
- Answer relevance and completeness.
- Citation precision, citation coverage, and source/version correctness.
- Correct abstention, false refusal, and unsupported-answer rates.
- Performance split by answerable, unanswerable, ambiguous, conflicting,
  obsolete-source, and adversarial subsets.

### Required evidence

- A versioned corpus with `document_id`, version, validity interval, status, and source.
- A versioned evaluation dataset separated from tuning examples.
- Retrieval evaluation independent of generation evaluation.
- Human-review rubric and machine evaluator version/configuration where used.
- Baseline, candidate, error analysis, and approved threshold record.
- Regression results in CI for the stable evaluation subset.

### Gates

- Answers blocked by policy or evidence rules have zero uncited authoritative claims in the critical evaluation set.
- Obsolete or unauthorized sources have zero acceptance as current evidence in the critical evaluation set.
- Every supported answer exposes source identity and version in the tested response contract.
- Numeric thresholds for relevance, groundedness, completeness, citations, and
  abstention are `TBD after baseline` and must be approved before the corresponding capability is release-ready.

## Agent Quality

| Measure | Method | Gate |
| --- | --- | --- |
| Intent resolution | Labeled synthetic conversation set | `TBD after baseline` by class; report macro and per-class metrics |
| Task completion | Scenario evaluator plus deterministic outcome checks | `TBD after baseline`; all critical safety scenarios pass |
| Task adherence | Policy/rubric evaluation | No prohibited action in critical suite |
| Tool selection | Expected-tool labels, including no-tool cases | `TBD after baseline`; 100% on critical write/no-write cases |
| Tool input accuracy | JSON Schema and semantic fixture checks | 100% schema validity; semantic threshold after baseline |
| Tool-call success | Integration result by dependency class | `TBD after baseline`; failures correctly classified |
| Tool-output utilization | Expected facts compared with response | `TBD after baseline`; no invented critical values |
| Policy compliance | Deterministic policy assertions | 100% of critical cases |
| HITL compliance | Negative and E2E write tests | 100%; zero unapproved writes |
| Authorization source | Architecture and negative tests | Zero decisions authorized solely by LLM output |

Agent evaluation must identify the agent, model, prompt, tool-contract, policy,
dataset, and evaluator versions used in each run.

## Security And Privacy

| Criterion | Required evidence | Gate |
| --- | --- | --- |
| Synthetic data only | Dataset provenance plus repository/fixture review | No known real personal or financial record |
| Secret hygiene | Secret scanning in local/CI workflow and `.gitignore` policy | Zero verified secrets in Git history or build artifacts |
| Deterministic authorization | Unit/integration/negative tests outside model prompts | 100% of critical authorization cases pass |
| HITL writes | Approval-state tests bound to actor/action/payload/expiry | Zero writes without valid approval |
| Least privilege | Tool/API scopes and negative cross-subject tests | Zero unauthorized reads/writes in critical suite |
| Prompt-injection resistance | Adversarial input and corpus cases | Zero policy/authorization bypass in critical suite; broader threshold after baseline |
| Data minimization | Log/audit/trace schema review and redaction tests | No secrets; no prohibited raw fields in sampled telemetry |
| Threat model | Versioned assets, actors, trust boundaries, threats, controls, and residual risks | Reviewed before cloud deployment and at `v1.0` |
| Dependency security | Locked dependencies, supported versions, and automated scanning | No unresolved critical issue; lower-severity policy documented later |
| Compliance claims | Documentation review | No unsupported legal, regulatory, or certification claim |

The project may state that it uses only synthetic data and follows selected
controls. It may not state that this proves compliance with Law N.° 29733, the
regulation of Law N.° 31814, SBS rules, or NIST AI RMF.

## Reliability

| Criterion | Required evidence | Gate |
| --- | --- | --- |
| Idempotent write | Concurrent and sequential replay tests using the same key | One business record and one stable ID per logical request |
| Idempotency conflict | Same key with materially different payload | Deterministic rejection; no second record |
| Retry classification | Unit and fault-injection tests by error class | Only approved transient failures retry |
| Retry bounds | Attempt/time budget assertions | No unbounded retry; configured maximum always enforced |
| Write retry safety | Timeout-before/after-persistence tests | No duplicate business record and unknown outcomes reconcile by key |
| Circuit breaker | State-transition and fail-fast tests | `CLOSED`, `OPEN`, and `HALF_OPEN` behavior passes |
| Persistent failure | Load/fault scenario | No retry storm in tested budget; calls fail fast while open |
| Event delivery | Integration tests for persistence/publication/replay | No lost logical event in tested recovery path; consumers tolerate redelivery |
| Graceful degradation | UC-006 E2E scenarios | Truthful status, no fabricated success, correlation ID returned |

Latency, throughput, availability, retry-count, timeout, and circuit thresholds
are `TBD after baseline`. They must be based on workload and failure-injection
measurements, then recorded as configuration and tests.

## Observability And Audit

- Every sampled E2E flow preserves one `correlation_id` across all implemented boundaries.
- Every distributed execution exposes a `trace_id` and correctly parented spans.
- Logs, metrics, traces, and audit events distinguish policy denial, validation
  failure, approval outcome, tool attempt, retry, circuit transition, persistence,
  event publication, and final response as applicable.
- An authorized reviewer can reconstruct UC-004 from proposal through final outcome
  using identifiers and hashes without requiring unrestricted prompt or payload capture.
- Telemetry redaction tests prove that configured secrets and prohibited fields are removed.
- Model, prompt, agent, policy, retrieval index, tool contract, and application
  versions are present where needed for reproducibility.
- Alert thresholds and retention targets are `TBD after baseline` and documented
  before `v0.9` deployment.

Mandatory gate: all critical E2E scenarios must be reconstructable from approved
telemetry/audit fields, with zero known secret exposure.

## Testing

| Layer | Minimum scope | Gate |
| --- | --- | --- |
| Unit | Domain rules, validation, policy, approval state, idempotency, retry decisions, circuit transitions | All tests pass |
| Integration | API/database, agent/tool, MCP/API, messaging, telemetry propagation | All mandatory tests pass in reproducible environment |
| Contract | OpenAPI, MCP schemas, event schemas, compatibility rules | No breaking mismatch in supported contracts |
| End-to-end | Six charter use cases, including negative and degraded paths | All critical scenarios pass |
| Evaluation | RAG, intent, agent, tool use, guardrails, abstention | Approved gates pass on versioned datasets |
| Security | Authorization, injection, secret, dependency, and data-leak checks | All critical checks pass |

Code coverage may be reported but is not a substitute for behavior and risk
coverage. A numeric coverage gate is `TBD after baseline`; that baseline begins in
`v0.2` and must exclude generated/vendor code while prioritizing critical branches.

## CI/CD

The final CI pipeline must run reproducible commands for:

- formatting/linting;
- static type checking;
- unit, integration, contract, E2E, and relevant evaluation suites;
- secret and dependency/security checks;
- container build and artifact metadata;
- infrastructure validation when IaC exists.

Mandatory jobs block merge/release on failure. Deployment cannot run when a
required gate fails. Environments, approvals, identities, artifacts, and rollback
behavior must be documented before cloud delivery. `v0.1` has no application
toolchain and therefore validates documentation and Git only.

## ML And MLOps

| Criterion | Required evidence | Gate |
| --- | --- | --- |
| Dataset versioning | Immutable identifier, schema, labels, provenance, split policy | Reproducible dataset materialization |
| ML baseline | TF-IDF + Logistic Regression run | Accuracy, macro/per-class precision, recall, F1, confusion matrix, latency, and seed recorded |
| Experiment tracking | Parameters, code/data version, environment, metrics, and artifacts | Independent rerun reproduces results within documented tolerance |
| Comparison | Baseline vs small Transformer vs LLM when authorized | Same held-out protocol; quality, latency, cost, determinism, maintenance, and failures reported |
| Selection | Decision record | Best-fit conclusion supported by evidence, not model novelty |
| Model lifecycle | Version, approval, rollback, monitoring plan | Required before a trained model routes application traffic |
| Drift/quality monitoring | Input/output and label-feedback plan using synthetic/approved data | Thresholds `TBD after baseline`; owner and response defined |

The project is successful even if the traditional baseline wins. Deep Learning is
included only when the experiment can produce a defensible conclusion.

## Documentation And Governance

`v1.0` requires:

- current README with implemented versus planned status;
- project charter and controlled scope;
- architecture diagrams and ADRs for material decisions;
- API, tool, event, and data contracts;
- setup, test, deployment, rollback, troubleshooting, and incident runbooks;
- RAG/agent evaluation datasets, rubrics, reports, and limitations;
- ML experiment report and model card when a model is selected;
- threat model and security assumptions;
- compliance reference documents and a control matrix that separates confirmed
  requirements, official guidance, project decisions, and assumptions;
- known risks, residual risks, debt, costs, and unsupported capabilities;
- evidence that links each Definition of Done item to a run or artifact.

All material claims must be traceable to implementation evidence or an official,
dated source. Documentation drift is a release defect.

## Portfolio Readiness

The portfolio is ready when an independent technical reviewer can, from the
repository and reproducible commands:

- understand the problem, users, scope, and non-goals in under 15 minutes;
- distinguish implemented, measured, planned, optional, and excluded capabilities;
- run the documented local happy path and critical tests without hidden global setup;
- inspect a grounded answer, an authorized read, an approved idempotent write, an abstention, and a degraded dependency case;
- follow one execution through contracts, audit, metrics, logs, and traces;
- reproduce the ML baseline and inspect RAG/agent evaluation results;
- understand why each major technology was selected through ADRs and evidence;
- see limitations and failed experiments without misleading claims;
- verify that no real banking data or secret is required.

Time-to-understand and setup-time targets are `TBD after an independent portfolio
review baseline`; the review protocol and findings must be recorded.

## Baseline And Threshold Procedure

For every criterion marked `TBD after baseline`:

1. Define the metric, direction, unit, evaluator, and failure semantics before running candidates.
2. Freeze and version representative development and held-out evaluation datasets.
3. Establish a naive or current-system baseline and record environment, seed, model, prompt, and dependency versions.
4. Run enough repetitions or samples to characterize variance where the component is nondeterministic.
5. Analyze errors by risk-relevant slice, not aggregate score alone.
6. Propose a threshold based on user harm, task requirements, baseline distribution, and acceptable regression budget.
7. Review and approve the threshold in a versioned decision record without tuning on the held-out set.
8. Add the stable subset and threshold to CI, with an explicit process for evaluator drift and intentional re-baselining.

A threshold cannot be lowered only because a candidate release failed it.

## Definition Of Done v1.0

`v1.0` is complete only when evidence confirms all of the following:

- RAG answers exclusively from authorized, effective sources and cites them.
- RAG abstains correctly when evidence is insufficient.
- Aegis reads authorized synthetic customer information through controlled tools.
- MCP tool contracts and authorization boundaries work as documented.
- Every write requires valid HITL approval and deterministic authorization.
- Repeated writes with one idempotency key do not duplicate the business record.
- Bounded retry handles only known transient failures.
- Circuit breaker handles persistent failures and exposes its state operationally.
- Messaging recovers without duplicating the complaint business effect.
- Audit, correlation, and trace evidence reconstruct critical executions.
- No known secret is in Git and prohibited sensitive content is absent from sampled telemetry.
- Unit, integration, contract, E2E, security, and AI evaluation gates pass.
- CI blocks mandatory failures and Docker runs the validated solution.
- The authorized Azure architecture is implemented or explicitly validated according to the approved `v0.9` plan.
- OpenTelemetry, threat model, control matrix, runbooks, README, ADRs, and measured portfolio results are current.

When every item passes, feature development stops. Optional AKS or multi-agent
experiments require separate approval after `v1.0`.

## v0.1.0 Milestone Success

The charter milestone itself is complete when:

- the five required charter documents exist and cross-reference a consistent boundary;
- README states what exists and does not present roadmap features as implemented;
- AGENTS.md preserves permanent operating rules without duplicating the master prompt;
- `.gitignore` protects local secrets and common generated artifacts;
- no application code, dependency, cloud resource, or later-phase scaffold was introduced;
- official source claims have a dated reference baseline;
- `git diff --check` succeeds;
- Git status and the final project tree are reported;
- a local commit is created only if Git identity already exists and only intended files are staged.
