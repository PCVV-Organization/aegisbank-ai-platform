from datetime import date

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active
from aegisbank_rag.dense_local import DenseLocalRetriever


def test_dense_retrieval_returns_finite_scores(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = DenseLocalRetriever()
    retriever.fit(chunks)
    hits = retriever.search("¿Cuáles son los tipos de comisiones?", top_k=3)
    assert hits
    for hit in hits:
        assert 0.0 < hit.score <= 1.0


def test_dense_retrieval_is_deterministic(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = DenseLocalRetriever()
    retriever.fit(chunks)
    query = "tasas de interés crédito"
    first = [hit.chunk_id for hit in retriever.search(query, top_k=3)]
    second = [hit.chunk_id for hit in retriever.search(query, top_k=3)]
    assert first == second


def test_dense_retrieval_method_label(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = DenseLocalRetriever()
    retriever.fit(chunks)
    hits = retriever.search("política de abstención", top_k=2)
    assert hits
    assert {hit.retrieval_method for hit in hits} == {"dense_local_lsa"}
