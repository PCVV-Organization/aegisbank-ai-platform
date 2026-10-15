# Cloud Configuration, Workload Identity, and Deployment Boundaries

> **Recorded status (2026-10-11):** `STAGING_FOUNDATION_DEPLOYED`; `PARTIAL_RUNTIME_ACCEPTANCE`.
> **Product boundary:** AegisBank AI Platform is a secure, reproducible educational banking-AI laboratory. It is not a commercial bank and does not process real financial transactions.
>
> This remains an architectural contract. The dated [staging-foundation evidence](../quality/AZURE-STAGING-FOUNDATION-EVIDENCE-20261011.md) proves only its listed deployment and runtime checks; it does not prove full acceptance or production readiness.

## Delivery Contract: Local First, Then Azure

Required sequence: **reproducible local environment → versioned cloud contract → explicitly authorized staging → acceptance evidence**. Configuration, images, Bicep templates, and workflows do not by themselves prove successful cloud execution.

- Local development, regression, and debugging use synthetic data.
- Azure should reuse application contracts and replace only infrastructure adapters.
- Staging provisioning requires explicit authorization and test evidence.
- Production may promote only the immutable artifact accepted in staging.

## 1. Configuration Boundary and Environment Model

The documented canonical configuration boundary is `aegisbank_agent.configuration`:

```text
LOCAL (SQLite / Foundry Local / local Redis / Docker pgvector / emulators)
  │
  │ SAME CONTRACTS, INTERFACES, AND DETERMINISTIC BEHAVIOR
  ▼
PRODUCTION (Managed Identity / App Configuration / Key Vault / managed Azure services)
```

### Configuration precedence

- **Local:** `explicit test overrides > process environment variables > optional .env.local > local provider / emulators`
- **Azure (staging/production):** `minimal container bootstrap > Azure App Configuration (through Entra ID) > Key Vault secret references > code constants`

`AEGISBANK_ENV` accepts `local`, `test`, `development`, `staging`, and `production`, plus historical local aliases `container` and `kubernetes-local`. Unknown or invalid values are documented to fail closed with `EnvironmentSelectionError`. Verify current implementation before relying on this contract.

## 2. Capability Matrix: Local vs. Azure Target

The states below are recorded design/adapter claims, not evidence of successful cloud validation.

| Capability | Local design | Azure target | Recorded cloud status | Limit before real deployment |
|---|---|---|---|---|
| LLM inference | Foundry Local (`http://127.0.0.1:5272/v1`, `phi-4-mini`) | Azure AI Foundry Models (`AIServices`, OpenAI v1-compatible endpoint) | `STAGING_DEPLOYED_AND_SYNTHETICALLY_EXERCISED` | The 2026-10-11 staging evidence covers Phi-4-mini inference through managed identity; Azure OpenAI quota is not required for this path. |
| Core Banking | Local FastAPI mock with embedded SQLite | External boundary / hosted service | `DOCUMENTED_ONLY` | Staging keeps the mock isolated. The agent must not access the Core Banking database directly. |
| RAG embeddings/vector store | Docker PostgreSQL + pgvector (`vector(32)`, HNSW) | Azure Database for PostgreSQL Flexible Server | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Current connection uses a psycopg DSN; Entra token authentication requires cloud testing. |
| Cache and vector search | Standalone local Docker Redis | Azure Managed Redis | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Entra authentication requires Azure Managed Redis-specific configuration and testing. |
| Messaging and events | Local Azure Service Bus Emulator (AMQP) | Azure Service Bus namespace | `PASSWORDLESS_ADAPTER_READY` | `AzureServiceBusMessageBus` is documented to use passwordless `DefaultAzureCredential` when given a namespace. |
| NoSQL storage | Azure Cosmos DB Emulator (port 8081) | Azure Cosmos DB NoSQL | `PASSWORDLESS_ADAPTER_READY` | `CosmosRepository` is documented to use `DefaultAzureCredential` in cloud environments. |
| Non-secret configuration | App Configuration Emulator / environment fallback | Azure App Configuration with labels | `PASSWORDLESS_IMPLEMENTED` | `AppConfigurationCloudProvider` is documented to use `DefaultAzureCredential` and hydrate unlabeled plus environment-labeled settings. |
| Unavoidable secrets | In-memory `LocalSyntheticSecretProvider` | Azure Key Vault (`AzureKeyVaultSecretProvider`) | `PASSWORDLESS_IMPLEMENTED` | `KeyVaultReferenceResolver` is documented to resolve `@Microsoft.KeyVault(...)` references using `DefaultAzureCredential`. |
| Identity/authentication | Local network trust / synthetic identity | User-assigned managed identity (Microsoft Entra ID) | `PASSWORDLESS_IMPLEMENTED` | Declared in Bicep with least-privilege workload roles; assignments are not proven by this document. |
| Telemetry/tracing | OpenTelemetry in memory / local console | Azure Monitor / Application Insights | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | OTel and W3C `traceparent` instrumentation are documented; Azure Monitor exporter requires staging validation. |

## 3. Secret and `.env` Policy

1. **No `.env.production`:** Do not create or require `.env.production` files in the repository or cloud containers.
2. **`.env.local` for local development only:** This is the only permitted dotenv convention for local developers and is listed in `.gitignore` and `.dockerignore`.
3. **Fail closed:** `load_local_dotenv()` considers `.env.local` only in a local environment. Staging and production do not load dotenv files. `foundry_local.py` also does not load dotenv at import time.
4. **Production runtime validation (`validate_runtime_configuration`):** The documented validator rejects App Configuration, Service Bus, and Cosmos emulators; loopback endpoints (`127.0.0.1`, `localhost`); default emulator keys; `DEBUG` or authentication-bypass flags; and requires valid HTTPS endpoints for App Configuration and Key Vault. Error messages must never print secret values or endpoints.

Verify these behaviors in current source and tests before claiming they are enforced.

## 4. Declarative Infrastructure and OIDC CI/CD

The documented [`deploy/azure/main.bicep`](../../deploy/azure/main.bicep) foundation includes a user-assigned managed identity, Azure App Configuration with local authentication disabled (`disableLocalAuth: true`), and Azure Key Vault with RBAC authorization and purge protection. The listed least-privilege roles are `App Configuration Data Reader` (`516239f1-63e1-4d78-a4de-a74fb236a071`) and `Key Vault Secrets User` (`4633458b-17de-408a-b874-0445c86b69ea`). Verify the template before deployment.

Staging and production parameter files are [`parameters.staging.json`](../../deploy/azure/parameters.staging.json) and [`parameters.production.json`](../../deploy/azure/parameters.production.json); they are intended to contain no secrets or sensitive values.

Static local template validation:

```powershell
az bicep build --file deploy/azure/main.bicep --stdout > $null
```

The documented GitHub Actions workflow [`deploy-staging.yml`](../../.github/workflows/deploy-staging.yml) uses `azure/login@v2` with OIDC federation and no `AZURE_CLIENT_SECRET`. Workflow presence is not execution evidence.

## 6. Azure for Students customer authentication

The current Azure for Students subscription denies External ID customer tenants
because the `Microsoft.AzureActiveDirectory/ciamDirectories` resource resolves
to the `United States` logical location, outside the subscription policy. The
staging laboratory therefore uses the explicit `synthetic-password` provider
documented in [Synthetic auth staging](../operations/SYNTHETIC-AUTH-STAGING.md).
It uses Cosmos DB data-plane RBAC and short-lived revocable sessions. This is a
laboratory boundary and does not establish production identity readiness.

- [RBAC least-privilege matrix](../operations/RBAC-LEAST-PRIVILEGE-MATRIX.md)
- [Staging acceptance runbook](../operations/STAGING-ACCEPTANCE-RUNBOOK.md)
- [Production deployment runbook](../operations/PRODUCTION-DEPLOYMENT-RUNBOOK.md)
