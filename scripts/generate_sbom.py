"""Generate CycloneDX SBOM in JSON format using pip-audit."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    repo_root = Path(__file__).resolve().parents[1]
    output_path = repo_root / "docs" / "security" / "sbom.json"
    output_path.parent.mkdir(parents=True, exist_ok=True)

    cmd = [
        sys.executable,
        "-m",
        "pip_audit",
        "-f",
        "cyclonedx-json",
        "-o",
        str(output_path),
    ]

    print(f"Generating SBOM at: {output_path}")
    res = subprocess.run(
        cmd, cwd=str(repo_root), capture_output=True, text=True, check=False
    )
    if res.returncode != 0:
        print(f"SBOM generation failed: {res.stderr}")
        return res.returncode

    print("SBOM successfully generated.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
