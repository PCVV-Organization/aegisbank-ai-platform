# Repository Instructions

## Mission

Build AegisBank AI Platform incrementally as a secure, educational banking AI
laboratory. It is not a real bank or production financial system.

## Permanent Rules

- Modify project files only inside `C:\aegisbank-ai-platform`.
- Use only synthetic, reproducible data. Never add real personal, banking, or confidential data.
- Work local first, then Docker, CI, and Azure in the approved roadmap order.
- Do not create paid Azure resources or run deployments without explicit approval.
- Start with one agent and a modular monolith. Do not introduce early microservices, AKS, or multi-agent flows.
- The LLM may interpret and propose; deterministic identity, policy, authorization, validation, and business rules decide.
- Require explicit HITL approval for every state-changing operation.
- Never commit secrets. Keep `.env` ignored and publish placeholders only in `.env.example` when needed.
- Minimize and redact sensitive content in logs, prompts, audit records, and telemetry.
- Add a dependency or technology only when it resolves a requirement, reduces a risk, or demonstrates a defined competency.
- Keep changes within the authorized milestone. Scope expansion requires an explicit decision.
- Preserve pre-existing OpenCode bootstrap artifacts unless a task explicitly targets them.
- Promote only verified, durable project knowledge to `.intelligence/`.

## Quality Rules

- Add tests appropriate to every implementation change.
- Separate unit, integration, contract, end-to-end, and AI evaluation concerns.
- Validate actual behavior before reporting `PASS`; never substitute expected behavior for executed evidence.
- Writes must be idempotent before any retry policy is enabled.
- Use bounded retries only for known transient failures and circuit breakers for persistent dependency failures.
- Propagate correlation and trace identifiers across every future execution boundary.
- Do not claim legal, regulatory, NIST, Microsoft, or banking certification/compliance.

## Milestone Workflow

1. Inspect the current repository and milestone state.
2. Explain the bounded change briefly.
3. Implement only the authorized phase.
4. Run relevant validation and correct failures.
5. Update status and documentation with real evidence.
6. Stop before the next milestone and request approval.

## Definition Of Done

A milestone is done only when its scoped artifacts are complete, required tests
and checks have actually passed, documentation reflects the observed result, and
remaining risks are reported. Never advance to the next milestone automatically.

## Baseline Validation

For documentation-only changes, run:

```powershell
git diff --check
git status --short
```

Use milestone-specific format, lint, type, test, security, evaluation, and build
commands once those toolchains exist.

## Local Tooling

OpenCode-native configuration lives in `opencode.json`. Anything below is
project-owned and reproducible via `npm install` in `.opencode/`.

### MCP servers

Project-owned MCP servers (all `type: "local"`, all launched via `node` against
paths inside `.opencode/node_modules/`; no `npx -y` re-downloads):

- `sequential-thinking` (`@modelcontextprotocol/server-sequential-thinking@2026.7.4`).
  Pre-installed in v0.1 ahead of need for the reasoning substrate `v0.5 - Agent
  and read-only tools` will rely on for HITL proposal decomposition.
  Justified under the "defined competency" clause.
- `filesystem` (`@modelcontextprotocol/server-filesystem@2026.7.10`,
  scoped to `C:/aegisbank-ai-platform`). Read-only base for read tools in v0.5.
  Justified under the "defined competency" clause.
- `git` (`@cyanheads/git-mcp-server@2.15.1` — substitute because
  `@modelcontextprotocol/server-git` is not published to npm; same MCP
  contract). `env.GIT_MCP_REPO_PATH` scoped to the project root.
- `everything` (`@modelcontextprotocol/server-everything@2026.8.18`).
  Anthropic's reference MCP server used as smoke-test target to validate
  the host MCP transport. Has echo, add, longRunningOperation, sampleLLM,
  getTinyImage, annotatedMessage, and structuredContent tools. Not for
  production agent calls.
- `context7` (`@upstash/context7-mcp@4.0.3`). Live library docs in-session.
  **Inert until `CONTEXT7_API_KEY` is rotated** — the env shipped in
  `opencode.json` is a placeholder; opencode logs "Request timed out" until
  the user replaces it. Rotate via the user's own secret store; never commit
  a real key.

Re-materialize after a clean checkout:

```powershell
Set-Location 'C:\aegisbank-ai-platform\.opencode'
npm install --no-audit --no-fund
```

### LSP servers

OpenCode LSP is disabled by default. This repository enables it via the `lsp`
block in `opencode.json`:

- `pyright` — handles `.py`, `.pyi`. Explicit `command` points to the local
  `pyright` install (`pyright@1.1.413`). Will be consumed by the v0.2
  `services/mock-core-banking/` codebase.
- `yaml-ls` — built-in; **not declared** in `opencode.json` (the validator
  requires `command` for any declared LSP, but built-ins auto-install when
  YAML files are detected). Red Hat yaml-language-server will appear on
  first `.yaml` / `.yml` open. Reserved for future Docker Compose / Azure
  configs.
- `powershell` — **not declared** either. `PowerShellEditorServices` is no
  longer distributed on PSGallery and has no npm equivalent; the PowerShell
  VSCode extension remains the supported distribution. Revisit when an
  upstream distribution re-emerges — at that point it can be added as a
  custom LSP with explicit `command`.

Disable automatic LSP downloads (CI / air-gapped) with
`OPENCODE_DISABLE_LSP_DOWNLOAD=true`.

### Retrieval policy

`.ai-env/retrieval-policy.json` adopts the codebase-memory router for this
project. Strategies wired:

- `exact` → `ripgrep` (or `git grep` fallback)
- `symbol` → `lsp` (pyright)
- `architecture` → `lsp` (re-points the `codebase-memory` stub to the
  working `pyright` LSP until a real codebase-memory provider ships)
- `knowledge` → `filesystem`, restricted to `AGENTS.md`, `.ai-env/**`,
  `docs/**`, `specs/**`, `docs/architecture/adr/**`, `README*`, `CHANGELOG*`,
  `PROGRESS.md`, `MIGRATION_CONTROL*`, `HANDOFF_NEXT_RUN*`
- `semantic` → disabled (default)

### Research notes

In-repo research findings captured under `docs/research/`:

- `pydantic-ai-mcp-integration.md` — v0.5 agent SDK decisions.
- `mcp-python-sdk-hitl-patterns.md` — v0.6 HITL proposal mediator patterns.

### Globally-installed skills

The following skills are installed at the user level (`~/.agents/skills/`) and
are auto-discovered by opencode sessions. They are NOT in the repo and NOT
re-installed by `npm install` in `.opencode/`. To re-install on a fresh
machine:

```powershell
npx -y skills@latest add wshobson/agents@e2e-testing-patterns -g -y
```

- `e2e-testing-patterns` (`wshobson/agents`, 21,252 installs at install time).
  Authoritative Playwright + Cypress patterns for E2E suites. Useful when v0.2
  schemas need real HTTP-level coverage or when v0.7 reliability introduces
  failure-injection. Note: AegisBank has no public UI today, so this skill
  applies to API-level E2E (httpx + pytest-httpx + respx) rather than
  browser-level E2E. The skill still informs contract, isolation, and
  flakiness-handling patterns.

### MCP smoke evidence

E2E handshake evidence lives at `.intelligence/smoke/mcp-smoke.json`. To
re-run after any MCP change:

```powershell
Set-Location 'C:\aegisbank-ai-platform\.opencode'
node scripts/smoke-mcp.mjs
```

The script uses `@modelcontextprotocol/sdk` over stdio; the report lists
each server, `tools/list` results, and connect timing. Re-run before any
change to the `mcp` block of `opencode.json`.
