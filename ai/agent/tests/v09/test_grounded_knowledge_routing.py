"""Acceptance tests for deterministic knowledge routing and safe abstention."""

from __future__ import annotations

from types import SimpleNamespace
from unittest.mock import MagicMock

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.observability.metrics import OperationalMetrics
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool
from aegisbank_agent.tools.registry import ToolRegistry


def _knowledge_tool(content: str) -> SearchKnowledgeTool:
    retriever = MagicMock()
    retriever.search.return_value = [
        SimpleNamespace(
            chunk_id="CHK-001",
            title="Política de crédito",
            topic="creditos",
            content=content,
            document_id="DOC-001",
            document_version="v1",
        )
    ]
    return SearchKnowledgeTool(retriever=retriever)


def test_existing_knowledge_is_retrieved_before_generation() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(content="El plazo es 60 meses.", tool_calls=None)
            )
        ]
    )
    metrics = OperationalMetrics()
    registry = ToolRegistry(
        [_knowledge_tool("El crédito personal tiene un plazo máximo de 60 meses.")]
    )

    result = AgentOrchestrator(client=client, registry=registry, metrics=metrics).run(
        "¿Cuál es el plazo máximo del crédito personal?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert [call.tool_name for call in result.tool_calls] == ["search_knowledge"]
    assert metrics.get_counter("knowledge_tool_invoked_count") == 1
    client.chat.completions.create.assert_called_once()


def test_missing_product_evidence_abstains_without_generation() -> None:
    client = MagicMock()
    metrics = OperationalMetrics()
    registry = ToolRegistry(
        [_knowledge_tool("El crédito personal tiene un plazo máximo de 60 meses.")]
    )

    result = AgentOrchestrator(client=client, registry=registry, metrics=metrics).run(
        "¿Cuál es el plazo máximo para un crédito vehicular?", customer_id="CUST-0001"
    )

    assert result.success is True
    assert result.tool_calls[0].tool_name == "search_knowledge"
    assert "No encuentro información suficiente" in result.answer
    assert metrics.get_counter("knowledge_abstention_count") == 1
    client.chat.completions.create.assert_not_called()


def test_pseudo_tool_text_is_not_executed() -> None:
    client = MagicMock()
    client.chat.completions.create.return_value = SimpleNamespace(
        choices=[
            SimpleNamespace(
                message=SimpleNamespace(
                    content='search_knowledge("consulta conceptual")', tool_calls=None
                )
            )
        ]
    )
    registry = ToolRegistry([_knowledge_tool("Evidencia de prueba")])

    result = AgentOrchestrator(client=client, registry=registry).run(
        "Hola, explícame qué es una tool call.", customer_id="CUST-0001"
    )

    assert result.success is True
    assert result.tool_calls == []
    assert "search_knowledge" in result.answer
