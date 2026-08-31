"""Single-agent orchestrator for AegisBank with MCP, HITL, Observability, and HOTL supervision."""

from __future__ import annotations

import json
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aegisbank_rag.foundry_local import DEFAULT_MODEL_ALIAS, resolve_foundry_base_url
from openai import OpenAI

from .constants import DEFAULT_MAX_TOOL_ROUNDS, SYSTEM_PROMPT_PATH
from .hitl import ApprovalRequest, HITLApprovalManager
from .knowledge_routing import has_sufficient_evidence, requires_authorized_knowledge
from .observability import Observability, create_observability
from .observability.audit import AuditEventType, AuditLogger, get_audit_logger
from .observability.context import ObservabilityContext
from .observability.hotl import HOTLSupervisor, get_hotl_supervisor
from .observability.logging import StructuredLogger, get_logger
from .observability.metrics import OperationalMetrics, get_metrics
from .observability.tracer import trace_span
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
    """Complete result of an agent run including audit trail and observability correlation."""

    answer: str
    customer_id: str
    tool_calls: list[ToolCallRecord] = field(default_factory=list)
    rounds: int = 0
    success: bool = True
    error: str | None = None
    approval_requests: list[ApprovalRequest] = field(default_factory=list)
    correlation_id: str = ""
    citations: list[dict[str, Any]] = field(default_factory=list)

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
            "correlation_id": self.correlation_id,
            "citations": self.citations,
        }


def load_system_prompt(path: Path = SYSTEM_PROMPT_PATH) -> str:
    """Load the canonical versioned agent system prompt."""
    payload = json.loads(path.read_text(encoding="utf-8"))
    return str(payload.get("system_instruction", "")).strip()


class AgentOrchestrator:
    """Orchestrates agent interactions with tracing, HOTL, and audit logging."""

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
        observability: Observability | None = None,
        write_enabled: bool = True,
        hotl_supervisor: HOTLSupervisor | None = None,
        metrics: OperationalMetrics | None = None,
        structured_logger: StructuredLogger | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._model = model
        self._registry = registry or ToolRegistry(include_write_tools=True)
        self._system_prompt = load_system_prompt(system_prompt_path)
        self._max_rounds = max_rounds
        self._hitl_manager = hitl_manager or HITLApprovalManager()
        self._approval_callback = approval_callback
        self._observability = observability or create_observability()
        self._write_enabled = write_enabled
        self._hotl = hotl_supervisor or get_hotl_supervisor()
        self._metrics = metrics or get_metrics()
        self._logger = structured_logger or get_logger()
        self._audit = audit_logger or get_audit_logger()

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

    @property
    def observability(self) -> Observability:
        return self._observability

    def disable_writes(self) -> None:
        """HOTL operator control: deny the only WRITE tool."""
        self._write_enabled = False

    def enable_writes(self) -> None:
        self._write_enabled = True

    @property
    def hotl_supervisor(self) -> HOTLSupervisor:
        return self._hotl

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
        correlation_id: str | None = None,
        approval_callback: Callable[[ApprovalRequest], bool] | None = None,
    ) -> AgentExecutionResult:
        """Run the agent loop with tracing, HOTL oversight, and audit trails."""
        start_time = time.perf_counter()
        obs_ctx = ObservabilityContext(customer_id=customer_id)
        if correlation_id:
            obs_ctx.correlation_id = correlation_id

        self._metrics.increment("request_count")
        self._audit.record(
            event_type=AuditEventType.AGENT_RUN_STARTED,
            correlation_id=obs_ctx.correlation_id,
            customer_id=customer_id,
            actor="USER",
            payload={"message_length": len(user_message), "model": self._model},
        )
        self._logger.info(
            "agent_run_started",
            context=obs_ctx,
            extra={"model": self._model},
        )

        with trace_span(
            "agent.run",
            attributes={
                "customer.id": customer_id,
                "correlation_id": obs_ctx.correlation_id,
                "gen_ai.model": self._model,
            },
        ):
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

            # Banking policy/product questions must be grounded before generation.
            knowledge_required = requires_authorized_knowledge(user_message)
            knowledge_tool = self._registry.get_tool("search_knowledge")
            if knowledge_required:
                self._metrics.increment("knowledge_required_count")
            if knowledge_required and knowledge_tool is None:
                self._metrics.increment("knowledge_tool_missed_count")
                self._metrics.increment("knowledge_abstention_count")
                return AgentExecutionResult(
                    answer=(
                        "No encuentro información suficiente en la base de conocimiento "
                        "autorizada para confirmar ese dato."
                    ),
                    customer_id=customer_id,
                    rounds=0,
                    success=True,
                    approval_requests=created_approvals,
                    correlation_id=obs_ctx.correlation_id,
                )
            if knowledge_required and knowledge_tool is not None:
                self._audit.record(
                    event_type=AuditEventType.TOOL_PROPOSED,
                    correlation_id=obs_ctx.correlation_id,
                    customer_id=customer_id,
                    actor="GROUNDING_POLICY",
                    payload={"tool_name": "search_knowledge"},
                )
                knowledge_start = time.perf_counter()
                with trace_span(
                    "retrieval.search_knowledge",
                    attributes={"tool.name": "search_knowledge"},
                ):
                    knowledge_result = self._registry.execute(
                        "search_knowledge", {"query": user_message}, context
                    )
                self._metrics.increment("knowledge_tool_invoked_count")
                self._metrics.record_latency(
                    "tool_latencies_ms", (time.perf_counter() - knowledge_start) * 1000.0
                )
                executed_records.append(
                    ToolCallRecord(
                        tool_name="search_knowledge",
                        arguments={"query": user_message},
                        result=knowledge_result,
                    )
                )
                self._audit.record(
                    event_type=AuditEventType.TOOL_EXECUTED,
                    correlation_id=obs_ctx.correlation_id,
                    customer_id=customer_id,
                    actor="GROUNDING_POLICY",
                    payload={"tool_name": "search_knowledge", "result": knowledge_result.data},
                )
                if not knowledge_result.success or not has_sufficient_evidence(
                    user_message, knowledge_result.data
                ):
                    self._metrics.increment("knowledge_abstention_count")
                    self._audit.record(
                        event_type=AuditEventType.AGENT_RUN_COMPLETED,
                        correlation_id=obs_ctx.correlation_id,
                        customer_id=customer_id,
                        actor="GROUNDING_POLICY",
                        payload={"status": "ABSTAIN", "reason": "KNOWLEDGE_GAP"},
                    )
                    citations = [
                        {
                            key: hit[key]
                            for key in ("document_id", "chunk_id", "title", "version")
                            if key in hit
                        }
                        for hit in (knowledge_result.data or {}).get("hits", [])
                    ]
                    return AgentExecutionResult(
                        answer=(
                            "No encuentro información suficiente en la base de conocimiento "
                            "autorizada para confirmar ese dato."
                        ),
                        customer_id=customer_id,
                        tool_calls=executed_records,
                        rounds=0,
                        success=True,
                        approval_requests=created_approvals,
                        correlation_id=obs_ctx.correlation_id,
                        citations=citations,
                    )
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Usa exclusivamente esta evidencia autorizada para responder. "
                            f"{json.dumps(knowledge_result.data, ensure_ascii=False)}"
                        ),
                    }
                )

            while current_round < self._max_rounds:
                current_round += 1

                # 1. LLM Chat Completions Call
                llm_start = time.perf_counter()
                self._metrics.increment("llm_call_count")
                try:
                    with trace_span(
                        "llm.chat",
                        attributes={
                            "gen_ai.system": "openai",
                            "gen_ai.model": self._model,
                            "round": current_round,
                        },
                    ):
                        response = self._call_completions(messages, tools)
                    llm_dur_ms = (time.perf_counter() - llm_start) * 1000.0
                    self._metrics.record_latency("llm_latencies_ms", llm_dur_ms)
                except Exception as exc:
                    self._metrics.increment("request_error_count")
                    total_dur_ms = (time.perf_counter() - start_time) * 1000.0
                    self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
                    self._logger.error(
                        "llm_call_failed",
                        context=obs_ctx,
                        error_code="LLM_COMMUNICATION_ERROR",
                        extra={"error": str(exc)},
                    )
                    return AgentExecutionResult(
                        answer="Error al comunicar con el modelo de lenguaje local.",
                        customer_id=customer_id,
                        tool_calls=executed_records,
                        rounds=current_round,
                        success=False,
                        error=str(exc),
                        approval_requests=created_approvals,
                        correlation_id=obs_ctx.correlation_id,
                    )

                choice = response.choices[0]
                msg = choice.message
                tool_calls = getattr(msg, "tool_calls", None)
                raw_finish_reason = getattr(choice, "finish_reason", None)
                finish_reason = (
                    raw_finish_reason
                    if raw_finish_reason is None
                    or isinstance(raw_finish_reason, (str, int, float, bool))
                    else None
                )
                self._logger.info(
                    "llm_response_observed",
                    context=obs_ctx,
                    extra={
                        "tools_provided": len(tools),
                        "tool_choice": "auto",
                        "finish_reason": finish_reason,
                        "structured_tool_call": bool(tool_calls),
                    },
                )

                if not tool_calls:
                    # Model provided direct final text answer
                    answer = msg.content or ""
                    total_dur_ms = (time.perf_counter() - start_time) * 1000.0
                    self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
                    self._audit.record(
                        event_type=AuditEventType.AGENT_RUN_COMPLETED,
                        correlation_id=obs_ctx.correlation_id,
                        customer_id=customer_id,
                        actor="AGENT",
                        payload={"rounds": current_round, "status": "SUCCESS"},
                    )
                    self._logger.info(
                        "agent_run_completed",
                        context=obs_ctx,
                        execution_status="SUCCESS",
                        latency_ms=total_dur_ms,
                    )
                    return AgentExecutionResult(
                        answer=answer.strip(),
                        customer_id=customer_id,
                        tool_calls=executed_records,
                        rounds=current_round,
                        success=True,
                        approval_requests=created_approvals,
                        correlation_id=obs_ctx.correlation_id,
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
                        parsed_args = (
                            json.loads(raw_args) if isinstance(raw_args, str) else raw_args
                        )
                        if not isinstance(parsed_args, dict):
                            parsed_args = {}
                    except json.JSONDecodeError:
                        parsed_args = {}

                    self._metrics.increment("tool_call_count")
                    self._audit.record(
                        event_type=AuditEventType.TOOL_PROPOSED,
                        correlation_id=obs_ctx.correlation_id,
                        customer_id=customer_id,
                        actor="AGENT",
                        payload={"tool_name": fn_name, "arguments": parsed_args},
                    )

                    # 2. Check HOTL Supervisor Kill-Switch before allowing write tools
                    if fn_name in WRITE_TOOLS and not self._hotl.is_write_allowed:
                        reason = self._hotl.kill_switch_reason or "Suspended by supervisor"
                        tool_result = ToolResult(
                            tool_name=fn_name,
                            success=False,
                            error=(
                                "Operación WRITE temporalmente deshabilitada por "
                                f"supervisión HOTL: {reason}."
                            ),
                        )
                        self._audit.record(
                            event_type=AuditEventType.TOOL_DENIED,
                            correlation_id=obs_ctx.correlation_id,
                            customer_id=customer_id,
                            actor="HOTL_SUPERVISOR",
                            payload={"tool_name": fn_name, "reason": reason},
                        )
                        self._logger.warning(
                            "tool_execution_denied_by_hotl",
                            context=obs_ctx,
                            tool_name=fn_name,
                            error_code="HOTL_KILL_SWITCH_ENGAGED",
                        )
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
                        continue

                    # 3. Check if this tool requires Human-in-the-Loop (HITL) approval
                    if fn_name in WRITE_TOOLS:
                        approval_req = self._hitl_manager.create_request(
                            tool_name=fn_name,
                            customer_id=customer_id,
                            arguments=parsed_args,
                        )
                        self._audit.record(
                            event_type=AuditEventType.HITL_REQUESTED,
                            correlation_id=obs_ctx.correlation_id,
                            customer_id=customer_id,
                            actor="SYSTEM",
                            payload={"approval_id": approval_req.approval_id, "tool_name": fn_name},
                        )

                        user_approved = False
                        if active_approval_cb is not None:
                            user_approved = active_approval_cb(approval_req)

                        if user_approved:
                            self._metrics.increment("hitl_approved_count")
                            approved_req = self._hitl_manager.approve(
                                approval_req.approval_id, customer_id
                            )
                            self._audit.record(
                                event_type=AuditEventType.HITL_APPROVED,
                                correlation_id=obs_ctx.correlation_id,
                                customer_id=customer_id,
                                actor="USER",
                                payload={"approval_id": approval_req.approval_id},
                            )

                            tool_start = time.perf_counter()
                            with trace_span(
                                f"tool.{fn_name}",
                                attributes={
                                    "tool.name": fn_name,
                                    "customer.id": customer_id,
                                    "hitl.approved": True,
                                },
                            ):
                                tool_result = self._registry.execute(fn_name, parsed_args, context)
                            tool_dur_ms = (time.perf_counter() - tool_start) * 1000.0
                            self._metrics.record_latency("tool_latencies_ms", tool_dur_ms)

                            if tool_result.success:
                                executed_req = self._hitl_manager.verify_and_mark_executed(
                                    approval_id=approval_req.approval_id,
                                    customer_id=customer_id,
                                    arguments_to_execute=parsed_args,
                                    execution_result=tool_result.data or {},
                                )
                                created_approvals.append(executed_req)
                                self._audit.record(
                                    event_type=AuditEventType.HITL_EXECUTED,
                                    correlation_id=obs_ctx.correlation_id,
                                    customer_id=customer_id,
                                    actor="SYSTEM",
                                    payload={
                                        "approval_id": approval_req.approval_id,
                                        "result": tool_result.data,
                                    },
                                )
                            else:
                                created_approvals.append(approved_req)
                                self._metrics.increment("tool_call_failure_count")
                        else:
                            self._metrics.increment("hitl_rejected_count")
                            rejected_req = self._hitl_manager.reject(
                                approval_req.approval_id,
                                customer_id,
                                reason="Rechazado por el usuario humano",
                            )
                            created_approvals.append(rejected_req)
                            self._audit.record(
                                event_type=AuditEventType.HITL_REJECTED,
                                correlation_id=obs_ctx.correlation_id,
                                customer_id=customer_id,
                                actor="USER",
                                payload={"approval_id": approval_req.approval_id},
                            )
                            tool_result = ToolResult(
                                tool_name=fn_name,
                                success=False,
                                error=(
                                    "Operación WRITE rechazada por el usuario humano. "
                                    "No se realizó ninguna modificación en Core Banking."
                                ),
                            )
                    else:
                        tool_start = time.perf_counter()
                        with trace_span(
                            f"tool.{fn_name}",
                            attributes={"tool.name": fn_name, "customer.id": customer_id},
                        ):
                            tool_result = self._registry.execute(fn_name, parsed_args, context)
                        tool_dur_ms = (time.perf_counter() - tool_start) * 1000.0
                        self._metrics.record_latency("tool_latencies_ms", tool_dur_ms)
                        if not tool_result.success:
                            self._metrics.increment("tool_call_failure_count")

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

            total_dur_ms = (time.perf_counter() - start_time) * 1000.0
            self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
            self._metrics.increment("request_error_count")
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
                correlation_id=obs_ctx.correlation_id,
            )
