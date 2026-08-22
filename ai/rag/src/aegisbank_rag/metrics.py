"""Retrieval evaluation metrics: Precision@k, Recall@k, MRR@k, nDCG@k."""

from __future__ import annotations

import math
from collections.abc import Iterable, Sequence

METRIC_NAMES: tuple[str, ...] = (
    "precision_at_5",
    "recall_at_5",
    "mrr_at_5",
    "ndcg_at_5",
)


def _to_set(relevant: Iterable[str]) -> set[str]:
    return {str(item) for item in relevant}


def precision_at_k(retrieved: Sequence[str], relevant: Sequence[str], *, k: int) -> float:
    if k <= 0:
        raise ValueError(f"k must be > 0 (got {k})")
    relevant_set = _to_set(relevant)
    if not relevant_set:
        return 0.0
    retrieved_at_k = list(retrieved[:k])
    if not retrieved_at_k:
        return 0.0
    hits = sum(1 for chunk_id in retrieved_at_k if chunk_id in relevant_set)
    return hits / k


def recall_at_k(retrieved: Sequence[str], relevant: Sequence[str], *, k: int) -> float:
    if k <= 0:
        raise ValueError(f"k must be > 0 (got {k})")
    relevant_set = _to_set(relevant)
    if not relevant_set:
        return 0.0
    retrieved_at_k = list(retrieved[:k])
    hits = sum(1 for chunk_id in retrieved_at_k if chunk_id in relevant_set)
    return hits / len(relevant_set)


def mrr_at_k(retrieved: Sequence[str], relevant: Sequence[str], *, k: int) -> float:
    if k <= 0:
        raise ValueError(f"k must be > 0 (got {k})")
    relevant_set = _to_set(relevant)
    if not relevant_set:
        return 0.0
    retrieved_at_k = list(retrieved[:k])
    for position, chunk_id in enumerate(retrieved_at_k, start=1):
        if chunk_id in relevant_set:
            return 1.0 / position
    return 0.0


def _discounted_gain(relevance: int, position: int) -> float:
    if relevance <= 0:
        return 0.0
    return (2**relevance - 1) / math.log2(position + 1)


def ndcg_at_k(
    retrieved: Sequence[str],
    relevant: Sequence[str],
    *,
    k: int,
) -> float:
    if k <= 0:
        raise ValueError(f"k must be > 0 (got {k})")
    relevant_set = _to_set(relevant)
    if not relevant_set:
        return 0.0
    dcg = 0.0
    for position, chunk_id in enumerate(list(retrieved[:k]), start=1):
        if chunk_id in relevant_set:
            dcg += _discounted_gain(1, position)
    ideal_count = min(len(relevant_set), k)
    idcg = sum(_discounted_gain(1, position) for position in range(1, ideal_count + 1))
    if idcg == 0.0:
        return 0.0
    return dcg / idcg


def compute_metrics(
    retrieved: Sequence[str],
    relevant: Sequence[str],
    *,
    k: int = 5,
) -> dict[str, float]:
    return {
        "precision_at_5": precision_at_k(retrieved, relevant, k=k),
        "recall_at_5": recall_at_k(retrieved, relevant, k=k),
        "mrr_at_5": mrr_at_k(retrieved, relevant, k=k),
        "ndcg_at_5": ndcg_at_k(retrieved, relevant, k=k),
    }
