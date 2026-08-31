"""Minimal local CLI for the v0.7 human approval workflow."""

from __future__ import annotations

import argparse
import tempfile
from pathlib import Path

from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.seed import seed_database

from .hitl import HITLApprovalManager
from .mcp_boundary import MCPApprovalGateway
from .tools.base import AgentContext


def main() -> None:
    parser = argparse.ArgumentParser(description="AegisBank v0.7 HITL demo")
    parser.add_argument("--customer-id", default="CUST-0001")
    parser.add_argument(
        "--category", default="INSTALLMENT", choices=["LOAN", "INSTALLMENT", "FEE", "GENERAL"]
    )
    parser.add_argument("--description", default="Cuota duplicada")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory(prefix="aegisbank-v07-") as directory:
        root = Path(directory)
        database_url = f"sqlite:///{root / 'core.sqlite'}"
        database = Database(database_url)
        database.create_schema()
        seed_database(database)
        context = AgentContext(args.customer_id)
        manager = HITLApprovalManager()
        gateway = MCPApprovalGateway(context, manager)
        request = gateway.propose({"category": args.category, "description": args.description})

        print(f"Tool: {request.tool_name}")
        print(f"Category: {args.category}")
        print(f"Description: {args.description}")
        print(f"Customer: {request.synthetic_customer_id}")
        decision = input("Approve? [y/N] ").strip().lower()
        if decision != "y":
            manager.reject(request.approval_id, context.session_customer_id)
            print("REJECTED: no MCP WRITE executed")
            database.dispose()
            return

        result = gateway.approve_and_call_stdio(
            Path(__file__).with_name("mcp_server.py"),
            request,
            database_url=database_url,
            approval_file=root / "approvals.json",
        )
        print(result.structured_content)
        database.dispose()


if __name__ == "__main__":
    main()
