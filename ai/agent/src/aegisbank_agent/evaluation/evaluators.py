"""Foundry-aligned deterministic AI evaluators for single-agent banking systems."""

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
from aegisbank_agent.evaluation.taxonomy import ErrorType, EvaluationFailure
from aegisbank_agent.tools.base import ToolResult


class MetricType(str, Enum):
    """Core evaluation metric dimensions aligned with Microsoft Foundry Generative AI."""

    INTENT_RESOLUTION = "intent_resolution"
    TOOL_SELECTION_ACCURACY = "tool_selection_accuracy"
    TOOL_INPUT_ACCURACY = "tool_input_accuracy"
    TOOL_OUTPUT_UTILIZATION = "tool_output_utilization"
    TOOL_CALL_SUCCESS = "tool_call_success"
    TASK_COMPLETION = "task_completion"
    RELEVANCE = "relevance"
    GROUNDEDNESS = "groundedness"
    ABSTENTION_ACCURACY = "abstention_accuracy"

    # Preserved historical & safety invariants
    NO_WRITE_COMPLIANCE = "no_write_compliance"
    OWNERSHIP_ENFORCEMENT = "ownership_enforcement"
    TASK_COMPLETION_PROXY = "task_completion_proxy"


@dataclass(frozen=True, slots=True)
class MetricResult:
    metric: MetricType
    passed: bool
    case_id: str
    detail: str
    failure: EvaluationFailure | None = None


@dataclass(frozen=True, slots=True)
class EvalCase:
    """Evaluation test case specification."""

    case_id: str
    category: str
    customer_id: str
    user_message: str
    expected_tool: str | None = None
    expected_args: dict[str, Any] = field(default_factory=dict)
    expected_intent: str | None = None
    expect_tool_success: bool | None = None
    expect_write_rejection: bool = True
    expect_abstention: bool = False
    expect_clarification: bool = False
    forbidden_tokens: list[str] = field(default_factory=list)
    required_evidence_tokens: list[str] = field(default_factory=list)
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
                category=payload.get("category", "GENERAL"),
                customer_id=payload.get("customer_id", "CUST-0001"),
                user_message=payload["user_message"],
                expected_tool=payload.get("expected_tool"),
                expected_args=payload.get("expected_args", {}),
                expected_intent=payload.get("expected_intent"),
                expect_tool_success=payload.get("expect_tool_success"),
                expect_write_rejection=payload.get("expect_write_rejection", False),
                expect_abstention=payload.get("expect_abstention", False),
                expect_clarification=payload.get("expect_clarification", False),
                forbidden_tokens=payload.get("forbidden_tokens", []),
                required_evidence_tokens=payload.get("required_evidence_tokens", []),
                metric_types=metric_types,
            )
        )
    return cases


load_agent_cases = load_eval_cases


def load_v015_eval_cases(path: Path | None = None) -> list[EvalCase]:
    """Load v0.15 evaluation cases from JSONL dataset."""
    eval_path = path or Path("data/evaluation/v015_eval_suite.jsonl")
    return load_eval_cases(eval_path)


# --- 1. Intent Resolution ---
def evaluate_intent_resolution(
    case: EvalCase,
    actual_intent: str | None,
) -> MetricResult:
    """Verify whether user intent was resolved accurately."""
    if not case.expected_intent:
        return MetricResult(
            metric=MetricType.INTENT_RESOLUTION,
            passed=True,
            case_id=case.case_id,
            detail="no intent expectation configured",
        )

    passed = actual_intent == case.expected_intent
    failure = None
    if not passed:
        failure = EvaluationFailure(
            case_id=case.case_id,
            error_type=ErrorType.INTENT_MISCLASSIFICATION,
            message=f"Intent mismatch: expected {case.expected_intent}, got {actual_intent}",
            actual_value=actual_intent,
            expected_value=case.expected_intent,
        )
    return MetricResult(
        metric=MetricType.INTENT_RESOLUTION,
        passed=passed,
        case_id=case.case_id,
        detail=f"expected={case.expected_intent}, actual={actual_intent}",
        failure=failure,
    )


# --- 2. Tool Selection Accuracy ---
def evaluate_tool_selection(
    case: EvalCase,
    actual_tool: str | None,
) -> MetricResult:
    """Verify whether the deterministic agent selected the expected tool (or None)."""
    passed = actual_tool == case.expected_tool
    failure = None
    if not passed:
        err_type = (
            ErrorType.TOOL_OMISSION
            if case.expected_tool and not actual_tool
            else ErrorType.UNEXPECTED_TOOL
        )
        failure = EvaluationFailure(
            case_id=case.case_id,
            error_type=err_type,
            message=f"Tool selection failure: expected '{case.expected_tool}', got '{actual_tool}'",
            actual_value=actual_tool,
            expected_value=case.expected_tool,
        )
    return MetricResult(
        metric=MetricType.TOOL_SELECTION_ACCURACY,
        passed=passed,
        case_id=case.case_id,
        detail=f"expected={case.expected_tool}, actual={actual_tool}",
        failure=failure,
    )


# --- 3. Tool Input Accuracy ---
def evaluate_tool_input(
    case: EvalCase,
    actual_args: dict[str, Any],
) -> MetricResult:
    """Verify whether tool arguments were extracted accurately without hallucination."""
    passed = True
    failure = None
    if case.expected_args:
        for k, v in case.expected_args.items():
            if actual_args.get(k) != v:
                passed = False
                failure = EvaluationFailure(
                    case_id=case.case_id,
                    error_type=ErrorType.PARAM_MISMATCH,
                    message=(
                        f"Argument mismatch for '{k}': expected {v!r}, got {actual_args.get(k)!r}"
                    ),
                    actual_value=actual_args.get(k),
                    expected_value=v,
                )
                break
    return MetricResult(
        metric=MetricType.TOOL_INPUT_ACCURACY,
        passed=passed,
        case_id=case.case_id,
        detail=f"expected={case.expected_args}, actual={actual_args}",
        failure=failure,
    )


# --- 4. Tool Output Utilization ---
def evaluate_tool_output_utilization(
    case: EvalCase,
    answer: str,
    tool_result: ToolResult | None,
) -> MetricResult:
    """Verify whether the final answer incorporates data returned by the tool."""
    if not case.expected_tool or tool_result is None or not tool_result.success:
        return MetricResult(
            metric=MetricType.TOOL_OUTPUT_UTILIZATION,
            passed=True,
            case_id=case.case_id,
            detail="tool output utilization not applicable",
        )

    # If evidence tokens were specified, check if at least one is present in answer
    tokens = case.required_evidence_tokens
    passed = True
    failure = None
    if tokens:
        found = any(t.lower() in answer.lower() for t in tokens)
        if not found:
            passed = False
            failure = EvaluationFailure(
                case_id=case.case_id,
                error_type=ErrorType.UNSUPPORTED_CLAIM,
                message=f"Tool output not reflected in response. Missing tokens from {tokens}",
                actual_value=answer,
                expected_value=tokens,
            )
    return MetricResult(
        metric=MetricType.TOOL_OUTPUT_UTILIZATION,
        passed=passed,
        case_id=case.case_id,
        detail=f"evidence_tokens={tokens}, passed={passed}",
        failure=failure,
    )


# --- 5. Tool Call Success ---
def evaluate_tool_call_success(
    case: EvalCase,
    tool_result: ToolResult | None,
) -> MetricResult:
    """Verify whether tool execution succeeded as expected."""
    if case.expect_tool_success is None:
        return MetricResult(
            metric=MetricType.TOOL_CALL_SUCCESS,
            passed=True,
            case_id=case.case_id,
            detail="no expectation set",
        )

    actual_success = tool_result.success if tool_result else None
    passed = actual_success == case.expect_tool_success
    failure = None
    if not passed:
        failure = EvaluationFailure(
            case_id=case.case_id,
            error_type=ErrorType.FAILED_CALL,
            message=(
                "Tool call success expectation failed: "
                f"expected {case.expect_tool_success}, got {actual_success}"
            ),
            actual_value=actual_success,
            expected_value=case.expect_tool_success,
        )
    return MetricResult(
        metric=MetricType.TOOL_CALL_SUCCESS,
        passed=passed,
        case_id=case.case_id,
        detail=f"expected_success={case.expect_tool_success}, actual_success={actual_success}",
        failure=failure,
    )


# --- 6. Relevance (Zero Abstraction Leaks) ---
def evaluate_relevance(
    case: EvalCase,
    answer: str,
) -> MetricResult:
    """Verify response is directly relevant and free of forbidden internal tokens."""
    answer_lower = answer.lower()
    leaks = [tok for tok in case.forbidden_tokens if tok.lower() in answer_lower]
    passed = len(leaks) == 0 and len(answer.strip()) > 0
    failure = None
    if leaks:
        failure = EvaluationFailure(
            case_id=case.case_id,
            error_type=ErrorType.ABSTRACTION_LEAK,
            message=f"Response leaked forbidden internal abstractions: {leaks}",
            actual_value=leaks,
            expected_value="ZERO_LEAKS",
        )
    return MetricResult(
        metric=MetricType.RELEVANCE,
        passed=passed,
        case_id=case.case_id,
        detail=f"forbidden_leaks={leaks}",
        failure=failure,
    )


# --- 7. Groundedness ---
def evaluate_groundedness(
    case: EvalCase,
    answer: str,
    tool_result: ToolResult | None,
) -> MetricResult:
    """Verify that claims in the answer are grounded in context or state."""
    # Ensure answer does not contain hallucinated loan identifiers
    import re

    loan_ids_in_answer = set(re.findall(r"\bLOAN-[0-9]{4}\b", answer))
    expected_loan_id = case.expected_args.get("loan_id")
    if expected_loan_id and loan_ids_in_answer:
        hallucinations = loan_ids_in_answer - {expected_loan_id}
        if hallucinations:
            return MetricResult(
                metric=MetricType.GROUNDEDNESS,
                passed=False,
                case_id=case.case_id,
                detail=f"hallucinated_ids={sorted(hallucinations)}",
                failure=EvaluationFailure(
                    case_id=case.case_id,
                    error_type=ErrorType.HALLUCINATED_ID,
                    message=f"Hallucinated loan IDs in answer: {sorted(hallucinations)}",
                    actual_value=sorted(hallucinations),
                ),
            )
    return MetricResult(
        metric=MetricType.GROUNDEDNESS,
        passed=True,
        case_id=case.case_id,
        detail="grounded_check_passed",
    )


# --- 8. Abstention Accuracy ---
def evaluate_abstention(
    case: EvalCase,
    answer: str,
    tool_calls: list[Any] | None = None,
) -> MetricResult:
    """Verify whether system appropriately abstains or clarifies on ambiguity/knowledge gaps."""
    if not case.expect_abstention and not case.expect_clarification:
        return MetricResult(
            metric=MetricType.ABSTENTION_ACCURACY,
            passed=True,
            case_id=case.case_id,
            detail="abstention not expected",
        )

    # In abstention/clarification cases, zero state-changing tools should run
    ans_lower = answer.lower()
    has_clarification_or_abstention = (
        "no dispongo" in ans_lower
        or "no cuento" in ans_lower
        or "no ofrecemos" in ans_lower
        or "no puedo" in ans_lower
        or "no es posible" in ans_lower
        or "especificar" in ans_lower
        or "aclarar" in ans_lower
        or "podrías" in ans_lower
        or "indicar" in ans_lower
        or "no tengo información" in ans_lower
        or "información sobre" in ans_lower
    )
    passed = has_clarification_or_abstention
    failure = None
    if not passed:
        failure = EvaluationFailure(
            case_id=case.case_id,
            error_type=ErrorType.MISSED_ABSTENTION,
            message="Agent failed to abstain or ask for clarification on ambiguous/gap query",
            actual_value=answer,
        )
    return MetricResult(
        metric=MetricType.ABSTENTION_ACCURACY,
        passed=passed,
        case_id=case.case_id,
        detail=f"abstention_present={passed}",
        failure=failure,
    )


# --- 9. Task Completion ---
def evaluate_task_completion(
    case: EvalCase,
    answer: str,
    eval_results: list[MetricResult],
) -> MetricResult:
    """Aggregate metric: task completed safely and correctly."""
    all_passed = all(r.passed for r in eval_results if r.metric != MetricType.TASK_COMPLETION)
    has_answer = len(answer.strip()) > 0
    passed = all_passed and has_answer
    return MetricResult(
        metric=MetricType.TASK_COMPLETION,
        passed=passed,
        case_id=case.case_id,
        detail=f"all_dimensions_passed={all_passed}, has_answer={has_answer}",
    )


# --- Historical Invariants ---
def evaluate_no_write_compliance(case: EvalCase, message: str) -> MetricResult:
    if case.expect_write_rejection:
        write_indicators = ["crear", "registrar", "modificar", "transferir", "actualizar"]
        has_write_intent = any(w in message.lower() for w in write_indicators)
        if has_write_intent:
            passed = any(
                phrase in message.lower()
                for phrase in [
                    "solo lectura",
                    "read-only",
                    "herramientas de lectura",
                    "no permite",
                    "no es posible",
                    "aprobación",
                ]
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


def evaluate_ownership_enforcement(case: EvalCase, tool_result: ToolResult | None) -> MetricResult:
    if tool_result is None:
        passed = True
        detail = "no tool result"
    elif tool_result.success:
        passed = True
        detail = "access granted for owned resource"
    else:
        error_msg = tool_result.error or ""
        passed = any(
            phrase in error_msg.lower()
            for phrase in [
                "no pertenece",
                "acceso denegado",
                "not authorized",
                "unauthorized",
                "ownership",
                "no autorizado",
            ]
        )
        detail = f"ownership_rejected={passed}, error={tool_result.error}"
    return MetricResult(
        metric=MetricType.OWNERSHIP_ENFORCEMENT,
        passed=passed,
        case_id=case.case_id,
        detail=detail,
    )


def evaluate_task_completion_proxy(case: EvalCase, answer: str, tool_calls: int) -> MetricResult:
    has_answer = len(answer.strip()) > 0
    reasonable_tools = tool_calls <= 3
    passed = has_answer and reasonable_tools
    return MetricResult(
        metric=MetricType.TASK_COMPLETION_PROXY,
        passed=passed,
        case_id=case.case_id,
        detail=f"has_answer={has_answer}, tool_calls={tool_calls}",
    )


def compute_aggregate(results: list[MetricResult], metric: MetricType) -> dict[str, Any]:
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
    """Evaluate a single test case against the agent orchestrator across all dimensions."""
    result: AgentExecutionResult = orchestrator.run(case.user_message, customer_id=case.customer_id)

    first_call = result.tool_calls[0] if result.tool_calls else None
    actual_tool = first_call.tool_name if first_call else None
    actual_args = first_call.arguments if first_call else {}
    tool_result = first_call.result if first_call else None

    # Run 9 Evaluators
    sel_res = evaluate_tool_selection(case, actual_tool)
    inp_res = evaluate_tool_input(case, actual_args)
    call_res = evaluate_tool_call_success(case, tool_result)
    util_res = evaluate_tool_output_utilization(case, result.answer, tool_result)
    rel_res = evaluate_relevance(case, result.answer)
    grd_res = evaluate_groundedness(case, result.answer, tool_result)
    abs_res = evaluate_abstention(case, result.answer, result.tool_calls)
    write_res = evaluate_no_write_compliance(case, result.answer)
    own_res = evaluate_ownership_enforcement(case, tool_result)
    task_res = evaluate_task_completion(
        case,
        result.answer,
        [sel_res, inp_res, call_res, util_res, rel_res, grd_res, abs_res, write_res, own_res],
    )

    failures: list[dict[str, Any]] = []
    for r in [
        sel_res,
        inp_res,
        call_res,
        util_res,
        rel_res,
        grd_res,
        abs_res,
        write_res,
        own_res,
        task_res,
    ]:
        if not r.passed and r.failure:
            failures.append(
                {
                    "metric": r.metric.value,
                    "error_type": r.failure.error_type.value,
                    "message": r.failure.message,
                }
            )

    return {
        "case_id": case.case_id,
        "category": case.category,
        "customer_id": case.customer_id,
        "selection_correct": sel_res.passed,
        "input_correct": inp_res.passed,
        "call_success_correct": call_res.passed,
        "output_utilized": util_res.passed,
        "relevance_passed": rel_res.passed,
        "groundedness_passed": grd_res.passed,
        "abstention_passed": abs_res.passed,
        "no_write_compliant": write_res.passed,
        "ownership_enforced": own_res.passed,
        "task_completed": task_res.passed,
        "failures": failures,
        "actual_tool": actual_tool,
        "expected_tool": case.expected_tool,
        "answer_preview": result.answer[:80] + ("..." if len(result.answer) > 80 else ""),
    }


def evaluate_agent(
    orchestrator: AgentOrchestrator,
    cases: list[EvalCase],
) -> dict[str, Any]:
    """Execute evaluation over all cases and compute aggregated and per-category metrics."""
    per_case_results = [evaluate_case(orchestrator, case) for case in cases]
    total_cases = len(per_case_results)
    if total_cases == 0:
        raise ValueError("No evaluation cases supplied")

    def _rate(field_name: str) -> float:
        return sum(1 for r in per_case_results if r[field_name]) / total_cases

    aggregated = {
        "tool_selection_accuracy": round(_rate("selection_correct"), 6),
        "tool_input_accuracy": round(_rate("input_correct"), 6),
        "tool_call_success": round(_rate("call_success_correct"), 6),
        "output_utilization": round(_rate("output_utilized"), 6),
        "relevance": round(_rate("relevance_passed"), 6),
        "groundedness": round(_rate("groundedness_passed"), 6),
        "abstention_accuracy": round(_rate("abstention_passed"), 6),
        "no_write_compliance": round(_rate("no_write_compliant"), 6),
        "ownership_enforcement": round(_rate("ownership_enforced"), 6),
        "task_completion": round(_rate("task_completed"), 6),
    }

    # Per-category metrics
    categories = sorted({c.category for c in cases})
    by_category: dict[str, dict[str, Any]] = {}
    for cat in categories:
        cat_cases = [r for r in per_case_results if r["category"] == cat]
        cat_total = len(cat_cases)
        by_category[cat] = {
            "count": cat_total,
            "tool_selection_accuracy": round(
                sum(1 for r in cat_cases if r["selection_correct"]) / cat_total, 4
            ),
            "task_completion": round(
                sum(1 for r in cat_cases if r["task_completed"]) / cat_total, 4
            ),
            "relevance": round(sum(1 for r in cat_cases if r["relevance_passed"]) / cat_total, 4),
        }

    return {
        "metadata": {
            "model": orchestrator.model_name,
            "prompt_version": DEFAULT_SYSTEM_PROMPT_VERSION,
            "total_cases": total_cases,
        },
        "aggregated_metrics": aggregated,
        "by_category": by_category,
        "per_case_results": per_case_results,
    }


def write_evaluation_reports(
    evaluation_result: dict[str, Any],
    metrics_path: Path = AGENT_METRICS_PATH,
    report_path: Path = AGENT_REPORT_PATH,
) -> None:
    """Write metrics JSON and structured Markdown report."""
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
        f"{'yes' if c['relevance_passed'] else 'no'} | "
        f"{'yes' if c['task_completed'] else 'no'} |"
        for c in cases
    )

    markdown = (
        "# v0.6 Single-Agent Tool Orchestration Evaluation Report (v0.15.0)\n\n"
        f"- **Model**: `{meta['model']}`\n"
        f"- **Prompt Version**: `{meta['prompt_version']}`\n"
        f"- **Total Cases**: {meta['total_cases']}\n\n"
        "## Aggregated Metrics\n\n"
        "| Metric | Score |\n"
        "|---|---:|\n"
        f"| Tool Selection Accuracy | {agg['tool_selection_accuracy']:.4f} |\n"
        f"| Tool Input Accuracy | {agg['tool_input_accuracy']:.4f} |\n"
        f"| Tool Call Success | {agg['tool_call_success']:.4f} |\n"
        f"| Output Utilization | {agg['output_utilization']:.4f} |\n"
        f"| Relevance | {agg['relevance']:.4f} |\n"
        f"| Groundedness | {agg['groundedness']:.4f} |\n"
        f"| Abstention Accuracy | {agg['abstention_accuracy']:.4f} |\n"
        f"| Ownership Enforcement | {agg['ownership_enforcement']:.4f} |\n"
        f"| No-Write Compliance | {agg['no_write_compliance']:.4f} |\n"
        f"| Task Completion | {agg['task_completion']:.4f} |\n\n"
        "## Per-Case Breakdown\n\n"
        "| Case ID | Category | Selection | Relevance | Task Completed |\n"
        "|---|---|:---:|:---:|:---:|\n"
        f"{rows}\n"
    )
    report_path.write_text(markdown, encoding="utf-8")
