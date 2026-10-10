# Production Foundation Implementation Report: Azure Staging Ready (2026-09-30 Snapshot)

> **Recorded milestone status:** `AZURE_STAGING_READY` means the repository's cloud implementation path was reported as prepared for validation. It does **not** mean `REAL_BANK_PRODUCTION_READY` or `PRODUCTION_READY`.
> **Repository recorded by the report:** `aegisbank-ai-platform`, `C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`.
> **Critical limitation:** The report explicitly recorded `AZURE_DEPLOYED=NO` and `CLOUD_VALIDATED=NO`; Azure resources were not provisioned. All test and static-validation results below are historical results from 2026-09-30, not rerun in this change.

## 1. Recorded Local/Staging/Production Design

| Capability | Local | Staging target | Production target | Recorded implementation classification |
|---|---|---|---|---|
| Environment guards | `local` / `development` / `test` | `staging`, fail-closed | `production`, fail-closed | `IMPLEMENTED_CLOUD_PATH` |
| Dotenv | Optional `.env.local` / `.env` | Reject `.env` | Reject `.env` | `IMPLEMENTED_CLOUD_PATH` |
| Configuration | `EnvironmentConfigurationProvider` / emulator | HTTPS `AppConfigurationCloudProvider` | HTTPS `AppConfigurationCloudProvider` | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Secrets | `LocalSyntheticSecretProvider` | `AzureKeyVaultSecretProvider` (RBAC) | `AzureKeyVaultSecretProvider` (RBAC) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Azure identity | `DefaultAzureCredential` for cloud development | `ManagedIdentityCredential` (UAMI) | `ManagedIdentityCredential` (UAMI) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Service Bus | Local emulator / connection string | Passwordless FQDN + Entra ID | Passwordless FQDN + Entra ID | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Cosmos DB | Local emulator (`COSMOS_KEY`) | Passwordless `TokenCredential` | Passwordless `TokenCredential` | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| PostgreSQL Flexible Server | Local psycopg DSN | Dynamic Entra token + TLS | Dynamic Entra token + TLS | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Redis | `redis://127.0.0.1:6379/0` | Azure Managed Redis seam (TLS) | Azure Managed Redis seam (TLS) | `PASSWORDLESS_REDIS=PARTIAL` (`READY_TO_VALIDATE`) |
| LLM provider | Host-based `FoundryLocalProvider` | `AzureFoundryProvider` (Entra ID) | `AzureFoundryProvider` (Entra ID) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Agent host | CLI + MCP stdio + local API | Hosted FastAPI `/api/v1/agent/run` | Hosted FastAPI `/api/v1/agent/run` | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Agent authentication | Synthetic identity (`CUST-0001`) | Bearer token required | Bearer token required | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Core Banking boundary | Local SQLite or HTTP API | HTTP API with authentication only | HTTP API with authentication only | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| Direct database access | Allowed in local unit tests | Blocked, fail-closed | Blocked, fail-closed | `IMPLEMENTED_CLOUD_PATH` |
| Infrastructure as code | `docker-compose.yml` | Bicep / Container Apps | Bicep / Container Apps | `IMPLEMENTED_CLOUD_PATH` (`VALIDATED_STATICALLY`) |
| CI/CD | Local tests + Fast Quality Gate | Manual GitHub Actions OIDC | Disabled/manual | `IMPLEMENTED_CLOUD_PATH` (`CONFIGURED_NOT_EXECUTED`) |

These are claims recorded by the 2026-09-30 report; verify current source and tests before treating any adapter path as implemented today.

## 2. Recorded App Configuration Key Catalog

The report described these as non-secret settings for `AppConfigurationCloudProvider`, selected by `staging` or `production` label. Values are examples from the dated report, not validated live configuration.

| Key | Type | Recorded staging example | Purpose |
|---|---|---|---|
| `aegisbank:agent:model_alias` | String | `phi-4-mini` | Azure AI Foundry deployment alias. |
| `aegisbank:agent:max_tool_rounds` | Integer | `3` | Deterministic maximum tool iterations. |
| `aegisbank:agent:timeout_seconds` | Float | `45.0` | Maximum inference/orchestration timeout. |
| `aegisbank:core_banking:base_url` | URL | `http://aegisbank-staging-core-banking` | Internal Mock Core Banking HTTP API endpoint. |
| `aegisbank:servicebus:fqdn` | FQDN | `aegisbank-staging-sb.servicebus.windows.net` | Service Bus namespace. |
| `aegisbank:servicebus:queue` | String | `aegisbank-events` | Event/service-request queue name. |
| `aegisbank:cosmos:endpoint` | URL | `https://aegisbank-staging-cosmos.documents.azure.com:443/` | Cosmos DB NoSQL account endpoint. |
| `aegisbank:cosmos:database` | String | `aegisbank-db` | Database for sessions and events. |
| `aegisbank:cosmos:container` | String | `agent-sessions` | Agent-state container. |
| `aegisbank:rag:postgres_host` | String | `aegisbank-staging-psql.postgres.database.azure.com` | PostgreSQL Flexible Server host. |
| `aegisbank:rag:postgres_db` | String | `aegisbank_rag` | Vector database with pgvector. |
| `aegisbank:rag:postgres_user` | String | `aegis_workload_identity` | Database principal linked to managed identity. |
| `aegisbank:rag:redis_host` | String | `aegisbank-staging-cache.redis.cache.windows.net` | Azure Managed Redis host with TLS. |
| `aegisbank:rag:redis_port` | Integer | `6380` | Secure Redis port. |
| `aegisbank:observability:service_name` | String | `aegisbank-agent` | OpenTelemetry service name. |
| `aegisbank:observability:sample_ratio` | Float | `1.0` | Distributed trace sampling ratio. |

## 3. Key Vault Secret Names (No Values)

The report states that no secret values—real or synthetic—belong in this catalog. It listed these optional identifiers for `KeyVaultReferenceResolver`:

| Secret name | Purpose |
|---|---|
| `aegisbank-jwt-signing-secret` | Signing/validation key for staging test tokens. |
| `aegisbank-external-partner-key` | Authentication for synthetic-bureau integration tests. |

These names do not prove that secrets exist in a vault.

## 4. Recorded RBAC Assignments

The report says these roles were declared in [`deploy/azure/main.bicep`](../../deploy/azure/main.bicep). Declaration does not prove assignment in Azure.

| Resource | Role | Role definition ID | Assigned identity |
|---|---|---|---|
| App Configuration | `App Configuration Data Reader` | `516239f1-63e1-4d78-a4de-a74fb236a071` | `id-aegisbank-staging-workload` |
| Key Vault | `Key Vault Secrets User` | `4633458b-17de-408a-b874-0445c86b69ea` | `id-aegisbank-staging-workload` |
| Service Bus | `Azure Service Bus Data Sender` | `69a216fc-b8fb-44d8-bc22-1f3c2cd27a39` | `id-aegisbank-staging-workload` |
| Service Bus | `Azure Service Bus Data Receiver` | `4f6d3a01-b2a5-4e24-9d14-70f80761a4c6` | `id-aegisbank-staging-workload` |
| Azure AI Foundry | `Cognitive Services OpenAI User` | `5e6ce059-de30-45e8-b8e7-e898950d9990` | `id-aegisbank-staging-workload` |

Verify role IDs and scope against current Azure sources before use; this translation preserves the original report and does not validate them.

## 5. Linked Operational Guides

- [Identity troubleshooting](IDENTITY-TROUBLESHOOTING.md)
- [RBAC least-privilege matrix](RBAC-LEAST-PRIVILEGE-MATRIX.md)
- [Staging acceptance runbook](STAGING-ACCEPTANCE-RUNBOOK.md)
- [Production deployment runbook](PRODUCTION-DEPLOYMENT-RUNBOOK.md)

## 6. Historical Milestone Validation Evidence

The source report recorded the following results on 2026-09-30:

1. 55 configuration, production-guard, agent API, blocked-database, versioned-Key-Vault, PostgreSQL-factory, and Redis-factory unit tests passed (`55 passed in 3.09s`).
2. Whole-source Pyright: `0 errors, 0 warnings, 0 informations`.
3. Ruff check and format passed; the report stated `437 files formatted`.
4. `az bicep build --file deploy/azure/main.bicep` completed without reported syntax warnings.
5. A staged-file review reported no tokens, private keys, or connection strings.

These results were not rerun during translation and do not establish that Azure was provisioned, deployed, or cloud-validated.
