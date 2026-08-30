import json

import pytest

from aegisbank_rag.context import build_context

from .support import make_hit


def test_context_is_deterministic_and_preserves_provenance() -> None:
    second = make_hit(
        chunk_id="chk_second__v2__c002_000000000002",
        document_id="second",
        version="v2",
        source="aegisbank/synthetic/second",
        rank=2,
    )
    first = make_hit()

    forward = build_context([second, first])
    reverse = build_context([first, second])

    assert forward.render_json() == reverse.render_json()
    assert forward.chunk_ids == (first.chunk_id, second.chunk_id)
    payload = json.loads(forward.render_json())
    assert payload["trust"] == "untrusted_retrieved_evidence"
    assert payload["entries"][1] == {
        "chunk_id": second.chunk_id,
        "content": second.content,
        "document_id": "second",
        "rank": 2,
        "source": "aegisbank/synthetic/second",
        "status": "active",
        "version": "v2",
    }


def test_context_excludes_superseded_versions() -> None:
    stale = make_hit(status="superseded", version="v1")
    current = make_hit(
        chunk_id="chk_test__v2__c001_000000000002",
        version="v2",
        rank=2,
    )

    context = build_context([stale, current])

    assert context.chunk_ids == (current.chunk_id,)
    assert context.entries[0].version == "v2"


def test_context_rejects_duplicate_chunk_provenance() -> None:
    hit = make_hit()

    with pytest.raises(ValueError, match="Duplicate retrieved chunk_id"):
        build_context([hit, hit])
