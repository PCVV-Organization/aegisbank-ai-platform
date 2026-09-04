"""Tests for OperationalMetrics, percentiles, and AgentOpsSummary."""

from __future__ import annotations

import pytest

from aegisbank_agent.observability.agentops import AgentOpsSummary
from aegisbank_agent.observability.audit import AuditLogger
from aegisbank_agent.observability.metrics import OperationalMetrics

pytestmark = pytest.mark.unit


def test_operational_metrics_and_percentiles() -> None:
    metrics = OperationalMetrics()

    metrics.increment("request_count", 10)
    metrics.increment("request_error_count", 1)
    metrics.increment("tool_call_count", 15)
    metrics.increment("tool_call_failure_count", 0)
    metrics.increment("hitl_approved_count", 4)
    metrics.increment("hitl_rejected_count", 1)

    # Record 100 latency samples: 1..100 ms
    for val in range(1, 101):
        metrics.record_latency("agent_run_latencies_ms", float(val))

    snap = metrics.snapshot()
    assert snap["counters"]["request_count"] == 10
    assert snap["counters"]["request_error_count"] == 1

    pcts = metrics.get_percentiles("agent_run_latencies_ms")
    assert pcts["count"] == 100
    assert pcts["p50"] == 50.5
    assert pcts["p95"] == 95.05
    assert pcts["p99"] == 99.01


def test_agentops_summary_generation_and_markdown() -> None:
    metrics = OperationalMetrics()
    audit = AuditLogger()

    metrics.increment("request_count", 20)
    metrics.increment("request_error_count", 1)  # 5% error rate
    metrics.increment("tool_call_count", 25)
    metrics.increment("tool_call_failure_count", 1)
    metrics.increment("hitl_approved_count", 8)
    metrics.increment("hitl_rejected_count", 2)
    metrics.record_latency("agent_run_latencies_ms", 120.0)

    summary = AgentOpsSummary(metrics=metrics, audit_logger=audit)
    report = summary.generate_report()

    assert report["status"] == "HEALTHY"
    assert report["total_requests"] == 20
    assert report["error_rate_pct"] == 5.0
    assert report["hitl_approval_rate_pct"] == 80.0
    assert report["tool_success_rate_pct"] == 96.0

    md = summary.to_markdown()
    assert "AegisBank AgentOps Report" in md
    assert "System Status" in md
    assert "80.0%" in md
