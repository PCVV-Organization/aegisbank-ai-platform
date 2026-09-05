"""MLflow experiment tracker for local, reproducible AI experimentation."""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any


class MLflowTracker:
    """Local-first MLflow tracking wrapper for agent evaluations and experimentation."""

    def __init__(
        self,
        tracking_uri: str | Path | None = None,
        experiment_name: str = "aegisbank-agent-evaluation",
    ) -> None:
        os.environ["MLFLOW_DISABLE_AGENT_HINT"] = "1"
        import mlflow

        self._mlflow = mlflow

        if tracking_uri is None:
            default_dir = Path("reports/mlruns")
            default_dir.mkdir(parents=True, exist_ok=True)
            db_path = (default_dir / "mlflow.db").resolve()
            self.tracking_uri = f"sqlite:///{db_path.as_posix()}"
        elif isinstance(tracking_uri, Path):
            tracking_uri.parent.mkdir(parents=True, exist_ok=True)
            self.tracking_uri = f"sqlite:///{tracking_uri.resolve().as_posix()}"
        else:
            self.tracking_uri = tracking_uri

        self._mlflow.set_tracking_uri(self.tracking_uri)
        self.experiment_name = experiment_name
        self.experiment = self._mlflow.set_experiment(experiment_name)
        self._active_run = None

    def start_run(
        self,
        run_name: str | None = None,
        tags: dict[str, str] | None = None,
    ) -> Any:
        """Start a new MLflow tracking run."""
        self._active_run = self._mlflow.start_run(run_name=run_name, tags=tags)
        return self._active_run

    def log_parameters(self, params: dict[str, Any]) -> None:
        """Log hyper-parameters and experiment configuration."""
        if params:
            str_params = {k: str(v) for k, v in params.items()}
            self._mlflow.log_params(str_params)

    def log_metrics(self, metrics: dict[str, float], step: int | None = None) -> None:
        """Log deterministic evaluation metrics."""
        if metrics:
            self._mlflow.log_metrics(metrics, step=step)

    def log_artifact(self, local_path: str | Path, artifact_path: str | None = None) -> None:
        """Register local JSON, JSONL, or Markdown artifacts."""
        path_str = str(local_path)
        self._mlflow.log_artifact(path_str, artifact_path=artifact_path)

    def end_run(self) -> None:
        """End the current MLflow run."""
        if self._active_run is not None:
            self._mlflow.end_run()
            self._active_run = None

    def __enter__(self) -> MLflowTracker:
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> None:
        self.end_run()
