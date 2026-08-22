from collections import Counter
from datetime import date

from aegisbank_rag.constants import ALLOWED_TOPICS
from aegisbank_rag.corpus import filter_active


def test_corpus_has_one_active_document_per_topic(documents) -> None:
    by_topic = Counter(doc.topic for doc in documents)
    for topic in ALLOWED_TOPICS:
        assert by_topic[topic] >= 1, f"missing topic {topic}"


def test_filter_active_excludes_superseded_versions(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    active = filter_active(documents, cutoff=cutoff)
    superseded = [doc for doc in documents if doc.status == "superseded"]
    assert superseded, "expected at least one superseded document for the test"
    superseded_ids = {(doc.document_id, doc.version) for doc in superseded}
    active_ids = {(doc.document_id, doc.version) for doc in active}
    assert superseded_ids.isdisjoint(active_ids)


def test_filter_active_returns_deterministic_results(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    first = filter_active(documents, cutoff=cutoff)
    second = filter_active(documents, cutoff=cutoff)
    assert [doc.document_id for doc in first] == [doc.document_id for doc in second]
    assert [doc.version for doc in first] == [doc.version for doc in second]


def test_active_corpus_has_one_active_creditos_version(documents) -> None:
    cutoff = date.fromisoformat("2026-12-31")
    active = filter_active(documents, cutoff=cutoff)
    creditos_active = [doc for doc in active if doc.document_id == "creditos_producto_general"]
    assert len(creditos_active) == 1
    assert creditos_active[0].version == "v2"
