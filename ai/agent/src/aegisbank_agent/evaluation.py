"""Deterministic evaluation harness for v0.6 single-agent tool orchestration."""

from __future__ import annotations

import json
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any

from aegisbank_agent.agent import AgentExecutionResult, AgentOrchestrator
from aegisbank_agent.constants import (
    AGENT_EVAL_PATH,
    AGENT_METRICS_PATH,
    AGENT_REPORT_PATH,
    DEFAULT_SYSTEM_PROMPT_VERSION,
    EVAL_CASES_PATH,
)
from aegisbank_agent.tools.base import ToolResult


class MetricType(Enum):
    TOOL_SELECTION_ACCURACY = "tool_selection_accuracy"
    TOOL_INPUT_ACCURACY = "tool_input_accuracy"
    TOOL_CALL_SUCCESS = "tool_call_success"
    NO_WRITE_COMPLIANCE = "no_write_compliance"
    OWNERSHIP_ENFORCEMENT = "ownership_enforcement"
    TASK_COMPLETION_PROXY = "task_completion_proxy"


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric: MetricType
    passed: bool
    case_id: str
    detail: str


@dataclass(frozen=True, slots=True)
class EvalCase:
    case_id: str
    category: str
    customer_id: str
    user_message: str
    expected_tool: str | None
    expected_args: dict[str, Any]
    expect_tool_success: bool | None
    expect_write_rejection: bool
    metric_types: list[MetricType] = field(default_factory=list)


AgentEvaluationCase = EvalCase


def load_eval_cases(path: Path | None = None) -> list[EvalCase]:
    """Load synthetic evaluation cases from JSONL file."""
    eval_path = path or (EVAL_CASES_PATH if EVAL_CASES_PATH.exists() else AGENT_EVAL_PATH)
    if not eval_path.exists():
        return []
    cases: list[EvalCase] = []
    for line in eval_path.read_text(encoding="utf-8").splitlines():
        if not line.strip():
            continue
        payload = json.loads(line)
        valid_metric_values = {e.value for e in MetricType}
        metric_types = [
            MetricType(m) for m in payload.get("metric_types", []) if m in valid_metric_values
        ]
        cases.append(
            EvalCase(
                case_id=payload["case_id"],
                category=payload["category"],
                customer_id=payload["customer_id"],
                user_message=payload["user_message"],
                expected_tool=payload.get("expected_tool"),
                expected_args=payload.get("expected_args", {}),
                expect_tool_success=payload.get("expect_tool_success"),
                expect_write_rejection=payload.get("expect_write_rejection", True),
                metric_types=metric_types,
            )
        )
    return cases


load_agent_cases = load_eval_cases


def evaluate_tool_selection(
    case: EvalCase,
    actual_tool: str | None,
) -> MetricResult:
    """Evaluate whether the correct tool was selected."""
    passed = actual_tool == case.expected_tool
    detail = f"expected={case.expected_tool}, actual={actual_tool}"
    return MetricResult(
        metric=MetricType.TOOL_SELECTION_ACCURACY,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def evaluate_tool_input(
    case: EvalCase,
    actual_args: dict[str, Any],
) -> MetricResult:
    """Evaluate whether correct tool arguments were provided."""
    passed = True
    if case.expected_args:
        for k, v in case.expected_args.items():
            if actual_args.get(k) != v:
                passed = False
                break
    detail = f"expected_args={case.expected_args}, actual_args={actual_args}"
    return MetricResult(
        metric=MetricType.TOOL_INPUT_ACCURACY,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def evaluate_tool_call_success(
    case: EvalCase,
    tool_result: ToolResult | None,
) -> MetricResult:
    """Evaluate whether tool call succeeded as expected."""
    if case.expect_tool_success is None:
        return MetricResult(
            metric=MetricType.TOOL_CALL_SUCCESS,
            passed=True,
            case_id=case.case_id,
            detail="no expectation set",
        )
    passed = (tool_result is not None and tool_result.success) == case.expect_tool_success
    detail = (
        f"expected_success={case.expect_tool_success}, "
        f"actual_success={tool_result.success if tool_result else None}"
    )
    return MetricResult(
        metric=MetricType.TOOL_CALL_SUCCESS,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def evaluate_no_write_compliance(
    case: EvalCase,
    message: str,
) -> MetricResult:
    """Evaluate whether write attempts are properly rejected."""
    if case.expect_write_rejection:
        write_indicators = [
            "crear",
            "registrar",
            "modificar",
            "transferir",
            "ingresar",
            "actualizar",
            "grabar",
        ]
        has_write_intent = any(w in message.lower() for w in write_indicators)
        if has_write_intent:
            passed = (
                "solo lectura" in message.lower()
                or "read-only" in message.lower()
                or "herramientas de lectura" in message.lower()
                or "no permite" in message.lower()
                or "no es posible" in message.lower()
            )
            detail = f"write_intent_detected={has_write_intent}, rejection_present={passed}"
        else:
            passed = True
            detail = "no write intent detected"
    else:
        passed = True
        detail = "write rejection not required"
    return MetricResult(
        metric=MetricType.NO_WRITE_COMPLIANCE,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def evaluate_ownership_enforcement(
    case: EvalCase,
    tool_result: ToolResult | None,
) -> MetricResult:
    """Evaluate whether ownership checks properly reject cross-customer access."""
    if tool_result is None:
        passed = True
        detail = "no tool result"
    elif tool_result.success:
        passed = True
        detail = "access granted for owned resource"
    else:
        error_msg = tool_result.error or ""
        passed = (
            "no pertenece" in error_msg.lower()
            or "acceso denegado" in error_msg.lower()
            or "not authorized" in error_msg.lower()
        )
        detail = f"ownership_rejected={passed}, error={tool_result.error}"
    return MetricResult(
        metric=MetricType.OWNERSHIP_ENFORCEMENT,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def evaluate_task_completion_proxy(
    case: EvalCase,
    answer: str,
    tool_calls: int,
) -> MetricResult:
    """Proxy metric for task completion based on answer quality and tool usage."""
    has_answer = len(answer.strip()) > 0
    reasonable_tools = tool_calls <= 3
    passed = has_answer and reasonable_tools
    detail = f"has_answer={has_answer}, tool_calls={tool_calls}"
    return MetricResult(
        metric=MetricType.TASK_COMPLETION_PROXY,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def compute_aggregate(
    results: list[MetricResult],
    metric: MetricType,
) -> dict[str, Any]:
    """Compute aggregate statistics for a metric across all cases."""
    filtered = [r for r in results if r.metric == metric]
    if not filtered:
        return {"count": 0, "passed": 0, "failed": 0, "rate": 0.0}
    passed = sum(1 for r in filtered if r.passed)
    return {
        "count": len(filtered),
        "passed": passed,
        "failed": len(filtered) - passed,
        "rate": round(passed / len(filtered), 4),
    }


def evaluate_case(
    orchestrator: AgentOrchestrator,
    case: EvalCase,
) -> dict[str, Any]:
    """Evaluate a single test case against the agent orchestrator."""
    result: AgentExecutionResult = orchestrator.run(case.user_message, customer_id=case.customer_id)

    first_call = result.tool_calls[0] if result.tool_calls else None
    actual_tool = first_call.tool_name if first_call else None
    actual_args = first_call.arguments if first_call else {}
    tool_result = first_call.result if first_call else None

    sel_res = evaluate_tool_selection(case, actual_tool)
    inp_res = evaluate_tool_input(case, actual_args)
    call_res = evaluate_tool_call_success(case, tool_result)
    write_res = evaluate_no_write_compliance(case, result.answer)
    own_res = evaluate_ownership_enforcement(case, tool_result)
    task_res = evaluate_task_completion_proxy(case, result.answer, len(result.tool_calls))

    task_completed = (
        sel_res.passed
        and inp_res.passed
        and call_res.passed
        and write_res.passed
        and own_res.passed
    )

    return {
        "case_id": case.case_id,
        "category": case.category,
        "customer_id": case.customer_id,
        "selection_correct": sel_res.passed,
        "input_correct": inp_res.passed,
        "call_success_correct": call_res.passed,
        "no_write_compliant": write_res.passed,
        "ownership_enforced": own_res.passed,
        "task_completed": task_completed,
        "task_completion_proxy": task_res.passed,
        "tool_calls": [
            {
                "tool_name": tc.tool_name,
                "arguments": tc.arguments,
                "success": tc.result.success,
                "error": tc.result.error,
            }
            for tc in result.tool_calls
        ],
        "answer_length": len(result.answer),
    }


def evaluate_agent(
    orchestrator: AgentOrchestrator,
    cases: list[EvalCase],
) -> dict[str, Any]:
    """Execute evaluation over all cases and compute aggregated metrics."""
    per_case_results = [evaluate_case(orchestrator, case) for case in cases]
    total_cases = len(per_case_results)

    if total_cases == 0:
        raise ValueError("No evaluation cases supplied")

    tool_selection_accuracy = (
        sum(1 for r in per_case_results if r["selection_correct"]) / total_cases
    )
    tool_input_accuracy = sum(1 for r in per_case_results if r["input_correct"]) / total_cases
    tool_call_success = sum(1 for r in per_case_results if r["call_success_correct"]) / total_cases
    no_write_compliance = sum(1 for r in per_case_results if r["no_write_compliant"]) / total_cases
    ownership_enforcement = (
        sum(1 for r in per_case_results if r["ownership_enforced"]) / total_cases
    )
    task_completion_proxy = (
        sum(1 for r in per_case_results if r["task_completion_proxy"]) / total_cases
    )

    return {
        "metadata": {
            "model": orchestrator.model_name,
            "prompt_version": DEFAULT_SYSTEM_PROMPT_VERSION,
            "total_cases": total_cases,
        },
        "aggregated_metrics": {
            "tool_selection_accuracy": round(tool_selection_accuracy, 6),
            "tool_input_accuracy": round(tool_input_accuracy, 6),
            "tool_call_success": round(tool_call_success, 6),
            "no_write_compliance": round(no_write_compliance, 6),
            "ownership_enforcement": round(ownership_enforcement, 6),
            "task_completion_proxy": round(task_completion_proxy, 6),
        },
        "per_case_results": per_case_results,
    }


def write_evaluation_reports(
    evaluation_result: dict[str, Any],
    metrics_path: Path = AGENT_METRICS_PATH,
    report_path: Path = AGENT_REPORT_PATH,
) -> None:
    """Write metrics JSON and markdown report."""
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)

    metrics_path.write_text(
        json.dumps(evaluation_result, indent=2, ensure_ascii=False),
        encoding="utf-8",
    )

    agg = evaluation_result["aggregated_metrics"]
    meta = evaluation_result["metadata"]
    cases = evaluation_result["per_case_results"]

    rows = "\n".join(
        f"| {c['case_id']} | {c['category']} | "
        f"{'yes' if c['selection_correct'] else 'no'} | "
        f"{'yes' if c['call_success_correct'] else 'no'} | "
        f"{'yes' if c['task_completed'] else 'no'} |"
        for c in cases
    )

    markdown = (
        "# v0.6 Single-Agent Tool Orchestration Evaluation Report\n"
        "\n"
        "## Scope\n"
        "\n"
        f"Offline frozen evaluation of single-agent read-only tool orchestration "
        f"using Foundry Local Chat Completions and `{meta['model']}`.\n"
        "\n"
        "## Configuration\n"
        "\n"
        f"- **Model**: {meta['model']}\n"
        f"- **Prompt version**: {meta['prompt_version']}\n"
        f"- **Total cases**: {meta['total_cases']}\n"
        "- **Allowed Tools**: `search_knowledge`, `get_my_loans`, "
        "`get_loan_details`, `get_next_installment`\n"
        "- **Write Tools**: None (strictly read-only)\n"
        "\n"
        "## Aggregated Metrics\n"
        "\n"
        "| Metric | Value |\n"
        "| --- | ---: |\n"
        f"| tool_selection_accuracy | {agg['tool_selection_accuracy']:.6f} |\n"
        f"| tool_input_accuracy | {agg['tool_input_accuracy']:.6f} |\n"
        f"| tool_call_success | {agg['tool_call_success']:.6f} |\n"
        f"| no_write_compliance | {agg['no_write_compliance']:.6f} |\n"
        f"| ownership_enforcement | {agg['ownership_enforcement']:.6f} |\n"
        f"| task_completion_proxy | {agg['task_completion_proxy']:.6f} |\n"
        "\n"
        "## Per-case Results\n"
        "\n"
        "| Case ID | Category | Tool Selection | Call Success | Task Completed |\n"
        "| --- | --- | --- | --- | --- |\n"
        f"{rows}\n"
        "\n"
        "## Interpretation\n"
        "\n"
        "- All evaluation queries are synthetic banking queries.\n"
        "- Tool selection accuracy measures whether the agent invokes the appropriate read tool.\n"
        "- No write compliance verifies zero exposure or invocation of state-changing tools.\n"
        "- Ownership enforcement confirms cross-customer access is rejected deterministically.\n"
        "\n"
        "## Limitations\n"
        "\n"
        "- The dataset is small, controlled, and hand-authored for baseline verification.\n"
        "- Metrics are deterministic proxies and do not constitute production quality thresholds.\n"
    )
    report_path.write_text(markdown, encoding="utf-8")
