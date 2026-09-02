"""Static acceptance for the reproducible Redis Open Source runtime pin."""

import runpy
from collections.abc import Callable
from pathlib import Path
from typing import cast

import pytest

REPO_ROOT = Path(__file__).resolve().parents[3]
FAKE_DIGEST = "a" * 64
_QUALITY_GATE = runpy.run_path(str(REPO_ROOT / "scripts" / "quality_gate.py"))
_check_redis_image_reproducibility = cast(
    Callable[[Path], tuple[bool, str]],
    _QUALITY_GATE["_check_redis_image_reproducibility"],
)


def _write_compose(tmp_path: Path, image: str) -> Path:
    compose = tmp_path / "deploy" / "local" / "docker-compose.yml"
    compose.parent.mkdir(parents=True)
    compose.write_text(
        f"services:\n  redis:\n    image: {image}\n    ports:\n      - '6379:6379'\n",
        encoding="utf-8",
    )
    return tmp_path


def test_repository_redis_image_is_exact_and_digest_pinned() -> None:
    ok, message = _check_redis_image_reproducibility(REPO_ROOT)
    assert ok, message
    assert "redis:8.10.1-trixie@sha256:" in message


@pytest.mark.parametrize(
    "image",
    [
        "redis:latest",
        "redis:8",
        "redis:8.10",
        f"redis:8.10.1-rc1@sha256:{FAKE_DIGEST}",
        f"redis:8.0.0-M03-alpine@sha256:{FAKE_DIGEST}",
        f"redis/redis-stack-server:8.10.1@sha256:{FAKE_DIGEST}",
    ],
)
def test_reproducibility_gate_rejects_floating_or_non_ga_images(tmp_path: Path, image: str) -> None:
    repo_root = _write_compose(tmp_path, image)
    ok, _ = _check_redis_image_reproducibility(repo_root)
    assert not ok


def test_reproducibility_gate_accepts_exact_ga_patch_and_digest(
    tmp_path: Path,
) -> None:
    image = f"redis:8.10.1-trixie@sha256:{FAKE_DIGEST}"
    repo_root = _write_compose(tmp_path, image)
    ok, message = _check_redis_image_reproducibility(repo_root)
    assert ok, message
