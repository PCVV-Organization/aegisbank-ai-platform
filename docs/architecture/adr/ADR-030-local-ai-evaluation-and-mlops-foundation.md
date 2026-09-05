# ADR-030: Local AI Evaluation and MLOps Foundation

- Status: Accepted for v0.15.0 local laboratory scope
- Date: 2026-09-04

## Context

An agent portfolio needs evidence that behavior improves, not only that a
single journey works. Historical intent-classifier holdouts and v0.6 agent
cases are frozen evidence and must not be tuned against.

## Decision

Create a separate `ml/evaluation` package with a new v0.15 dataset. It scores
explicit agent traces deterministically across intent resolution, tool
selection/input, output utilization, call success, task completion, relevance,
groundedness, abstention, ownership, and no-write safety. The local evaluator
is conceptually aligned with Microsoft Foundry dimensions, but is not claimed
to be the hosted Foundry evaluator.

Runs use MLflow `3.16.0` with a local SQLite tracking backend and local
artifacts. A deterministic baseline/candidate fixture demonstrates the A/B
contract; production runs may replace fixture traces with real agent traces.
Wilson intervals, bootstrap confidence intervals, two-proportion tests,
Cohen's h, reliability analysis, Brier/ECE, and PSI drift are recorded.

Promotion fails on critical regressions or thresholds, especially ownership,
no-write safety, and tool routing. Azure ML, hosted MLflow, Foundry evaluators,
remote monitoring, and production drift pipelines remain `CLOUD-PENDING`.

## Consequences

- Evaluation becomes repeatable and reviewable as artifacts and MLflow runs.
- Statistical significance is reported separately from practical effect size.
- A candidate cannot be promoted merely because its aggregate average rises.
- The new dataset cannot silently alter historical holdout claims.
