from datetime import date

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active
from aegisbank_rag.evaluation import (
    build_active_corpus,
    evaluate,
    load_qrels,
    load_queries,
    make_retrievers,
)


def test_evaluation_is_deterministic(documents) -> None:
    active = build_active_corpus(documents)
    chunks = chunk_corpus(active)
    queries = load_queries()
    qrels = load_qrels()
    retrievers = make_retrievers()
    first = evaluate(chunks, queries, qrels, retrievers, top_k=5)
    second = evaluate(chunks, queries, qrels, retrievers, top_k=5)
    assert (
        first["aggregates"]["lexical_tfidf"]["ndcg_at_5"]
        == second["aggregates"]["lexical_tfidf"]["ndcg_at_5"]
    )
    assert (
        first["aggregates"]["dense_local_lsa"]["ndcg_at_5"]
        == second["aggregates"]["dense_local_lsa"]["ndcg_at_5"]
    )
    assert (
        first["aggregates"]["hybrid_rrf"]["ndcg_at_5"]
        == second["aggregates"]["hybrid_rrf"]["ndcg_at_5"]
    )


def test_chunking_is_deterministic_for_two_runs(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks_a = chunk_corpus(filter_active(documents, cutoff=cutoff))
    chunks_b = chunk_corpus(filter_active(documents, cutoff=cutoff))
    assert [c.chunk_id for c in chunks_a] == [c.chunk_id for c in chunks_b]
    assert [c.content for c in chunks_a] == [c.content for c in chunks_b]
