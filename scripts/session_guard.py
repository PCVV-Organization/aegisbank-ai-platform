"""Cooperative single-writer guard for shared AegisBank working trees.

Enforces 'Single Writer, Many Readers' on the local repository working tree without worktrees.
Uses atomic filesystem advisory locking in `.coordination/active-writer.json`.
"""

from __future__ import annotations

import argparse
import fnmatch
import json
import os
import subprocess
import uuid
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
LOCK_DIR = ROOT / ".coordination"
LOCK_PATH = LOCK_DIR / "active-writer.json"


def _git(*args: str, cwd: Path | None = None) -> str:
    result = subprocess.run(
        ["git", *args],
        cwd=str(cwd or ROOT),
        capture_output=True,
        text=True,
        check=False,
    )
    return result.stdout


def _get_git_head(repo_root: Path | None = None) -> str:
    return _git("rev-parse", "HEAD", cwd=repo_root).strip()


def _get_git_status_files(repo_root: Path | None = None) -> list[str]:
    stdout = _git("status", "--porcelain=v2", "--untracked-files=all", cwd=repo_root)
    paths: list[str] = []
    for line in stdout.splitlines():
        if not line or line.startswith("#"):
            continue
        fields = line.split(" ", 8)
        if line.startswith(("1 ", "u ")) and len(fields) >= 9:
            paths.append(fields[8])
        elif line.startswith("2 ") and len(fields) >= 10:
            paths.append(fields[9].split("\t", 1)[-1])
        elif line.startswith("? "):
            paths.append(line[2:])
    return paths


def _get_staged_paths(repo_root: Path | None = None) -> list[str]:
    stdout = _git("diff", "--name-only", "--cached", cwd=repo_root)
    return [p for p in stdout.splitlines() if p.strip()]


def _matches_allowed(path: str, patterns: list[str]) -> bool:
    normalized = path.replace("\\", "/")
    for pattern in patterns:
        norm_pat = pattern.replace("\\", "/")
        if fnmatch.fnmatch(normalized, norm_pat):
            return True
        if norm_pat.endswith("/**"):
            prefix = norm_pat[:-3]
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
        elif norm_pat.endswith("/*"):
            prefix = norm_pat[:-2]
            if normalized == prefix or normalized.startswith(prefix + "/"):
                return True
    return False


def _resolve_session_id(value: str | None) -> str:
    return (
        value or os.environ.get("AEGISBANK_SESSION_ID") or f"session-{uuid.uuid4().hex}"
    )


class SessionGuard:
    """Manages atomic advisory writer locking and boundary verification."""

    def __init__(self, repo_root: Path | None = None) -> None:
        self.repo_root = repo_root or ROOT
        self.coord_dir = self.repo_root / ".coordination"
        self.lock_file = self.coord_dir / "active-writer.json"

    def acquire(
        self,
        session_id: str | None,
        milestone: str,
        allowed_paths: list[str],
        baseline_head: str | None = None,
    ) -> int:
        session = _resolve_session_id(session_id)
        current_head = baseline_head or _get_git_head(self.repo_root)
        baseline_paths = sorted(_get_git_status_files(self.repo_root))

        payload = {
            "session_id": session,
            "pid": os.getpid(),
            "ppid": os.getppid() if hasattr(os, "getppid") else None,
            "started_at_utc": datetime.now(timezone.utc).isoformat(),
            "baseline_head": current_head,
            "milestone": milestone,
            "allowed_paths": allowed_paths,
            "baseline_paths": baseline_paths,
        }

        self.coord_dir.mkdir(parents=True, exist_ok=True)
        try:
            descriptor = os.open(
                str(self.lock_file), os.O_WRONLY | os.O_CREAT | os.O_EXCL
            )
        except FileExistsError:
            print("AEGISBANK_CROSS_SESSION_WRITER_ACTIVE")
            return 2

        with os.fdopen(descriptor, "w", encoding="utf-8") as stream:
            json.dump(payload, stream, indent=2)
            stream.write("\n")

        print(json.dumps(payload, indent=2))
        return 0

    def check(self, session_id: str | None) -> int:
        if not self.lock_file.exists():
            print("AEGISBANK_CROSS_SESSION_WRITER_NOT_ACTIVE")
            return 2

        try:
            payload = json.loads(self.lock_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"AEGISBANK_CROSS_SESSION_LOCK_CORRUPTED: {exc}")
            return 2

        session = _resolve_session_id(session_id)
        if payload.get("session_id") != session:
            print("AEGISBANK_CROSS_SESSION_WRITER_NOT_OWNER")
            return 2

        current_head = _get_git_head(self.repo_root)
        if current_head != payload.get("baseline_head"):
            print("AEGISBANK_CROSS_SESSION_HEAD_MOVED")
            return 3

        patterns = payload.get("allowed_paths", [])
        baseline_paths = set(payload.get("baseline_paths", []))
        current_changed = _get_git_status_files(self.repo_root)

        collisions = {
            path
            for path in current_changed
            if path not in baseline_paths
            and path != ".coordination/active-writer.json"
            and not _matches_allowed(path, patterns)
        }
        if collisions:
            print("AEGISBANK_CROSS_SESSION_PATH_COLLISION")
            print(json.dumps(sorted(collisions)))
            return 4

        staged_paths = _get_staged_paths(self.repo_root)
        staged_out_of_band = {
            path for path in staged_paths if not _matches_allowed(path, patterns)
        }
        if staged_out_of_band:
            print("AEGISBANK_CROSS_SESSION_STAGED_OUT_OF_BAND")
            print(json.dumps(sorted(staged_out_of_band)))
            return 5

        print("AEGISBANK_CROSS_SESSION_CHECK_PASS")
        return 0

    def release(self, session_id: str | None) -> int:
        if not self.lock_file.exists():
            print("AEGISBANK_CROSS_SESSION_WRITER_NOT_ACTIVE")
            return 2

        try:
            payload = json.loads(self.lock_file.read_text(encoding="utf-8"))
        except (OSError, json.JSONDecodeError) as exc:
            print(f"AEGISBANK_CROSS_SESSION_LOCK_CORRUPTED: {exc}")
            return 2

        session = _resolve_session_id(session_id)
        if payload.get("session_id") != session:
            print("AEGISBANK_CROSS_SESSION_WRITER_NOT_OWNER")
            return 2

        self.lock_file.unlink()
        print("AEGISBANK_CROSS_SESSION_RELEASED")
        return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("command", choices=("acquire", "check", "release"))
    parser.add_argument("--session-id")
    parser.add_argument("--baseline-head")
    parser.add_argument("--milestone", default="unspecified")
    parser.add_argument("--allowed-path", action="append", default=[])
    parser.add_argument(
        "--allowed-paths",
        default=None,
        help="Comma-separated list of allowed path patterns",
    )
    args = parser.parse_args(argv)

    guard = SessionGuard()
    if args.command == "acquire":
        patterns = list(args.allowed_path)
        if args.allowed_paths:
            patterns.extend(
                p.strip() for p in args.allowed_paths.split(",") if p.strip()
            )
        return guard.acquire(
            session_id=args.session_id,
            milestone=args.milestone,
            allowed_paths=patterns,
            baseline_head=args.baseline_head,
        )
    elif args.command == "check":
        return guard.check(session_id=args.session_id)
    elif args.command == "release":
        return guard.release(session_id=args.session_id)
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
