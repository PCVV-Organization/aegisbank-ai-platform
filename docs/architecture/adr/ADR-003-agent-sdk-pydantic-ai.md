# ADR-003: Agent SDK choice for `v0.5 - Agent and read-only tools`

- Status: Accepted
- Date: 2026-08-21
- Milestone target: v0.5
- Deciders: project owner (user), AegisBank AI Platform
- Supersedes: none
- Related: `docs/research/pydantic-ai-mcp-integration.md`, AGENTS.md "Local Tooling"

## Context

`v0.5` requires an agent SDK to host **Aegis** with read-only tools (charter
`v0.5 - Agent and read-only tools`). The SDK must:

1. Speak MCP (the project standard for tool wiring).
2. Validate tool inputs against `contracts/*.schema.json` (already in repo).
3. Support HITL proposal decomposition for the v0.6 mediator.
4. Be Python-native (matches the rest of the modular monolith in
   `services/mock-core-banking/`).
5. Be production-mature, not research-grade.

Candidates evaluated:

| Option | MCP client | Pydantic-native | License | Verdict |
|---|---|---|---|---|
| `pydantic-ai` | native (Pydantic AI Harness) | yes | MIT | strong fit |
| `openai-agents-python` | yes | partial | Apache-2.0 | viable |
| `langgraph` | yes (via langchain-mcp-adapters) | partial | MIT | over-scoped for one agent |
| hand-rolled | DIY | yes | n/a | rejected: reinvents HITL/middleware |

## Decision

Adopt **`pydantic-ai`** as the agent SDK for `v0.5`.

## Consequences

### Positive

- Reuses the existing `pydantic` v2 schemas already declared in
  `services/mock-core-banking/pyproject.toml`.
- Native MCP client (`pydantic_ai.mcp`) maps tools 1-to-1 with our
  `Aegis-Read` MCP server (planned v0.5 deliverable).
- Pydantic AI Harness (`/pydantic/pydantic-ai-harness`) provides reusable
  tools, hooks, and sub-agents — but the project defers sub-agents per rule
  "Start with one agent and a modular monolith".
- Output schema validation aligns with `contracts/*.schema.json` from
  bootstrap; tooling to generate clients from those schemas is already
  available (`datamodel-code-generator` if needed).
- MIT license; no per-seat cost.

### Negative

- Vendor coupling to Pydantic team. Mitigation: thin adapter layer at the
  Aegis entrypoint so swapping to `openai-agents-python` is mechanical.
- Some Pydantic AI features (Durable Execution, Graph iterators) are
  preview-grade. Mitigation: pin to the current stable v2 line, not pre-releases.

### Neutral

- Requires `pyproject.toml` at `services/aegis-agent/` (planned). The
  v0.5 work cannot start until that scaffold is approved.

## Deferred (not decided here)

- Whether to adopt Pydantic AI Harness as a secondary dependency (it
  currently overlaps with project-owned skills; defer to first use case).
- Whether to enable Pydantic AI's `graph` execution mode (defers until
  v1.2 multi-agent is on the table — single-agent flow only).
