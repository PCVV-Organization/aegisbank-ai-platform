"""Unit tests for MLflowTracker with local reproducible SQLite store."""

from __future__ import annotations

from pathlib import Path

import pytest

from aegisbank_agent.mlops.tracker import MLflowTracker

pytestmark = pytest.mark.unit


def test_mlflow_tracker_lifecycle(tmp_path: Path) -> None:
    db_file = tmp_path / "test_mlruns.db"
    tracker = MLflowTracker(
        tracking_uri=db_file,
        experiment_name="test-experiment-local",
    )

    with tracker:
        run = tracker.start_run(run_name="candidate_v015", tags={"version": "v0.15.0"})
        assert run is not None

        tracker.log_parameters({"model": "phi-4-mini", "prompt": "agent-system-v003"})
        tracker.log_metrics({"tool_selection_accuracy": 1.0, "relevance": 0.95})

        artifact_file = tmp_path / "eval_artifact.json"
        artifact_file.write_text('{"status": "passed"}', encoding="utf-8")
        tracker.log_artifact(artifact_file, artifact_path="results")

    # Verify db file was created
    assert db_file.exists()
