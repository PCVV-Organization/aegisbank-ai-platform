# ADR-008: Local retrieval before Azure AI Search

## Status

Accepted for `v0.4`.

## Context

A future RAG pipeline needs a candidate-document retriever before any
generator is connected. The natural production target is Azure AI Search with
embeddings, vector indexes, and semantic rankers. Committing to Azure AI
Search as the retrieval layer would force the project to depend on an Azure
deployment, an embedding model selection, and network-side ranking
configurations before any reproducible metric exists.

The project also needs to demonstrate measurable behaviour on synthetic,
reproducible banking data before external search infrastructure is introduced.

## Decision

Build a local, byte-deterministic retrieval foundation as the `v0.4`
baseline. It must:

- index a synthetic Spanish banking corpus with versioned metadata
  (`document_id`, `version`, `effective_from`, `effective_to`, `status`,
  `source`);
- chunk documents deterministically into reproducible chunk IDs;
- expose a `Retriever` interface with at least three implementations:
  lexical TF-IDF, dense TF-IDF plus TruncatedSVD/LSA, and a hybrid
  Reciprocal Rank Fusion (RRF) ranker;
- produce Precision@k, Recall@k, MRR@k, and nDCG@k via a frozen offline
  evaluation dataset;
- be reproducible by seed so the same metrics can be regenerated at any
  later point.

The local TruncatedSVD/LSA dense baseline is explicitly **not** equivalent to
modern embeddings produced by Azure AI Search. It is a vector baseline that
fits in memory and runs offline.

## Alternatives

- **Azure AI Search as the only retriever:** rejected because it would
  couple retrieval metrics to external configuration and to the Azure
  deployment status, neither of which the project controls at `v0.4`.
- **Pure lexical retrieval only:** rejected because it provides no option to
  compare against a vector baseline and would prevent the project from
  measuring the cost of adding a dense channel.
- **Vendor-only embeddings in-process:** rejected because it would replace
  the local baseline dependency with a heavier model dependency before any
  metric is known.

## Consequences

- The pipeline is reproducible and zero-infrastructure.
- The `Retriever` interface allows a future Azure AI Search implementation
  to be swapped in without changing downstream consumers (chunking,
  evaluation, citation metadata).
- TruncatedSVD/LSA cannot represent out-of-vocabulary terms and cannot
  capture paraphrastic meaning. Strong paraphrase behaviour must wait for a
  later, separately authorized experiment.
- Initial retrieval metrics on a synthetic corpus do not transfer to real
  banking traffic and must not be presented as production thresholds.
