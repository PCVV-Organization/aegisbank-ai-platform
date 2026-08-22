# ADR-009: Hybrid retrieval with Reciprocal Rank Fusion

## Status

Accepted for `v0.4`.

## Context

Lexical TF-IDF retrieval is precise on exact vocabulary but misses
paraphrases and semantic vicinity. The local dense baseline
(TF-IDF plus TruncatedSVD/LSA) broadens coverage but ignores word order and
shares vocabulary limits. The project must commit to a single, fixed way of
combining both rankings in `v0.4` so that hybrid metrics remain comparable
across runs.

Reciprocal Rank Fusion (RRF) is an established, parameter-light rank
aggregation technique. It is widely used in production search stacks precisely
because it requires no score normalisation across underlying rankers and its
single parameter `k` is easy to keep frozen across experiments.

## Decision

Implement a `HybridRRFRetriever` that:

- fits both `LexicalRetriever` and `DenseLocalRetriever` on the same
  filtered active chunk set;
- gathers a pool of candidates from each (twice the configured top-k, with a
  floor of `min(LSA_COMPONENTS * 2, top_k)`);
- applies RRF with the frozen constant `k = 60`;
- exposes results under `retrieval_method = "hybrid_rrf"` so downstream
  consumers can distinguish them from lexical or dense hits.

No learned re-ranking, no score normalisation, and no learned fusion
weights are used in `v0.4`. Any later optimisation of `k` or fusion weights
requires a new ADR and must not be back-applied to the frozen `v0.4` metrics.

## Alternatives

- **Score-based convex combination:** rejected because lexical and dense
  scores live in different ranges and any `v0.4` normalisation would shift
  every metric.
- **Cascade (use dense only when lexical score is low):** rejected because
  the threshold would have to be tuned against the frozen `v0.4` evaluation
  set, which would invalidate the offline benchmark.
- **Learned fusion (a trained linear blender):** rejected for `v0.4` because
  it would require holding out evaluation data and introducing a model
  dependency before a reproducible baseline exists.

## Consequences

- Hybrid retrieval is reproducible because both underlying retrievers are
  reproducible and RRF is deterministic.
- The frozen `k = 60` makes later metric comparisons interpretable: any
  change in hybrid numbers must come from the corpus, the queries, or the
  retrievers, never from a silently re-tuned `k`.
- The hybrid retriever inherits all lexical and dense limitations,
  including the LSA paraphrase gap.
- Any future ranking experiment that tries to improve `v0.4` numbers must
  start from this ADR's constraints, not from a different fusion rule.
