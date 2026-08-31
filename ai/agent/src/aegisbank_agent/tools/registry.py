"""Tool registry and deterministic execution gate."""

from __future__ import annotations

from typing import Any

from .banking_tools import (
    CreateServiceRequestTool,
    GetLoanDetailsTool,
    GetMyLoansTool,
    GetNextInstallmentTool,
)
from .base import AgentContext, FunctionTool, ToolResult
from .knowledge_tools import SearchKnowledgeTool


class ToolRegistry:
    """Deterministic registry enforcing allowed tool sets."""

    def __init__(
        self,
        tools: list[FunctionTool] | None = None,
        *,
        include_write_tools: bool = False,
    ) -> None:
        self._tools: dict[str, FunctionTool] = {}
        if tools is None:
            default_tools: list[FunctionTool] = [
                SearchKnowledgeTool(),
                GetMyLoansTool(),
                GetLoanDetailsTool(),
                GetNextInstallmentTool(),
            ]
            if include_write_tools:
                default_tools.append(CreateServiceRequestTool())

            for tool in default_tools:
                self.register(tool)
        else:
            for tool in tools:
                self.register(tool)

    def register(self, tool: FunctionTool) -> None:
        self._tools[tool.name] = tool

    @property
    def allowed_tool_names(self) -> list[str]:
        return sorted(self._tools.keys())

    def get_tool(self, name: str) -> FunctionTool | None:
        return self._tools.get(name)

    def export_openai_tools(self) -> list[dict[str, Any]]:
        return [tool.to_openai_tool() for tool in self._tools.values()]

    def execute(
        self,
        name: str,
        arguments: dict[str, Any],
        context: AgentContext,
    ) -> ToolResult:
        tool = self._tools.get(name)
        if tool is None:
            return ToolResult(
                tool_name=name,
                success=False,
                error=(
                    f"Herramienta '{name}' no permitida o desconocida. "
                    "Herramientas disponibles: "
                    f"{', '.join(self.allowed_tool_names)}."
                ),
            )
        try:
            return tool.execute(arguments, context)
        except Exception as exc:
            return ToolResult(
                tool_name=name,
                success=False,
                error=f"Error inesperado al ejecutar '{name}': {exc}",
            )
