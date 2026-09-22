"""Unit tests for AgentOrchestrator execution lifecycle and round limits."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


class DummyChoice:
    def __init__(self, message: Any):
        self.message = message


class DummyResponse:
    def __init__(self, message: Any):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[Any] | None = None):
        self.content = content
        self.tool_calls = tool_calls


class DummyFunctionCall:
    def __init__(self, name: str, arguments: str):
        self.name = name
        self.arguments = arguments


class DummyToolCall:
    def __init__(self, call_id: str, name: str, arguments: str):
        self.id = call_id
        self.function = DummyFunctionCall(name, arguments)


def test_agent_direct_response() -> None:
    """Agent handles conversational message with zero tool calls in exactly one round."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Hola, ¿en qué puedo ayudarte hoy?")
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=ToolRegistry([]),
    )
    result = orchestrator.run("Hola", customer_id="CUST-0001")
    assert result.success
    assert result.rounds == 1
    assert len(result.tool_calls) == 0
    assert "Hola" in result.answer


def test_model_cannot_execute_tool_outside_query_policy(tool_registry: ToolRegistry) -> None:
    """A registered tool remains forbidden when it was not granted to this query."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(DummyMessage(tool_calls=[DummyToolCall("unexpected", "get_my_loans", "{}")])),
        DummyResponse(DummyMessage(content="Hola, puedo orientarte.")),
    ]
    execute = MagicMock(wraps=tool_registry.execute)
    tool_registry.execute = execute
    result = AgentOrchestrator(client=mock_client, registry=tool_registry).run(
        "Hola", customer_id="CUST-0001"
    )
    execute.assert_not_called()
    assert len(result.tool_calls) == 1
    assert not result.tool_calls[0].result.success
    assert result.tool_calls[0].result.error == "TOOL_NOT_ALLOWED_FOR_QUERY"


def test_agent_tool_execution_flow(tool_registry: ToolRegistry) -> None:
    """Agent executes tool calls across multiple rounds and produces grounded answer."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.side_effect = [
        DummyResponse(
            DummyMessage(
                content=None,
                tool_calls=[DummyToolCall("call_1", "get_my_loans", "{}")],
            )
        ),
        DummyResponse(
            DummyMessage(
                content="Tienes 2 préstamos: LOAN-0001 y LOAN-0002.",
                tool_calls=None,
            )
        ),
    ]

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=tool_registry,
    )
    result = orchestrator.run("¿Cuáles son mis préstamos?", customer_id="CUST-0001")
    assert result.success
    assert result.rounds == 2
    assert len(result.tool_calls) == 1
    assert result.tool_calls[0].tool_name == "get_my_loans"
    assert result.tool_calls[0].result.success is True
    assert "LOAN-0001" in result.answer


@pytest.mark.parametrize("max_rounds", [1, 2, 3])
def test_agent_max_rounds_enforcement(tool_registry: ToolRegistry, max_rounds: int) -> None:
    """Agent aborts with failure when tool loop reaches max_rounds limit."""
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(
            content=None,
            tool_calls=[DummyToolCall("call_loop", "get_my_loans", "{}")],
        )
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=tool_registry,
        max_rounds=max_rounds,
    )
    result = orchestrator.run("Mis préstamos", customer_id="CUST-0001")
    assert not result.success
    assert result.rounds == max_rounds
    assert len(result.tool_calls) == max_rounds
    assert "límite" in result.answer.lower() or "maximum" in result.answer.lower()


def test_agent_default_and_custom_max_rounds() -> None:
    """Agent initializes with default 3 rounds or custom setting."""
    mock_client = MagicMock()
    default_orchestrator = AgentOrchestrator(registry=ToolRegistry(), client=mock_client)
    assert default_orchestrator._max_rounds == 3

    custom_orchestrator = AgentOrchestrator(
        registry=ToolRegistry(), max_rounds=5, client=mock_client
    )
    assert custom_orchestrator._max_rounds == 5


def test_agent_uses_tool_choice_auto_for_unconstrained_queries() -> None:
    """Agent defaults to tool_choice='auto' when query is unconstrained."""
    registry = ToolRegistry()
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Respuesta sin herramientas.")
    )

    orchestrator = AgentOrchestrator(registry=registry, client=mock_client)
    orchestrator.run("Consulta general", customer_id="CUST-0001")
    call_kwargs = mock_client.chat.completions.create.call_args
    assert call_kwargs is not None
    assert call_kwargs.kwargs.get("tool_choice") == "auto"
