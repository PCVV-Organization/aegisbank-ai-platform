"""Command-line interface for the AegisBank Agent component."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from .agent import AgentOrchestrator
from .constants import (
    AGENT_METRICS_PATH,
    AGENT_REPORT_PATH,
    DEFAULT_MODEL_ALIAS,
    EVAL_CASES_PATH,
    LIVE_AGENT_METRICS_PATH,
    LIVE_AGENT_REPORT_PATH,
)
from .evaluation import evaluate_agent, load_agent_cases, write_evaluation_reports


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegisbank-agent",
        description="Single-agent tool orchestration for AegisBank v0.6",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    # run subcommand
    run_parser = subparsers.add_parser("run", help="Run a single query through the agent")
    run_parser.add_argument("query", help="User question or request")
    run_parser.add_argument(
        "--customer-id",
        type=str,
        default="CUST-0001",
        help="Synthetic customer ID for session context (default: CUST-0001)",
    )
    run_parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_ALIAS,
        help=f"Model alias (default: {DEFAULT_MODEL_ALIAS})",
    )

    # evaluate subcommand
    eval_parser = subparsers.add_parser(
        "evaluate",
        help="Run offline evaluation over frozen agent test cases",
    )
    eval_parser.add_argument(
        "--cases-path",
        type=Path,
        default=EVAL_CASES_PATH,
        help="Path to evaluation cases JSONL",
    )
    eval_parser.add_argument(
        "--metrics-output",
        type=Path,
        default=AGENT_METRICS_PATH,
        help="Path to write metrics JSON",
    )
    eval_parser.add_argument(
        "--report-output",
        type=Path,
        default=AGENT_REPORT_PATH,
        help="Path to write report markdown",
    )
    eval_parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_ALIAS,
        help=f"Model alias (default: {DEFAULT_MODEL_ALIAS})",
    )

    live_parser = subparsers.add_parser(
        "evaluate-live",
        help="Run the frozen synthetic evaluation once against Foundry Local",
    )
    live_parser.add_argument("--cases-path", type=Path, default=EVAL_CASES_PATH)
    live_parser.add_argument("--metrics-output", type=Path, default=LIVE_AGENT_METRICS_PATH)
    live_parser.add_argument("--report-output", type=Path, default=LIVE_AGENT_REPORT_PATH)
    live_parser.add_argument("--model", type=str, default=DEFAULT_MODEL_ALIAS)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)

    if args.command == "run":
        orchestrator = AgentOrchestrator(model=args.model)
        result = orchestrator.run(args.query, customer_id=args.customer_id)
        print(f"\n[Customer ID]: {result.customer_id}")
        print(f"[Rounds]: {result.rounds}")
        print(f"[Tools Executed]: {len(result.tool_calls)}")
        for i, tc in enumerate(result.tool_calls, 1):
            print(f"  {i}. {tc.tool_name}({tc.arguments}) -> Success={tc.result.success}")
        print("\n[Respuesta]:")
        print(result.answer)
        return 0

    if args.command == "evaluate":
        cases = load_agent_cases(args.cases_path)
        orchestrator = AgentOrchestrator(model=args.model)
        eval_result = evaluate_agent(orchestrator, cases)
        write_evaluation_reports(
            eval_result,
            metrics_path=args.metrics_output,
            report_path=args.report_output,
        )
        agg = eval_result["aggregated_metrics"]
        print(f"Evaluated {len(cases)} cases successfully.")
        print(f"Tool Selection Accuracy: {agg['tool_selection_accuracy']:.4f}")
        print(f"Tool Call Success:       {agg['tool_call_success']:.4f}")
        print(f"No Write Compliance:     {agg['no_write_compliance']:.4f}")
        print(f"Ownership Enforcement:   {agg['ownership_enforcement']:.4f}")
        print(f"Report written to: {args.report_output}")
        return 0

    if args.command == "evaluate-live":
        if args.metrics_output.exists() or args.report_output.exists():
            raise FileExistsError("Refusing to overwrite existing v0.6 live evaluation report")
        cases = load_agent_cases(args.cases_path)
        orchestrator = AgentOrchestrator(model=args.model)
        eval_result = evaluate_agent(orchestrator, cases)
        eval_result["metadata"]["evaluation_mode"] = "live_local_once"
        eval_result["metadata"]["provider"] = "foundry-local"
        write_evaluation_reports(
            eval_result,
            metrics_path=args.metrics_output,
            report_path=args.report_output,
        )
        print(eval_result["aggregated_metrics"])
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
