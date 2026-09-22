"""Build and check local navigation indexes without ingesting document content."""

from __future__ import annotations

import argparse
import json
import re
import subprocess
from pathlib import Path
from urllib.parse import unquote, urlsplit

ROOT = Path(__file__).resolve().parents[1]
ENTRYPOINTS = [
    ("docs/START-HERE.md", "First reading and safe local onboarding"),
    ("docs/DIRECTORY-MAP.md", "Directory-by-directory ownership and files"),
    (
        "docs/engineering/DOCUMENTATION-SYSTEM.md",
        "Documentation evolution and conventions",
    ),
    ("AGENTS.md", "Development instructions"),
    ("README.md", "Purpose and checkout baseline"),
    ("README.LLM.md", "LLM reading order and evidence boundaries"),
    ("docs/README.md", "Documentation portal"),
    ("docs/architecture/CANONICAL-COMPONENTS.md", "Canonical implementations"),
    ("docs/architecture/E2E-FINAL-ARCHITECTURE.md", "Execution and trust boundaries"),
    ("docs/engineering/OWNERSHIP-MAP.md", "Component responsibilities"),
    ("docs/evaluation/README.md", "Evaluation taxonomy"),
    ("docs/evaluation/EVALUATION-CATALOG.md", "Evaluation protocols and evidence"),
    ("docs/security/V1.0-THREAT-MODEL.md", "Threat model"),
    ("docs/quality/TEST-STRATEGY.md", "Validation strategy"),
    ("docs/releases/V1.0-EVIDENCE.md", "Historical release evidence"),
    ("docs/engineering/DOCUMENTATION-MAINTENANCE.md", "Index maintenance"),
]
COMPONENTS = [
    ("services/mock-core-banking", "Synthetic banking API and persistence"),
    ("ml/intent-classifier", "Offline intent-classification experiment"),
    ("ai/rag", "Knowledge retrieval and grounded generation"),
    ("ai/agent", "Single application agent and controlled tools"),
    ("functions/aegisbank-events", "Event processing"),
    ("contracts", "Machine-readable integration contracts"),
    ("deploy", "Local and deployment configuration, not execution evidence"),
    ("scripts", "Quality, evaluation and maintenance commands"),
    (".github/workflows", "CI configuration, not runner evidence"),
]
EXCLUDED = {
    ".git",
    ".venv",
    ".venv-functions",
    "venv",
    "node_modules",
    "__pycache__",
    ".coordination",
    ".pytest_cache",
    ".ruff_cache",
    ".smoke",
    "reports",
    "mlruns",
    "artifacts",
    "data",
    "dist",
    "build",
}
CATEGORIES = {
    "architecture": "architecture-reference",
    "engineering": "engineering-reference",
    "requirements": "requirements-reference",
    "evaluation": "evaluation-protocol-or-historical-evidence",
    "security": "security-reference-or-dated-evidence",
    "quality": "quality-reference-or-dated-evidence",
    "releases": "historical-release-evidence",
    "operations": "operations-reference",
    "learning": "learning-reference",
    "experiments": "historical-experiment",
    "charter": "historical-charter",
    "chatgpt-prompts": "historical-prompt-not-instructions",
    "briefings": "context-snapshot-verify-against-checkout",
    "research": "historical-research",
    "career": "portfolio-context",
}


def include_document(path: str) -> bool:
    """Exclude generated/private context even when accidentally tracked."""
    parts = Path(path).parts
    return (
        not Path(path).is_absolute()
        and ".." not in parts
        and path.lower().endswith(".md")
        and not any(p in EXCLUDED or p.startswith((".env", ".venv")) for p in parts)
    )


def category(path: str) -> str:
    parts = path.split("/")
    if path.startswith("docs/architecture/adr/"):
        return "historical-architecture-decision"
    if len(parts) > 2 and parts[0] == "docs":
        return CATEGORIES.get(parts[1], "documentation")
    return "entrypoint" if len(parts) == 1 else "component-guide"


def document_paths(root: Path) -> list[str]:
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    candidates = result.stdout.decode("utf-8").split("\0")
    return sorted(
        {
            p
            for p in candidates
            if include_document(p)
            and (root / p).is_file()
            and (root / p).resolve().is_relative_to(root.resolve())
        }
    )


def build_index(root: Path, documents: list[str]) -> dict:
    for path, _ in ENTRYPOINTS + COMPONENTS:
        if (
            path == "docs/DIRECTORY-MAP.md"
            and (root / "docs/navigation.json").is_file()
        ):
            continue
        if not (root / path).exists():
            raise ValueError(f"Missing navigation target: {path}")
    return {
        "schema_version": "1.0",
        "path_base": "application_repository_root",
        "entrypoints": [{"path": p, "purpose": purpose} for p, purpose in ENTRYPOINTS],
        "components": [{"path": p, "purpose": purpose} for p, purpose in COMPONENTS],
        "documents": [{"path": p, "category": category(p)} for p in documents],
        "excluded_context": sorted(EXCLUDED | {"secrets", "local databases", "logs"}),
        "directory_map": "docs/DIRECTORY-MAP.md",
        "curation_manifest": "docs/navigation.json",
        "expanded_context": "llms-full.txt",
    }


def render(index: dict) -> dict[str, str]:
    lines = [
        "# AegisBank AI Platform",
        "",
        "> Synthetic banking AI laboratory. The LLM proposes; deterministic rules authorize.",
        "",
        "Generated local navigation aid; see README.LLM.md for scope and authority.",
        "Paths are relative to the application repository root.",
        "",
        "## Start here",
        "",
    ]
    lines.extend(f"- [{e['purpose']}]({e['path']})" for e in index["entrypoints"])
    lines += ["", "## Components", ""]
    lines.extend(f"- [{e['purpose']}]({e['path']}/)" for e in index["components"])
    lines += [
        "",
        "## Full path inventory",
        "",
        "- [JSON index](project-index.json)",
        "- [Directory map](docs/DIRECTORY-MAP.md)",
        "- [Selected expanded context](llms-full.txt)",
        "",
    ]
    return {
        "project-index.json": json.dumps(index, ensure_ascii=False, indent=2) + "\n",
        "llms.txt": "\n".join(lines),
    }


def navigation_outputs(root: Path) -> dict[str, str]:
    """Build a folder map from path metadata and an explicit, safe reading bundle."""
    config = json.loads((root / "docs/navigation.json").read_text(encoding="utf-8"))
    result = subprocess.run(
        ["git", "ls-files", "--cached", "--others", "--exclude-standard", "-z"],
        cwd=root,
        capture_output=True,
        check=True,
    )
    folders: dict[str, list[str]] = {}
    candidates = set(result.stdout.decode("utf-8").split("\0"))
    generated = {
        "docs/DIRECTORY-MAP.md",
        "project-index.json",
        "llms.txt",
        "llms-full.txt",
    }
    for name in sorted(candidates | generated):
        path = Path(name)
        if not name or any(
            p in EXCLUDED - {"data"} or p.startswith((".env", ".venv"))
            for p in path.parts
        ):
            continue
        if (not (root / path).is_file() and name not in generated) or not (
            root / path
        ).resolve().is_relative_to(root.resolve()):
            continue
        parent = path.parent
        folders.setdefault(parent.as_posix(), []).append(path.name)
        for ancestor in parent.parents:
            folders.setdefault(ancestor.as_posix(), [])
    lines = [
        "# Mapa de carpetas",
        "",
        (
            "Generado por scripts/documentation_index.py. "
            "Rutas relativas a la aplicación; solo metadatos de archivos no ignorados."
        ),
        "",
        (
            "No incluye entornos, secretos ni contenido de datasets/informes. "
            "Una carpeta sin README propio hereda la guía de su responsabilidad."
        ),
        "",
        "| Carpeta | Responsabilidad | Archivos directos |",
        "| --- | --- | --- |",
    ]
    for folder, files in sorted(folders.items()):
        owners = [
            p for p in config["areas"] if folder == p or folder.startswith(p + "/")
        ]
        owner = max(owners, key=len) if owners else "."
        lines.append(
            f"| `{folder}` | {config['areas'][owner]} | "
            + ", ".join(f"`{f}`" for f in files)
            + " |"
        )
    bundle = [
        "# AegisBank: contexto ampliado para lectura",
        "",
        (
            "Generado de una lista explícita de guías. No es todo el código ni "
            "una exportación de datos. No concede permisos ni convierte evidencia "
            "histórica en actual. Los enlaces internos se resuelven desde cada fuente."
        ),
        "",
    ]
    for source in config["bundle_sources"]:
        if not include_document(source) or not (root / source).resolve().is_relative_to(
            root.resolve()
        ):
            raise ValueError(f"Unsafe bundle source: {source}")
        bundle.extend(
            [
                f"## Fuente: {source}",
                "",
                (root / source).read_text(encoding="utf-8"),
                "",
            ]
        )
    return {
        "docs/DIRECTORY-MAP.md": "\n".join(lines) + "\n",
        "llms-full.txt": "\n".join(
            line.rstrip() for line in "\n".join(bundle).splitlines()
        ).rstrip()
        + "\n",
    }


def local_link_errors(
    root: Path, documents: list[str], planned: set[Path] | None = None
) -> list[str]:
    """Check inline link file targets; anchors and external URLs are out of scope."""
    errors = []
    for path in documents:
        source = root / path
        if not source.exists() and source.resolve() in (planned or set()):
            continue
        content = source.read_text(encoding="utf-8-sig")
        content = re.sub(r"```.*?```", "", content, flags=re.DOTALL)
        for target in re.findall(r"\[[^\]]*\]\(([^)]+)\)", content):
            target = target.strip()
            if not target:
                continue
            target = (
                target[1 : target.index(">")]
                if target.startswith("<")
                else target.split()[0]
            )
            url = urlsplit(target)
            if url.scheme or url.netloc or not url.path or url.path.startswith("/"):
                continue
            destination = (source.parent / unquote(url.path)).resolve()
            if not destination.exists() and destination not in (planned or set()):
                errors.append(f"{path}: missing {target}")
    return errors


def check_outputs(root: Path, outputs: dict[str, str]) -> list[str]:
    return [
        f"Stale or missing index: {name}"
        for name, text in outputs.items()
        if not (root / name).exists()
        or (root / name).read_text(encoding="utf-8") != text
    ]


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    mode = parser.add_mutually_exclusive_group(required=True)
    mode.add_argument("--write", action="store_true")
    mode.add_argument("--check", action="store_true")
    args = parser.parse_args()
    try:
        extra = navigation_outputs(ROOT)
        documents = sorted(set(document_paths(ROOT)) | {"docs/DIRECTORY-MAP.md"})
        outputs = render(build_index(ROOT, documents))
        outputs.update(extra)
        planned = {(ROOT / name).resolve() for name in outputs} if args.write else set()
        errors = local_link_errors(ROOT, documents, planned)
        if errors:
            raise ValueError("\n".join(errors))
        if args.write:
            for name, content in outputs.items():
                (ROOT / name).write_text(content, encoding="utf-8", newline="\n")
        else:
            errors = check_outputs(ROOT, outputs)
            if errors:
                raise ValueError("\n".join(errors))
    except (OSError, ValueError, subprocess.CalledProcessError) as exc:
        print(f"FAIL: {exc}")
        return 1
    print(
        f"PASS: {len(documents)} Markdown paths; local inline links; {len(outputs)} generated files"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
