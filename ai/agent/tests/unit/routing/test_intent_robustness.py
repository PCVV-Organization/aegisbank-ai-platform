"""Unit tests for intent robustness, metamorphic paraphrasing, and pseudo-call defense."""

from __future__ import annotations

import json
from unittest.mock import MagicMock

import pytest
from mock_core_banking.persistence.database import Database

import aegisbank_agent.agent as agent_module
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


def test_malformed_function_serialization_is_not_exposed_to_customer() -> None:
    """Provider protocol text must never leak into a visible banking answer."""
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetLoanDetailsTool(db)])
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(
        _Message(content='functools([{"name":"search_knowledge"}])')
    )

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("¿Qué estados puede tener un préstamo?", customer_id="CUST-0001")

    assert result.success is True
    assert "functools" not in result.answer
    assert "interpretar" in result.answer


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


def test_first_person_highest_balance_query_enforces_account_data() -> None:
    """Complex first-person comparative query triggers account data pre-fetching."""
    from aegisbank_agent.knowledge_routing import account_tool_allowlist, requires_account_data

    query = (
        "¿dime cual es el prestamo con más saldo pendiente que tengo y que fechas de pago tengo??"
    )
    assert requires_account_data(query) is True
    allowlist = account_tool_allowlist(query)
    assert "get_my_loans" in allowlist
    assert "get_next_installment" in allowlist


def test_comparative_loan_query_plan_picks_highest_balance_without_llm() -> None:
    """Comparative query finds highest balance loan deterministically with 0 rounds."""
    db = create_default_database()
    registry = ToolRegistry([GetMyLoansTool(db), GetLoanDetailsTool(db)])
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)

    result = orchestrator.run(
        "¿cuál de mis préstamos tiene más saldo pendiente?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert result.rounds == 0
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_my_loans"
    assert "LOAN-0001" in result.answer
    assert "2800" in result.answer
    assert mock_client.chat.completions.create.call_count == 0


def test_comparative_query_with_installment_dates_executes_deterministically() -> None:
    """Compound comparative query executes get_my_loans and get_next_installment with 0 rounds."""
    db = create_default_database()
    registry = ToolRegistry(
        [
            GetMyLoansTool(db),
            GetLoanDetailsTool(db),
            GetNextInstallmentTool(db),
        ]
    )
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)

    result = orchestrator.run(
        "¿dime cual es el prestamo con más saldo pendiente que tengo y que fechas de pago tengo??",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert result.rounds == 0
    assert len(result.tool_calls) == 2
    executed_names = [tc.tool_name for tc in result.tool_calls]
    assert executed_names == ["get_my_loans", "get_next_installment"]
    assert "LOAN-0001" in result.answer
    assert "2800" in result.answer
    assert "Cuota vencida" in result.answer or "Próxima cuota" in result.answer
    assert "venció" in result.answer or "vence" in result.answer
    assert mock_client.chat.completions.create.call_count == 0


def test_next_payment_query_prefetches_installments_without_llm_call() -> None:
    """A generic due-date question resolves the earliest real customer installment."""
    db = create_default_database()
    registry = ToolRegistry(
        [
            GetMyLoansTool(db),
            GetLoanDetailsTool(db),
            GetNextInstallmentTool(db),
        ]
    )
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)

    result = orchestrator.run(
        "¿Cuándo es mi próxima fecha de pago?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert result.rounds == 0
    assert [call.tool_name for call in result.tool_calls] == [
        "get_my_loans",
        "get_next_installment",
        "get_next_installment",
    ]
    assert "vence" in result.answer or "venció" in result.answer
    assert mock_client.chat.completions.create.call_count == 0


def test_subsequent_anaphora_resolves_loan_after_comparative_query() -> None:
    """After a comparative loan query, subsequent turn resolves 'el último préstamo' to winner."""
    db = create_default_database()
    registry = ToolRegistry(
        [
            GetMyLoansTool(db),
            GetLoanDetailsTool(db),
            GetNextInstallmentTool(db),
        ]
    )
    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)

    # Turn 1: Comparative query
    result1 = orchestrator.run(
        "¿cuál es el préstamo con mayor saldo pendiente?",
        customer_id="CUST-0001",
        session_id="session-test-anaphora",
    )
    assert result1.success is True
    assert "LOAN-0001" in result1.answer

    # Turn 2: Anaphora resolution
    result2 = orchestrator.run(
        "¿cuál fue el último préstamo porque el que te consulté?",
        customer_id="CUST-0001",
        session_id="session-test-anaphora",
    )
    assert result2.success is True
    assert result2.rounds == 0
    assert len(result2.tool_calls) == 1
    assert result2.tool_calls[0].tool_name == "get_loan_details"
    assert result2.tool_calls[0].arguments == {"loan_id": "LOAN-0001"}
    assert "LOAN-0001" in result2.answer


def test_placeholder_leak_in_llm_answer_is_intercepted() -> None:
    """When LLM leaks placeholders, orchestrator intercepts it with safe banking refusal."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(
        _Message(
            content=(
                "El préstamo con el mayor saldo pendiente es [Nombre del Préstamo]. "
                "Las fechas de pago son [Fecha de Pago 1], [Fecha de Pago 2]."
            )
        )
    )
    orchestrator = AgentOrchestrator(client=mock_client)
    result = orchestrator.run("Consulta general", customer_id="CUST-0001")

    assert result.success is False
    assert "PLACEHOLDER_LEAK" in (result.error or "")
    assert "No pude consultar la información verificada" in result.answer
    assert "[Nombre" not in result.answer


def test_fake_waiting_process_hallucination_is_intercepted() -> None:
    """When LLM outputs process hallucination / fake waiting, orchestrator intercepts it."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(
        _Message(
            content=(
                "Dame un momento... [Breve pausa mientras el asistente realiza la consulta]. "
                "Tu saldo está disponible."
            )
        )
    )
    orchestrator = AgentOrchestrator(client=mock_client)
    result = orchestrator.run("Consulta general", customer_id="CUST-0001")

    assert result.success is False
    assert "PROCESS_HALLUCINATION" in (result.error or "")
    assert "No pude consultar la información verificada" in result.answer
    assert "Breve pausa" not in result.answer


def test_fake_tool_claim_without_tools_is_intercepted() -> None:
    """When LLM claims to retrieve data without tool execution, orchestrator rejects."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = _Response(
        _Message(content="He encontrado los detalles de tus préstamos. Todo está en orden.")
    )
    orchestrator = AgentOrchestrator(client=mock_client, registry=ToolRegistry([]))
    result = orchestrator.run("Consulta sobre mi situación bancaria", customer_id="CUST-0001")

    assert result.success is False
    assert "FALSE_TOOL_EXECUTION_CLAIM" in (result.error or "")
    assert "No pude consultar la información verificada" in result.answer


def test_foundry_client_uses_bounded_configured_timeout_and_retries(monkeypatch) -> None:
    """The local client leaves enough time for normal CPU/GPU inference."""
    fake_openai = MagicMock()
    monkeypatch.setattr(agent_module, "OpenAI", fake_openai)
    monkeypatch.delenv("AEGISBANK_FOUNDRY_TIMEOUT_SECONDS", raising=False)
    monkeypatch.delenv("AEGISBANK_FOUNDRY_MAX_RETRIES", raising=False)

    AgentOrchestrator(base_url="http://127.0.0.1:51747/v1")

    assert fake_openai.call_args.kwargs["timeout"] == 45.0
    assert fake_openai.call_args.kwargs["max_retries"] == 2


def test_foundry_client_honors_local_timeout_override(monkeypatch) -> None:
    """An operator can lower or raise the bounded local-client timeout explicitly."""
    fake_openai = MagicMock()
    monkeypatch.setattr(agent_module, "OpenAI", fake_openai)
    monkeypatch.setenv("AEGISBANK_FOUNDRY_TIMEOUT_SECONDS", "60")
    monkeypatch.setenv("AEGISBANK_FOUNDRY_MAX_RETRIES", "1")

    AgentOrchestrator(base_url="http://127.0.0.1:51747/v1")

    assert fake_openai.call_args.kwargs["timeout"] == 60.0
    assert fake_openai.call_args.kwargs["max_retries"] == 1


def test_foundry_busy_response_is_retried_before_returning_an_error(monkeypatch) -> None:
    """Transient Foundry contention is retried without inventing a response."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        Exception("Error code: 500 - Infer Request is busy"),
        _Response(_Message(content="¡Hola! ¿Cómo puedo ayudarte hoy?")),
    ]
    monkeypatch.setenv("AEGISBANK_FOUNDRY_BUSY_MAX_RETRIES", "1")
    monkeypatch.setenv("AEGISBANK_FOUNDRY_BUSY_RETRY_BASE_SECONDS", "0")
    orchestrator = AgentOrchestrator(client=mock_client, registry=ToolRegistry([]))

    result = orchestrator.run("Di hola", customer_id="CUST-0001")

    assert result.success is True
    assert result.answer == "¡Hola! ¿Cómo puedo ayudarte hoy?"
    assert mock_client.chat.completions.create.call_count == 2


def test_foundry_timeout_returns_safe_error_without_hallucination() -> None:
    """LLM timeout returns structured safe error and never hallucinates account data."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = Exception("Request timed out.")
    orchestrator = AgentOrchestrator(client=mock_client)

    result = orchestrator.run("Explícame las opciones de financiamiento", customer_id="CUST-0001")

    assert result.success is False
    assert "Request timed out." in (result.error or "")
    assert "Error al comunicar con Foundry Local" in result.answer
    assert "[" not in result.answer
