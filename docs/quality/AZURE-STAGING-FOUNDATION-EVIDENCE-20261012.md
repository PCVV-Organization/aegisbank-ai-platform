# Azure Staging Foundation Evidence — 2026-10-12

> **Status:** `STAGING_FOUNDATION_DEPLOYED`; `STAGING_ACCEPTANCE_PARTIAL`.
> **Scope:** Synthetic AegisBank staging infrastructure in `rg-aegisbank-staging`.
> This record does not claim production readiness.

## Deployment

Deployment `aegisbank-staging-foundation-v18` completed with state `Succeeded`.
Follow-up deployment `aegisbank-staging-foundation-v20` also completed with
state `Succeeded` after publishing the JWT-enabled Agent image.
Both Container Apps were reconciled with immutable ACR images:

- Agent: `aegisbankstagingacr.azurecr.io/aegisbank-agent:jwtv20-20261012`
- Core Banking: `aegisbankstagingacr.azurecr.io/mock-core-banking:7512f96a2b24`

The Foundry account is `aegisbank-staging-ai` with deployment
`aegisbank-phi-4-mini`. The workload identity retains the least-privilege
Foundry and Service Bus sender assignments. The Entra API registration is
`9f259d8f-e15d-4978-b3bf-6fc73634fefd` with audience
`api://9f259d8f-e15d-4978-b3bf-6fc73634fefd`. A synthetic extension property
named `extension_9f259d8fe15d4978b3bf6fc73634fefd_customer_id` was registered;
no users, passwords, client secrets, or personal data were created.

## Executed checks

| Check | Result | Evidence |
|---|---|---|
| Agent liveness | `PASS` | Public `GET /health/live` returned HTTP 200 and `{"status":"alive"}`. |
| Agent readiness | `PASS` | Public `GET /health/ready` returned HTTP 200 and `{"status":"ready","environment":"staging"}`. |
| Invalid bearer rejection | `PASS` | `POST /api/v1/agent/run` with an arbitrary bearer returned HTTP 503: `Cloud JWT verification is not configured`. |
| Configured JWT rejection | `PASS` | On `v20`, the same arbitrary bearer returned HTTP 401: `Invalid Bearer token`. |
| Core Banking resource | `PASS` | ARM reports the Container App `Succeeded` with the expected `azurecr.io` image. |
| Bicep compilation | `PASS` | `az bicep build --file deploy/azure/main.bicep --stdout`. |
| Documentation index | `PASS` | `python -B scripts/documentation_index.py --check`: 202 Markdown paths and 4 generated files. |

## Remaining acceptance work

`STAGING_ACCEPTED` is not declared. A signed token carrying a synthetic
`customer_id` value has not been exercised yet. Private
App Configuration and Key Vault connectivity, Cosmos persistence, authenticated
RAG/IDOR/HITL/idempotency/messaging/telemetry checks, and the corresponding
synthetic acceptance evidence remain open. `Microsoft.App` still reports
`Registering` even though this deployment completed successfully.

