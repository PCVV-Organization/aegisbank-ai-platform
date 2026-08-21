# AegisBank Mock Core Banking

Local, deterministic backend for the `v0.2.0 - Core Banking Mock` milestone of
AegisBank AI Platform.

> This is a local educational mock. It is not a real core banking system.

It uses only reproducible synthetic data and deliberately implements no AI,
authentication, payment, transfer, credit-decision, or production banking capability.

## Purpose

The service establishes the typed HTTP and relational persistence boundary that
later milestones can consume. It demonstrates:

- versioned REST endpoints and explicit Pydantic response models;
- SQLAlchemy 2.x persistence with session-per-request lifecycle;
- transaction commit/rollback for one internal service-request write;
- deterministic synthetic `Customer`, `Loan`, `Installment`, and `ServiceRequest` data;
- consistent error envelopes and `X-Correlation-ID` propagation;
- isolated SQLite databases for automated tests.

The service is a single FastAPI application organized as a modular monolith:

```text
HTTP routes
    -> Pydantic API contracts
    -> domain rules and typed errors
    -> repositories
    -> SQLAlchemy ORM
    -> local SQLite
```

ORM models and HTTP schemas are separate. The domain layer contains pure money
and next-installment rules rather than persistence objects.

## Requirements

- Python `3.14.x`
- Project-local virtual environment at `C:\aegisbank-ai-platform\.venv`

Runtime and development versions are pinned in [`pyproject.toml`](pyproject.toml).
The current FastAPI/Starlette `TestClient` uses `httpx2`, as recommended by the
current Starlette documentation.

## Setup

Run from the repository root:

```powershell
python -m venv .venv
.venv\Scripts\python.exe -m pip install -e "services/mock-core-banking[dev]"
```

No global Python package or external database is required.

## Configuration

The application reads these optional environment variables:

| Variable | Safe default |
| --- | --- |
| `AEGISBANK_ENV` | `development` |
| `AEGISBANK_DATABASE_URL` | Local SQLite file at `data/local/aegisbank-dev.db` |

The default path is resolved from the service location, not from a user profile.
No `.env` file or secret is required.

## Run

From the repository root:

```powershell
.venv\Scripts\python.exe -m uvicorn mock_core_banking.main:app `
  --app-dir services/mock-core-banking/src `
  --host 127.0.0.1 `
  --port 8001
```

The documented default binds only to `127.0.0.1`. The application does not enable
wildcard CORS. OpenAPI is available at `http://127.0.0.1:8001/openapi.json` and
Swagger UI at `http://127.0.0.1:8001/docs`.

## Test And Quality

Run from the repository root:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m compileall services/mock-core-banking/src
```

Tests create isolated databases under pytest temporary directories. They do not
read from or write to the development database.

## Endpoints

| Method | Path | Purpose |
| --- | --- | --- |
| `GET` | `/health/live` | Confirm that the process is alive |
| `GET` | `/health/ready` | Execute a read-only `SELECT 1` against the datastore |
| `GET` | `/api/v1/customers/{customer_id}` | Read one synthetic customer |
| `GET` | `/api/v1/customers/{customer_id}/loans` | Read only that customer's synthetic loans |
| `GET` | `/api/v1/loans/{loan_id}` | Read one synthetic loan |
| `GET` | `/api/v1/loans/{loan_id}/installments/next` | Read the next applicable synthetic installment |
| `POST` | `/api/v1/service-requests` | Create one synthetic service request |
| `GET` | `/api/v1/service-requests/{service_request_id}` | Read one synthetic service request |

The next-installment rule excludes `PAID` records. Among `OVERDUE` and `PENDING`
records, it selects the earliest `due_date`, then lowest `installment_number`, then
lowest `installment_id`. If no record is applicable, the API returns
`INSTALLMENT_NOT_FOUND` with HTTP 404.

All monetary fields cross the API as decimal strings and use `Decimal`/`NUMERIC`
internally. `Installment.total_due` must equal the sum of principal, interest, and fees.

## Error And Correlation Contract

Every response includes `X-Correlation-ID`. A safe client value is preserved;
otherwise the service generates a UUID.

Errors use one envelope and do not expose SQL, paths, stack traces, or secrets:

```json
{
  "error": {
    "code": "CUSTOMER_NOT_FOUND",
    "message": "Synthetic customer was not found.",
    "correlation_id": "example-request-001"
  }
}
```

## Deterministic Seed

Each new datastore receives exactly:

- 3 synthetic customers;
- 4 synthetic loans;
- 10 synthetic installments;
- 2 synthetic service requests.

Re-running the seed only adds missing fixture IDs. It does not delete or overwrite
service requests created through the API.

## Write Boundary

`POST /api/v1/service-requests` is an internal mock-core capability. Its existence
does not authorize a future agent to invoke it directly. Agent exposure remains
blocked until `v0.6`, where deterministic authorization and explicit HITL approval
will be introduced. Idempotency, retry, circuit breaker, and messaging remain
deferred to `v0.7`.

No fake approval mechanism is implemented in this service.

## Known Limitations

- No authentication or authorization; use only on the local loopback interface.
- No idempotency protection or safe retry policy for the write endpoint.
- Sequential service-request ID allocation is sufficient only for this local,
  single-process milestone and is not a production concurrency strategy.
- SQLite differs from PostgreSQL in concurrency, type, migration, and operational behavior.
- Schema creation uses SQLAlchemy metadata; migrations are intentionally deferred.
- No messaging, distributed tracing, Docker, Azure, agent, MCP, RAG, or ML integration.

## Structure

```text
services/mock-core-banking/
|-- pyproject.toml
|-- README.md
|-- src/mock_core_banking/
|   |-- api/          # HTTP routes and dependencies
|   |-- domain/       # Pure rules, enums, and typed errors
|   |-- persistence/  # ORM, database lifecycle, repositories, and seed
|   |-- schemas/      # Pydantic request/response contracts
|   `-- main.py       # FastAPI application factory and lifespan
`-- tests/
    |-- unit/
    `-- integration/
```
