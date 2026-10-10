# Machine Learning

Classical ML experiments are separate from the LLM agent and its deterministic policy layer. A model prediction is not authorization, identity verification, or a credit decision.

## Components

- [Intent classifier](intent-classifier/src/aegisbank_intent_classifier/README.md) — bounded intent-classification experiment

## Change guidance

Use synthetic, reproducible data. Keep training, development, and held-out evaluation data separate; do not tune against holdouts. Report measured results and limitations. See the project [README](../README.md), [maturity matrix](../docs/requirements/V1.0-MATURITY-MATRIX.md), and [evaluation catalog](../docs/evaluation/EVALUATION-CATALOG.md).
