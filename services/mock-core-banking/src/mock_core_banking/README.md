# Mock Core Banking Package

Package map for the synthetic local banking API. This is educational laboratory software, not a real banking system.

- `main.py` — application construction and entry point
- `api/` — HTTP routes and request dependencies
- `schemas/` — API input and output models
- `domain/` — deterministic domain rules
- `persistence/` — local storage and repository adapters

Keep business rules deterministic, use synthetic data, and test interface changes at the relevant layer. See the service [README](../../README.md) and project [canonical component guide](../../../../docs/architecture/CANONICAL-COMPONENTS.md).
