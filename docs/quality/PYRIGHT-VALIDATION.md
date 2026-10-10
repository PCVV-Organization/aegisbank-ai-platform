# Pyright Type Validation

## Purpose

`pyrightconfig.json` defines the canonical scope of application static analysis. It includes the four roots that make up the modular monolith: agent orchestration, RAG, intent classifier, and Core Banking. It excludes artifacts, virtual environments, caches, tests, and Functions, which have separate execution lifecycles and dependencies.

The configuration uses the local `.venv/Scripts/python.exe` interpreter through `venvPath` and `venv`. It does not lower diagnostic severity or use suppressions. Each component's annotations and adapters remain the source of truth for its type contract.

## Run

Run from the application Git root:

```powershell
node ..\tools\node\node_modules\pyright\index.js `
  --pythonpath .venv\Scripts\python.exe --outputjson
```

The command takes no positional paths; `pyrightconfig.json` alone defines the analyzed sources. This keeps local and future automated runs aligned. Inspect `errorCount`, `warningCount`, and `filesAnalyzed` in the JSON before claiming a clean baseline.

## Limits

Pyright checks static contracts; it does not replace unit, integration, contract, end-to-end, or FAST-gate suites. Validate Functions paths in their own environment when that scope is authorized.
