"""Operational metrics aggregation and latency percentile calculations."""

from __future__ import annotations

import math
import threading
from typing import Any


class OperationalMetrics:
    """Thread-safe collector for operational counters and latency histograms."""

    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._counters: dict[str, int] = {
            "request_count": 0,
            "request_error_count": 0,
            "llm_call_count": 0,
            "tool_call_count": 0,
            "tool_call_failure_count": 0,
            "hitl_approved_count": 0,
            "hitl_rejected_count": 0,
            "retry_count": 0,
            "circuit_breaker_open_count": 0,
            "outbox_pending_count": 0,
            "dlq_count": 0,
        }
        self._latencies: dict[str, list[float]] = {
            "agent_run_latencies_ms": [],
            "llm_latencies_ms": [],
            "tool_latencies_ms": [],
        }

    def increment(self, counter_name: str, delta: int = 1) -> int:
        """Increment a counter metric thread-safely."""
        with self._lock:
            val = self._counters.get(counter_name, 0) + delta
            self._counters[counter_name] = val
            return val

    def record_latency(self, metric_name: str, latency_ms: float) -> None:
        """Record an execution latency measurement."""
        with self._lock:
            if metric_name not in self._latencies:
                self._latencies[metric_name] = []
            self._latencies[metric_name].append(latency_ms)

    def get_counter(self, counter_name: str) -> int:
        with self._lock:
            return self._counters.get(counter_name, 0)

    def get_percentiles(self, metric_name: str) -> dict[str, float]:
        """Compute p50, p95, p99 percentiles for a latency histogram."""
        with self._lock:
            values = sorted(self._latencies.get(metric_name, []))

        if not values:
            return {"p50": 0.0, "p95": 0.0, "p99": 0.0, "count": 0, "avg": 0.0}

        def _calc_p(pct: float) -> float:
            k = (len(values) - 1) * (pct / 100.0)
            f = math.floor(k)
            c = math.ceil(k)
            if f == c:
                return float(values[int(k)])
            d0 = values[int(f)] * (c - k)
            d1 = values[int(c)] * (k - f)
            return float(d0 + d1)

        return {
            "p50": round(_calc_p(50), 2),
            "p95": round(_calc_p(95), 2),
            "p99": round(_calc_p(99), 2),
            "count": len(values),
            "avg": round(sum(values) / len(values), 2),
        }

    def snapshot(self) -> dict[str, Any]:
        """Generate a complete dictionary snapshot of operational metrics."""
        with self._lock:
            counters_copy = dict(self._counters)

        percentiles = {k: self.get_percentiles(k) for k in self._latencies}
        return {
            "counters": counters_copy,
            "latencies": percentiles,
        }

    def reset(self) -> None:
        """Reset all metrics (useful between test cases)."""
        with self._lock:
            for k in self._counters:
                self._counters[k] = 0
            for k in self._latencies:
                self._latencies[k].clear()


_GLOBAL_METRICS = OperationalMetrics()


def get_metrics() -> OperationalMetrics:
    """Retrieve global operational metrics instance."""
    return _GLOBAL_METRICS
