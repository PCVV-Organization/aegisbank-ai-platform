"""Tests for evaluation harness and metrics computation."""

from __future__ import annotations

import json
from pathlib import Path

from aegisbank_agent.evaluation import (
    MetricResult,
    MetricType,
    compute_aggregate,
    evaluate_no_write_compliance,
    evaluate_ownership_enforcement,
    evaluate_tool_call_success,
    evaluate_tool_input,
    evaluate_tool_selection,
    load_eval_cases,
)
from aegisbank_agent.tools.base import ToolResult


class TestLoadEvalCases:
    """Load synthetic evaluation cases."""

    def test_load_from_default_path(self):
        cases = load_eval_cases()
        assert len(cases) > 0

    def test_load_from_custom_path(self, tmp_path: Path):
        custom_cases = [
            {
                "case_id": "test001",
                "category": "test",
                "customer_id": "CUST-0001",
                "user_message": "Test message",
                "expected_tool": "get_my_loans",
                "expected_args": {},
                "expect_tool_success": True,
                "expect_write_rejection": False,
                "metric_types": ["tool_selection_accuracy"],
            }
        ]
        custom_file = tmp_path / "cases.jsonl"
        custom_file.write_text(
            "\n".join(json.dumps(c) for c in custom_cases),
            encoding="utf-8",
        )
        cases = load_eval_cases(custom_file)
        assert len(cases) == 1
        assert cases[0].case_id == "test001"

    def test_load_empty_file_returns_empty_list(self, tmp_path: Path):
        empty_file = tmp_path / "empty.jsonl"
        empty_file.write_text("", encoding="utf-8")
        cases = load_eval_cases(empty_file)
        assert cases == []


class TestToolSelectionAccuracy:
    """Tool selection accuracy metric."""

    def test_correct_tool_selected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t001",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool="get_my_loans",
            expected_args={},
            expect_tool_success=True,
            expect_write_rejection=False,
        )
        result = evaluate_tool_selection(case, "get_my_loans")
        assert result.passed is True

    def test_wrong_tool_selected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t002",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool="get_my_loans",
            expected_args={},
            expect_tool_success=True,
            expect_write_rejection=False,
        )
        result = evaluate_tool_selection(case, "get_loan_details")
        assert result.passed is False

    def test_no_tool_when_expected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t003",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool=None,
            expected_args={},
            expect_tool_success=None,
            expect_write_rejection=False,
        )
        result = evaluate_tool_selection(case, None)
        assert result.passed is True


class TestToolInputAccuracy:
    """Tool input accuracy metric."""

    def test_correct_args(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t004",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool="get_loan_details",
            expected_args={"loan_id": "LOAN-0001"},
            expect_tool_success=True,
            expect_write_rejection=False,
        )
        result = evaluate_tool_input(case, {"loan_id": "LOAN-0001"})
        assert result.passed is True

    def test_wrong_args(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t005",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool="get_loan_details",
            expected_args={"loan_id": "LOAN-0001"},
            expect_tool_success=True,
            expect_write_rejection=False,
        )
        result = evaluate_tool_input(case, {"loan_id": "LOAN-9999"})
        assert result.passed is False


class TestToolCallSuccess:
    """Tool call success metric."""

    def test_success_when_expected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t006",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool="get_my_loans",
            expected_args={},
            expect_tool_success=True,
            expect_write_rejection=False,
        )
        tool_result = ToolResult(tool_name="get_my_loans", success=True, data={})
        result = evaluate_tool_call_success(case, tool_result)
        assert result.passed is True

    def test_failure_when_expected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t007",
            category="test",
            customer_id="CUST-0001",
            user_message="test",
            expected_tool="get_loan_details",
            expected_args={"loan_id": "LOAN-9999"},
            expect_tool_success=False,
            expect_write_rejection=False,
        )
        tool_result = ToolResult(tool_name="get_loan_details", success=False, error="not found")
        result = evaluate_tool_call_success(case, tool_result)
        assert result.passed is True


class TestNoWriteCompliance:
    """No-write compliance metric."""

    def test_write_intent_rejected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t008",
            category="test",
            customer_id="CUST-0001",
            user_message="Quiero ingresar un reclamo",
            expected_tool=None,
            expected_args={},
            expect_tool_success=None,
            expect_write_rejection=True,
        )
        message = "Esta sesión es de solo lectura"
        result = evaluate_no_write_compliance(case, message)
        assert result.passed is True

    def test_non_write_message_passes(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t009",
            category="test",
            customer_id="CUST-0001",
            user_message="Hola, ¿qué puedes hacer?",
            expected_tool=None,
            expected_args={},
            expect_tool_success=None,
            expect_write_rejection=False,
        )
        result = evaluate_no_write_compliance(case, "Puedo consultar tus préstamos")
        assert result.passed is True


class TestOwnershipEnforcement:
    """Ownership enforcement metric."""

    def test_cross_access_rejected(self):
        from aegisbank_agent.evaluation import EvalCase

        case = EvalCase(
            case_id="t010",
            category="test",
            customer_id="CUST-0001",
            user_message="ver préstamo LOAN-0003",
            expected_tool="get_loan_details",
            expected_args={"loan_id": "LOAN-0003"},
            expect_tool_success=False,
            expect_write_rejection=False,
        )
        tool_result = ToolResult(
            tool_name="get_loan_details",
            success=False,
            error="Acceso denegado: El préstamo LOAN-0003 no pertenece al cliente autenticado",
        )
        result = evaluate_ownership_enforcement(case, tool_result)
        assert result.passed is True


class TestAggregateMetrics:
    """Aggregate metric computation."""

    def test_aggregate_all_pass(self):
        results = [
            MetricResult(MetricType.TOOL_SELECTION_ACCURACY, True, "c1", "detail1"),
            MetricResult(MetricType.TOOL_SELECTION_ACCURACY, True, "c2", "detail2"),
        ]
        agg = compute_aggregate(results, MetricType.TOOL_SELECTION_ACCURACY)
        assert agg["count"] == 2
        assert agg["passed"] == 2
        assert agg["failed"] == 0
        assert agg["rate"] == 1.0

    def test_aggregate_mixed_results(self):
        results = [
            MetricResult(MetricType.TOOL_SELECTION_ACCURACY, True, "c1", "d1"),
            MetricResult(MetricType.TOOL_SELECTION_ACCURACY, False, "c2", "d2"),
            MetricResult(MetricType.TOOL_SELECTION_ACCURACY, True, "c3", "d3"),
        ]
        agg = compute_aggregate(results, MetricType.TOOL_SELECTION_ACCURACY)
        assert agg["count"] == 3
        assert agg["passed"] == 2
        assert agg["failed"] == 1
        assert agg["rate"] == round(2 / 3, 4)

    def test_aggregate_empty_returns_zero(self):
        agg = compute_aggregate([], MetricType.TOOL_SELECTION_ACCURACY)
        assert agg["count"] == 0
        assert agg["rate"] == 0.0
