import pytest

from aegisbank_rag.metrics import (
    compute_metrics,
    mrr_at_k,
    ndcg_at_k,
    precision_at_k,
    recall_at_k,
)


def test_precision_recall_mrr_ndcg_have_expected_extremes() -> None:
    assert precision_at_k(["a", "b"], ["a"], k=2) == pytest.approx(0.5)
    assert recall_at_k(["a", "b"], ["a"], k=2) == pytest.approx(1.0)
    assert mrr_at_k(["b", "a"], ["a"], k=2) == pytest.approx(0.5)
    assert ndcg_at_k(["a", "b"], ["a"], k=2) == pytest.approx(1.0)


def test_metrics_return_zero_when_no_relevant_chunks() -> None:
    assert precision_at_k(["a"], [], k=1) == 0.0
    assert recall_at_k(["a"], [], k=1) == 0.0
    assert mrr_at_k(["a"], [], k=1) == 0.0
    assert ndcg_at_k(["a"], [], k=1) == 0.0


def test_metrics_return_zero_for_empty_retrieved() -> None:
    assert precision_at_k([], ["a"], k=5) == 0.0
    assert recall_at_k([], ["a"], k=5) == 0.0
    assert mrr_at_k([], ["a"], k=5) == 0.0
    assert ndcg_at_k([], ["a"], k=5) == 0.0


def test_compute_metrics_returns_all_four_metrics() -> None:
    metrics = compute_metrics(["a", "b", "c"], ["a", "d"], k=5)
    assert set(metrics) == {
        "precision_at_5",
        "recall_at_5",
        "mrr_at_5",
        "ndcg_at_5",
    }


def test_invalid_k_raises() -> None:
    with pytest.raises(ValueError):
        precision_at_k([], [], k=0)
    with pytest.raises(ValueError):
        recall_at_k([], [], k=0)
    with pytest.raises(ValueError):
        mrr_at_k([], [], k=0)
    with pytest.raises(ValueError):
        ndcg_at_k([], [], k=0)
