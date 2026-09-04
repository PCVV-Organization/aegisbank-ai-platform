"""Comprehensive regression suite for v0.13.0-R1: Intent Robustness & Conversational Relevance.

Validates:
1. Metamorphic paraphrase matrix for loan detail queries (>=6 variants without
   requiring the word 'préstamo').
2. Prevention and defense against textual pseudo-tool-calls when banking data is required.
3. Multi-loan disambiguation without guessing when loan ID is absent.
4. Conversational relevance and abstraction leak prevention in system prompt v003.
5. Triaging of claims inquiries: DOMAIN_SCHEMA vs RAG vs CLARIFICATION.
"""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.knowledge_routing import (
    classify_service_inquiry,
    extract_loan_id,
    requires_account_data,
)
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.registry import ToolRegistry


class _Choice:
    def __init__(self, message: object):
        self.message = message


class _Response:
    def __init__(self, message: object):
        self.choices = [_Choice(message)]


class _Message:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


def _tool_call(name: str, arguments: dict[str, str], call_id: str = "CALL-001") -> object:
    fn = type("Function", (), {"name": name, "arguments": json.dumps(arguments)})()
    return type("ToolCall", (), {"id": call_id, "function": fn})()


# ---------------------------------------------------------------------------
# 1. Unit Extractor and Allowlist Classification
# ---------------------------------------------------------------------------


def test_extract_loan_id_canonical_cases() -> None:
    assert extract_loan_id("Dame detalle de mi prestamo LOAN-0001") == "LOAN-0001"
    assert extract_loan_id("Dame detalle de mi LOAN-0001") == "LOAN-0001"
    assert extract_loan_id("Muéstrame LOAN-0001") == "LOAN-0001"
    assert extract_loan_id("Información sobre loan-0002") == "LOAN-0002"
    assert extract_loan_id("Detalle de LOAN-9999 por favor") == "LOAN-9999"
    assert extract_loan_id("¿Cuáles son mis préstamos?") is None
    assert extract_loan_id("Hola") is None
    assert extract_loan_id("LOAN-12") is None  # Invalid: not 4 digits


def test_requires_account_data_robustness() -> None:
    # Queries with loan ID must trigger account data even without 'préstamo'
    assert requires_account_data("Dame detalle de mi LOAN-0001") is True
    assert requires_account_data("Muéstrame LOAN-0001") is True
    assert requires_account_data("Información sobre LOAN-0001") is True
    assert requires_account_data("Consultar LOAN-0001") is True
    assert requires_account_data("Estado de LOAN-0001") is True

    # General knowledge queries must NOT be falsely marked as account data
    assert requires_account_data("¿Cuáles son los requisitos de un crédito?") is False
    assert requires_account_data("¿Cuál es la tasa de interés?") is False
    assert requires_account_data("Hola, buenas tardes") is False


# ---------------------------------------------------------------------------
# 2. Metamorphic Paraphrase Matrix for GET_LOAN_DETAILS (>= 6 variants)
# ---------------------------------------------------------------------------


@pytest.mark.parametrize(
    "query",
    [
        "Dame detalle de mi prestamo LOAN-0001",
        "Dame detalle de mi LOAN-0001",
        "Muéstrame LOAN-0001",
        "Información sobre LOAN-0001",
        "Detalle de LOAN-0001",
        "Consultar LOAN-0001",
        "Estado de LOAN-0001",
    ],
)
def test_metamorphic_paraphrase_matrix_loan_details(query: str) -> None:
    """Metamorphic invariant: all paraphrases of LOAN-0001 inspection must route,
    execute get_loan_details, verify customer ownership, and avoid pseudo tool calls.
    """
    db = create_default_database()
    registry = ToolRegistry(
        [
            GetMyLoansTool(db),
            GetLoanDetailsTool(db),
            GetNextInstallmentTool(db),
        ]
    )

    tc = _tool_call("get_loan_details", {"loan_id": "LOAN-0001"})
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[tc])),
        _Response(
            _Message(content="El préstamo LOAN-0001 se encuentra activo con saldo pendiente.")
        ),
    ]
    metrics = OperationalMetrics()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry, metrics=metrics)

    result = orchestrator.run(query, customer_id="CUST-0001")

    # Invariants
    assert result.success is True
    assert result.customer_id == "CUST-0001"
    executed_tools = [c.tool_name for c in result.tool_calls]
    assert "get_loan_details" in executed_tools

    # Find the loan detail call record
    detail_record = next(c for c in result.tool_calls if c.tool_name == "get_loan_details")
    assert detail_record.arguments.get("loan_id") == "LOAN-0001"
    assert detail_record.result.success is True  # Ownership check passed
    assert detail_record.result.data.get("loan_id") == "LOAN-0001"

    # Zero pseudo-tool-calls
    assert metrics.get_counter("pseudo_tool_call_count") == 0


def test_metamorphic_cross_customer_ownership_defense() -> None:
    """Verify that loan belonging to another customer is strictly denied even with paraphrase."""
    db = create_default_database()
    registry = ToolRegistry([GetLoanDetailsTool(db)])

    # LOAN-0003 belongs to CUST-0002 in synthetic seed
    tc = _tool_call("get_loan_details", {"loan_id": "LOAN-0003"})
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        _Response(_Message(tool_calls=[tc])),
        _Response(_Message(content="No tienes acceso a ese préstamo.")),
    ]

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Muéstrame LOAN-0003", customer_id="CUST-0001")

    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_loan_details"
    assert result.tool_calls[0].result.success is False
    assert "no pertenece" in (result.tool_calls[0].result.error or "")


# ---------------------------------------------------------------------------
# 3. Pseudo-Tool-Call Regression Defense
# ---------------------------------------------------------------------------


def test_pseudo_tool_call_text_is_strictly_rejected_when_banking_data_required() -> None:
    """When a banking query requires account data and the orchestrator falls
    back to the model (no explicit loan id), the model must NOT substitute a
    real structured call with raw text like 'get_my_loans()'. The orchestrator
    must detect and reject the pseudo-call.
    """
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetLoanDetailsTool(db)])
    metrics = OperationalMetrics()
    audit = AuditLogger()

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(_Message(content="get_my_loans()"))

    orchestrator = AgentOrchestrator(
        client=mock_client, registry=registry, metrics=metrics, audit_logger=audit
    )
    result = orchestrator.run("Dame detalle de mis prestamos", customer_id="CUST-0001")

    assert result.success is False
    assert "Structured tool call was not emitted" in (result.error or "")
    assert "No pude obtener una respuesta estructurada" in result.answer
    assert metrics.get_counter("pseudo_tool_call_count") >= 1
    assert metrics.get_counter("banking_tool_missed_count") >= 1


# ---------------------------------------------------------------------------
# 4. Multi-Loan Disambiguation Without Guessing
# ---------------------------------------------------------------------------


def test_loan_detail_without_id_disambiguates_multi_loans() -> None:
    """Query 'Dame detalle de mi préstamo' without ID must NOT guess an ID when customer
    has multiple loans. The orchestrator must instruct the model to ask the user.
    """
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetLoanDetailsTool(db)])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(
        _Message(
            content=(
                "Tienes dos préstamos registrados: LOAN-0001 y LOAN-0002. "
                "¿De cuál de ellos te gustaría ver el detalle?"
            )
        )
    )

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Dame detalle de mi préstamo", customer_id="CUST-0001")

    assert result.success is True
    # get_my_loans must have executed to discover available loans
    assert any(c.tool_name == "get_my_loans" for c in result.tool_calls)
    # get_loan_details must NOT have been called with a guessed ID
    assert not any(c.tool_name == "get_loan_details" for c in result.tool_calls)

    # Verify that the system prompt directed the model not to guess
    call_messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    system_contents = [m["content"] for m in call_messages if m["role"] == "system"]
    assert any("NO adivines" in c for c in system_contents)


# ---------------------------------------------------------------------------
# 5. Conversational Relevance & Abstraction Leak Defense
# ---------------------------------------------------------------------------


def test_system_prompt_v003_loaded_by_default() -> None:
    orchestrator = AgentOrchestrator(client=MagicMock())
    assert (
        "agent-system-v003" in orchestrator.system_prompt
        or "Abstraction Leak" in orchestrator.system_prompt
    )
    # Must contain prohibition of internal tool names
    assert "NUNCA menciones nombres de herramientas" in orchestrator.system_prompt


def test_capability_discovery_dialogue_hides_tool_names() -> None:
    """When asked '¿Qué puedes hacer?', response must not leak tool names."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(
        _Message(
            content=(
                "Puedo ayudarte a consultar tus préstamos, revisar saldos y cuotas "
                "pendientes, brindarte información sobre políticas y tasas, y "
                "registrar solicitudes de servicio."
            )
        )
    )

    orchestrator = AgentOrchestrator(client=mock_client)
    result = orchestrator.run("¿Qué puedes hacer?", customer_id="CUST-0001")

    assert result.success is True
    for banned in (
        "get_my_loans",
        "get_loan_details",
        "create_service_request",
        "search_knowledge",
    ):
        assert banned not in result.answer


# ---------------------------------------------------------------------------
# 6. Ambiguity Clarification Policy (DOMAIN_SCHEMA vs RAG vs CLARIFICATION)
# ---------------------------------------------------------------------------


def test_service_inquiry_triaging() -> None:
    assert (
        classify_service_inquiry("¿Qué requiero para que mi reclamo tenga efecto?")
        == "CLARIFICATION"
    )
    assert (
        classify_service_inquiry("¿Qué campos se necesitan para registrar un reclamo?")
        == "DOMAIN_SCHEMA"
    )
    assert (
        classify_service_inquiry("¿Cuáles son las categorías de reclamo soportadas?")
        == "DOMAIN_SCHEMA"
    )
    assert classify_service_inquiry("¿Cuál es la política de reclamos de AegisBank?") == "RAG"
    assert classify_service_inquiry("Hola") == "OTHER"
    assert classify_service_inquiry("¿Cuáles son mis préstamos?") == "OTHER"


def test_ambiguous_claim_question_prompts_clarification_without_tools() -> None:
    """Ambiguous claim inquiry must ask for clarification without executing arbitrary tools."""
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client)

    result = orchestrator.run(
        "¿Qué requiero para que mi reclamo tenga efecto?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert len(result.tool_calls) == 0
    assert mock_client.chat.completions.create.call_count == 0  # Deterministic clarification
    assert (
        "aclararme a qué te refieres" in result.answer
        or "precisarme a qué te refieres" in result.answer
    )
    assert "esquema" in result.answer or "catálogo" in result.answer or "categoría" in result.answer
