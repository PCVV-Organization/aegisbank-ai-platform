"""Single-agent orchestrator for AegisBank with MCP, HITL, Observability, and HOTL supervision."""

from __future__ import annotations

import json
import os
import re
import time
from collections.abc import Callable
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any

from aegisbank_rag.foundry_local import DEFAULT_MODEL_ALIAS, resolve_foundry_base_url
from openai import OpenAI

from .constants import DEFAULT_MAX_TOOL_ROUNDS, SYSTEM_PROMPT_PATH
from .hitl import ApprovalRequest, HITLApprovalManager
from .knowledge_routing import (
    account_tool_allowlist,
    asks_for_payment_dates,
    asks_loan_ownership,
    classify_service_inquiry,
    extract_customer_ids,
    extract_loan_id,
    has_fake_tool_claim,
    has_placeholder_leak,
    has_process_hallucination,
    has_sufficient_evidence,
    is_comparative_loan_query,
    is_cross_customer_attempt,
    is_greeting,
    is_last_loan_reference,
    requires_account_data,
    requires_authorized_knowledge,
)
from .observability import Observability, create_observability
from .observability.audit import AuditEventType, AuditLogger, get_audit_logger
from .observability.context import ObservabilityContext
from .observability.hotl import HOTLSupervisor, get_hotl_supervisor
from .observability.logging import StructuredLogger, get_logger
from .observability.metrics import OperationalMetrics, get_metrics
from .observability.tracer import trace_span
from .session_store import OwnershipViolationError, SQLiteSessionStore
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
        session_store: SQLiteSessionStore | None = None,
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
        self._session_store = session_store or SQLiteSessionStore()

        if client is not None:
            self._client = client
            self._base_url = base_url or "custom"
        else:
            self._base_url = base_url or resolve_foundry_base_url()
            timeout = float(os.getenv("AEGISBANK_FOUNDRY_TIMEOUT_SECONDS", "30"))
            retries = int(os.getenv("AEGISBANK_FOUNDRY_MAX_RETRIES", "2"))
            self._client = OpenAI(
                base_url=self._base_url,
                api_key=_PLACEHOLDER_API_KEY,
                timeout=timeout,
                max_retries=retries,
            )

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

    def _call_completions(
        self,
        messages: list[dict[str, Any]],
        tools: list[dict[str, Any]],
        tool_choice: Any = "auto",
    ) -> Any:
        if hasattr(self._client, "chat") and hasattr(self._client.chat, "completions"):
            return self._client.chat.completions.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
            )
        if hasattr(self._client, "create"):
            return self._client.create(
                model=self._model,
                messages=messages,
                tools=tools,
                tool_choice=tool_choice,
            )
        raise AttributeError("LLM client does not provide a create completion interface")

    @staticmethod
    def _format_loan_details_answer(data: dict[str, Any], query: str = "") -> str:
        """Render a user-facing summary from a ``get_loan_details`` payload."""
        if not isinstance(data, dict):
            return "Tengo los datos del préstamo solicitados."
        loan_id = data.get("loan_id", "")
        customer_id = data.get("customer_id", "")
        product = data.get("product_code", "")
        currency = data.get("currency", "")
        outstanding = data.get("outstanding_balance", "")
        principal = data.get("principal_amount", "")
        status = data.get("status", "")

        prefix = ""
        if query and asks_loan_ownership(query):
            prefix = (
                f"Sí, el préstamo {loan_id} pertenece a tu cuenta autorizada ({customer_id}).\n\n"
            )

        return (
            f"{prefix}Préstamo {loan_id} ({product}, {currency}): "
            f"saldo pendiente {outstanding} de {principal}. Estado: {status}."
        )

    @staticmethod
    def _format_installment_answer(data: dict[str, Any]) -> str:
        """Render a user-facing summary from a ``get_next_installment`` payload."""
        if not isinstance(data, dict):
            return ""
        if not data.get("has_next_installment"):
            return "No hay cuotas pendientes ni vencidas para este préstamo."
        installment_id = data.get("installment_id", "")
        due_date = data.get("due_date", "")
        total_due = data.get("total_due", "")
        status = data.get("status", "")
        return (
            f"Próxima cuota {installment_id} (vence {due_date}): "
            f"total a pagar {total_due}. Estado: {status}."
        )

    def run(
        self,
        user_message: str,
        *,
        customer_id: str,
        session_id: str | None = None,
        correlation_id: str | None = None,
        approval_callback: Callable[[ApprovalRequest], bool] | None = None,
    ) -> AgentExecutionResult:
        """Run the agent loop with tracing, HOTL oversight, and audit trails."""
        start_time = time.perf_counter()
        obs_ctx = ObservabilityContext(customer_id=customer_id)
        if correlation_id:
            obs_ctx.correlation_id = correlation_id
        effective_session_id = session_id or f"session-{customer_id}"
        try:
            session = self._session_store.get_or_create(effective_session_id, customer_id)
        except OwnershipViolationError:
            self._audit.record(
                event_type=AuditEventType.TOOL_DENIED,
                correlation_id=obs_ctx.correlation_id,
                customer_id=customer_id,
                actor="SESSION_GUARD",
                payload={"reason": "SESSION_OWNERSHIP_VIOLATION"},
            )
            return AgentExecutionResult(
                answer="No tienes acceso a esta sesión de conversación.",
                customer_id=customer_id,
                success=False,
                error="Session ownership violation",
                correlation_id=obs_ctx.correlation_id,
            )

        # Deterministic Cross-Customer Inquiry Guard
        if is_cross_customer_attempt(user_message, customer_id):
            mentioned = extract_customer_ids(user_message)
            self._logger.warning(
                "Cross-customer banking query deterministically denied",
                context=obs_ctx,
                extra={
                    "session_customer_id": customer_id,
                    "mentioned_customers": mentioned,
                },
            )
            self._audit.record(
                event_type=AuditEventType.TOOL_DENIED,
                correlation_id=obs_ctx.correlation_id,
                customer_id=customer_id,
                actor="SECURITY_GUARD",
                payload={
                    "reason": "CROSS_CUSTOMER_ATTEMPT",
                    "session_customer_id": customer_id,
                    "mentioned_customers": mentioned,
                },
            )
            total_dur_ms = (time.perf_counter() - start_time) * 1000.0
            self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
            return AgentExecutionResult(
                answer="No puedo consultar información bancaria de otro cliente desde esta sesión.",
                customer_id=customer_id,
                rounds=0,
                tool_calls=[],
                success=False,
                error="Cross-customer access denied",
                correlation_id=obs_ctx.correlation_id,
            )

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
            # Ambiguous claims / service request clarification
            if classify_service_inquiry(user_message) == "CLARIFICATION":
                self._logger.info(
                    "clarification_requested",
                    context=obs_ctx,
                    execution_status="CLARIFICATION",
                    extra={"routing_mode": "AMBIGUITY_CLARIFICATION"},
                )
                total_dur_ms = (time.perf_counter() - start_time) * 1000.0
                self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
                clarification_text = (
                    "Para orientarte adecuadamente, ¿podrías precisarme a qué te refieres?\n"
                    "- Si deseas conocer los datos requeridos para registrar un reclamo en el "
                    "sistema (categoría y motivo), te los indico desde nuestro catálogo "
                    "de servicios.\n"
                    "- Si buscas los requisitos o la política institucional para la procedencia de "
                    "un reclamo, consulto la base de conocimiento autorizada."
                )
                return AgentExecutionResult(
                    answer=clarification_text,
                    customer_id=customer_id,
                    tool_calls=[],
                    rounds=0,
                    success=True,
                    correlation_id=obs_ctx.correlation_id,
                )

            context = AgentContext(session_customer_id=customer_id)
            all_tools = self._registry.export_openai_tools()
            account_required = requires_account_data(user_message)
            account_allowlist = account_tool_allowlist(user_message) if account_required else []
            if is_greeting(user_message):
                tools = []
            elif account_required:
                self._metrics.increment("banking_data_required_count")
                self._metrics.increment("forced_routing_count")
                tools = [
                    tool
                    for tool in all_tools
                    if tool["function"]["name"] in account_allowlist
                    or tool["function"]["name"] in WRITE_TOOLS
                ]
            else:
                tools = all_tools
            active_approval_cb = approval_callback or self._approval_callback

            messages: list[dict[str, Any]] = [
                {"role": "system", "content": self._system_prompt},
                {"role": "user", "content": user_message},
            ]

            executed_records: list[ToolCallRecord] = []
            created_approvals: list[ApprovalRequest] = []
            current_round = 0
            account_result: ToolResult | None = None
            account_model_calls = 0

            # Resolve the account list deterministically before asking for a follow-up tool.
            if account_required and "get_my_loans" in account_allowlist:
                with trace_span(
                    "tool.get_my_loans",
                    attributes={
                        "tool.name": "get_my_loans",
                        "customer.id": customer_id,
                        "routing.mode": "POLICY_ENFORCED_ROUTING",
                    },
                ):
                    account_result = self._registry.execute("get_my_loans", {}, context)
                self._metrics.increment("banking_tool_invoked_count")
                executed_records.append(ToolCallRecord("get_my_loans", {}, account_result))
                messages.append(
                    {
                        "role": "system",
                        "content": (
                            "Datos autorizados de la sesión actual. Usa únicamente estos "
                            f"datos: {json.dumps(account_result.data, ensure_ascii=False)}"
                        ),
                    }
                )
                if not account_result.success:
                    self._metrics.increment("banking_tool_missed_count")
                    return AgentExecutionResult(
                        answer="No pude consultar los datos bancarios de la sesión.",
                        customer_id=customer_id,
                        tool_calls=executed_records,
                        success=False,
                        error=account_result.error,
                        correlation_id=obs_ctx.correlation_id,
                    )
                tools = [
                    tool
                    for tool in all_tools
                    if (
                        tool["function"]["name"] in account_allowlist
                        or tool["function"]["name"] in WRITE_TOOLS
                    )
                    and tool["function"]["name"] != "get_my_loans"
                ]

                loans = (account_result.data or {}).get("loans", [])
                if is_comparative_loan_query(user_message):
                    if not loans:
                        return AgentExecutionResult(
                            answer="No tienes préstamos registrados en este momento.",
                            customer_id=customer_id,
                            tool_calls=executed_records,
                            rounds=0,
                            success=True,
                            correlation_id=obs_ctx.correlation_id,
                        )
                    highest_loan = max(
                        loans,
                        key=lambda item: float(item.get("outstanding_balance", 0.0)),
                    )
                    winner_loan_id = str(highest_loan.get("loan_id", ""))
                    if winner_loan_id:
                        self._session_store.record_loan_access(
                            effective_session_id, customer_id, winner_loan_id
                        )

                    installment_clause = ""
                    if asks_for_payment_dates(user_message):
                        inst_start = time.perf_counter()
                        with trace_span(
                            "tool.get_next_installment",
                            attributes={
                                "tool.name": "get_next_installment",
                                "customer.id": customer_id,
                                "routing.mode": "COMPARATIVE_PLAN_FORCED",
                                "aegisbank.loan_id": winner_loan_id,
                            },
                        ):
                            inst_result = self._registry.execute(
                                "get_next_installment",
                                {"loan_id": winner_loan_id},
                                context,
                            )
                        self._metrics.increment("banking_tool_invoked_count")
                        self._metrics.record_latency(
                            "tool_latencies_ms", (time.perf_counter() - inst_start) * 1000.0
                        )
                        executed_records.append(
                            ToolCallRecord(
                                tool_name="get_next_installment",
                                arguments={"loan_id": winner_loan_id},
                                result=inst_result,
                            )
                        )
                        if inst_result.success and inst_result.data:
                            inst_data = inst_result.data
                            if inst_data.get("has_next_installment"):
                                installment_clause = (
                                    f"\nPróxima cuota {inst_data.get('installment_id')} "
                                    f"(vence {inst_data.get('due_date')}): total a pagar "
                                    f"{inst_data.get('total_due')}. "
                                    "(Nota: el sistema expone la próxima cuota a vencer; "
                                    "no dispone de un calendario completo de cuotas futuras)."
                                )
                            else:
                                installment_clause = (
                                    "\nNo hay cuotas pendientes ni vencidas para este préstamo."
                                )
                        else:
                            installment_clause = (
                                "\nNo se pudo consultar la próxima cuota del préstamo."
                            )

                    prod = highest_loan.get("product_code", "")
                    curr = highest_loan.get("currency", "")
                    try:
                        out_bal = float(highest_loan.get("outstanding_balance", 0.0))
                    except ValueError, TypeError:
                        out_bal = 0.0
                    try:
                        prin_bal = float(highest_loan.get("principal_amount", 0.0))
                    except ValueError, TypeError:
                        prin_bal = 0.0
                    st = highest_loan.get("status", "")

                    comparative_answer = (
                        f"El préstamo con mayor saldo pendiente es {winner_loan_id} "
                        f"({prod}, {curr}): saldo pendiente {out_bal:.2f} de {prin_bal:.2f}. "
                        f"Estado: {st}.{installment_clause}"
                    )
                    total_dur_ms = (time.perf_counter() - start_time) * 1000.0
                    self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
                    self._audit.record(
                        event_type=AuditEventType.AGENT_RUN_COMPLETED,
                        correlation_id=obs_ctx.correlation_id,
                        customer_id=customer_id,
                        actor="COMPARATIVE_PLANNER",
                        payload={
                            "plan": "COMPARATIVE_LOAN_QUERY",
                            "winner_loan_id": winner_loan_id,
                            "loans_compared": len(loans),
                            "rounds": 0,
                            "status": "SUCCESS",
                        },
                    )
                    self._logger.info(
                        "comparative_loan_query_completed",
                        context=obs_ctx,
                        execution_status="SUCCESS",
                        latency_ms=total_dur_ms,
                    )
                    return AgentExecutionResult(
                        answer=comparative_answer,
                        customer_id=customer_id,
                        tool_calls=executed_records,
                        rounds=0,
                        success=True,
                        correlation_id=obs_ctx.correlation_id,
                    )

                if (
                    len(loans) > 1
                    and extract_loan_id(user_message) is None
                    and "detalle" in user_message.lower()
                ):
                    ids = ", ".join(str(loan_item.get("loan_id")) for loan_item in loans)
                    messages.append(
                        {
                            "role": "system",
                            "content": (
                                "El cliente solicitó detalle de préstamo pero posee múltiples "
                                f"préstamos ({ids}) sin especificar cuál. NO adivines ni inventes "
                                "un préstamo. Pídele al cliente que elija cuál de ellos desea "
                                "consultar."
                            ),
                        }
                    )
                    tools = []

            # Deterministic loan-detail execution: when the user explicitly
            # referenced a ``LOAN-XXXX`` and the allowlist already pinpoints the
            # single detail tool, execute it without depending on the model's
            # structured tool call. Without this block the orchestrator would
            # bounce into the LLM with ``auto`` tool_choice on queries that
            # mention only a loan id, which is exactly what produced the
            # pseudo-tool-call bug discovered during manual E2E review.
            forced_loan_id = extract_loan_id(user_message)
            if forced_loan_id is None and is_last_loan_reference(user_message):
                forced_loan_id = session.last_loan_id
                if forced_loan_id is None:
                    return AgentExecutionResult(
                        answer=(
                            "No tengo un préstamo previo registrado en esta sesión. "
                            "Indícame el ID del préstamo que deseas consultar."
                        ),
                        customer_id=customer_id,
                        rounds=0,
                        success=True,
                        correlation_id=obs_ctx.correlation_id,
                    )
            if (
                account_required
                and forced_loan_id is not None
                and "get_my_loans" not in account_allowlist
                and account_allowlist == ["get_loan_details"]
            ):
                forced_tool = "get_loan_details"
                with trace_span(
                    f"tool.{forced_tool}",
                    attributes={
                        "tool.name": forced_tool,
                        "customer.id": customer_id,
                        "routing.mode": "LOAN_ID_POLICY_FORCED",
                        "aegisbank.loan_id": forced_loan_id,
                    },
                ):
                    forced_result = self._registry.execute(
                        forced_tool, {"loan_id": forced_loan_id}, context
                    )
                self._metrics.increment("banking_tool_invoked_count")
                executed_records.append(
                    ToolCallRecord(
                        tool_name=forced_tool,
                        arguments={"loan_id": forced_loan_id},
                        result=forced_result,
                    )
                )
                total_dur_ms = (time.perf_counter() - start_time) * 1000.0
                self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
                if not forced_result.success:
                    self._metrics.increment("banking_tool_missed_count")
                    error_message = forced_result.error or (
                        "No pude consultar el detalle del préstamo."
                        if forced_tool == "get_loan_details"
                        else "No pude consultar la próxima cuota del préstamo."
                    )
                    return AgentExecutionResult(
                        answer=error_message,
                        customer_id=customer_id,
                        tool_calls=executed_records,
                        rounds=0,
                        success=False,
                        error=forced_result.error,
                        correlation_id=obs_ctx.correlation_id,
                    )
                answer = (
                    self._format_installment_answer(forced_result.data)
                    if forced_tool == "get_next_installment"
                    else self._format_loan_details_answer(forced_result.data, user_message)
                )
                self._session_store.record_loan_access(
                    effective_session_id, customer_id, forced_loan_id
                )
                return AgentExecutionResult(
                    answer=answer,
                    customer_id=customer_id,
                    tool_calls=executed_records,
                    rounds=0,
                    success=True,
                    correlation_id=obs_ctx.correlation_id,
                )

            selected_tool = tools[0]["function"]["name"] if len(tools) == 1 else None
            effective_tool_choice: Any = (
                {"type": "function", "function": {"name": selected_tool}}
                if account_required and selected_tool
                else "auto"
            )

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
                        response = self._call_completions(
                            messages, tools, tool_choice=effective_tool_choice
                        )
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
                        answer=(
                            "Error al comunicar con el modelo de lenguaje local (Foundry Local). "
                            "Puedes continuar realizando consultas bancarias estructuradas "
                            "indicando el identificador del préstamo (ej. LOAN-0001)."
                        ),
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
                        "routing_mode": (
                            "POLICY_ENFORCED_ROUTING" if account_required else "AUTO_ROUTING"
                        ),
                        "effective_tool_choice": effective_tool_choice,
                        "finish_reason": finish_reason,
                        "structured_tool_call": bool(tool_calls),
                    },
                )

                if not tool_calls:
                    if account_result is not None and not any(
                        rec.tool_name == "get_my_loans" for rec in executed_records
                    ):
                        executed_records.append(ToolCallRecord("get_my_loans", {}, account_result))
                    content_str = msg.content or ""
                    raw_tool_patterns = (
                        r"\bget_loan_details\s*\(",
                        r"\bget_my_loans\s*\(",
                        r"\bget_next_installment\s*\(",
                        r"\bcreate_service_request\s*\(",
                    )
                    is_pseudo_tool = account_required and (
                        any(name in content_str for name in account_allowlist)
                        or any(re.search(pat, content_str) for pat in raw_tool_patterns)
                    )
                    if is_pseudo_tool:
                        self._metrics.increment("pseudo_tool_call_count")
                        self._metrics.increment("banking_tool_missed_count")
                        self._audit.record(
                            event_type=AuditEventType.TOOL_DENIED,
                            correlation_id=obs_ctx.correlation_id,
                            customer_id=customer_id,
                            actor="ROUTING_POLICY",
                            payload={
                                "reason": "PSEUDO_TOOL_CALL",
                                "content_length": len(content_str),
                            },
                        )
                        return AgentExecutionResult(
                            answer=(
                                "No pude obtener una respuesta estructurada del sistema bancario."
                            ),
                            customer_id=customer_id,
                            tool_calls=executed_records,
                            rounds=current_round,
                            success=False,
                            error="Structured tool call was not emitted",
                            correlation_id=obs_ctx.correlation_id,
                        )
                    # Model provided direct final text answer
                    answer = msg.content or ""

                    # Invariant: NO ACCOUNT FACTS WITHOUT AUTHORIZED TOOL EVIDENCE
                    # Guard against: PLACEHOLDER_LEAK, PROCESS_HALLUCINATION,
                    # FALSE_TOOL_EXECUTION_CLAIM, UNGROUNDED_ACCOUNT_RESPONSE
                    has_placeholder = has_placeholder_leak(answer)
                    has_proc_hallucination = has_process_hallucination(answer)
                    has_fake_claim = has_fake_tool_claim(answer) and not any(
                        r.result.success for r in executed_records
                    )
                    has_ungrounded_account = account_required and not any(
                        r.result.success for r in executed_records
                    )

                    if (
                        has_proc_hallucination
                        or has_placeholder
                        or has_fake_claim
                        or has_ungrounded_account
                    ):
                        violation_reason = (
                            "PROCESS_HALLUCINATION"
                            if has_proc_hallucination
                            else "PLACEHOLDER_LEAK"
                            if has_placeholder
                            else "FALSE_TOOL_EXECUTION_CLAIM"
                            if has_fake_claim
                            else "UNGROUNDED_ACCOUNT_RESPONSE"
                        )
                        self._metrics.increment("banking_tool_missed_count")
                        self._audit.record(
                            event_type=AuditEventType.TOOL_DENIED,
                            correlation_id=obs_ctx.correlation_id,
                            customer_id=customer_id,
                            actor="ROUTING_POLICY",
                            payload={
                                "reason": violation_reason,
                                "raw_answer_length": len(answer),
                            },
                        )
                        self._logger.warning(
                            "ungrounded_or_placeholder_response_intercepted",
                            context=obs_ctx,
                            error_code=violation_reason,
                        )
                        total_dur_ms = (time.perf_counter() - start_time) * 1000.0
                        self._metrics.record_latency("agent_run_latencies_ms", total_dur_ms)
                        return AgentExecutionResult(
                            answer=(
                                "No pude consultar la información verificada de tus cuentas "
                                "en este momento. Por seguridad bancaria, no proporciono "
                                "estimaciones ni datos no confirmados."
                            ),
                            customer_id=customer_id,
                            tool_calls=executed_records,
                            rounds=current_round,
                            success=False,
                            error=f"Ungrounded account response rejected ({violation_reason})",
                            correlation_id=obs_ctx.correlation_id,
                        )

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
                    if fn_name in account_allowlist:
                        self._metrics.increment("banking_tool_invoked_count")
                    self._audit.record(
                        event_type=AuditEventType.TOOL_PROPOSED,
                        correlation_id=obs_ctx.correlation_id,
                        customer_id=customer_id,
                        actor="AGENT",
                        payload={"tool_name": fn_name, "arguments": parsed_args},
                    )

                    if fn_name == "get_my_loans" and account_result is not None:
                        account_model_calls += 1
                        if account_model_calls > 1:
                            executed_records.append(
                                ToolCallRecord("get_my_loans", {}, account_result)
                            )
                        tool_result = account_result
                        messages.append(
                            {
                                "role": "tool",
                                "tool_call_id": tc.id,
                                "name": fn_name,
                                "content": json.dumps(tool_result.as_dict(), ensure_ascii=False),
                            }
                        )
                        continue

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
                    if fn_name == "get_loan_details" and tool_result.success:
                        loan_id = str(parsed_args.get("loan_id", ""))
                        if loan_id:
                            self._session_store.record_loan_access(
                                effective_session_id, customer_id, loan_id
                            )

                    messages.append(
                        {
                            "role": "tool",
                            "tool_call_id": tc.id,
                            "name": fn_name,
                            "content": json.dumps(tool_result.as_dict(), ensure_ascii=False),
                        }
                    )
                effective_tool_choice = "auto"
                tools = all_tools

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
