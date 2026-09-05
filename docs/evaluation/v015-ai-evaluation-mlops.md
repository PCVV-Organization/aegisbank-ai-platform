# v0.15: AI Evaluation, Experimentation & MLOps

## Purpose

v0.15 measures agent behavior scientifically. It does not claim that local
evaluators are Microsoft's hosted Foundry evaluators. The evaluator consumes a
plain `EvaluationTrace`, so deterministic fixtures and real agent runs share
one contract.

## Vocabulary

- **Experiment:** a named question and fixed evaluation protocol.
- **Run:** one execution of a variant with parameters and metrics.
- **Artifact:** durable output such as JSON results, taxonomy, or a confusion matrix.
- **Baseline/candidate:** the current and proposed behavior under the same dataset.
- **A/B test:** compare variants without changing the dataset between runs.
- **Confidence interval:** plausible range for an estimated metric.
- **p-value:** evidence against equal performance under a stated null hypothesis.
- **Effect size:** practical magnitude, reported here as Cohen's h for proportions.
- **Calibration:** whether predicted confidence agrees with observed correctness.
- **Drift:** change from a frozen reference distribution.
- **Evaluation gate:** deterministic rule that blocks promotion on critical regressions.

## Reproducible Run

```powershell
$env:PYTHONPATH = "ml/evaluation/src"
python scripts/run_v015_evaluation.py
```

The command records baseline and candidate runs in a local MLflow SQLite
backend under `reports/mlruns-v015/`, writes
`reports/v015-evaluation-report.json`, and returns non-zero if the candidate
violates the gate. The synthetic traces include the regression
`Dame detalle de mi LOAN-0001` and equivalent paraphrases.

## Statistical Interpretation

The null hypothesis for a proportion comparison is equal baseline and
candidate rates. A low p-value is evidence against that hypothesis, but the
confidence interval and effect size determine whether the change is useful.
Small datasets can show a large observed gain without statistical significance.
No candidate is promoted from aggregate gain alone: ownership, no-write
safety, tool routing, and task completion must also pass their thresholds.

## Calibration and Drift

The classifier's historical holdout remains untouched. New reliability reports
use predicted probabilities and labels to calculate multiclass Brier score and
ECE. Drift uses PSI over synthetic categorical reference/current samples:
`DATA_DRIFT`, `PREDICTION_DRIFT`, and `MODEL_PERFORMANCE_DRIFT` are separate
measurements. Cloud monitoring and Azure ML tracking remain `CLOUD-PENDING`.
