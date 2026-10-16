# Plan

1. Add an additive API execution-mode field derived from observed orchestration evidence.
2. Render the field in the chat UI without exposing provider errors or secrets.
3. Add contract and UI tests for the three modes.
4. Validate locally, then execute a cloud probe and report the remaining Foundry quota/provider state separately.
