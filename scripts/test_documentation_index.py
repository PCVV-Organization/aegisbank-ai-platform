"""Regression tests for navigation drift, local links and context exclusions."""

import json
import subprocess
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

import documentation_index as index


class DocumentationIndexTests(unittest.TestCase):
    def test_github_readme_shadow_is_rejected_case_insensitively(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / ".github").mkdir()
            (root / "README.md").write_text("# Public introduction\n", encoding="utf-8")
            automation = root / ".github/CI-GUIDE.md"
            automation.write_text("# Automation\n", encoding="utf-8")
            index.validate_reading_contract(root)
            for name in ["README.md", "Readme.MD", "README.rst", "README"]:
                with self.subTest(name=name):
                    shadow = root / ".github" / name
                    shadow.write_text("# Shadow\n", encoding="utf-8")
                    with self.assertRaisesRegex(ValueError, "shadows the root"):
                        index.validate_reading_contract(root)
                    shadow.unlink()

    def test_project_brief_budget_accepts_limit_and_rejects_overflow(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "docs").mkdir()
            brief = root / "docs/PROJECT-BRIEF.md"
            brief.write_text("word " * 600, encoding="utf-8")
            index.validate_reading_contract(root)
            brief.write_text("word " * 601, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "600-word context budget"):
                index.validate_reading_contract(root)

    def test_bundle_contains_only_curated_sources_and_stays_deterministic(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "docs").mkdir()
            (root / "README.md").write_text("# Selected\n", encoding="utf-8")
            (root / "private.md").write_text("DO NOT INCLUDE", encoding="utf-8")
            (root / "docs/navigation.json").write_text(
                json.dumps({"areas": {".": "test"}, "bundle_sources": ["README.md"]}),
                encoding="utf-8",
            )
            first = index.navigation_outputs(root)
            self.assertIn("# Selected", first["llms-full.txt"])
            self.assertIn("## Source: README.md", first["llms-full.txt"])
            self.assertIn("# Directory Map", first["docs/DIRECTORY-MAP.md"])
            self.assertNotIn("DO NOT INCLUDE", first["llms-full.txt"])
            for path, content in first.items():
                (root / path).write_text(content, encoding="utf-8")
            self.assertEqual(first, index.navigation_outputs(root))

    def test_bundle_rejects_parent_escape_and_private_sources(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / "docs").mkdir()
            for source in [
                "../outside.md",
                ".env.md",
                "data/private.md",
                "reports/output.md",
            ]:
                (root / "docs/navigation.json").write_text(
                    json.dumps({"areas": {".": "test"}, "bundle_sources": [source]}),
                    encoding="utf-8",
                )
                with (
                    self.subTest(source=source),
                    self.assertRaisesRegex(ValueError, "Unsafe"),
                ):
                    index.navigation_outputs(root)

    def test_private_and_generated_context_is_excluded(self):
        for path in [
            ".env.md",
            "reports/result.md",
            "ai/rag/data/corpus/private.md",
            ".venv/site-packages/README.md",
            "mlruns/run/readme.md",
            "../outside.md",
            "data/local/readme.md",
            ".coordination/session.md",
        ]:
            with self.subTest(path=path):
                self.assertFalse(index.include_document(path))
        self.assertTrue(index.include_document("docs/evaluation/README.md"))

    def test_git_inventory_respects_ignore_and_includes_new_docs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            subprocess.run(["git", "init", "-q", str(root)], check=True)
            (root / ".gitignore").write_text("private/\n", encoding="utf-8")
            (root / "README.md").write_text("# Readme\n", encoding="utf-8")
            (root / "private").mkdir()
            (root / "private/secret.md").write_text("private", encoding="utf-8")
            self.assertEqual(index.document_paths(root), ["README.md"])

    def test_historical_archive_is_not_classified_as_active_documentation(self):
        self.assertEqual(
            index.category("history/chatgpt-prompts/001_PROMPT.md"),
            "historical-archive",
        )

    def test_missing_component_fails_instead_of_publishing_broken_index(self):
        with (
            tempfile.TemporaryDirectory() as directory,
            patch.object(index, "ENTRYPOINTS", []),
            patch.object(index, "COMPONENTS", [("missing", "component")]),
            self.assertRaisesRegex(ValueError, "Missing navigation target"),
        ):
            index.build_index(Path(directory), [])

    def test_initial_generation_allows_only_planned_output_links(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "README.md").write_text("[index](llms.txt)\n", encoding="utf-8")
            self.assertEqual(len(index.local_link_errors(root, ["README.md"])), 1)
            self.assertEqual(
                index.local_link_errors(
                    root, ["README.md"], {(root / "llms.txt").resolve()}
                ),
                [],
            )

    def test_check_detects_missing_and_modified_outputs(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            outputs = {"index.json": '{"schema_version":"1.0"}\n'}
            self.assertEqual(len(index.check_outputs(root, outputs)), 1)
            (root / "index.json").write_text(outputs["index.json"], encoding="utf-8")
            self.assertEqual(index.check_outputs(root, outputs), [])
            (root / "index.json").write_text("{}", encoding="utf-8")
            self.assertEqual(len(index.check_outputs(root, outputs)), 1)

    def test_links_detect_missing_files_and_accept_encoded_paths(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            (root / "existing file.md").write_text("# Existing", encoding="utf-8")
            (root / "README.md").write_text(
                "[valid](existing%20file.md#section)\n"
                "[external](https://example.invalid/no-network)\n"
                "[missing](absent.md)\n```text\n[example](not-a-real-link)\n```\n",
                encoding="utf-8",
            )
            self.assertEqual(
                index.local_link_errors(root, ["README.md"]),
                ["README.md: missing absent.md"],
            )


if __name__ == "__main__":
    unittest.main()
