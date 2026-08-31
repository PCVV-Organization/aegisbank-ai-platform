"""Base types and interfaces for read-only function tools."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class AgentContext:
    """Deterministic runtime context injected into each agent session."""

    session_customer_id: str


@dataclass(frozen=True, slots=True)
class ToolResult:
    """Normalized structured result returned by a function tool."""

    tool_name: str
    success: bool
    data: Any = None
    error: str | None = None

    def as_dict(self) -> dict[str, Any]:
        out: dict[str, Any] = {
            "tool_name": self.tool_name,
            "success": self.success,
        }
        if self.data is not None:
            out["data"] = self.data
        if self.error is not None:
            out["error"] = self.error
        return out


class FunctionTool(ABC):
    """Abstract base class for all agent function tools."""

    @property
    @abstractmethod
    def name(self) -> str: ...

    @property
    @abstractmethod
    def description(self) -> str: ...

    @property
    @abstractmethod
    def parameters_schema(self) -> dict[str, Any]: ...

    @abstractmethod
    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult: ...

    def to_openai_tool(self) -> dict[str, Any]:
        return {
            "type": "function",
            "function": {
                "name": self.name,
                "description": self.description,
                "parameters": self.parameters_schema,
            },
        }
