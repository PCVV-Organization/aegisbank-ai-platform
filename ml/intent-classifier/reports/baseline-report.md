# v0.3 Intent Classification Baseline Report

## Scope

This is a reproducible classical ML baseline over a small synthetic Spanish corpus.
It is not evidence of production operation and does not authorize any banking action.

## Frozen Protocol

- Primary metric: `macro_f1`
- Random state: `42`
- Pipeline: word TF-IDF plus Logistic Regression
- Holdout evaluated once after configuration freeze
- Post-holdout tuning: none

## Dummy Baseline Holdout

| Metric | Value |
| --- | ---: |
| accuracy | 0.200000 |
| macro_precision | 0.040000 |
| macro_recall | 0.200000 |
| macro_f1 | 0.066667 |
| weighted_f1 | 0.066667 |

## TF-IDF + Logistic Regression Cross-validation

| Metric | Mean | Std |
| --- | ---: | ---: |
| accuracy | 0.997500 | 0.005000 |
| macro_precision | 0.997647 | 0.004706 |
| macro_recall | 0.997500 | 0.005000 |
| macro_f1 | 0.997498 | 0.005005 |
| weighted_f1 | 0.997498 | 0.005005 |

## Holdout Results

| Metric | Value |
| --- | ---: |
| accuracy | 1.000000 |
| macro_precision | 1.000000 |
| macro_recall | 1.000000 |
| macro_f1 | 1.000000 |
| weighted_f1 | 1.000000 |

## Per-class Results

| Label | Precision | Recall | F1 | Support |
| --- | ---: | ---: | ---: | ---: |
| informational | 1.000000 | 1.000000 | 1.000000 | 20 |
| account_query | 1.000000 | 1.000000 | 1.000000 | 20 |
| service_request | 1.000000 | 1.000000 | 1.000000 | 20 |
| sensitive_action | 1.000000 | 1.000000 | 1.000000 | 20 |
| unsupported | 1.000000 | 1.000000 | 1.000000 | 20 |

## Confusion Matrix

Label order: `informational`, `account_query`, `service_request`, `sensitive_action`, `unsupported`

```json
[[20, 0, 0, 0, 0], [0, 20, 0, 0, 0], [0, 0, 20, 0, 0], [0, 0, 0, 20, 0], [0, 0, 0, 0, 20]]
```

## Error Analysis

No holdout examples were misclassified. This result is likely influenced by
the balanced, template-generated corpus and must not be generalized to real
traffic.

## Limitations

The corpus is synthetic, balanced, small, predominantly Spanish, and generated from
controlled templates. It contains no production traffic or real customer behavior.
Generator artifacts and domain simplification can inflate apparent performance.
The probabilities exposed by Logistic Regression were not calibrated or interpreted
as confidence. No production suitability is claimed.
