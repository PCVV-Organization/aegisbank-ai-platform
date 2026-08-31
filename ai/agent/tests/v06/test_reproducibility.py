"""Tests for deterministic reproducibility of agent runs."""

from __future__ import annotations

from typing import Any
from unittest.mock import MagicMock

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.registry import ToolRegistry


class MockChatCompletion:
    """Deterministic mock chat completion for reproducibility testing."""

    def __init__(self, responses: list[dict[str, Any]]):
        self._responses = responses
        self._call_count = 0

    def create(self, **kwargs: Any) -> MagicMock:
        idx = min(self._call_count, len(self._responses) - 1)
        response_data = self._responses[idx]
        self._call_count += 1

        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        choice = mock_response.choices[0]
        choice.message = MagicMock()
        choice.message.content = response_data.get("content", "")
        tool_calls = response_data.get("tool_calls")
        if tool_calls:
            choice.message.tool_calls = tool_calls
        else:
            choice.message.tool_calls = None
        return mock_response


class TestDeterministicSessionContext:
    """Session customer_id is preserved across all tool calls."""

    def test_customer_id_in_context(self):
        context = AgentContext(session_customer_id="CUST-0001")
        assert context.session_customer_id == "CUST-0001"

    def test_customer_id_immutable(self):
        context = AgentContext(session_customer_id="CUST-0001")
        with pytest.raises(Exception):
            context.session_customer_id = "CUST-0002"


class TestDeterministicToolExecution:
    """Tool execution is deterministic - same input yields same output."""

    def test_same_arguments_same_result(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result1 = registry.execute("get_my_loans", {}, context)
        result2 = registry.execute("get_my_loans", {}, context)
        assert result1.as_dict() == result2.as_dict()

    def test_same_loan_id_same_result(self):
        registry = ToolRegistry()
        context = AgentContext(session_customer_id="CUST-0001")
        result1 = registry.execute("get_loan_details", {"loan_id": "LOAN-0001"}, context)
        result2 = registry.execute("get_loan_details", {"loan_id": "LOAN-0001"}, context)
        assert result1.as_dict() == result2.as_dict()


class TestDeterministicAgentRun:
    """Agent run with same inputs produces same outputs."""

    def test_same_message_same_customer_same_result(self):
        registry = ToolRegistry()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Same answer"
        mock_response.choices[0].message.tool_calls = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        orchestrator = AgentOrchestrator(registry=registry, client=mock_client, max_rounds=3)

        result1 = orchestrator.run("same message", customer_id="CUST-0001")
        result2 = orchestrator.run("same message", customer_id="CUST-0001")

        assert result1.answer == result2.answer
        assert result1.customer_id == result2.customer_id
        assert result1.rounds == result2.rounds

    def test_different_customer_different_context(self):
        registry = ToolRegistry()
        mock_response = MagicMock()
        mock_response.choices = [MagicMock()]
        mock_response.choices[0].message.content = "Done"
        mock_response.choices[0].message.tool_calls = None

        mock_client = MagicMock()
        mock_client.chat.completions.create.return_value = mock_response

        orchestrator = AgentOrchestrator(registry=registry, client=mock_client, max_rounds=3)

        result1 = orchestrator.run("test", customer_id="CUST-0001")
        result2 = orchestrator.run("test", customer_id="CUST-0002")

        assert result1.customer_id == "CUST-0001"
        assert result2.customer_id == "CUST-0002"


class TestDeterministicEvaluationDataset:
    """Evaluation dataset produces reproducible results."""

    def test_eval_cases_have_required_fields(self):
        from aegisbank_agent.evaluation import load_eval_cases

        cases = load_eval_cases()
        for case in cases:
            assert case.case_id
            assert case.category
            assert case.customer_id
            assert case.user_message
            assert case.expect_write_rejection in (True, False)

    def test_eval_cases_are_jsonl_serializable(self):
        import json

        from aegisbank_agent.evaluation import load_eval_cases

        cases = load_eval_cases()
        for case in cases:
            serialized = {
                "case_id": case.case_id,
                "category": case.category,
                "customer_id": case.customer_id,
                "user_message": case.user_message,
                "expected_tool": case.expected_tool,
                "expected_args": case.expected_args,
                "expect_tool_success": case.expect_tool_success,
                "expect_write_rejection": case.expect_write_rejection,
                "metric_types": [m.value for m in case.metric_types],
            }
            json.dumps(serialized)


class TestDeterministicSeedData:
    """Core Banking seed data is deterministic."""

    def test_seed_timestamp_is_deterministic(self):
        from mock_core_banking.persistence.seed import SEED_TIMESTAMP

        assert SEED_TIMESTAMP.year == 2026
        assert SEED_TIMESTAMP.month == 1
        assert SEED_TIMESTAMP.day == 1
