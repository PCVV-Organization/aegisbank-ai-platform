# v0.4 RAG Retrieval Report

## Scope

Local, byte-deterministic retrieval foundation over a synthetic Spanish banking corpus. The primary metric is `ndcg_at_5`.

## Aggregated Metrics @ top-5

| Method | nDCG@5 | MRR@5 | Precision@5 | Recall@5 |
| --- | ---: | ---: | ---: | ---: |
| lexical_tfidf | 0.352323 | 0.532407 | 0.188889 | 0.351852 |
| dense_local_lsa | 0.352323 | 0.532407 | 0.188889 | 0.351852 |
| hybrid_rrf | 0.352323 | 0.532407 | 0.188889 | 0.351852 |

## Per-category breakdown @ top-5

### lexical_tfidf

| Category | nDCG@5 | MRR@5 | Precision@5 | Recall@5 |
| --- | ---: | ---: | ---: | ---: |
| direct | 0.463147 | 0.690476 | 0.257143 | 0.476190 |
| ood | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| paraphrase | 0.233915 | 0.350000 | 0.160000 | 0.266667 |
| version | 0.643404 | 1.000000 | 0.266667 | 0.555556 |

### dense_local_lsa

| Category | nDCG@5 | MRR@5 | Precision@5 | Recall@5 |
| --- | ---: | ---: | ---: | ---: |
| direct | 0.463147 | 0.690476 | 0.257143 | 0.476190 |
| ood | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| paraphrase | 0.233915 | 0.350000 | 0.160000 | 0.266667 |
| version | 0.643404 | 1.000000 | 0.266667 | 0.555556 |

### hybrid_rrf

| Category | nDCG@5 | MRR@5 | Precision@5 | Recall@5 |
| --- | ---: | ---: | ---: | ---: |
| direct | 0.463147 | 0.690476 | 0.257143 | 0.476190 |
| ood | 0.000000 | 0.000000 | 0.000000 | 0.000000 |
| paraphrase | 0.233915 | 0.350000 | 0.160000 | 0.266667 |
| version | 0.643404 | 1.000000 | 0.266667 | 0.555556 |

## Coverage of Out-of-Domain Queries

| Method | OOD queries with no relevant | Hits accidentally returned |
| --- | ---: | ---: |
| lexical_tfidf | 3 | 6 |
| dense_local_lsa | 3 | 6 |
| hybrid_rrf | 3 | 6 |

## Interpretation

- All corpora, queries, and qrels are synthetic. Metrics therefore describe behaviour on the controlled corpus and not on real banking traffic.
- LSA dense vectors are a purely local baseline; they do not approximate modern embedders nor Azure AI Search ranking.
- Hybrid RRF combines lexical and dense rankings with a fixed `k=60`. The value is frozen for `v0.4`; tuning is out of scope.
- Out-of-domain queries are expected to return no relevant chunk. If a method surfaces a non-empty list for an OOD query it is counted as accidental and may justify future thresholding.

## Limitations

- The corpus is small, hand-authored, and fully synthetic.
- TruncatedSVD/LSA cannot represent out-of-vocabulary tokens and shows limited paraphrastic strength.
- The hybrid ranker does not tune weights. Any later optimisation requires separate authorization and must not be back-applied to `v0.4` metrics.
