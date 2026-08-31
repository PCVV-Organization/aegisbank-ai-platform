"""Unified Quality Gate & DevSecOps Verification Script for AegisBank AI Platform.

Executes all automated quality, security, contract, and test gates in deterministic order.
Produces a machine-readable JSON report (reports/quality_gate_summary.json) and terminal summary.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path


@dataclass
class GateResult:
    name: str
    command: str
    status: str  # PASS, FAIL, SKIPPED, BLOCKED
    duration_seconds: float
    output_snippet: str
    error_message: str | None = None


def _run_cmd(cmd: list[str], cwd: Path) -> tuple[int, str, str]:
    res = subprocess.run(
        cmd,
        cwd=str(cwd),
        capture_output=True,
        text=True,
        check=False,
    )
    return res.returncode, res.stdout, res.stderr


def _scan_for_secrets(repo_root: Path) -> tuple[bool, str]:
    """Scan tracked repository files for unredacted secrets and private keys."""
    secret_patterns = [
        (
            re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH )?PRIVATE KEY-----"),
            "Private Key",
        ),
        (
            re.compile(
                r"(?:api[_-]?key|secret|password)\s*=\s*['\"][A-Za-z0-9_\-]{20,}['\"]",
                re.IGNORECASE,
            ),
            "High-entropy Secret Assignment",
        ),
        (re.compile(r"sk-[A-Za-z0-9]{32,}"), "OpenAI / AI Secret Key"),
        (re.compile(r"ghp_[A-Za-z0-9]{36}"), "GitHub Personal Access Token"),
    ]

    scanned_files = 0
    findings = []

    # Check git tracked files only
    ret, stdout, _ = _run_cmd(["git", "ls-files"], repo_root)
    if ret != 0:
        return False, "Failed to list git tracked files for secret scanning."

    tracked_files = stdout.strip().splitlines()
    for rel_path in tracked_files:
        if not rel_path.strip():
            continue
        file_path = repo_root / rel_path
        # Ignore binary or large files
        if file_path.suffix in {
            ".png",
            ".jpg",
            ".jpeg",
            ".webp",
            ".ico",
            ".bin",
            ".db",
            ".sqlite",
            ".onnx",
            ".pkl",
        }:
            continue
        if not file_path.exists() or not file_path.is_file():
            continue

        try:
            content = file_path.read_text(encoding="utf-8", errors="ignore")
            scanned_files += 1
            for pattern, desc in secret_patterns:
                for line_idx, line in enumerate(content.splitlines(), start=1):
                    # Ignore placeholder lines, docs, or tests mentioning example strings
                    lower = line.lower()
                    if (
                        "example" in lower
                        or "dummy" in lower
                        or "mock" in lower
                        or "placeholder" in lower
                    ):
                        continue
                    if pattern.search(line):
                        findings.append(f"{rel_path}:{line_idx} - {desc}")
        except (OSError, UnicodeDecodeError):
            continue

    if findings:
        return (
            False,
            f"Secret scanning detected {len(findings)} potential secret(s):\n"
            + "\n".join(findings[:10]),
        )

    return True, f"Scanned {scanned_files} files. 0 unredacted secrets detected."


def run_quality_gates(
    repo_root: Path, secrets_only: bool = False
) -> tuple[int, list[GateResult]]:
    results: list[GateResult] = []
    py_exec = sys.executable

    # Define all gates
    if secrets_only:
        start = time.time()
        ok, msg = _scan_for_secrets(repo_root)
        dur = time.time() - start
        results.append(
            GateResult(
                name="Secret Scanning Gate",
                command="internal:scan_for_secrets",
                status="PASS" if ok else "FAIL",
                duration_seconds=round(dur, 3),
                output_snippet=msg,
            )
        )
        return (0 if ok else 1), results

    gates = [
        ("Static Analysis: Ruff Lint", [py_exec, "-m", "ruff", "check", "."]),
        (
            "Static Analysis: Ruff Format",
            [py_exec, "-m", "ruff", "format", "--check", "."],
        ),
        ("Python Bytecode Compilation", [py_exec, "-m", "compileall", "-q", "."]),
        (
            "Core Banking Tests & Contracts",
            [py_exec, "-m", "pytest", "services/mock-core-banking/tests"],
        ),
        (
            "ML Intent Classifier Tests",
            [py_exec, "-m", "pytest", "ml/intent-classifier/tests"],
        ),
        ("AI RAG Tests", [py_exec, "-m", "pytest", "ai/rag/tests"]),
        (
            "AI Agent Tests, Contracts & E2E",
            [py_exec, "-m", "pytest", "ai/agent/tests"],
        ),
        (
            "SAST Scan (Bandit)",
            [
                py_exec,
                "-m",
                "bandit",
                "-ll",
                "-r",
                "ai/agent/src",
                "ai/rag/src",
                "ml/intent-classifier/src",
                "services/mock-core-banking/src",
            ],
        ),
        ("SCA Audit (pip-audit)", [py_exec, "-m", "pip_audit"]),
    ]

    all_passed = True

    for name, cmd in gates:
        print(f"[*] Running gate: {name}...")
        start_time = time.time()
        ret, stdout, stderr = _run_cmd(cmd, repo_root)
        duration = round(time.time() - start_time, 3)

        output = stdout.strip() if stdout.strip() else stderr.strip()
        status = "PASS" if ret == 0 else "FAIL"

        if ret != 0:
            all_passed = False
            print(f"    [!] FAILED ({duration}s)")
        else:
            print(f"    [+] PASSED ({duration}s)")

        results.append(
            GateResult(
                name=name,
                command=" ".join(cmd),
                status=status,
                duration_seconds=duration,
                output_snippet=output[-500:] if len(output) > 500 else output,
                error_message=stderr if ret != 0 else None,
            )
        )

    # Secret scanning gate
    print("[*] Running gate: Secret Scanning Gate...")
    start_time = time.time()
    ok, msg = _scan_for_secrets(repo_root)
    duration = round(time.time() - start_time, 3)
    if not ok:
        all_passed = False
        print(f"    [!] FAILED ({duration}s)")
    else:
        print(f"    [+] PASSED ({duration}s)")

    results.append(
        GateResult(
            name="Secret Scanning Gate",
            command="internal:scan_for_secrets",
            status="PASS" if ok else "FAIL",
            duration_seconds=duration,
            output_snippet=msg,
        )
    )

    # Git Diff Check Gate
    print("[*] Running gate: Git Whitespace & Syntax Diff Check...")
    start_time = time.time()
    ret, stdout, _ = _run_cmd(["git", "diff", "--check"], repo_root)
    duration = round(time.time() - start_time, 3)
    if ret != 0:
        all_passed = False
        print(f"    [!] FAILED ({duration}s)")
    else:
        print(f"    [+] PASSED ({duration}s)")

    results.append(
        GateResult(
            name="Git Whitespace & Diff Check",
            command="git diff --check",
            status="PASS" if ret == 0 else "FAIL",
            duration_seconds=duration,
            output_snippet=stdout if stdout else "No whitespace errors detected.",
        )
    )

    return (0 if all_passed else 1), results


def main() -> int:
    parser = argparse.ArgumentParser(
        description="AegisBank Quality Gate & DevSecOps Runner"
    )
    parser.add_argument(
        "--gate-secrets-only",
        action="store_true",
        help="Run only the secret scanning gate",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    exit_code, results = run_quality_gates(
        repo_root, secrets_only=args.gate_secrets_only
    )

    report_payload = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "overall_status": "PASS" if exit_code == 0 else "FAIL",
        "total_gates": len(results),
        "passed_gates": sum(1 for r in results if r.status == "PASS"),
        "failed_gates": sum(1 for r in results if r.status == "FAIL"),
        "gates": [asdict(r) for r in results],
    }

    report_file = reports_dir / "quality_gate_summary.json"
    report_file.write_text(json.dumps(report_payload, indent=2), encoding="utf-8")

    print("\n" + "=" * 70)
    print(
        f"AEGISBANK QUALITY GATE SUMMARY: {'ALL GATES PASSED (PASS)' if exit_code == 0 else 'GATE FAILURES DETECTED (FAIL)'}"
    )
    print(f"Report written to: {report_file}")
    print("=" * 70)
    for r in results:
        badge = "[PASS]" if r.status == "PASS" else "[FAIL]"
        print(f"  {badge:7} | {r.duration_seconds:6.2f}s | {r.name}")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
