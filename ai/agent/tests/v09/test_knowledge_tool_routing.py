"""Acceptance tests for Policy-Enforced Grounded Knowledge Tool Routing in v0.9.1."""

from __future__ import annotations

from unittest.mock import MagicMock

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.knowledge_routing import requires_authorized_knowledge
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.observability.tracer import get_memory_exporter, setup_tracer
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry


class DummyChoice:
    def __init__(self, message: object):
        self.message = message


class DummyResponse:
    def __init__(self, message: object):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


def test_requires_authorized_knowledge_classification() -> None:
    query_vehicular = "¿Cuáles son los plazos máximos para un crédito vehicular?"
    assert requires_authorized_knowledge(query_vehicular) is True
    assert requires_authorized_knowledge("¿Cuál es la tasa de interés de los créditos?") is True
    assert requires_authorized_knowledge("¿Qué comisiones cobran?") is True
    assert requires_authorized_knowledge("Hola, buenos días") is False
    assert requires_authorized_knowledge("Muchas gracias por la ayuda") is False


def test_existing_knowledge_triggers_search_and_grounded_answer() -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = ToolRegistry([SearchKnowledgeTool()])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(
            content="El plazo para un crédito personal en AegisBank es entre 6 y 60 meses."
        )
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    result = orchestrator.run(
        "¿Cuáles son los plazos de un crédito personal?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert result.tool_calls[0].result.success is True
    assert "6 y 60 meses" in result.answer

    assert metrics.get_counter("knowledge_required_count") == 1
    assert metrics.get_counter("knowledge_tool_invoked_count") == 1
    assert metrics.get_counter("knowledge_abstention_count") == 0


def test_missing_knowledge_triggers_search_and_explicit_abstention() -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()
    registry = ToolRegistry([SearchKnowledgeTool()])

    mock_client = MagicMock()
    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
        audit_logger=audit,
    )

    # Missing product "crédito vehicular" in synthetic catalog
    result = orchestrator.run(
        "¿Cuáles son los plazos máximos para un crédito vehicular?",
        customer_id="CUST-0001",
    )

    assert result.success is True
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert "No encuentro información suficiente" in result.answer

    assert metrics.get_counter("knowledge_required_count") == 1
    assert metrics.get_counter("knowledge_tool_invoked_count") == 1
    assert metrics.get_counter("knowledge_abstention_count") == 1


def test_greeting_does_not_force_knowledge_search() -> None:
    metrics = OperationalMetrics()
    registry = ToolRegistry([SearchKnowledgeTool()])

    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="¡Hola! ¿En qué puedo ayudarte hoy?")
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=registry,
        metrics=metrics,
    )

    result = orchestrator.run("Hola, buenas tardes", customer_id="CUST-0001")

    assert result.success is True
    assert len(result.tool_calls) == 0
    assert metrics.get_counter("knowledge_required_count") == 0
    assert metrics.get_counter("knowledge_tool_invoked_count") == 0
    assert "¡Hola!" in result.answer


def test_textual_pseudo_call_is_not_parsed_as_tool() -> None:
    """Ensure raw string containing search_knowledge(...) is not parsed as a tool."""
    registry = ToolRegistry([SearchKnowledgeTool()])
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content='Para responder, necesito buscar: search_knowledge("plazos")')
    )

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("Hola, ¿cómo estás?", customer_id="CUST-0001")

    # Non-banking query: no tools executed despite pseudo-call text in answer
    assert len(result.tool_calls) == 0
    assert 'search_knowledge("plazos")' in result.answer


def test_knowledge_routing_otel_tracing_spans() -> None:
    setup_tracer()
    exporter = get_memory_exporter()
    exporter.clear()

    registry = ToolRegistry([SearchKnowledgeTool()])
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Tasa fija según contrato.")
    )

    orchestrator = AgentOrchestrator(client=mock_client, registry=registry)
    result = orchestrator.run("¿Cuál es la tasa de interés?", customer_id="CUST-0001")

    assert result.success is True
    spans = exporter.get_finished_spans()
    span_names = [s.name for s in spans]
    assert "agent.run" in span_names
    assert "retrieval.search_knowledge" in span_names
