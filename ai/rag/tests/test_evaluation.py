from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.evaluation import (
    build_active_corpus,
    evaluate,
    load_qrels,
    load_queries,
    make_retrievers,
)


def test_queries_have_categories(queries) -> None:
    categories = {query.category for query in queries}
    assert {"direct", "paraphrase", "version", "ood"}.issubset(categories)


def test_qrels_cover_all_query_ids(queries, qrels) -> None:
    qids = {query.query_id for query in queries}
    rels = {qrel.query_id for qrel in qrels}
    assert qids == rels


def test_offline_evaluation_metrics_run(documents) -> None:
    active = build_active_corpus(documents)
    chunks = chunk_corpus(active)
    queries = load_queries()
    qrels = load_qrels()
    report = evaluate(chunks, queries, qrels, make_retrievers(), top_k=5)
    assert report["queries_evaluated"] == len(queries)
    for method, metrics in report["aggregates"].items():
        for metric_name in (
            "precision_at_5",
            "recall_at_5",
            "mrr_at_5",
            "ndcg_at_5",
        ):
            value = metrics[metric_name]["mean"]
            assert 0.0 <= value <= 1.0, f"{method} {metric_name} out of range"


def test_ood_queries_are_recognised(queries) -> None:
    ood_ids = [q.query_id for q in queries if q.category == "ood"]
    assert len(ood_ids) >= 1


def test_version_query_targets_active_version(qrels, chunk_index) -> None:
    version_qrel = next(qrel for qrel in qrels if qrel.category == "version")
    relevant_ids = set(version_qrel.relevant)
    assert relevant_ids
    for chunk_id in relevant_ids:
        chunk = chunk_index[chunk_id]
        assert chunk.status == "active"
