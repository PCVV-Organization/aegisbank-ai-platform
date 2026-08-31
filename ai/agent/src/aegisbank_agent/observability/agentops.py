"""AgentOps operational report and health summary generator."""

from __future__ import annotations

from typing import Any

from .audit import AuditLogger, get_audit_logger
from .metrics import OperationalMetrics, get_metrics


class AgentOpsSummary:
    """Consolidates metrics, traces, and audit logs into an operational health report."""

    def __init__(
        self,
        metrics: OperationalMetrics | None = None,
        audit_logger: AuditLogger | None = None,
    ) -> None:
        self._metrics = metrics or get_metrics()
        self._audit = audit_logger or get_audit_logger()

    def generate_report(self) -> dict[str, Any]:
        """Generate structured operational health summary."""
        snap = self._metrics.snapshot()
        counters = snap["counters"]
        latencies = snap["latencies"]

        req_total = counters.get("request_count", 0)
        req_errors = counters.get("request_error_count", 0)
        error_rate = round((req_errors / req_total * 100.0), 2) if req_total > 0 else 0.0

        tool_total = counters.get("tool_call_count", 0)
        tool_failures = counters.get("tool_call_failure_count", 0)
        tool_success_rate = (
            round(((tool_total - tool_failures) / tool_total * 100.0), 2)
            if tool_total > 0
            else 100.0
        )

        hitl_approved = counters.get("hitl_approved_count", 0)
        hitl_rejected = counters.get("hitl_rejected_count", 0)
        hitl_total = hitl_approved + hitl_rejected
        hitl_approval_rate = (
            round((hitl_approved / hitl_total * 100.0), 2) if hitl_total > 0 else 100.0
        )

        agent_p95 = latencies.get("agent_run_latencies_ms", {}).get("p95", 0.0)

        # Evaluate health status
        status = "HEALTHY"
        if error_rate > 10.0 or counters.get("circuit_breaker_open_count", 0) > 0:
            status = "DEGRADED"
        if error_rate > 30.0:
            status = "UNHEALTHY"

        return {
            "status": status,
            "total_requests": req_total,
            "error_rate_pct": error_rate,
            "tool_call_count": tool_total,
            "tool_success_rate_pct": tool_success_rate,
            "hitl_approval_rate_pct": hitl_approval_rate,
            "agent_p95_latency_ms": agent_p95,
            "retries_count": counters.get("retry_count", 0),
            "circuit_breaker_trips": counters.get("circuit_breaker_open_count", 0),
            "dlq_messages_count": counters.get("dlq_count", 0),
            "total_audit_events": len(self._audit.list_events()),
        }

    def to_markdown(self) -> str:
        """Format operational report as human-readable Markdown."""
        rep = self.generate_report()
        return (
            f"## AegisBank AgentOps Report\n\n"
            f"- **System Status:** `{rep['status']}`\n"
            f"- **Total Requests:** {rep['total_requests']} "
            f"(Error Rate: {rep['error_rate_pct']}%)\n"
            f"- **Tool Calls:** {rep['tool_call_count']} "
            f"(Success Rate: {rep['tool_success_rate_pct']}%)\n"
            f"- **HITL Approvals:** {rep['hitl_approval_rate_pct']}%\n"
            f"- **Agent Latency p95:** {rep['agent_p95_latency_ms']} ms\n"
            f"- **Retries:** {rep['retries_count']} | "
            f"**Circuit Breaker Openings:** {rep['circuit_breaker_trips']}\n"
            f"- **DLQ Messages:** {rep['dlq_messages_count']}\n"
            f"- **Audit Records Recorded:** {rep['total_audit_events']}\n"
        )
