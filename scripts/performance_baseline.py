"""Reproducible, bounded local baseline for safe health and READ journeys.

This is a laboratory measurement, not a production load generator. It uses only
the synthetic in-process Core Banking API and never invokes a WRITE endpoint.
"""

from __future__ import annotations

import argparse
import json
import statistics
import sys
import time
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
for source_root in (
    REPO_ROOT / "services" / "mock-core-banking" / "src",
    REPO_ROOT / "ai" / "agent" / "src",
):
    sys.path.insert(0, str(source_root))

from mock_core_banking.config import Settings
from mock_core_banking.main import create_app
from starlette.testclient import TestClient


def _percentile(values: list[float], percentile: float) -> float:
    ordered = sorted(values)
    if len(ordered) == 1:
        return ordered[0]
    position = (len(ordered) - 1) * percentile
    lower = int(position)
    upper = min(lower + 1, len(ordered) - 1)
    fraction = position - lower
    return ordered[lower] + (ordered[upper] - ordered[lower]) * fraction


def _measure(client: TestClient, path: str, iterations: int) -> dict[str, object]:
    samples: list[float] = []
    errors = 0
    for _ in range(iterations):
        started = time.perf_counter()
        response = client.get(path, headers={"X-Correlation-ID": "perf-baseline"})
        samples.append((time.perf_counter() - started) * 1000)
        errors += response.status_code >= 400
    return {
        "iterations": iterations,
        "errors": errors,
        "error_rate": round(errors / iterations, 4),
        "latency_ms": {
            "p50": round(_percentile(samples, 0.50), 2),
            "p95": round(_percentile(samples, 0.95), 2),
            "p99": round(_percentile(samples, 0.99), 2),
            "mean": round(statistics.mean(samples), 2),
        },
    }


def run(iterations: int) -> dict[str, object]:
    if iterations < 5 or iterations > 500:
        raise ValueError("iterations must be between 5 and 500")
    app = create_app(Settings(database_url="sqlite:///:memory:"))
    with TestClient(app) as client:
        journeys = {
            "health_live": _measure(client, "/health/live", iterations),
            "safe_read_loan": _measure(client, "/api/v1/loans/LOAN-0001", iterations),
        }
    return {
        "schema": "aegisbank.performance-baseline.v1",
        "scope": "LOCAL-LAB-ONLY",
        "write_endpoints_called": False,
        "iterations": iterations,
        "journeys": journeys,
    }


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--iterations", type=int, default=25)
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    report = run(args.iterations)
    rendered = json.dumps(report, indent=2) + "\n"
    if args.output:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        args.output.write_text(rendered, encoding="utf-8")
    print(rendered, end="")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
