"""Unit tests for intent robustness, metamorphic paraphrasing, and pseudo-call defense."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from mock_core_banking.persistence.database import Database

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.tools.banking_tools import (
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
    create_default_database,
)
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


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


def _make_registry(database: Database) -> ToolRegistry:
    return ToolRegistry(
        [
            GetMyLoansTool(database),
            GetLoanDetailsTool(database),
            GetNextInstallmentTool(database),
        ]
    )


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
        "informacion del credito loan-0001",
        "saldo de LOAN-0002",
        "Detalle de mi préstamo LOAN-0001",
    ],
)
def test_metamorphic_paraphrase_matrix_loan_details(query: str, in_memory_db: Database) -> None:
    """Metamorphic invariant: all paraphrases of loan inspection must route and execute
    get_loan_details, verify customer ownership, and prevent pseudo-tool-calls.
    """
    registry = _make_registry(in_memory_db)
    mock_client = MagicMock()
    metrics = OperationalMetrics()
    audit = AuditLogger()
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run(query, customer_id="CUST-0001")

    assert result.success is True
    assert result.customer_id == "CUST-0001"
    executed_tools = [c.tool_name for c in result.tool_calls]
    assert "get_loan_details" in executed_tools

    detail_record = next(c for c in result.tool_calls if c.tool_name == "get_loan_details")
    assert detail_record.result.success is True
    assert "get_loan_details(" not in (result.answer or "")
    assert metrics.get_counter("pseudo_tool_call_count") == 0


def test_metamorphic_cross_customer_ownership_defense() -> None:
    """Verify that loan belonging to another customer is strictly denied."""
    db = create_default_database()
    registry = ToolRegistry([GetLoanDetailsTool(db)])

    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Muéstrame LOAN-0003", customer_id="CUST-0001")

    assert result.success is False
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_loan_details"
    assert result.tool_calls[0].result.success is False
    assert "no pertenece" in (result.tool_calls[0].result.error or "")


def test_pseudo_tool_call_text_is_strictly_rejected_when_banking_data_required() -> None:
    """When account data is required, model text imitating a tool call is strictly rejected."""
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


def test_loan_detail_without_id_disambiguates_multi_loans() -> None:
    """Query without ID must not guess an ID when customer has multiple loans."""
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
    assert any(c.tool_name == "get_my_loans" for c in result.tool_calls)
    assert not any(c.tool_name == "get_loan_details" for c in result.tool_calls)

    call_messages = mock_client.chat.completions.create.call_args.kwargs["messages"]
    system_contents = [m["content"] for m in call_messages if m["role"] == "system"]
    assert any("NO adivines" in c for c in system_contents)


def test_system_prompt_v003_loaded_by_default() -> None:
    """Default system prompt enforces abstraction leak rules."""
    orchestrator = AgentOrchestrator(client=MagicMock())
    assert (
        "agent-system-v003" in orchestrator.system_prompt
        or "Abstraction Leak" in orchestrator.system_prompt
    )
    assert "NUNCA menciones nombres de herramientas" in orchestrator.system_prompt


def test_greeting_does_not_enumerate_categories_or_tool_names() -> None:
    """Greeting response remains courteous and concise without dumping tool names."""
    registry = _make_registry(create_default_database())
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content="¡Hola! Soy Aegis, tu asistente bancario. ¿En qué puedo ayudarte hoy?",
                    tool_calls=None,
                )
            )
        ]
    )
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Hola, ¿hay alguien?", customer_id="CUST-0001")

    assert result.success is True
    answer = (result.answer or "").lower()
    for internal_token in ("loan", "installment", "fee", "general", "get_", "search_"):
        assert internal_token not in answer
    assert len(result.tool_calls) == 0


def test_capability_query_response_uses_user_facing_language_only() -> None:
    """Capability query explains features in banking terms without tool names."""
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


def test_ambiguous_complaint_question_requests_clarification() -> None:
    """Ambiguous complaint question returns clarification without executing arbitrary tools."""
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client)
    result = orchestrator.run(
        "¿Qué requiero para que mi reclamo tenga efecto?", customer_id="CUST-0001"
    )

    assert result.success is True
    answer_lower = (result.answer or "").lower()
    assert any(token in answer_lower for token in ("aclar", "precis", "refier"))
    assert len(result.tool_calls) == 0
    assert mock_client.chat.completions.create.call_count == 0


def test_unknown_loan_id_returns_clean_ownership_error(in_memory_db: Database) -> None:
    """Nonexistent loan ID produces safe customer error without unhandled exception."""
    registry = _make_registry(in_memory_db)
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Muéstrame LOAN-9999", customer_id="CUST-0001")

    assert result.success is False
    answer_lower = (result.answer or "").lower()
    assert "no pertenece" in answer_lower or "no encontrado" in answer_lower
