"""Constants and path definitions for the AegisBank Agent component."""

from __future__ import annotations

from pathlib import Path

DEFAULT_MODEL_ALIAS: str = "phi-4-mini"
DEFAULT_SYSTEM_PROMPT_VERSION: str = "agent-system-v001"
DEFAULT_MAX_TOOL_ROUNDS: int = 3

PACKAGE_DIR: Path = Path(__file__).resolve().parent
AGENT_ROOT_DIR: Path = PACKAGE_DIR.parent.parent
PROMPTS_DIR: Path = PACKAGE_DIR / "prompts"
SYSTEM_PROMPT_PATH: Path = PROMPTS_DIR / f"{DEFAULT_SYSTEM_PROMPT_VERSION}.json"

DATA_DIR: Path = AGENT_ROOT_DIR / "data"
AGENT_EVAL_PATH: Path = DATA_DIR / "agent-eval.jsonl"
EVAL_CASES_PATH: Path = DATA_DIR / "eval-cases.jsonl"

REPORTS_DIR: Path = AGENT_ROOT_DIR / "reports"
AGENT_METRICS_PATH: Path = REPORTS_DIR / "agent-metrics.json"
AGENT_REPORT_PATH: Path = REPORTS_DIR / "agent-report.md"
LIVE_AGENT_METRICS_PATH: Path = REPORTS_DIR / "agent-live-metrics.json"
LIVE_AGENT_REPORT_PATH: Path = REPORTS_DIR / "agent-live-report.md"
