"""stdio entry point for the AegisBank local MCP server."""

from __future__ import annotations

import os

from mock_core_banking.persistence.database import Database
from mock_core_banking.persistence.seed import seed_database

from .hitl import HITLApprovalManager
from .mcp_boundary import JsonApprovalStore, create_mcp_server
from .tools.base import AgentContext


async def main() -> None:
    database = Database(os.environ.get("AEGISBANK_DATABASE_URL", "sqlite:///:memory:"))
    database.create_schema()
    seed_database(database)
    manager = HITLApprovalManager()
    store_path = os.environ.get("AEGISBANK_APPROVAL_FILE")
    if store_path:
        store = JsonApprovalStore(__import__("pathlib").Path(store_path))
        # The stdio child reads approvals written by the host before tools/call.
        original_get = manager.get_request

        def get_request(approval_id: str):
            request = store.load(approval_id)
            if request is not None:
                manager._requests[approval_id] = request
            return original_get(approval_id)

        manager.get_request = get_request  # type: ignore[method-assign]
    server = create_mcp_server(
        database,
        AgentContext(os.environ.get("AEGISBANK_CUSTOMER_ID", "CUST-0001")),
        manager,
    )
    try:
        await server.run_stdio_async()
    finally:
        database.dispose()


if __name__ == "__main__":
    import asyncio

    asyncio.run(main())
