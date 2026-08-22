# AegisBank RAG Retrieval Foundation

Local, reproducible retrieval foundation for the `v0.4.0 - RAG Retrieval &
Evaluation Foundation` milestone of AegisBank AI Platform.

> This is a local educational retrieval layer. It does not call Azure AI
> Search, does not run an LLM, and does not integrate with Core Banking yet.
> It only produces candidate chunks plus deterministic metrics.

## What It Is

A frozen lexical plus dense-local retrieval pipeline over a synthetic banking
corpus. The dense baseline is TF-IDF reduced with TruncatedSVD (LSA). The
hybrid ranker fuses both signals with Reciprocal Rank Fusion (RRF). The
pipeline is reproducible by seed, the corpus is versioned, and the evaluation
dataset provides offline metrics.

The component exists to provide a measurable retrieval reference before any
LLM, agent, MCP integration, or Azure AI Search deployment is attempted.

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
- It does not call any LLM.
- It does not authorize actions, run an agent, or talk to MCP.
- It does not claim production relevance.

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
.venv\Scripts\python.exe -m ruff check ai/rag
.venv\Scripts\python.exe -m ruff format --check ai/rag
.venv\Scripts\python.exe -m compileall ai/rag/src
```

## Reproducibility

Corpus generation, chunk ID assignment, vectorizer fitting, and TruncatedSVD
randomization all use `RANDOM_STATE = 42`. The corpus SHA-256 fingerprint is
recorded in `data/corpus-manifest.json`.

## Limitations

- The corpus is synthetic, hand-authored, and small.
- TF-IDF plus LSA is a strong lexical baseline but cannot capture semantic
  paraphrase the way modern dense embedders can.
- Retrieval metrics on synthetic data do not transfer to real banking
  traffic.
- Hybrid RRF weights are not tuned against any production data.
