# ADR-004: Vector store integration strategy for `v0.4 - RAG`

- Status: Accepted
- Date: 2026-08-21
- Milestone target: v0.4
- Deciders: project owner (user), AegisBank AI Platform
- Supersedes: none
- Related: AGENTS.md "Local Tooling", ADR-003

## Context

`v0.4 - RAG` requires a vector store for the Aegis RAG pipeline over the
synthetic knowledge corpus. The integration shape must:

1. Run local-first (rule: "Work local first, then Docker, CI, and Azure").
2. Be deterministic and reproducible (rule: "Use only synthetic, reproducible data").
3. Avoid exposing SQL / raw query language to the LLM (rule: "deterministic
   identity, policy, authorization, validation, and business rules decide").
4. Survive a Docker compose for evaluation harness.

Candidates evaluated:

| Option | Surface | License | Verdict |
|---|---|---|---|
| `chromadb` in-process (Python lib) | API in our service | Apache-2.0 | strong fit |
| `chromadb-mcp@0.1.0` (community npm MCP) | MCP tool | Proprietary (single maintainer) | rejected |
| Qdrant / Weaviate hosted | server | Apache-2.0 / BSD | rejected for v0.4 (overkill) |
| In-memory numpy/faiss | DIY | Apache-2.0 | rejected: reinvents metadata |

The community `chromadb-mcp@0.1.0` is technically feasible but listed as
**Proprietary** with one maintainer, one version, published 5 months ago
— too fragile for a foundational dependency. We can revisit when Chroma
themselves publish an MCP server (they have not, as of 2026-08-21).

## Decision

Use **`chromadb` in-process from `services/rag-pipeline/`** (planned).
No MCP wrapper for the vector store in v0.4.

## Consequences

### Positive

- Deterministic, version-pinned Python library we control.
- Reads / writes happen through our own code path, so all access is
  deterministic and auditable — consistent with "HITL for state-changing".
- Avoids a single-maintainer proprietary dependency.
- Compatible with the local-first rule: `pip install chromadb` in a venv
  is enough for v0.4 development.

### Negative

- No standard MCP surface for the vector store. Mitigation: when v0.5
  Aegis needs to query the store, we expose it through our project-owned
  `Aegis-Read` MCP server (planned) — not via Chroma's protocol.
- Chroma version drift risk. Mitigation: pin in `pyproject.toml`.

### Neutral

- Docker compose stays simple: one service for the pipeline that owns
  chromadb locally (no separate vector store container in v0.4).

## Deferred (not decided here)

- Whether to switch to Qdrant for v1.0+ when evaluation traffic scales.
- Whether to expose the vector store through MCP in v0.5+ (depends on
  whether Aegis needs cross-service vector access; not needed in v0.4).
