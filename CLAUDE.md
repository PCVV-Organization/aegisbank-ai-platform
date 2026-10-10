# AegisBank Application — Claude Code Instructions

This is the independent Git repository for the AegisBank educational banking
application, a Python modular monolith. The outer `ai-env` checkout is separate.

## Shared contract and required reading

1. [AGENTS.md](AGENTS.md) is the authoritative application contract: synthetic
   data, mandatory human approval, modular monolith, and commit policy.
2. [README.LLM.md](README.LLM.md) defines context, path resolution, and source
   selection.
3. [Canonical components](docs/architecture/CANONICAL-COMPONENTS.md) identifies
   existing implementations before new components are created.
4. [End-to-end architecture](docs/architecture/E2E-FINAL-ARCHITECTURE.md)
   describes read and write flows.

## Editing and writer lock

Acquire the session lock before editing:

```powershell
python -B scripts/session_guard.py acquire --session-id <ID> --milestone <M> --allowed-paths "<P>"
```

Check it before editing, staging, or committing:

```powershell
python -B scripts/session_guard.py check --session-id <ID>
```

Release this session's lock when finished:

```powershell
python -B scripts/session_guard.py release --session-id <ID>
```

This is a cooperative working-tree lock, not an operating-system security
boundary.

## Validation commands

- Application virtual environment: `.venv\Scripts\python.exe`
- Documentation and application checks:

```powershell
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
.\.venv\Scripts\python.exe -m pytest
git diff --check
```

## Permanent rules

- Use synthetic data only. Never add real personal, banking, or confidential data.
- Require explicit human confirmation for every banking write or service request.
- Keep shared instructions in `AGENTS.md`; do not duplicate or contradict them
  in assistant-specific files.
- Do not edit generated `project-index.json`, `llms.txt`, `llms-full.txt`, or
  `docs/DIRECTORY-MAP.md` by hand. Regenerate them with
  `python -B scripts/documentation_index.py --write`.
- Accepted ADRs are append-only. Supersede them with a new ADR instead of
  editing or deleting the accepted record.
