# Azure Staging Foundation Evidence — 2026-10-11

> **Status:** `STAGING_FOUNDATION_DEPLOYED`; `STAGING_ACCEPTANCE_PARTIAL`.
> **Scope:** Synthetic AegisBank staging infrastructure in `rg-aegisbank-staging`. This evidence does not claim production readiness.

## Executed deployment

`az deployment group create` completed with state `Succeeded` for deployment
`aegisbank-staging-foundry-v9`. It applied the immutable Agent image
`aegisbankstagingacr.azurecr.io/aegisbank-agent:1281bd8a7b3a` (digest
`sha256:33e87240c48f1466dbf9a28819eccb2357b29cd53a11fab15c2842392fe12df1`).

The later deployment `aegisbank-staging-jwt-v10` completed with state
`Succeeded` and made `aegisbankstagingacr.azurecr.io/aegisbank-agent:a2f3f58c6d1a`
the running revision. This image replaces the temporary synthetic bearer smoke
boundary with Entra JWT verification that fails closed until a tenant and
audience are configured.

The deployment created and configured:

- Azure AI Services account `aegisbank-staging-ai` and its
  `aegisbank-phi-4-mini` deployment (`Phi-4-mini-instruct`, version `1`,
  `GlobalStandard`, capacity `1`).
- The Foundry endpoint
  `https://aegisbank-staging-ai.services.ai.azure.com/openai/v1`.
- The runtime user-assigned identity role `Cognitive Services OpenAI User` at
  the Foundry account scope.
- Agent environment variables for the Foundry endpoint/deployment and the
  Core Banking internal FQDN.

The formerly inherited `Azure Service Bus Data Receiver` assignment was removed
from the Agent workload identity. It retains only `Azure Service Bus Data Sender`
at the namespace scope.

## Executed runtime acceptance

| Check | Result | Observed evidence |
|---|---|---|
| `STG-01` liveness | `PASS` | Public `GET /health/live` returned `200` and `{"status":"alive"}`. |
| `STG-02` readiness | `PASS` | Public `GET /health/ready` returned `200` and `{"status":"ready","environment":"staging"}`. |
| `STG-06` Foundry inference | `PASS` | A synthetic authenticated request, `Di hola en una frase.`, returned HTTP `200`, `rounds: 1`, and `Hola, ¿en qué puedo ayudarte hoy?`. |
| RAG routing smoke | `PASS` | A synthetic `DELINQUENT` question returned HTTP `200` through `search_knowledge` with `rounds: 0`; the deterministic retrieval route did not invoke the model. |
| Cloud auth hardening | `PASS` | On the later JWT-hardened revision, public liveness/readiness returned `200`; a bearer value without configured Entra validation returned HTTP `503`, not an authenticated response. |

No real customer data, credentials, banking transactions, or state-changing
operations were used.

## Remaining acceptance work

The following acceptance cases are still open and prevent a full
`STAGING_ACCEPTED` or any production claim:

- `STG-03` App Configuration hydration through the deployed private endpoint.
- `STG-04` end-user Entra JWT validation with an approved tenant, audience, and
  synthetic customer claim. The deployed service correctly fails closed until
  those configuration values and a valid signed token exist.
- `STG-05` Key Vault reference resolution through the deployed private endpoint.
- `STG-07` through `STG-14`: cited RAG, IDOR, HITL reject/approve, idempotency,
  messaging delivery, and telemetry redaction evidence.
- Network design for private App Configuration and Key Vault access from the
  Container Apps environment, including private endpoints and DNS.
- Cosmos DB declaration in Bicep and a cloud persistence acceptance check.

## Reproducibility commands

```powershell
az deployment group show --resource-group rg-aegisbank-staging --name aegisbank-staging-foundry-v9 --query properties.provisioningState --output tsv
curl.exe --include https://aegisbank-staging-agent.mangostone-a76fbcd7.westus2.azurecontainerapps.io/health/live
curl.exe --include https://aegisbank-staging-agent.mangostone-a76fbcd7.westus2.azurecontainerapps.io/health/ready
```

Run state-changing or authenticated acceptance requests only with an explicitly
authorized synthetic target.
