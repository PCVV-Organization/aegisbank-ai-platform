from datetime import date

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active
from aegisbank_rag.dense_local import DenseLocalRetriever
from aegisbank_rag.hybrid import HybridRRFRetriever
from aegisbank_rag.lexical import LexicalRetriever
from aegisbank_rag.retriever import reciprocal_rank_fusion


def test_hybrid_uses_fused_method_label(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = HybridRRFRetriever()
    retriever.fit(chunks)
    hits = retriever.search("¿Cómo se crea un reclamo?", top_k=3)
    assert hits
    assert {hit.retrieval_method for hit in hits} == {"hybrid_rrf"}


def test_hybrid_run_is_deterministic(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = HybridRRFRetriever()
    retriever.fit(chunks)
    query = "categorías de reclamos y estados"
    first = [hit.chunk_id for hit in retriever.search(query, top_k=5)]
    second = [hit.chunk_id for hit in retriever.search(query, top_k=5)]
    assert first == second


def test_rrf_handles_overlap_and_unique_lists(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    lexical = LexicalRetriever()
    dense = DenseLocalRetriever()
    lexical.fit(chunks)
    dense.fit(chunks)
    lexical_hits = lexical.search("crédito", top_k=3)
    dense_hits = dense.search("crédito", top_k=3)
    fused = reciprocal_rank_fusion([lexical_hits, dense_hits])
    assert fused
    assert all(hit.retrieval_method == "hybrid_rrf" for hit in fused)


def test_rrf_scores_are_in_descending_order(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    lexical = LexicalRetriever()
    lexical.fit(chunks)
    retriever = HybridRRFRetriever()
    retriever.fit(chunks)
    fused = retriever.search("tasas y comisiones", top_k=5)
    scores = [hit.score for hit in fused]
    assert scores == sorted(scores, reverse=True)
