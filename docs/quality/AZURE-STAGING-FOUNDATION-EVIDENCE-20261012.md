# Azure Staging Foundation Evidence — 2026-10-12

> **Status:** `STAGING_FOUNDATION_DEPLOYED`; `STAGING_ACCEPTANCE_PARTIAL`.
> **Scope:** Synthetic AegisBank staging infrastructure in `rg-aegisbank-staging`.
> This record does not claim production readiness.

## Deployment

Deployment `aegisbank-staging-foundation-v18` completed with state `Succeeded`.
Both Container Apps were reconciled with immutable ACR images:

- Agent: `aegisbankstagingacr.azurecr.io/aegisbank-agent:a2f3f58c6d1a`
- Core Banking: `aegisbankstagingacr.azurecr.io/mock-core-banking:7512f96a2b24`

The Foundry account is `aegisbank-staging-ai` with deployment
`aegisbank-phi-4-mini`. The workload identity retains the least-privilege
Foundry and Service Bus sender assignments. Entra tenant and audience values
remain empty until an approved API registration and synthetic customer claim
exist; cloud authentication therefore fails closed.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Agent liveness | `PASS` | Public `GET /health/live` returned HTTP 200 and `{"status":"alive"}`. |
| Agent readiness | `PASS` | Public `GET /health/ready` returned HTTP 200 and `{"status":"ready","environment":"staging"}`. |
| Invalid bearer rejection | `PASS` | `POST /api/v1/agent/run` with an arbitrary bearer returned HTTP 503: `Cloud JWT verification is not configured`. |
| Core Banking resource | `PASS` | ARM reports the Container App `Succeeded` with the expected `azurecr.io` image. |
| Bicep compilation | `PASS` | `az bicep build --file deploy/azure/main.bicep --stdout`. |
| Documentation index | `PASS` | `python -B scripts/documentation_index.py --check`: 202 Markdown paths and 4 generated files. |

## Remaining acceptance work

`STAGING_ACCEPTED` is not declared. End-user Entra JWT validation, private
App Configuration and Key Vault connectivity, Cosmos persistence, authenticated
RAG/IDOR/HITL/idempotency/messaging/telemetry checks, and the corresponding
synthetic acceptance evidence remain open. `Microsoft.App` still reports
`Registering` even though this deployment completed successfully.

