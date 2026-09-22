# AegisBank RAG

## Current scope and historical baselines

The platform now integrates this component with the agent and includes pgvector
and Redis retrieval adapters. See the [platform README](../../README.md),
[canonical components](../../docs/architecture/CANONICAL-COMPONENTS.md), and
[evaluation catalog](../../docs/evaluation/EVALUATION-CATALOG.md).

The sections below describe the **v0.4/v0.5 baseline**. Their integration
exclusions and measured results apply to that experiment, not the current
platform as a whole. Setup and CLI examples are run from the application root.

## Historical v0.4/v0.5 baseline

Local retrieval baseline plus the provider-neutral candidate implementation
for `v0.5.0 - Grounded Generation & LLM Evaluation`.

> `v0.4` retrieval is complete and frozen. `v0.5` has a measured Foundry Local
> baseline over six held-out cases. No Azure resource, cloud cost, agent, MCP,
> HITL, tool, or Core Banking integration is included.

## What It Is

A frozen lexical plus dense-local retrieval pipeline over a synthetic banking
corpus. The dense baseline is TF-IDF reduced with TruncatedSVD (LSA). The
hybrid ranker fuses both signals with Reciprocal Rank Fusion (RRF). The
pipeline is reproducible by seed, the corpus is versioned, and the evaluation
dataset provides offline metrics.

The retrieval component provides a measurable reference before any external
search deployment. The grounded-generation candidate adds deterministic
context and output controls without selecting or calling an LLM vendor.

## Why Not Azure AI Search Yet

Azure AI Search embeddings, managed vector indexes, and skill sets would add
external dependencies without a local baseline to compare against. A purely
local, byte-deterministic retrieval pipeline lets the project establish
reproducible metrics first. The `Retriever` interface is designed so a future
Azure-backed implementation can replace the current one without changing
consumers.

## What It Is Not

- It does not use real banking knowledge.
- It does not embed text with Azure OpenAI embeddings.
- The retrieval-only baseline does not require an LLM. The current package includes
  the optional Foundry Local adapter for grounded generation.
- It does not authorize actions, run an agent, or talk to MCP.
- It does not claim production relevance.

## Historical v0.5 Candidate Implementation

Status: `MEASURED - FOUNDRY LOCAL BASELINE`.

- `LLMProvider` isolates provider/model integration from grounding rules.
- `build_context` emits canonical JSON and retains `document_id`, `version`,
  `chunk_id`, and `source`; superseded hits are excluded.
- `rag-answer-v001` is the only answer prompt and treats retrieved content as
  untrusted evidence rather than instructions.
- `GroundedAnswer` requires exactly `answer`, `citations`, and `abstained`.
- Non-abstained answers require citations, and every citation is checked
  against the chunks actually supplied to the model.
- Empty active context abstains without invoking a provider.
- Prompt-development and held-out generation-evaluation cases are separate.

The fixed-context generation harness measures groundedness, answer relevance,
completeness, citation validity, citation coverage, abstention correctness,
unsupported-claim rate, and prompt-injection resistance. The observed
Foundry Local baseline is recorded in `reports/generation-metrics.json`; it
does not re-score or tune v0.4 retrieval and defines no production thresholds.

## Setup

Use the repository's existing virtual environment.

```powershell
.venv\Scripts\python.exe -m pip install -e "ai/rag[dev]"
```

## Commands

```powershell
.venv\Scripts\python.exe -m aegisbank_rag.cli index
.venv\Scripts\python.exe -m aegisbank_rag.cli search "<query>" --top-k 5
.venv\Scripts\python.exe -m aegisbank_rag.cli evaluate
```

The `evaluate` command runs the frozen evaluation against the synthetic
queries and qrels and rewrites `reports/retrieval-metrics.json` plus
`reports/retrieval-report.md`. Future invocations become reproducibility
checks; they must never be used to tune weights or thresholds.

## Quality Checks

```powershell
.venv\Scripts\python.exe -m pytest ai/rag/tests
.venv\Scripts\python.exe -m pytest ai/rag/tests/v05
.venv\Scripts\python.exe -m ruff check ai/rag
.venv\Scripts\python.exe -m ruff format --check ai/rag
.venv\Scripts\python.exe -m compileall ai/rag/src
```

## Reproducibility

Corpus generation, chunk ID assignment, vectorizer fitting, and TruncatedSVD
randomization all use `RANDOM_STATE = 42`. The corpus SHA-256 fingerprint is
recorded in `data/corpus-manifest.json`.

Generation evaluation uses disjoint files
`data/generation-prompt-dev.jsonl` and `data/generation-eval.jsonl`. Fixed
contexts isolate generation measurements from frozen retrieval measurements.

## Limitations

- The corpus is synthetic, hand-authored, and small.
- TF-IDF plus LSA is a strong lexical baseline but cannot capture semantic
  paraphrase the way modern dense embedders can.
- Retrieval metrics on synthetic data do not transfer to real banking
  traffic.
- Hybrid RRF weights are not tuned against any production data.
- Prompt-injection resistance has only deterministic contract coverage until
  the held-out adversarial case is executed against an authorized live model.
- Lexical generation metrics are transparent proxies, not semantic or
  production-quality guarantees.
