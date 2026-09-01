"""Unified Quality Gate & DevSecOps Verification Script for AegisBank AI Platform.

Executes all automated quality, security, contract, architecture integrity, and test gates in deterministic order.
Produces a machine-readable JSON report (reports/quality_gate_summary.json) and terminal summary.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[1]
if str(REPO_ROOT) not in sys.path:
    sys.path.insert(0, str(REPO_ROOT))


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


def _check_architecture_inventory(repo_root: Path) -> tuple[bool, str]:
    """Verify presence and validity of canonical components catalog and ownership map."""
    canonical_file = repo_root / "docs" / "architecture" / "CANONICAL-COMPONENTS.md"
    ownership_file = repo_root / "docs" / "engineering" / "OWNERSHIP-MAP.md"

    if not canonical_file.exists():
        return False, f"Missing {canonical_file}"
    if not ownership_file.exists():
        return False, f"Missing {ownership_file}"

    canonical_text = canonical_file.read_text(encoding="utf-8")
    required_sections = [
        "AgentOrchestrator",
        "ToolRegistry",
        "HITLApprovalManager",
        "RetryPolicy",
        "CircuitBreaker",
    ]
    missing = [s for s in required_sections if s not in canonical_text]
    if missing:
        return (
            False,
            f"CANONICAL-COMPONENTS.md missing required components: {', '.join(missing)}",
        )

    return True, "Canonical Components catalog and Ownership Map verified."


def _session_guard_result(repo_root: Path) -> GateResult:
    """Validate active writer if running under an active session."""
    from scripts.session_guard import SessionGuard

    guard = SessionGuard(repo_root)
    if not guard.lock_file.exists():
        return GateResult(
            name="Cross-Session Writer Guard",
            command="internal:session_guard.check",
            status="SKIPPED",
            duration_seconds=0.0,
            output_snippet="No active session lock; standalone quality run permitted.",
        )

    try:
        lock_data = json.loads(guard.lock_file.read_text(encoding="utf-8"))
        default_session_id = lock_data.get("session_id", "opencode-v0110")
    except (OSError, json.JSONDecodeError):
        default_session_id = "opencode-v0110"

    session_id = os.environ.get("AEGISBANK_SESSION_ID", default_session_id)
    started = time.time()
    ret = guard.check(session_id)
    dur = round(time.time() - started, 3)
    return GateResult(
        name="Cross-Session Writer Guard",
        command="internal:session_guard.check",
        status="PASS" if ret == 0 else "FAIL",
        duration_seconds=dur,
        output_snippet=(
            "Session lock verified for active session."
            if ret == 0
            else "Session guard check failed."
        ),
    )


def run_quality_gates(
    repo_root: Path,
    secrets_only: bool = False,
    containers: bool = False,
    kubernetes: bool = False,
    data: bool = False,
    cosmos: bool = False,
    redis: bool = False,
) -> tuple[int, list[GateResult]]:
    results: list[GateResult] = []
    py_exec = sys.executable

    # Session Guard verification
    session_result = _session_guard_result(repo_root)
    results.append(session_result)
    if session_result.status == "FAIL":
        return 1, results

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

    if containers:
        container_cmd = [py_exec, "scripts/container_acceptance.py"]
        print("[*] Running gate: Container Integration Acceptance...")
        started = time.time()
        ret, stdout, stderr = _run_cmd(container_cmd, repo_root)
        duration = round(time.time() - started, 3)
        output = stdout.strip() if stdout.strip() else stderr.strip()
        results.append(
            GateResult(
                name="Container Integration Acceptance",
                command=" ".join(container_cmd),
                status="PASS" if ret == 0 else "FAIL",
                duration_seconds=duration,
                output_snippet=output[-500:],
                error_message=stderr if ret else None,
            )
        )
        if ret:
            all_passed = False

    if kubernetes:
        k8s_cmd = [
            py_exec,
            "-m",
            "pytest",
            "ai/agent/tests/kubernetes/test_kubernetes_acceptance.py",
        ]
        print("[*] Running gate: Kubernetes Integration Acceptance...")
        started = time.time()
        ret, stdout, stderr = _run_cmd(k8s_cmd, repo_root)
        duration = round(time.time() - started, 3)
        output = stdout.strip() if stdout.strip() else stderr.strip()
        results.append(
            GateResult(
                name="Kubernetes Integration Acceptance",
                command=" ".join(k8s_cmd),
                status="PASS" if ret == 0 else "FAIL",
                duration_seconds=duration,
                output_snippet=output[-500:],
                error_message=stderr if ret else None,
            )
        )
        if ret:
            all_passed = False

    if data:
        data_cmd = [
            py_exec,
            "scripts/evaluate_retrievers_v012.py",
        ]
        print("[*] Running gate: PostgreSQL + pgvector Data Acceptance...")
        started = time.time()
        ret, stdout, stderr = _run_cmd(data_cmd, repo_root)
        duration = round(time.time() - started, 3)
        output = stdout.strip() if stdout.strip() else stderr.strip()
        results.append(
            GateResult(
                name="PostgreSQL + pgvector Data Acceptance",
                command=" ".join(data_cmd),
                status="PASS" if ret == 0 else "FAIL",
                duration_seconds=duration,
                output_snippet=output[-500:],
                error_message=stderr if ret else None,
            )
        )
        if ret:
            all_passed = False

    if cosmos:
        cosmos_cmd = [
            py_exec,
            "-m",
            "pytest",
            "ai/agent/tests/cosmos",
            "ai/agent/tests/contracts/test_cosmos_contracts.py",
        ]
        print("[*] Running gate: Azure Cosmos DB NoSQL Acceptance...")
        started = time.time()
        ret, stdout, stderr = _run_cmd(cosmos_cmd, repo_root)
        duration = round(time.time() - started, 3)
        output = stdout.strip() if stdout.strip() else stderr.strip()
        results.append(
            GateResult(
                name="Azure Cosmos DB NoSQL Acceptance",
                command=" ".join(cosmos_cmd),
                status="PASS" if ret == 0 else "FAIL",
                duration_seconds=duration,
                output_snippet=output[-500:],
                error_message=stderr if ret else None,
            )
        )
        if ret:
            all_passed = False

    if redis:
        redis_cmd = [
            py_exec,
            "-m",
            "pytest",
            "ai/rag/tests/test_redis_cache.py",
            "ai/rag/tests/test_redis_retriever.py",
        ]
        print("[*] Running gate: Redis Cache & Vector Search Acceptance...")
        started = time.time()
        ret, stdout, stderr = _run_cmd(redis_cmd, repo_root)
        duration = round(time.time() - started, 3)
        output = stdout.strip() if stdout.strip() else stderr.strip()
        results.append(
            GateResult(
                name="Redis Cache & Vector Search Acceptance",
                command=" ".join(redis_cmd),
                status="PASS" if ret == 0 else "FAIL",
                duration_seconds=duration,
                output_snippet=output[-500:],
                error_message=stderr if ret else None,
            )
        )
        if ret:
            all_passed = False

    # Architecture Inventory Gate
    print("[*] Running gate: Architecture Inventory & Ownership Gate...")
    start_time = time.time()
    ok, msg = _check_architecture_inventory(repo_root)
    duration = round(time.time() - start_time, 3)
    if not ok:
        all_passed = False
        print(f"    [!] FAILED ({duration}s)")
    else:
        print(f"    [+] PASSED ({duration}s)")

    results.append(
        GateResult(
            name="Architecture Inventory Gate",
            command="internal:check_architecture_inventory",
            status="PASS" if ok else "FAIL",
            duration_seconds=duration,
            output_snippet=msg,
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
    parser.add_argument(
        "--gate-containers",
        "--include-containers",
        dest="gate_containers",
        action="store_true",
        help="Run opt-in Docker Compose integration acceptance; requires Docker and MSSQL_SA_PASSWORD",
    )
    parser.add_argument(
        "--gate-kubernetes",
        "--include-kubernetes",
        dest="gate_kubernetes",
        action="store_true",
        help="Run opt-in Kubernetes integration acceptance; requires local Kubernetes cluster",
    )
    parser.add_argument(
        "--gate-data",
        "--include-data",
        dest="gate_data",
        action="store_true",
        help="Run opt-in PostgreSQL + pgvector data integration acceptance; requires local PostgreSQL",
    )
    parser.add_argument(
        "--gate-cosmos",
        "--include-cosmos",
        dest="gate_cosmos",
        action="store_true",
        help="Run opt-in Azure Cosmos DB NoSQL integration acceptance; requires local Cosmos emulator",
    )
    parser.add_argument(
        "--gate-redis",
        "--include-redis",
        dest="gate_redis",
        action="store_true",
        help="Run opt-in Redis Cache & Vector Search acceptance; requires local Redis",
    )
    args = parser.parse_args()

    repo_root = Path(__file__).resolve().parents[1]
    reports_dir = repo_root / "reports"
    reports_dir.mkdir(parents=True, exist_ok=True)

    exit_code, results = run_quality_gates(
        repo_root,
        secrets_only=args.gate_secrets_only,
        containers=args.gate_containers,
        kubernetes=args.gate_kubernetes,
        data=args.gate_data,
        cosmos=args.gate_cosmos,
        redis=args.gate_redis,
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
        badge = (
            "[PASS]"
            if r.status == "PASS"
            else ("[SKIP]" if r.status == "SKIPPED" else "[FAIL]")
        )
        print(f"  {badge:7} | {r.duration_seconds:6.2f}s | {r.name}")
    print("=" * 70)

    return exit_code


if __name__ == "__main__":
    sys.exit(main())
