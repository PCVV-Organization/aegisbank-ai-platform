"""Tests for evaluation harness and report generation."""

from __future__ import annotations

from pathlib import Path
from unittest.mock import MagicMock

import pytest

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.evaluation import (
    evaluate_agent,
    load_agent_cases,
    write_evaluation_reports,
)
from aegisbank_agent.tools.registry import ToolRegistry

pytestmark = pytest.mark.unit


class DummyChoice:
    def __init__(self, message: object):
        self.message = message


class DummyResponse:
    def __init__(self, message: object):
        self.choices = [DummyChoice(message)]


class DummyMessage:
    def __init__(self, content: str | None = None, tool_calls: list[object] | None = None):
        self.content = content
        self.tool_calls = tool_calls


def test_load_agent_cases() -> None:
    cases = load_agent_cases()
    assert len(cases) > 0
    case_ids = [c.case_id for c in cases]
    assert "v06e001" in case_ids or "ae001" in case_ids


def test_evaluate_agent_mock_run(tmp_path: Path) -> None:
    cases = load_agent_cases()[:2]
    mock_client = MagicMock()
    mock_client.chat.completions.create.return_value = DummyResponse(
        DummyMessage(content="Respuesta simulada directa.")
    )

    orchestrator = AgentOrchestrator(
        client=mock_client,
        registry=ToolRegistry([]),
    )

    eval_result = evaluate_agent(orchestrator, cases)
    assert "aggregated_metrics" in eval_result
    assert eval_result["metadata"]["total_cases"] == 2

    metrics_path = tmp_path / "test-metrics.json"
    report_path = tmp_path / "test-report.md"

    write_evaluation_reports(
        eval_result,
        metrics_path=metrics_path,
        report_path=report_path,
    )

    assert metrics_path.exists()
    assert report_path.exists()
    assert "# v0.6 Single-Agent" in report_path.read_text(encoding="utf-8")
