"""Command-line interface for the AegisBank Agent component with HITL support."""

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
from .hitl import ApprovalRequest


def cli_approval_callback(request: ApprovalRequest) -> bool:
    """Prompt user interactively in CLI to approve or reject a WRITE operation."""
    print("\n" + "=" * 50)
    print(" [HITL] SOLICITUD DE APROBACIÓN REQUERIDA (WRITE)")
    print("=" * 50)
    print(f"Tool:     {request.tool_name}")
    for k, v in request.normalized_arguments.items():
        print(f"{k.capitalize()}: {v}")
    print(f"Customer: {request.synthetic_customer_id}")
    print("=" * 50)
    try:
        choice = input("Approve? [y/N]: ").strip().lower()
        return choice == "y"
    except EOFError, KeyboardInterrupt:
        return False


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegisbank-agent",
        description=(
            "Single-agent tool orchestration for AegisBank AI Platform (v1.0.7) with MCP and HITL"
        ),
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
        "--session-id",
        type=str,
        default=None,
        help="Durable conversation session ID (default: one session per customer)",
    )
    run_parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL_ALIAS,
        help=f"Model alias (default: {DEFAULT_MODEL_ALIAS})",
    )
    run_parser.add_argument(
        "--approve-writes",
        action="store_true",
        help="Automatically approve write operations without interactive prompt (for tests)",
    )
    run_parser.add_argument(
        "--reject-writes",
        action="store_true",
        help="Automatically reject write operations (default DENY behavior)",
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
        if args.approve_writes:
            approval_cb = lambda req: True  # noqa: E731
        elif args.reject_writes:
            approval_cb = lambda req: False  # noqa: E731
        else:
            approval_cb = cli_approval_callback

        orchestrator = AgentOrchestrator(model=args.model, approval_callback=approval_cb)
        result = orchestrator.run(
            args.query,
            customer_id=args.customer_id,
            session_id=args.session_id,
        )

        print(f"\n[Customer ID]: {result.customer_id}")
        print(f"[Rounds]: {result.rounds}")
        print(f"[Tools Executed]: {len(result.tool_calls)}")
        for i, tc in enumerate(result.tool_calls, 1):
            print(f"  {i}. {tc.tool_name}({tc.arguments}) -> Success={tc.result.success}")
        if result.approval_requests:
            print(f"[Approvals]: {len(result.approval_requests)}")
            for req in result.approval_requests:
                print(f"  - {req.approval_id} ({req.tool_name}) -> Status={req.status.value}")
        print("\n[Respuesta]:")
        print(result.answer)
        return 0

    if args.command in ("evaluate", "evaluate-live"):
        is_live = args.command == "evaluate-live"
        cases = load_agent_cases(args.cases_path)
        orchestrator = AgentOrchestrator(model=args.model)
        result = evaluate_agent(orchestrator, cases)
        write_evaluation_reports(
            result,
            metrics_path=args.metrics_output,
            report_path=args.report_output,
        )
        agg = result["aggregated_metrics"]
        prefix = "Live" if is_live else "Offline"
        print(f"{prefix} evaluated {len(cases)} cases successfully.")
        print(f"Tool Selection Accuracy: {agg['tool_selection_accuracy']:.4f}")
        print(f"Tool Call Success:       {agg['tool_call_success']:.4f}")
        print(f"No Write Compliance:     {agg['no_write_compliance']:.4f}")
        print(f"Ownership Enforcement:   {agg['ownership_enforcement']:.4f}")
        print(f"Report written to: {args.report_output}")
        return 0

    return 1


if __name__ == "__main__":
    sys.exit(main())
