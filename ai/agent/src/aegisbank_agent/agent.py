"""Single-agent orchestrator for AegisBank with MCP and HITL integration."""

from __future__ import annotations

import json
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aegisbank_rag.foundry_local import DEFAULT_MODEL_ALIAS, resolve_foundry_base_url
from openai import OpenAI

from .constants import DEFAULT_MAX_TOOL_ROUNDS, SYSTEM_PROMPT_PATH
from .hitl import ApprovalRequest, HITLApprovalManager
from .tools.base import AgentContext, ToolResult
from .tools.registry import ToolRegistry

_PLACEHOLDER_API_KEY: str = "none"

WRITE_TOOLS: set[str] = {"create_service_request"}


@dataclass(frozen=True, slots=True)
class ToolCallRecord:
    """Record of a tool call executed during agent orchestration."""

    tool_name: str
    arguments: dict[str, Any]
    result: ToolResult


@dataclass(frozen=True, slots=True)
class AgentExecutionResult:
    """Complete result of an agent run including audit trail."""

    answer: str
    customer_id: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    rounds: int = 0
    success: bool = True
    error: str | None = None
    approval_requests: list[ApprovalRequest] = field(default_factory=list)

    def as_dict(self) -> dict[str, Any]:
        return {
            "answer": self.answer,
            "customer_id": self.customer_id,
            "tool_calls": [
                {
                    "tool_name": tc.tool_name,
                    "arguments": tc.arguments,
                    "result": tc.result.as_dict(),
                }
                for tc in self.tool_calls
            ],
            "rounds": self.rounds,
            "success": self.success,
            "error": self.error,
            "approval_requests": [req.as_dict() for req in self.approval_requests],
        }


def load_system_prompt(path: Path = SYSTEM_PROMPT_PATH) -> str:
    """Load the canonical versioned agent system prompt."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("system_instruction", "")).strip()


class AgentOrchestrator:
    """Orchestrates single-agent interactions using read-only and HITL write tools."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL_ALIAS,
        registry: ToolRegistry | None = None,
        system_prompt_path: Path = SYSTEM_PROMPT_PATH,
        base_url: str | None = None,
        client: Any | None = None,
        max_rounds: int = DEFAULT_MAX_TOOL_ROUNDS,
        hitl_manager: HITLApprovalManager | None = None,
        approval_callback: Callable[[ApprovalRequest], bool] | None = None,
    ) -> None:
        self._model = model
        self._registry = registry or ToolRegistry(include_write_tools=True)
        self._system_prompt = load_system_prompt(system_prompt_path)
        self._max_rounds = max_rounds
        self._hitl_manager = hitl_manager or HITLApprovalManager()
        self._approval_callback = approval_callback

        if client is not None:
            self._client = client
            self._base_url = base_url or "custom"
        else:
            self._base_url = base_url or resolve_foundry_base_url()
            self._client = OpenAI(base_url=self._base_url, api_key=_PLACEHOLDER_API_KEY)

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def registry(self) -> ToolRegistry:
        return self._registry

    @property
    def system_prompt(self) -> str:
        return self._system_prompt

    @property
    def hitl_manager(self) -> HITLApprovalManager:
        return self._hitl_manager

    def _call_completions(self, messages: list[dict[str, Any]], tools: list[dict[str, Any]]) -> Any:
        if hasattr(self._client, "chat") and hasattr(self._client.chat, "completions"):
            return self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        if hasattr(self._client, "create"):
            return self._client.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice="auto",
            )
        raise AttributeError("LLM client does not provide a create completion interface")

    def run(
        self,
        user_message: str,
        *,
        customer_id: str,
        approval_callback: Callable[[ApprovalRequest], bool] | None = None,
    ) -> AgentExecutionResult:
        """Run the agent loop over user input with session customer isolation and HITL oversight."""
        context = AgentContext(session_customer_id=customer_id)
        tools = self._registry.export_openai_tools()
        active_approval_cb = approval_callback or self._approval_callback

        messages: list[dict[str, Any]] = [
            {"role": "system", "content": self._system_prompt},
            {"role": "user", "content": user_message},
        ]

        executed_records: list[ToolCallRecord] = []
        created_approvals: list[ApprovalRequest] = []
        current_round = 0

        while current_round < self._max_rounds:
            current_round += 1

            try:
                response = self._call_completions(messages, tools)
            except Exception as exc:
                return AgentExecutionResult(
                    answer="Error al comunicar con el modelo de lenguaje local.",
                    customer_id=customer_id,
                    tool_calls=executed_records,
                    rounds=current_round,
                    success=False,
                    error=str(exc),
                    approval_requests=created_approvals,
                )

            choice = response.choices[0]
            msg = choice.message
            tool_calls = getattr(msg, "tool_calls", None)

            if not tool_calls:
                # Model provided direct final text answer
                answer = msg.content or ""
                return AgentExecutionResult(
                    answer=answer.strip(),
                    customer_id=customer_id,
                    tool_calls=executed_records,
                    rounds=current_round,
                    success=True,
                    approval_requests=created_approvals,
                )

            # Append assistant message with tool calls to conversation history
            assistant_msg: dict[str, Any] = {
                "role": "assistant",
                "content": msg.content or None,
                "tool_calls": [
                    {
                        "id": tc.id,
                        "type": "function",
                        "function": {
                            "name": tc.function.name,
                            "arguments": tc.function.arguments,
                        },
                    }
                    for tc in tool_calls
                ],
            }
            messages.append(assistant_msg)

            # Execute each requested tool deterministically
            for tc in tool_calls:
                fn_name = tc.function.name
                raw_args = tc.function.arguments or "{}"

                try:
                    parsed_args = json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                    if not isinstance(parsed_args, dict):
                        parsed_args = {}
                except json.JSONDecodeError:
                    parsed_args = {}

                # Check if this tool requires Human-in-the-Loop (HITL) approval
                if fn_name in WRITE_TOOLS:
                    approval_req = self._hitl_manager.create_request(
                        tool_name=fn_name,
                        customer_id=customer_id,
                        arguments=parsed_args,
                    )

                    user_approved = False
                    if active_approval_cb is not None:
                        user_approved = active_approval_cb(approval_req)

                    if user_approved:
                        approved_req = self._hitl_manager.approve(
                            approval_req.approval_id, customer_id
                        )
                        tool_result = self._registry.execute(fn_name, parsed_args, context)
                        if tool_result.success:
                            executed_req = self._hitl_manager.verify_and_mark_executed(
                                approval_id=approval_req.approval_id,
                                customer_id=customer_id,
                                arguments_to_execute=parsed_args,
                                execution_result=tool_result.data or {},
                            )
                            created_approvals.append(executed_req)
                        else:
                            created_approvals.append(approved_req)
                    else:
                        rejected_req = self._hitl_manager.reject(
                            approval_req.approval_id,
                            customer_id,
                            reason="Rechazado por el usuario humano",
                        )
                        created_approvals.append(rejected_req)
                        tool_result = ToolResult(
                            tool_name=fn_name,
                            success=False,
                            error=(
                                "Operación WRITE rechazada por el usuario humano. "
                                "No se realizó ninguna modificación en Core Banking."
                            ),
                        )
                else:
                    tool_result = self._registry.execute(fn_name, parsed_args, context)

                executed_records.append(
                    ToolCallRecord(
                        tool_name=fn_name,
                        arguments=parsed_args,
                        result=tool_result,
                    )
                )

                messages.append(
                    {
                        "role": "tool",
                        "tool_call_id": tc.id,
                        "name": fn_name,
                        "content": json.dumps(tool_result.as_dict(), ensure_ascii=False),
                    }
                )

        return AgentExecutionResult(
            answer=(
                "Se alcanzó el límite máximo de llamadas a herramientas "
                "sin obtener respuesta final."
            ),
            customer_id=customer_id,
            tool_calls=executed_records,
            rounds=current_round,
            success=False,
            error="Maximum tool rounds exceeded",
            approval_requests=created_approvals,
        )
