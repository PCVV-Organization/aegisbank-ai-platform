"""Tests for AgentOrchestrator loop and behavior."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.tools.registry import ToolRegistry


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


def test_agent_tool_execution_flow(tool_registry: ToolRegistry) -> None:
    mock_client = MagicMock()
    # First turn: model requests get_my_loans
    # Second turn: model provides final answer with loans summary
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


def test_agent_max_rounds_exceeded(tool_registry: ToolRegistry) -> None:
    mock_client = MagicMock()
    # Model endlessly requests tool calls
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(
            content=None,
            tool_calls=[DummyToolCall("call_loop", "get_my_loans", "{}")],
        )
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=tool_registry,
        max_rounds=2,
    )
    result = orchestrator.run("Mis préstamos", customer_id="CUST-0001")
    assert not result.success
    assert result.rounds == 2
    assert len(result.tool_calls) == 2
    assert "límite máximo" in result.answer
