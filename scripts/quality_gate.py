"""Run AegisBank's deterministic local quality gates in order."""

from __future__ import annotations

import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
ARTIFACTS = ROOT / "artifacts" / "quality"
PYTHON = sys.executable
PYTHONPATH = os.pathsep.join(
    [
        str(ROOT / "ai" / "agent" / "src"),
        str(ROOT / "ai" / "rag" / "src"),
        str(ROOT / "services" / "mock-core-banking" / "src"),
    ]
)
SOURCE_DIRS = [
    ROOT / "ai" / "agent" / "src",
    ROOT / "ai" / "rag" / "src",
    ROOT / "services" / "mock-core-banking" / "src",
    ROOT / "ml" / "intent-classifier" / "src",
]
SECRET_PATTERN = re.compile(
    r"(?i)(api[_-]?key\s*[:=]\s*['\"][^'\"]{8,}|password\s*[:=]\s*['\"][^'\"]{8,}|"
    r"-----BEGIN (RSA |EC |OPENSSH )?PRIVATE KEY-----)"
)


def run_gate(
    name: str, command: list[str], *, env: dict[str, str] | None = None
) -> bool:
    print(f"[GATE] {name}: {' '.join(command)}")
    result = subprocess.run(command, cwd=ROOT, env=env, text=True, check=False)
    passed = result.returncode == 0
    print(f"[{'PASS' if passed else 'FAIL'}] {name}")
    return passed


def secret_gate() -> bool:
    tracked = (
        subprocess.run(
            ["git", "ls-files", "-z"], cwd=ROOT, capture_output=True, check=True
        )
        .stdout.decode()
        .split("\0")
    )
    findings: list[str] = []
    for name in tracked:
        if not name:
            continue
        if name.endswith((".pem", ".key", ".p12", ".pfx")) or Path(name).name == ".env":
            findings.append(name)
            continue
        path = ROOT / name
        if path.is_file() and SECRET_PATTERN.search(
            path.read_text(encoding="utf-8", errors="ignore")
        ):
            findings.append(name)
    payload = {
        "gate": "secret_scan",
        "status": "PASS" if not findings else "FAIL",
        "findings": findings,
    }
    (ARTIFACTS / "secret-scan.json").write_text(
        json.dumps(payload, indent=2), encoding="utf-8"
    )
    return not findings


def test_gate(env: dict[str, str]) -> bool:
    """Run each package separately because each package owns a conftest.py."""
    erase = subprocess.run(
        [PYTHON, "-m", "coverage", "erase"], cwd=ROOT, env=env, check=False
    )
    if erase.returncode != 0:
        return False
    packages = [
        ("ai/agent/tests", "ai/agent/src/aegisbank_agent"),
        ("ai/rag/tests", "ai/rag/src/aegisbank_rag"),
        (
            "services/mock-core-banking/tests",
            "services/mock-core-banking/src/mock_core_banking",
        ),
        (
            "ml/intent-classifier/tests",
            "ml/intent-classifier/src/aegisbank_intent_classifier",
        ),
    ]
    for test_path, source_path in packages:
        result = subprocess.run(
            [
                PYTHON,
                "-m",
                "pytest",
                "--import-mode=importlib",
                test_path,
                f"--cov={source_path}",
                "--cov-append",
                "--cov-report=",
            ],
            cwd=ROOT,
            env=env,
            check=False,
        )
        if result.returncode != 0:
            return False
    report = subprocess.run(
        [PYTHON, "-m", "coverage", "json", "-o", "artifacts/quality/coverage.json"],
        cwd=ROOT,
        env=env,
        check=False,
    )
    return report.returncode == 0


def main() -> int:
    ARTIFACTS.mkdir(parents=True, exist_ok=True)
    env = os.environ.copy()
    env["PYTHONPATH"] = PYTHONPATH + os.pathsep + env.get("PYTHONPATH", "")
    gates: list[tuple[str, list[str]]] = [
        ("lint", [PYTHON, "-m", "ruff", "check", "."]),
        (
            "format",
            [
                PYTHON,
                "-m",
                "ruff",
                "format",
                "--check",
                "ai/rag",
                "ai/agent",
                "services/mock-core-banking",
                "ml/intent-classifier",
            ],
        ),
        (
            "compileall",
            [
                PYTHON,
                "-m",
                "compileall",
                "-q",
                *(str(path.relative_to(ROOT)) for path in SOURCE_DIRS),
            ],
        ),
        (
            "sast-bandit",
            [
                PYTHON,
                "-m",
                "bandit",
                "-r",
                *(str(path.relative_to(ROOT)) for path in SOURCE_DIRS),
                "--severity-level",
                "medium",
                "-f",
                "json",
                "-o",
                "artifacts/quality/bandit.json",
            ],
        ),
    ]
    results: dict[str, str] = {}
    for name, command in gates:
        results[name] = "PASS" if run_gate(name, command, env=env) else "FAIL"
    results["tests-and-coverage"] = "PASS" if test_gate(env) else "FAIL"

    audit = subprocess.run(
        [
            PYTHON,
            "-m",
            "pip_audit",
            "--format",
            "json",
            "--output",
            "artifacts/quality/pip-audit.json",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        check=False,
    )
    results["sca-pip-audit"] = (
        "PASS" if audit.returncode == 0 else "DEPENDENCY_AUDIT_BLOCKED_OR_FINDINGS"
    )
    sbom = subprocess.run(
        [
            PYTHON,
            "-m",
            "pip_audit",
            "--format",
            "cyclonedx-json",
            "--output",
            "artifacts/quality/sbom.cdx.json",
        ],
        cwd=ROOT,
        env=env,
        text=True,
        check=False,
    )
    results["sbom"] = "PASS" if sbom.returncode == 0 else "FAIL"
    results["secret-scan"] = "PASS" if secret_gate() else "FAIL"
    summary = {
        "quality_gate": "PASS"
        if all(value == "PASS" for value in results.values())
        else "FAIL",
        "gates": results,
    }
    (ARTIFACTS / "summary.json").write_text(
        json.dumps(summary, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, indent=2))
    return 0 if summary["quality_gate"] == "PASS" else 1


if __name__ == "__main__":
    raise SystemExit(main())
