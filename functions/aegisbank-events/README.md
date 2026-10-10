# AegisBank Events Function

This function app processes CloudEvents in the local/laboratory event workflow. It is not a substitute for the interactive agent's deterministic authorization or human approval requirements.

## Key files

- `function_app.py` — function and trigger declarations
- `cloud_event.py` — CloudEvent envelope parsing
- `handler.py` — event handling and service coordination
- `local.settings.example.json` — non-secret local configuration template

Use synthetic sample events only. Keep real local settings out of version control. Verify implementation and tests before making claims about delivery, deduplication, or runtime behavior.
