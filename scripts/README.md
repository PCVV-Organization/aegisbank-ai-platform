# Maintenance and Evaluation Commands

Run commands from the application Git root. Use the application's `.venv` for
tests and runtime commands; the global Python interpreter may not have the
required packages installed.

| Command | What it checks or does | Effects and requirements |
|---|---|---|
| `python -B scripts/documentation_index.py --check` | Checks navigation, paths, and generated files | Read-only; standard Python and Git |
| `python -B scripts/documentation_index.py --write` | Regenerates indexes and LLM context | Writes four declared files; acquire SessionGuard first |
| `python -B -m unittest discover -s scripts -p test_documentation_index.py` | Tests the documentation generator | Uses isolated temporary directories |
| `python -B scripts/session_guard.py --help` | Shows the coordination command contract | `acquire`/`release` change lock state; `check` inspects it |
| `.venv/Scripts/python.exe scripts/quality_gate.py --fast` | Runs Ruff, compilation, suites, evaluation, inventory, and secret checks | Requires SessionGuard and `AEGISBANK_SESSION_ID`; writes reports and artifacts |
| `.venv/Scripts/python.exe scripts/evaluation_gate.py` | Compares simulated traces and applies promotion policy | Writes reports/MLflow data; not a live-model evaluation |
| `run_local_red_team.py`, `run_phase22_live.py` | Opt-in evaluations with a local model | Preserve existing reports first; Foundry required, and Phase 2.2 also requires pgvector |
| `container_acceptance.py`, `functions_runtime_acceptance.py`, `appconfig_emulator_acceptance.py` | Accepts local infrastructure integrations | Requires local services; inspect configuration and effects first |
| `evaluate_retrievers_v012.py`, `capture_pgvector_query_plans.py` | Evaluates retrieval and SQL plans | Verify pgvector and evidence output locations first |
| `generate_sbom.py`, `performance_baseline.py` | Creates a dependency inventory or performance measurements | Generates artifacts; results are not universal security or performance proof |

Do not run every script by default. Some write reports, create data, or require
services. Read a script's help, source, and milestone scope before running it.
Use the [test strategy](../docs/quality/TEST-STRATEGY.md) to select suites.
