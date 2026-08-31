"""AegisBank local Model Context Protocol (MCP) server implementation."""

from __future__ import annotations

import json

from mcp import types
from mcp.server.mcpserver import MCPServer
from mock_core_banking.persistence.database import Database

from aegisbank_agent.hitl import HITLApprovalManager
from aegisbank_agent.tools.banking_tools import (
    CreateServiceRequestTool,
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from aegisbank_agent.tools.base import AgentContext, ToolResult
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool


def create_aegisbank_mcp_server(
    database: Database | None = None,
    hitl_manager: HITLApprovalManager | None = None,
) -> MCPServer:
    """Create and configure the official AegisBank MCP Server."""
    server = MCPServer("aegisbank-mcp-server")
    approval_mgr = hitl_manager or HITLApprovalManager()

    # Tool instances
    search_tool = SearchKnowledgeTool()
    loans_tool = GetMyLoansTool(database)
    loan_details_tool = GetLoanDetailsTool(database)
    installment_tool = GetNextInstallmentTool(database)
    create_sr_tool = CreateServiceRequestTool(database)

    @server.tool(
        name="search_knowledge",
        description=(
            "Busca información oficial en las políticas, requisitos y documentación "
            "general de AegisBank (por ejemplo: requisitos para créditos, tasas, plazos)."
        ),
        annotations=types.ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
        ),
    )
    async def search_knowledge_tool(query: str) -> str:
        try:
            res: ToolResult = search_tool.execute(
                {"query": query}, AgentContext(session_customer_id="SYSTEM")
            )
            return json.dumps(res.as_dict(), ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Error en búsqueda: {str(exc)}"})

    @server.tool(
        name="get_my_loans",
        description="Obtiene la lista de préstamos pertenecientes al cliente autenticado.",
        annotations=types.ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
        ),
    )
    async def get_my_loans_tool(customer_id: str) -> str:
        try:
            res: ToolResult = loans_tool.execute({}, AgentContext(session_customer_id=customer_id))
            return json.dumps(res.as_dict(), ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"success": False, "error": f"Error al consultar préstamos: {str(exc)}"}
            )

    @server.tool(
        name="get_loan_details",
        description="Obtiene el detalle financiero y estado de un préstamo del cliente.",
        annotations=types.ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
        ),
    )
    async def get_loan_details_tool(loan_id: str, customer_id: str) -> str:
        try:
            res: ToolResult = loan_details_tool.execute(
                {"loan_id": loan_id}, AgentContext(session_customer_id=customer_id)
            )
            return json.dumps(res.as_dict(), ensure_ascii=False)
        except Exception as exc:
            return json.dumps(
                {"success": False, "error": f"Error al consultar detalle: {str(exc)}"}
            )

    @server.tool(
        name="get_next_installment",
        description="Obtiene los datos de la próxima cuota a pagar de un préstamo del cliente.",
        annotations=types.ToolAnnotations(
            read_only_hint=True,
            destructive_hint=False,
        ),
    )
    async def get_next_installment_tool(loan_id: str, customer_id: str) -> str:
        try:
            res: ToolResult = installment_tool.execute(
                {"loan_id": loan_id}, AgentContext(session_customer_id=customer_id)
            )
            return json.dumps(res.as_dict(), ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Error al consultar cuota: {str(exc)}"})

    @server.tool(
        name="create_service_request",
        description=(
            "Crea una solicitud de servicio o reclamo bancario para el cliente. "
            "Requiere aprobación humana explícita (approval_id)."
        ),
        annotations=types.ToolAnnotations(
            read_only_hint=False,
            destructive_hint=False,
        ),
    )
    async def create_service_request_tool(
        category: str,
        description: str,
        customer_id: str,
        approval_id: str | None = None,
    ) -> str:
        try:
            if not approval_id:
                return json.dumps(
                    {
                        "success": False,
                        "error": (
                            "Operación WRITE rechazada: requiere un "
                            "'approval_id' aprobado por un humano."
                        ),
                    },
                    ensure_ascii=False,
                )

            # Verify through HITL approval manager
            arguments_to_verify = {"category": category, "description": description}
            try:
                # Pre-execution check
                _ = approval_mgr.get_request(approval_id)
            except Exception as e:
                return json.dumps({"success": False, "error": str(e)}, ensure_ascii=False)

            # Execute Core Banking write
            res: ToolResult = create_sr_tool.execute(
                arguments_to_verify, AgentContext(session_customer_id=customer_id)
            )

            if res.success:
                approval_mgr.verify_and_mark_executed(
                    approval_id=approval_id,
                    customer_id=customer_id,
                    arguments_to_execute=arguments_to_verify,
                    execution_result=res.data or {},
                )

            return json.dumps(res.as_dict(), ensure_ascii=False)
        except Exception as exc:
            return json.dumps({"success": False, "error": f"Error al crear solicitud: {str(exc)}"})

    return server
