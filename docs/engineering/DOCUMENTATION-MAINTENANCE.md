# Documentation and LLM Context Maintenance

## Artifact roles

- `README.md`: product purpose, documented status, and entry points for people.
- `README.LLM.md`: repository roots, authority, task-based retrieval, and limits.
- `AGENTS.md`: development instructions; do not duplicate the technical catalog.
- `llms.txt`: generated concise map of entry points.
- `project-index.json`: generated path inventory for tools.
- `llms-full.txt`: generated, explicitly selected guides with source labels.
- `docs/DIRECTORY-MAP.md`: generated directory and file responsibilities.
- `docs/navigation.json`: curated bundle sources and directory descriptions.
- `docs/README.md`: thematic documentation portal.
- Component README: local use and scope of that component; label old baselines
  with their evidence dates.
- Evidence belongs in quality or release documentation; new runtime output goes
  in `reports/` according to the owning script.
- ADRs and experiments preserve historical records; do not move them merely to
  make the tree look tidy.

## Regenerate and validate

From the application Git root, after acquiring the writer lock:

```powershell
python -B scripts/documentation_index.py --write
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
git diff --check
git status --short
```

The generator uses only the Python standard library and Git. It obtains tracked
and non-ignored Markdown paths, excludes local and private generated context,
sorts the inventory, and validates entry points and components. The indexes
store paths. `llms-full.txt` includes only the guides listed in
`docs/navigation.json`; the generator does not read secrets, datasets, or
reports.

Entry points and categories are defined in
[`scripts/documentation_index.py`](../../scripts/documentation_index.py). If a
path or guide changes, regenerate all four derived files. `--check` is
read-only and fails on stale indexes, missing paths, or broken local inline
file links.

The link checker covers local inline Markdown file targets, including
directories. It does not validate anchors, remote URLs, HTML links, or
reference-style links. A documentation PASS does not prove application
behavior.

## Evidence freshness

The generator also enforces the root GitHub README convention and the project
brief's 600-word budget. Naming and content conventions are defined in
[the documentation standard](DOCUMENTATION-STANDARD.md). Check both when adding
a new guide. `.github/CI-GUIDE.md` owns automation documentation.

Use Git and dated evidence to establish technical status. Do not duplicate
version tables across the outer workspace and application. Keep dates on
historical results and distinguish uncommitted changes from releases. A
documentation-only cleanup does not justify changing package versions or
publishing tags.

## Separate workspace levels

The outer workspace has its own README and links to this application. Its
instructions belong in its own `AGENTS.md` and orchestration contract. Do not
copy ai-env tooling into the application. The application index uses relative
paths and works in a standalone clone.

Ai-env has an independent generator: run
`python -B .ai-env/build_docs.py --write`, then `--check` from the outer
workspace root. The [documentation system](DOCUMENTATION-SYSTEM.md) defines
what to update for each change type.
