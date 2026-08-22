from datetime import date

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.corpus import filter_active
from aegisbank_rag.hybrid import HybridRRFRetriever


def test_hits_carry_required_citation_fields(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = HybridRRFRetriever()
    retriever.fit(chunks)
    hits = retriever.search("crédito", top_k=3)
    for hit in hits:
        d = hit.as_dict()
        for required in (
            "document_id",
            "document_version",
            "chunk_id",
            "content",
            "score",
            "rank",
            "source",
        ):
            assert required in d
            assert d[required] != ""


def test_ranks_are_one_indexed_and_continuous(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = HybridRRFRetriever()
    retriever.fit(chunks)
    hits = retriever.search("tasas de interés", top_k=4)
    assert [hit.rank for hit in hits] == list(range(1, len(hits) + 1))


def test_hits_expose_status_and_effective_range(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    chunks = chunk_corpus(filter_active(documents, cutoff=cutoff))
    retriever = HybridRRFRetriever()
    retriever.fit(chunks)
    hits = retriever.search("reclamo", top_k=3)
    for hit in hits:
        assert hit.status in {"draft", "active", "superseded", "retired"}
        assert hit.effective_from
