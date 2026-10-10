# AI Components

AI-related code is organized by responsibility. The agent interprets requests and proposes bounded actions; deterministic policy and human approval govern consequential operations. Retrieval supplies context but does not authorize tool use. Classical ML experiments are maintained separately.

## Components

- [Agent](agent/README.md) — request orchestration, tools, and policy boundary
- [Retrieval-augmented generation](rag/README.md) — document ingestion, retrieval, and grounded context
- [Intent classifier](../ml/intent-classifier/src/aegisbank_intent_classifier/README.md) — separate ML experiment

## Change guidance

Read [canonical components](../docs/architecture/CANONICAL-COMPONENTS.md) before adding a parallel implementation. Use synthetic data only and consult the project [AGENTS.md](../AGENTS.md) before code changes.
