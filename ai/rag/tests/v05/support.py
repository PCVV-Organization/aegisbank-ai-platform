from __future__ import annotations

import json
from collections.abc import Sequence

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.provider import LLMProvider, LLMRequest
from aegisbank_rag.retriever import RetrievalHit, Retriever


class RecordingProvider(LLMProvider):
    def __init__(
        self,
        *,
        response: str | None = None,
        responses_by_query: dict[str, str] | None = None,
    ) -> None:
        self._response = response
        self._responses_by_query = responses_by_query or {}
        self.requests: list[LLMRequest] = []

    @property
    def provider_name(self) -> str:
        return "deterministic-test-provider"

    @property
    def model_name(self) -> str:
        return "deterministic-test-model"

    def generate(self, request: LLMRequest) -> str:
        self.requests.append(request)
        if self._response is not None:
            return self._response
        query = json.loads(request.user_prompt)["query"]
        return self._responses_by_query[query]


class FixedRetriever(Retriever):
    name = "fixed_test_retriever"

    def __init__(self, hits: Sequence[RetrievalHit]) -> None:
        self._hits = list(hits)

    def fit(self, chunks: Sequence[Chunk]) -> None:
        del chunks

    def search(self, query: str, *, top_k: int = 5) -> list[RetrievalHit]:
        if not query.strip():
            raise ValueError("Query must not be empty")
        return self._hits[:top_k]


def make_hit(
    *,
    chunk_id: str = "chk_test__v1__c001_000000000001",
    document_id: str = "test_document",
    version: str = "v1",
    content: str = "Evidencia sintética válida.",
    source: str = "aegisbank/synthetic/test",
    status: str = "active",
    rank: int = 1,
) -> RetrievalHit:
    return RetrievalHit(
        document_id=document_id,
        document_version=version,
        chunk_id=chunk_id,
        title="Test document",
        topic="test",
        content=content,
        source=source,
        status=status,
        effective_from="2026-01-01",
        effective_to=None,
        score=1.0 / rank,
        rank=rank,
        retrieval_method="test",
    )


def answer_json(answer: str, citations: Sequence[str], *, abstained: bool = False) -> str:
    return json.dumps(
        {
            "answer": answer,
            "citations": list(citations),
            "abstained": abstained,
        },
        ensure_ascii=False,
    )
