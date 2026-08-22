from collections import Counter

from aegisbank_rag.chunking import chunk_corpus


def test_chunk_ids_are_unique(chunks) -> None:
    ids = [chunk.chunk_id for chunk in chunks]
    assert len(ids) == len(set(ids))


def test_chunk_ids_carry_document_id_and_version(chunks) -> None:
    for chunk in chunks:
        assert chunk.document_id in chunk.chunk_id
        assert f"__{chunk.document_version}__" in chunk.chunk_id


def test_chunk_ids_are_byte_deterministic(documents) -> None:
    first = chunk_corpus(documents)
    second = chunk_corpus(documents)
    assert [chunk.chunk_id for chunk in first] == [chunk.chunk_id for chunk in second]


def test_no_document_produces_zero_chunks(documents) -> None:
    for document in documents:
        chunks_for_doc = chunk_corpus([document])
        assert chunks_for_doc, f"document {document.document_id} produced no chunks"


def test_chunk_metadata_preserves_provenance(chunks) -> None:
    for chunk in chunks:
        assert chunk.document_id
        assert chunk.document_version
        assert chunk.title
        assert chunk.topic
        assert chunk.source
        assert chunk.status in (
            "draft",
            "active",
            "superseded",
            "retired",
        )


def test_chunk_count_matches_manifest(chunks) -> None:
    by_topic = Counter(chunk.topic for chunk in chunks)
    for topic, count in by_topic.items():
        assert count >= 1, f"topic {topic} produced no chunks"
