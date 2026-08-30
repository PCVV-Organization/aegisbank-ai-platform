import pytest

from aegisbank_rag.generation import (
    GroundedGenerator,
    GroundingValidationError,
    generate_grounded_answer,
    parse_grounded_answer,
)
from aegisbank_rag.prompting import load_prompt
from aegisbank_rag.provider import LLMProvider

from .support import FixedRetriever, RecordingProvider, answer_json, make_hit


def test_provider_boundary_is_abstract() -> None:
    with pytest.raises(TypeError):
        LLMProvider()  # type: ignore[abstract]


def test_pipeline_returns_structured_grounded_answer() -> None:
    hit = make_hit(content="La cuota contiene capital e intereses.")
    provider = RecordingProvider(
        response=answer_json("La cuota contiene capital e intereses.", [hit.chunk_id])
    )
    generator = GroundedGenerator(FixedRetriever([hit]), provider)

    result = generator.answer("¿Qué contiene la cuota?")

    assert result.as_dict() == {
        "answer": "La cuota contiene capital e intereses.",
        "citations": [hit.chunk_id],
        "abstained": False,
    }
    assert generator.prompt_version == "rag-answer-v001"
    assert provider.requests[0].prompt_version == "rag-answer-v001"


def test_invented_citation_is_rejected() -> None:
    hit = make_hit()
    provider = RecordingProvider(
        response=answer_json("Respuesta no verificable.", ["chk_inventado"])
    )

    with pytest.raises(GroundingValidationError, match="not present in retrieved context"):
        generate_grounded_answer(provider, load_prompt(), "Consulta", [hit])


def test_no_active_evidence_abstains_without_calling_provider() -> None:
    provider = RecordingProvider(response="not used")
    stale = make_hit(status="superseded")

    result = generate_grounded_answer(provider, load_prompt(), "Consulta", [stale])

    assert result.abstained is True
    assert result.citations == ()
    assert result.answer == load_prompt().abstention_answer
    assert provider.requests == []


def test_noncanonical_abstention_is_rejected() -> None:
    provider = RecordingProvider(response=answer_json("No lo sé.", [], abstained=True))

    with pytest.raises(GroundingValidationError, match="registered response"):
        generate_grounded_answer(provider, load_prompt(), "Consulta", [make_hit()])


@pytest.mark.parametrize(
    "raw_response,error",
    [
        ("not-json", "not valid JSON"),
        ('{"answer":"x","citations":[]}', "exactly answer"),
        ('{"answer":"x","citations":[],"abstained":false}', "requires at least one"),
        (
            '{"answer":"x","citations":["chk_a"],"abstained":true}',
            "cannot contain citations",
        ),
        (
            '{"answer":"x","citations":["chk_a","chk_a"],"abstained":false}',
            "unique non-empty",
        ),
    ],
)
def test_structured_output_contract_rejects_invalid_responses(
    raw_response: str,
    error: str,
) -> None:
    with pytest.raises(GroundingValidationError, match=error):
        parse_grounded_answer(raw_response)
