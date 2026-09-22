"""Local MCP boundary and deterministic human approval gate."""

from __future__ import annotations

import asyncio
import json
import os
import sys
from pathlib import Path
from typing import Any

from mcp import Client
from mcp.client.stdio import StdioServerParameters
from mcp.server import MCPServer
from mcp.types import ToolAnnotations
from mock_core_banking.persistence.database import Database

from .hitl import ApprovalRequest, ApprovalStatus, HITLApprovalManager
from .tools.banking_tools import (
    CreateServiceRequestTool,
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from .tools.base import AgentContext
from .tools.knowledge_tools import SearchKnowledgeTool
from .tools.registry import ToolRegistry

READ_TOOL_NAMES = (
    "search_knowledge",
    "get_my_loans",
    "get_loan_details",
    "get_next_installment",
)
WRITE_TOOL_NAME = "create_service_request"
MCP_TOOL_NAMES = (*READ_TOOL_NAMES, WRITE_TOOL_NAME)


def _error(code: str, message: str) -> dict[str, Any]:
    return {"success": False, "error": {"code": code, "message": message}}


def _result(result: Any) -> dict[str, Any]:
    if result.success:
        return {"success": True, "data": result.data}
    return _error("TOOL_EXECUTION_FAILED", "Tool execution failed")


def create_mcp_server(
    database: Database,
    context: AgentContext,
    approval_manager: HITLApprovalManager | None = None,
) -> MCPServer:
    """Create exactly one local MCP server with four reads and one gated write."""
    registry = ToolRegistry(
        tools=[
            SearchKnowledgeTool(),
            GetMyLoansTool(database),
            GetLoanDetailsTool(database),
            GetNextInstallmentTool(database),
            CreateServiceRequestTool(database),
        ]
    )
    manager = approval_manager or HITLApprovalManager()
    server = MCPServer(
        "AegisBank Local MCP",
        version="0.7.0",
        instructions="Synthetic banking tools. WRITE requires a prior human approval.",
    )

    @server.tool(
        name="search_knowledge",
        description=registry.get_tool("search_knowledge").description,  # type: ignore[union-attr]
        annotations=ToolAnnotations(read_only_hint=True),
    )
    def search_knowledge(query: str) -> dict[str, Any]:
        return _result(registry.execute("search_knowledge", {"query": query}, context))

    @server.tool(
        name="get_my_loans",
        description=registry.get_tool("get_my_loans").description,  # type: ignore[union-attr]
        annotations=ToolAnnotations(read_only_hint=True),
    )
    def get_my_loans() -> dict[str, Any]:
        return _result(registry.execute("get_my_loans", {}, context))

    @server.tool(
        name="get_loan_details",
        description=registry.get_tool("get_loan_details").description,  # type: ignore[union-attr]
        annotations=ToolAnnotations(read_only_hint=True),
    )
    def get_loan_details(loan_id: str) -> dict[str, Any]:
        return _result(registry.execute("get_loan_details", {"loan_id": loan_id}, context))

    @server.tool(
        name="get_next_installment",
        description=registry.get_tool("get_next_installment").description,  # type: ignore[union-attr]
        annotations=ToolAnnotations(read_only_hint=True),
    )
    def get_next_installment(loan_id: str) -> dict[str, Any]:
        return _result(registry.execute("get_next_installment", {"loan_id": loan_id}, context))

    write_tool = registry.get_tool(WRITE_TOOL_NAME)
    assert write_tool is not None

    @server.tool(
        name=WRITE_TOOL_NAME,
        description=write_tool.description,
        annotations=ToolAnnotations(read_only_hint=False, destructive_hint=False),
    )
    def create_service_request(
        approval_id: str,
        category: str,
        description: str,
    ) -> dict[str, Any]:
        """Execute a service request only when its exact proposal is approved."""
        arguments = {"category": category, "description": description}
        try:
            request = manager.get_request(approval_id)
            if request.tool_name != WRITE_TOOL_NAME:
                return _error("TOOL_MISMATCH", "Approval is not for create_service_request")
            if request.synthetic_customer_id != context.session_customer_id:
                return _error(
                    "CUSTOMER_MISMATCH", "Approval customer does not match session customer"
                )
            if request.status != ApprovalStatus.APPROVED:
                return _error("APPROVAL_REQUIRED", "Explicit human approval is required")
            if request.normalized_arguments != arguments:
                return _error("ARGUMENT_TAMPERING", "Arguments differ from the approved proposal")
            result = registry.execute(WRITE_TOOL_NAME, arguments, context)
            if not result.success:
                return _result(result)
            manager.verify_and_mark_executed(
                approval_id,
                context.session_customer_id,
                arguments,
                result.as_dict(),
            )
            return _result(result)
        except Exception:
            return _error("MCP_WRITE_FAILED", "The requested operation could not be executed")

    return server


class MCPApprovalGateway:
    """Host-side MCP client that performs HITL before any WRITE tools/call."""

    def __init__(self, context: AgentContext, approval_manager: HITLApprovalManager) -> None:
        self.context = context
        self.approval_manager = approval_manager

    def propose(self, arguments: dict[str, Any]) -> ApprovalRequest:
        """Create the exact proposal shown to the human; customer ID is runtime-owned."""
        normalized = {
            "category": arguments.get("category"),
            "description": arguments.get("description"),
        }
        return self.approval_manager.create_request(
            WRITE_TOOL_NAME,
            self.context.session_customer_id,
            normalized,
        )

    def approve_and_call(self, server: MCPServer, request: ApprovalRequest) -> Any:
        approved = self.approval_manager.approve(
            request.approval_id,
            self.context.session_customer_id,
        )
        return asyncio.run(self._call_in_process(server, approved))

    def approve_and_call_stdio(
        self,
        server_script: Path,
        request: ApprovalRequest,
        *,
        database_url: str,
        approval_file: Path,
    ) -> Any:
        approved = self.approval_manager.approve(
            request.approval_id,
            self.context.session_customer_id,
        )
        JsonApprovalStore(approval_file).save(approved)
        result, _ = call_stdio_sync(
            server_script,
            WRITE_TOOL_NAME,
            {"approval_id": approved.approval_id, **approved.normalized_arguments},
            customer_id=self.context.session_customer_id,
            database_url=database_url,
            approval_file=approval_file,
        )
        if result.structured_content.get("success") is True:
            self.approval_manager.verify_and_mark_executed(
                approved.approval_id,
                self.context.session_customer_id,
                approved.normalized_arguments,
                result.structured_content,
            )
        return result

    async def _call_in_process(self, server: MCPServer, request: ApprovalRequest) -> Any:
        async with Client(server) as client:
            return await client.call_tool(
                WRITE_TOOL_NAME,
                {"approval_id": request.approval_id, **request.normalized_arguments},
            )


class JsonApprovalStore:
    """Small local bridge for passing approvals to a stdio child process."""

    def __init__(self, path: Path) -> None:
        self.path = path

    def save(self, request: ApprovalRequest) -> None:
        self.path.parent.mkdir(parents=True, exist_ok=True)
        records: dict[str, Any] = {}
        if self.path.exists():
            records = json.loads(self.path.read_text(encoding="utf-8"))
        records[request.approval_id] = request.as_dict()
        temporary = self.path.with_suffix(".tmp")
        temporary.write_text(json.dumps(records, ensure_ascii=False), encoding="utf-8")
        temporary.replace(self.path)

    def load(self, approval_id: str) -> ApprovalRequest | None:
        if not self.path.exists():
            return None
        record = json.loads(self.path.read_text(encoding="utf-8")).get(approval_id)
        if record is None:
            return None
        from datetime import datetime

        return ApprovalRequest(
            approval_id=record["approval_id"],
            tool_name=record["tool_name"],
            synthetic_customer_id=record["synthetic_customer_id"],
            normalized_arguments=record["normalized_arguments"],
            status=ApprovalStatus(record["status"]),
            created_at=datetime.fromisoformat(record["created_at"]),
            reviewed_at=(
                datetime.fromisoformat(record["reviewed_at"]) if record.get("reviewed_at") else None
            ),
            rejection_reason=record.get("rejection_reason"),
            execution_result=record.get("execution_result"),
        )


async def call_stdio(
    server_script: Path,
    tool_name: str,
    arguments: dict[str, Any],
    *,
    customer_id: str,
    database_url: str,
    approval_file: Path,
) -> tuple[Any, str]:
    """Call the local MCP server over stdio and return result plus protocol version."""
    params = StdioServerParameters(
        command=sys.executable,
        args=["-m", "aegisbank_agent.mcp_server"],
        cwd=server_script.parents[4],
        env={
            **os.environ,
            "PYTHONPATH": os.pathsep.join(
                str(path)
                for path in (
                    server_script.parents[1],
                    server_script.parents[4] / "services" / "mock-core-banking" / "src",
                    server_script.parents[4] / "ai" / "rag" / "src",
                )
            ),
            "AEGISBANK_CUSTOMER_ID": customer_id,
            "AEGISBANK_DATABASE_URL": database_url,
            "AEGISBANK_APPROVAL_FILE": str(approval_file),
        },
    )
    async with Client(params) as client:
        result = await client.call_tool(tool_name, arguments)
        return result, client.protocol_version


def call_stdio_sync(*args: Any, **kwargs: Any) -> tuple[Any, str]:
    return asyncio.run(call_stdio(*args, **kwargs))
