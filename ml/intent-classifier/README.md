# AegisBank Intent Classification Baseline

## Purpose

This component evaluates whether a small classical ML pipeline can classify
synthetic Spanish banking queries before any later comparison with more complex
language systems. It is an educational baseline, not a production model, and it
is not integrated with the Core Banking Mock.

## Labels

- `informational`: general product or institutional information.
- `account_query`: information about a fictional customer's loan or installments.
- `service_request`: creation or tracking of a synthetic request or complaint.
- `sensitive_action`: an action that must not be automated by this classifier.
- `unsupported`: content outside the banking experiment's domain.

Classification as `sensitive_action` never authorizes or executes an action.

## Synthetic-data Warning

All 500 records are generated locally from controlled templates. The dataset
contains no real logs, chats, customers, financial records, private datasets, or
personal data. Its balanced and template-generated nature can inflate metrics.

## Dataset Generation

After setup, regenerate the byte-deterministic JSONL dataset and manifest:

```powershell
.venv\Scripts\python.exe -m aegisbank_intent_classifier.cli generate
```

The generator creates 25 template groups per label and four variations per group.
Twenty groups per class belong to TRAIN and five to HOLDOUT. The manifest records
the SHA-256 fingerprint without volatile timestamps.

## Evaluation Methodology

The experiment compares `DummyClassifier(strategy="most_frequent")` with one
`Pipeline` containing word TF-IDF and Logistic Regression. The primary metric is
macro-F1. Five-fold `StratifiedGroupKFold` cross-validation uses TRAIN only and
keeps every `template_group_id` wholly within one side of each fold.

The frozen configuration is evaluated once on HOLDOUT after dataset validation,
tests, CV behavior, and parameters are fixed. No hyperparameter search or
post-holdout tuning is permitted in `v0.3`.

## Setup

Use the repository's existing Python 3.14 virtual environment:

```powershell
Set-Location 'C:\aegisbank-ai-platform'
.venv\Scripts\python.exe -m pip install -e "ml/intent-classifier[dev]"
```

## Commands

```powershell
.venv\Scripts\python.exe -m aegisbank_intent_classifier.cli generate
.venv\Scripts\python.exe -m aegisbank_intent_classifier.cli validate
.venv\Scripts\python.exe -m aegisbank_intent_classifier.cli evaluate
.venv\Scripts\python.exe -m aegisbank_intent_classifier.cli predict "¿Cuándo vence mi próxima cuota?"
```

The `predict` command trains the small baseline from TRAIN each time. No binary
model is committed or loaded from an external source.

`evaluate` deterministically rewrites the canonical reports. The official `v0.3`
holdout was opened once after configuration freeze; any future invocation is a
reproducibility check and must never be used for post-holdout tuning.

## Results

The frozen experiment produced these observed results:

| Evaluation | Accuracy | Macro-F1 |
| --- | ---: | ---: |
| Dummy holdout | 0.200000 | 0.066667 |
| Model CV mean | 0.997500 | 0.997498 |
| Model CV std | 0.005000 | 0.005005 |
| Model holdout | 1.000000 | 1.000000 |

The holdout confusion matrix is diagonal with 20 examples per class and no
misclassifications. This near-perfect result likely reflects the balanced,
template-generated language. It is not evidence of performance on real users.
Full deterministic data are in `reports/baseline-metrics.json`; interpretation
and error analysis are in `reports/baseline-report.md`.

## Quality Checks

```powershell
.venv\Scripts\python.exe -m pytest ml/intent-classifier/tests
.venv\Scripts\python.exe -m ruff check services/mock-core-banking ml/intent-classifier
.venv\Scripts\python.exe -m ruff format --check services/mock-core-banking ml/intent-classifier
.venv\Scripts\python.exe -m compileall ml/intent-classifier/src
```

## Reproducibility

Generation, split assignment, cross-validation, Dummy baseline, and model
configuration use seed `42` where randomness exists. Tests compare regenerated
dataset bytes, group folds, TRAIN-only predictions, and deterministic metrics.
The dataset SHA-256 is
`db250b5993e892610d29a2cc53bdafcff08d085df29deecf9a53515a13308664`.

## Limitations

- Synthetic and template-generated corpus.
- Exactly balanced labels rather than real prevalence.
- Small sample and group counts.
- Predominantly Spanish language.
- No production traffic or real customer behavior.
- No probability calibration.
- No integration, action execution, or production suitability claim.
