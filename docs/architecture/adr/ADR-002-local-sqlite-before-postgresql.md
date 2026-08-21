# ADR-002: Local SQLite Before PostgreSQL

## Status

Accepted for `v0.2`.

## Context

The Mock Core Banking milestone needs relational persistence, foreign keys,
transactions, deterministic seed data, and isolated integration tests. The project
must work locally before Docker, CI, or Azure and must not require an external
database during `v0.2`.

PostgreSQL is the intended later relational datastore, but adding it now would
require a local server or container and would advance infrastructure work outside
the approved milestone.

## Decision

Use SQLite only as the local `v0.2` datastore. Use a separate temporary SQLite
file for each test and ignore the development database in Git.

Keep SQLAlchemy ORM models separate from Pydantic HTTP schemas and access data
through a database/session/repository boundary. Use portable SQLAlchemy 2.x
expressions for application queries. This reduces coupling when PostgreSQL is
introduced later, but it does not make migration a configuration-only change.

PostgreSQL remains the target relational datastore for a later authorized phase.
The migration must include dialect testing, schema migrations, concurrency tests,
connection management, and operational validation.

## Alternatives Considered

| Alternative | Reason not selected for `v0.2` |
| --- | --- |
| Local PostgreSQL installation | Adds machine-level setup and violates the zero-external-service goal |
| PostgreSQL in Docker | Docker is explicitly outside `v0.2` |
| Hosted PostgreSQL | Violates local-first delivery and may create cost or secret-management requirements |
| In-memory dictionaries | Do not demonstrate relational constraints, transactions, or SQL persistence |
| JSON files | Require custom consistency and concurrency behavior without relational guarantees |

## Consequences

Positive consequences:

- no external datastore process or cloud resource is required;
- Python includes the SQLite driver;
- each test receives an isolated temporary database;
- foreign keys and check constraints provide useful local validation;
- deterministic fixtures can be recreated without committing database files.

Negative consequences:

- SQLite concurrency and locking differ materially from PostgreSQL;
- decimal, enum, datetime, and constraint behavior require PostgreSQL revalidation;
- metadata-based schema creation is not a migration strategy;
- connection pooling and production operations are not exercised;
- application-level sequential ID allocation is only suitable for this local mock.

SQLite is a development convenience for an educational mock. It is not presented
as an appropriate datastore for a real core banking system.
