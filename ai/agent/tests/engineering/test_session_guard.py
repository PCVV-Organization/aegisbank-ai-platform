"""Engineering and cross-session coordination tests for session_guard."""

from __future__ import annotations

import json
from pathlib import Path
from unittest.mock import patch

import pytest
from scripts.session_guard import SessionGuard


@pytest.fixture
def temp_repo(tmp_path: Path) -> Path:
    coord = tmp_path / ".coordination"
    coord.mkdir(parents=True, exist_ok=True)
    return tmp_path


def test_first_writer_acquires_lock_successfully(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        ret = guard.acquire("session-alpha", "v0.10.1", ["docs/**", "scripts/**"])
        assert ret == 0
        assert guard.lock_file.exists()

        data = json.loads(guard.lock_file.read_text(encoding="utf-8"))
        assert data["session_id"] == "session-alpha"
        assert data["milestone"] == "v0.10.1"
        assert data["baseline_head"] == "f97253e"


def test_second_writer_blocked_when_lock_held(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        assert guard.acquire("session-alpha", "v0.10.1", ["docs/**"]) == 0
        # Second writer attempts to acquire
        ret = guard.acquire("session-beta", "v0.10.1", ["ai/agent/**"])
        assert ret != 0  # Blocked


def test_check_passes_when_conditions_met(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=["docs/readme.md"]),
    ):
        guard.acquire("session-alpha", "v0.10.1", ["docs/**"])
        ret = guard.check("session-alpha")
        assert ret == 0


def test_path_outside_allowlist_blocked_on_check(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        guard.acquire("session-alpha", "v0.10.1", ["docs/**"])

    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch(
            "scripts.session_guard._get_git_status_files",
            return_value=["ai/agent/src/agent.py"],
        ),
    ):
        ret = guard.check("session-alpha")
        assert ret != 0  # Path collision


def test_moved_head_blocked_on_check(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        guard.acquire("session-alpha", "v0.10.1", ["docs/**"])

    with (
        patch("scripts.session_guard._get_git_head", return_value="a1b2c3d"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        ret = guard.check("session-alpha")
        assert ret != 0  # Head moved


def test_same_session_releases_lock(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        guard.acquire("session-alpha", "v0.10.1", ["docs/**"])
        assert guard.lock_file.exists()

        ret = guard.release("session-alpha")
        assert ret == 0
        assert not guard.lock_file.exists()


def test_different_session_cannot_release_lock(temp_repo: Path) -> None:
    guard = SessionGuard(temp_repo)
    with (
        patch("scripts.session_guard._get_git_head", return_value="f97253e"),
        patch("scripts.session_guard._get_git_status_files", return_value=[]),
    ):
        guard.acquire("session-alpha", "v0.10.1", ["docs/**"])

        ret = guard.release("session-intruder")
        assert ret != 0
        assert guard.lock_file.exists()  # Lock retained
