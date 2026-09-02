# ADR-005: Evaluation of deferred local-tooling items

- Status: Proposed
- Date: 2026-08-21
- Deciders: project owner (user), AegisBank AI Platform
- Related: ADR-001, ADR-003, ADR-004, `AGENTS.md` "Local Tooling",
  `.intelligence/smoke/mcp-smoke.json`

## Context

Per the previous ADRs and `AGENTS.md`, several local-tooling items were
recorded as "blocked" or "deferred". This ADR evaluates each one against
the project rule *"Add a dependency or technology only when it resolves a
requirement, reduces a risk, or demonstrates a defined competency"* (from
`AGENTS.md`) and decides whether it can be installed now (and how), or must
remain deferred.

The E2E smoke on 2026-08-21 confirmed all 4 MCP servers reach `tools/list`
via `@modelcontextprotocol/sdk` over stdio (evidence:
`.intelligence/smoke/mcp-smoke.json`, 56 tools total).

## Items

### 1. Docker LSP (compose / Dockerfile)

**Status today**: no npm package; the opencode-built-in `yaml-ls` covers
Compose YAML but is generic.

**Evaluation**:

- **Requirement?** — Yes, **defensive**: when `docker-compose.yml` lands
  in `v0.2+`, the team needs structural validation against the Compose
  schema. Without validation, mis-indented service definitions fail at
  docker runtime instead of at edit time.
- **Risk reduced?** — Yes: catching compose errors at edit time is
  cheaper than at container-start time.
- **Defined competency?** — Partial. Composition is not a "core"
  AegisBank competency; it is plumbing.

**Decision**: **Configure the existing `yaml-ls` build-in (already
auto-installed by opencode) with the Compose JSON Schema URL via
`initializationOptions`. This does not require installing any new
package.**

Configuration shape (do not apply until a Compose file exists):

```jsonc
"lsp": {
  "yaml-ls": {
    "initialization": {
      "schemaStore": {
        "enable": true,
        "url": "https://json.schemastore.org/compose-spec/compose-spec.json"
      }
    }
  }
}
```

Apply this only after the first `docker-compose.yml` lands in the repo.

### 2. PowerShellEditorServices LSP

**Status today**: removed from PSGallery; no npm equivalent; not a
built-in for opencode.

**Evaluation**:

- **Requirement?** — Marginal. PowerShell scripts in this project live
  in `$USERPROFILE/.config/opencode/scripts/*.ps1` (outside this
  repo's LSP scope anyway). Repo-local PowerShell is rare.
- **Risk reduced?** — Limited. Editing mistakes in
  `init-opencode-project.ps1` are caught by the bootstrap smoke test,
  not by LSP.
- **Defined competency?** — No. PowerShell editing is not a core
  AegisBank competency.

**Decision**: **Remain deferred indefinitely.** No action this turn.
Revisit only if a future milestone introduces substantive PowerShell
code in the repo.

### 3. `context7-mcp` MCP (live library docs in-session)

**Status today**: package available; `CONTEXT7_API_KEY` env var is a
placeholder (`ctx7sk-PLACEHOLDER-ROTATE-AT-DASHBOARD`), so the server
would error out at runtime.

**Evaluation**:

- **Requirement?** — Yes, **demonstrated**: `find-docs` skill and the
  MCP Python SDK HITL research note (`docs/research/`) would benefit
  from in-session docs for `pydantic-ai`, `chromadb`, `tenacity`,
  `prometheus-client`, etc., as v0.3+ work begins.
- **Risk reduced?** — Yes: avoids LLM hallucinating an API surface.
- **Defined competency?** — Yes: bringing current API knowledge into
  the agent loop is a defined competency for v0.3+.

**Decision**: **Install now with the existing placeholder key, marked
"disabled until key rotated" in `opencode.json`.** When the user
rotates `CONTEXT7_API_KEY`, the server lights up automatically with no
config change.

How (apply immediately):

1. `pnpm add @upstash/context7-mcp` in `.opencode/`.
2. Add to `opencode.json`:

```jsonc
"context7": {
  "type": "local",
  "command": [
    "node",
    "C:/aegisbank-ai-platform/.opencode/node_modules/@upstash/context7-mcp/dist/index.js"
  ],
  "enabled": true,
  "env": {
    "CONTEXT7_API_KEY": "ctx7sk-PLACEHOLDER-ROTATE-AT-DASHBOARD"
  }
}
```

3. Document in `AGENTS.md` as "inert until key rotated".

Risk to mitigate: the placeholder key is shipped in plain text in
`opencode.json`. Acceptable because this file is project-owned and
`.gitignore`'d in the bootstrap, but flag in `.intelligence/` that
**no real key may be committed** even after rotation.

### 4. Custom Aegis skills (`aegis-redaction-check`,
`aegis-contract-validator`, `aegis-write-proposal-format`,
`aegis-tool-authorization-check`, `aegis-hallucination-detect`)

**Status today**: not created.

**Evaluation**:

- **Requirement?** — Not yet. The behaviors these skills encode
  (redaction, contract validation, proposal formatting, tool
  authorization, hallucination detection) live inside Aegis (v0.5+)
  itself, not as separate skills consumed by the opencode agent.
- **Risk reduced?** — N/A without a target consumer.
- **Defined competency?** — Only once a concrete Aegis run produces
  the failure modes these skills would catch.

**Decision**: **Remain deferred to v0.5.** When the first Aegis
implementation hits a real failure mode (re-exposure of PII, contract
drift, etc.), create the narrowest possible skill at that moment per
the "create when validated" rule.

### 5. Codebase-memory provider (structural graph of code)

**Status today**: OpenCode Global reports `codebase-memory → not_installed`
and falls back to `lsp` / `ripgrep` for `architecture` strategy.

**Evaluation**:

- **Requirement?** — Marginal at v0.1. The project has <30 source files;
  `git grep` + `pyright` LSP covers symbol and architecture queries
  already. Codebase Memory becomes useful when the codebase passes
  ~5k files and call graphs are needed in-session.
- **Risk reduced?** — No real risk today.
- **Defined competency?** — Yes, but requires project adoption of the
  provider globally — outside the scope of this turn.

**Decision**: **Change `architecture` provider in
`.ai-env/retrieval-policy.json` to `"provider": "lsp"`** so the
router doesn't take the dead branch. Keeps the path open to flip
back to `codebase-memory` once a global provider ships.

### 6. `pydantic-ai` Python install

**Status today**: not installable without a `pyproject.toml` for
`services/aegis-agent/` (planned v0.5 deliverable).

**Evaluation**:

- **Requirement?** — Tied to v0.5 kickoff. Once v0.5 is approved, a
  fresh `services/aegis-agent/` is needed anyway.
- **Risk reduced?** — Defers to v0.5 planning.

**Decision**: **Remain deferred to v0.5.** Do not pre-create the
`services/aegis-agent/` skeleton in v0.1; that would re-introduce the
scope-creep risk we explicitly ruled out earlier.

### 7. `chromadb` Python install

**Status today**: ADR-004 chose in-process `chromadb`. Install path
is `services/rag-pipeline/pyproject.toml` (v0.4).

**Evaluation**:

- **Requirement?** — Tied to v0.4 kickoff.

**Decision**: **Remain deferred to v0.4.**

## Summary of this ADR

| # | Item | Decision |
|---|---|---|
| 1 | Docker LSP | Configure existing `yaml-ls` with Compose schema when first compose file lands |
| 2 | PowerShell LSP | Deferred indefinitely |
| 3 | `context7-mcp` MCP | **Install this turn** with placeholder key |
| 4 | Custom Aegis skills | Deferred to v0.5 |
| 5 | Codebase-memory provider | Re-point `architecture` provider to `lsp` |
| 6 | `pydantic-ai` Python | Deferred to v0.5 scaffold |
| 7 | `chromadb` Python | Deferred to v0.4 scaffold |
