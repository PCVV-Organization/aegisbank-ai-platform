"""Grounded generation orchestration and strict response validation."""

from __future__ import annotations

import json
from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any

from aegisbank_rag.context import GroundingContext, build_context
from aegisbank_rag.prompting import PromptDefinition, build_llm_request, load_prompt
from aegisbank_rag.provider import LLMProvider
from aegisbank_rag.retriever import RetrievalHit, Retriever


class GroundingValidationError(ValueError):
    """Raised when generated output violates the grounded answer contract."""


@dataclass(frozen=True, slots=True)
class GroundedAnswer:
    answer: str
    citations: tuple[str, ...]
    abstained: bool

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "citations": list(self.citations),
            "abstained": self.abstained,
        }


def parse_grounded_answer(raw_response: str) -> GroundedAnswer:
    try:
        payload = json.loads(raw_response)
    except json.JSONDecodeError as exc:
        raise GroundingValidationError("LLM response is not valid JSON") from exc
    if not isinstance(payload, dict) or set(payload) != {"answer", "citations", "abstained"}:
        raise GroundingValidationError(
            "LLM response must contain exactly answer, citations, and abstained"
        )
    answer = payload["answer"]
    citations = payload["citations"]
    abstained = payload["abstained"]
    if not isinstance(answer, str) or not answer.strip():
        raise GroundingValidationError("answer must be non-empty text")
    if not isinstance(citations, list) or any(not isinstance(item, str) for item in citations):
        raise GroundingValidationError("citations must be a list of chunk IDs")
    if len(citations) != len(set(citations)) or any(not item.strip() for item in citations):
        raise GroundingValidationError("citations must be unique non-empty chunk IDs")
    if not isinstance(abstained, bool):
        raise GroundingValidationError("abstained must be a boolean")
    if abstained and citations:
        raise GroundingValidationError("An abstained answer cannot contain citations")
    if not abstained and not citations:
        raise GroundingValidationError("A non-abstained answer requires at least one citation")
    return GroundedAnswer(
        answer=answer.strip(),
        citations=tuple(citations),
        abstained=abstained,
    )


def validate_citations(answer: GroundedAnswer, context: GroundingContext) -> None:
    available = set(context.chunk_ids)
    invented = set(answer.citations) - available
    if invented:
        raise GroundingValidationError(
            f"Citations were not present in retrieved context: {sorted(invented)}"
        )


def validate_grounded_output(
    answer: GroundedAnswer,
    context: GroundingContext,
    prompt: PromptDefinition,
) -> None:
    validate_citations(answer, context)
    if answer.abstained and answer.answer != prompt.abstention_answer:
        raise GroundingValidationError("Abstained answer differs from the registered response")


class GroundedGenerator:
    """Compose retrieval, context construction, generation, and validation."""

    def __init__(
        self,
        retriever: Retriever,
        provider: LLMProvider,
        *,
        prompt: PromptDefinition | None = None,
    ) -> None:
        self._retriever = retriever
        self._provider = provider
        self._prompt = prompt or load_prompt()

    @property
    def prompt_version(self) -> str:
        return self._prompt.version

    def answer(self, query: str, *, top_k: int = 5) -> GroundedAnswer:
        if not query.strip():
            raise ValueError("Query must not be empty")
        hits = self._retriever.search(query, top_k=top_k)
        return self.answer_from_hits(query, hits)

    def answer_from_hits(
        self,
        query: str,
        hits: Sequence[RetrievalHit],
    ) -> GroundedAnswer:
        return generate_grounded_answer(
            self._provider,
            self._prompt,
            query,
            hits,
        )


def generate_grounded_answer(
    provider: LLMProvider,
    prompt: PromptDefinition,
    query: str,
    hits: Sequence[RetrievalHit],
) -> GroundedAnswer:
    """Generate from explicit hits and reject any citation outside that context."""

    generated, context = request_grounded_answer(provider, prompt, query, hits)
    validate_grounded_output(generated, context, prompt)
    return generated


def request_grounded_answer(
    provider: LLMProvider,
    prompt: PromptDefinition,
    query: str,
    hits: Sequence[RetrievalHit],
) -> tuple[GroundedAnswer, GroundingContext]:
    """Parse a provider answer before provenance validation for evaluation use."""

    if not query.strip():
        raise ValueError("Query must not be empty")
    context = build_context(hits)
    if not context.entries:
        return (
            GroundedAnswer(
                answer=prompt.abstention_answer,
                citations=(),
                abstained=True,
            ),
            context,
        )
    request = build_llm_request(prompt, query, context)
    generated = parse_grounded_answer(provider.generate(request))
    return generated, context
