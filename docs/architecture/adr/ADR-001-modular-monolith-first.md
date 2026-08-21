# ADR-001: Modular Monolith First

## Status

Accepted for `v0.2`.

## Context

AegisBank needs a deterministic local backend before later milestones introduce
ML, RAG, an agent, MCP, reliability patterns, containers, or Azure. The first
backend must be simple enough to run and test locally while preserving explicit
boundaries between HTTP contracts, domain rules, and persistence.

Distributing the four small domain entities across network services would add
deployment, failure, security, observability, and contract-management concerns
before any requirement demonstrates a need for those boundaries.

## Decision

Implement the Mock Core Banking capability as one FastAPI deployable organized as
a modular monolith.

The internal boundaries are:

- `api`: versioned HTTP routes and request-scoped dependencies;
- `schemas`: Pydantic request and response contracts;
- `domain`: pure money/selection rules, enums, and typed errors;
- `persistence`: SQLAlchemy models, repositories, sessions, and deterministic seed.

The application uses one relational datastore and one process. Modules interact
through Python calls, not network protocols. A session is scoped to a request, and
the write operation owns an explicit transaction boundary.

## Alternatives Considered

| Alternative | Reason not selected for `v0.2` |
| --- | --- |
| Multiple microservices | Adds network failure modes, deployment units, and distributed contracts without an independent lifecycle or scale requirement |
| Event-driven write path | Messaging and delivery semantics belong to the approved `v0.7` milestone |
| Azure Functions | Violates local-first sequencing and introduces a cloud/runtime boundary before local behavior is stable |
| A single unstructured module | Small initially, but obscures API, domain, and persistence responsibilities needed by later milestones |

## Consequences

Positive consequences:

- one local command starts the backend;
- transactions remain easy to reason about;
- tests run without network services;
- the API, domain, and persistence can evolve independently inside one deployable;
- later extraction remains possible if evidence demonstrates lifecycle, scaling,
  ownership, security-boundary, or failure-isolation needs.

Negative consequences:

- modules share one process and one failure boundary;
- components cannot scale or deploy independently;
- discipline and tests must enforce internal boundaries;
- this decision does not prove that future service extraction will be trivial.

The project will not introduce microservices merely because more endpoints are added.
