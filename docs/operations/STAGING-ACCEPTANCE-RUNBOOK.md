# Azure Staging Acceptance Contract and Runbook

> **Recorded status (2026-10-11):** `STAGING_FOUNDATION_DEPLOYED`; `STAGING_ACCEPTANCE_PARTIAL`.
> **Purpose:** Define end-to-end acceptance checks for Azure staging and distinguish executed evidence from checks that remain open.
> **Evidence:** The dated [staging-foundation evidence](../quality/AZURE-STAGING-FOUNDATION-EVIDENCE-20261011.md) records the deployed immutable image, Foundry model, managed-identity role, public health checks, and a synthetic inference request. It does not authorize production promotion.

## 1. Preconditions

1. The base infrastructure in `deploy/azure/main.bicep` has been successfully deployed to the specifically authorized `rg-aegisbank-staging` resource group.
2. Required non-secret bootstrap settings are present in the approved runtime configuration:
   - `AEGISBANK_ENV=staging`
   - `AZURE_APPCONFIG_ENDPOINT=https://<prefix>-staging-config.azconfig.io`
   - `AZURE_KEY_VAULT_URL=https://<prefix>-staging-kv.vault.azure.net/`
   - `AEGISBANK_SERVICEBUS_NAMESPACE=<prefix>-staging.servicebus.windows.net`
   - `AEGISBANK_FOUNDRY_ENDPOINT=https://<foundry-account>.cognitiveservices.azure.com/`
   - `AEGISBANK_FOUNDRY_DEPLOYMENT_NAME=<approved-foundry-deployment>`
   - `AEGISBANK_ENTRA_TENANT_ID=<approved-tenant-guid>`
   - `AEGISBANK_ENTRA_AUDIENCE=<registered-api-application-id-uri-or-client-id>`
   - `AEGISBANK_ENTRA_CUSTOMER_ID_CLAIM=<approved-synthetic-customer-claim>`
3. The assigned workload identity has the required roles from the [RBAC matrix](RBAC-LEAST-PRIVILEGE-MATRIX.md).
4. No `.env` or `.env.local` file is present in the container or runtime environment.
5. All direct Bicep commands for this staging target explicitly pass `location=westus2` and `identityLocation=westus2`; the resource group's default location is not the Foundry account's location.
6. Before a rerun, query the existing Foundry role assignment. Pass its exact ARM resource name as `foundryRoleAssignmentName`; role-assignment identifiers are immutable and ARM rejects attempts to adopt an assignment with a different name.

## 2. Acceptance Test Cases (14 Checks)

| ID | Area | Check | Expected result/evidence |
|---|---|---|---|
| `STG-01` | Process liveness | `GET /health/live` | `200 OK`, `{"status":"alive"}`; no external dependency checks. |
| `STG-02` | Readiness | `GET /health/ready` | `200 OK`, `{"status":"ready"}`; providers initialized without secret disclosure. |
| `STG-03` | App Configuration | Connect and hydrate `staging` label | Reads expected settings/feature flags through `DefaultAzureCredential`; no local keys. |
| `STG-04` | Entra identity | Passwordless authentication | No client secret, SAS connection string, or persisted token in environment variables. |
| `STG-05` | Key Vault reference | Resolve synthetic reference | Resolves a synthetic test secret reference; no real credential is introduced. |
| `STG-06` | Cloud model inference | Chat completion | Test inference uses an Entra bearer token; model/resource access must be authorized. |
| `STG-07` | RAG retrieval | Retrieval with citations | Authorized synthetic banking query returns a cited answer such as `[DOC-xxx]`. |
| `STG-08` | RAG abstention | Out-of-corpus or malicious query | Agent deterministically abstains rather than inventing policy. |
| `STG-09` | Own-customer read | Read own account | `CUST-0001` credentials can read only `CUST-0001` synthetic data. |
| `STG-10` | IDOR prevention | Cross-customer access attempt | `CUST-0001` cannot read or mutate `CUST-0002`; expect `OwnershipViolationError` / HTTP 403. |
| `STG-11` | HITL write rejection | Human rejects a service request | No database mutation (`0 rows affected`). |
| `STG-12` | HITL write approval | Human explicitly approves a request | Exactly one mutation and the expected Service Bus event. |
| `STG-13` | Idempotency/retry | Repeat a write with the same `idempotency_key` | Returns the prior result without duplicate operations or charges. |
| `STG-14` | Secret redaction | Inspect telemetry | No Entra tokens, connection strings, passwords, or unmasked card numbers in logs/traces. |

All identifiers and test data must be synthetic. Do not use real customer or financial data.

## 3. Example Acceptance Commands

The endpoints below are examples only. Do not run them until cloud provisioning, target scope, credentials, cost, and test actions are explicitly approved.

```powershell
$env:AEGISBANK_ENV = "staging"
$env:AZURE_APPCONFIG_ENDPOINT = "https://aegisbank-staging-config.azconfig.io"
$env:AZURE_KEY_VAULT_URL = "https://aegisbank-staging-kv.vault.azure.net/"
$env:AEGISBANK_SERVICEBUS_NAMESPACE = "aegisbank-staging.servicebus.windows.net"
$env:AEGISBANK_FOUNDRY_ENDPOINT = "https://aegisbank-staging-ai.cognitiveservices.azure.com/"
$env:AEGISBANK_FOUNDRY_DEPLOYMENT_NAME = "aegisbank-phi-4-mini"
$env:AEGISBANK_ENTRA_TENANT_ID = "<approved-tenant-guid>"
$env:AEGISBANK_ENTRA_AUDIENCE = "<registered-api-application-id-uri-or-client-id>"
$env:AEGISBANK_ENTRA_CUSTOMER_ID_CLAIM = "customer_id"

# Validate runtime configuration for the explicitly approved target.
& .\.venv\Scripts\python.exe -c "from aegisbank_agent.configuration import validate_runtime_configuration, resolve_runtime_environment; validate_runtime_configuration(resolve_runtime_environment())"

# Run the documented E2E routing/contract test.
& .\.venv\Scripts\python.exe -m pytest ai/agent/tests/integration/banking/test_banking_routing_e2e.py -v
```

## 4. Pass/Fail Criteria

- **Accepted (`STAGING_ACCEPTED`):** All 14 checks pass with recorded evidence, correlated W3C traces, and no regressions.
- **Rejected (`STAGING_REJECTED`):** Any IDOR failure, secret leakage, or HITL bypass immediately blocks production promotion and requires the rollback process.

No status may be upgraded without actual execution evidence.
