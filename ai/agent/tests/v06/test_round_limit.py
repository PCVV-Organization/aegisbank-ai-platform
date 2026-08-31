"""Tests for max tool rounds enforcement."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.tools.registry import ToolRegistry


class MockChatCompletions:
    """Mock chat completions that returns a sequence of responses."""

    def __init__(self, responses: list[dict[str, Any]]):
        self._responses = responses
        self._index = 0

    def create(self, **kwargs: Any) -> MagicMock:
        if self._index < len(self._responses):
            response = self._responses[self._index]
            self._index += 1
        else:
            response = {"choices": [{"message": {"content": "Final answer", "tool_calls": None}}]}
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        choice = mock_response.choices[0]
        choice.message = MagicMock()
        choice.message.content = response.get("content", "")
        tool_calls = response.get("tool_calls")
        if tool_calls:
            choice.message.tool_calls = tool_calls
        else:
            choice.message.tool_calls = None
        return mock_response


class MockClient:
    """Mock OpenAI-compatible client."""

    def __init__(self, responses: list[dict[str, Any]]):
        self.chat = MagicMock()
        self.chat.completions = MockChatCompletions(responses)


class TestRoundLimitEnforcement:
    """Agent must stop after max_rounds even if no final answer."""

    def test_respects_max_rounds_limit(self):
        registry = ToolRegistry()
        tool_call = MagicMock()
        tool_call.id = "call_1"
        tool_call.function = MagicMock()
        tool_call.function.name = "get_my_loans"
        tool_call.function.arguments = "{}"

        responses = [
            {"tool_calls": [tool_call]},
            {"tool_calls": [tool_call]},
            {"tool_calls": [tool_call]},
        ] * 10

        mock_client = MockClient(responses)
        orchestrator = AgentOrchestrator(
            registry=registry,
            client=mock_client,
            max_rounds=3,
        )
        result = orchestrator.run("test message", customer_id="CUST-0001")
        assert result.rounds == 3
        assert (
            "límite" in result.answer.lower()
            or "maximum" in result.answer.lower()
            or not result.success
        )

    def test_max_rounds_default_is_three(self):
        registry = ToolRegistry()
        orchestrator = AgentOrchestrator(registry=registry)
        assert orchestrator._max_rounds == 3

    def test_max_rounds_customizable(self):
        registry = ToolRegistry()
        orchestrator = AgentOrchestrator(registry=registry, max_rounds=5)
        assert orchestrator._max_rounds == 5


class TestRoundCounting:
    """Round counter increments correctly."""

    def test_single_round_when_no_tool_calls(self):
        registry = ToolRegistry()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Direct answer"
        mock_response.choices[0].message.tool_calls = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        orchestrator = AgentOrchestrator(registry=registry, client=mock_client, max_rounds=3)
        result = orchestrator.run("hello", customer_id="CUST-0001")
        assert result.rounds == 1
        assert result.success is True


class TestToolChoiceAuto:
    """Agent uses tool_choice=auto as required."""

    def test_creates_with_tool_choice_auto(self):
        registry = ToolRegistry()
        mock_client = MagicMock()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "test"
        mock_response.choices[0].message.tool_calls = None
        mock_client.chat.completions.create.return_value = mock_response

        orchestrator = AgentOrchestrator(registry=registry, client=mock_client)
        orchestrator.run("test", customer_id="CUST-0001")
        call_kwargs = mock_client.chat.completions.create.call_args
        assert call_kwargs is not None
        assert call_kwargs.kwargs.get("tool_choice") == "auto"
