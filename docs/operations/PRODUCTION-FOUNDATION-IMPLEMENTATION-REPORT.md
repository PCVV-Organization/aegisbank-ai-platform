# Informe de Implementación de la Base Productiva: Azure Staging Ready

> **Estado del Milestone:** `AZURE_STAGING_READY`
> **Clasificación Explícita:** `AZURE_STAGING_READY` (NO `REAL_BANK_PRODUCTION_READY` ni `PRODUCTION_READY`).
> **Ámbito:** Repositorio de aplicación `C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`.
> **Fecha de Cierre:** 2026-09-30.
> **Garantía:** Cero regresión local (`LOCAL_REGRESSION=0`), emuladores y flujo de desarrollo preservados íntegramente. Recursos Azure no aprovisionados (`AZURE_DEPLOYED=NO`, `CLOUD_VALIDATED=NO`).

---

## 1. Arquitectura Dual: LOCAL vs. STAGING vs. PRODUCCIÓN

| Capacidad / Componente | Entorno LOCAL | Entorno STAGING | Entorno PRODUCCIÓN | Clasificación de Implementación |
|---|---|---|---|---|
| **Ambiente y Guardias** | `local` / `development` / `test` | `staging` (fail-closed) | `production` (fail-closed) | `IMPLEMENTED_CLOUD_PATH` |
| **Dotenv Policy** | Carga `.env.local` / `.env` opcional | Bloqueo absoluto de `.env` | Bloqueo absoluto de `.env` | `IMPLEMENTED_CLOUD_PATH` |
| **Configuración** | `EnvironmentConfigurationProvider` / Emulator | `AppConfigurationCloudProvider` (HTTPS) | `AppConfigurationCloudProvider` (HTTPS) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Secretos** | `LocalSyntheticSecretProvider` | `AzureKeyVaultSecretProvider` (RBAC) | `AzureKeyVaultSecretProvider` (RBAC) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Identidad Azure** | `DefaultAzureCredential` (desarrollo cloud) | `ManagedIdentityCredential` (UAMI) | `ManagedIdentityCredential` (UAMI) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Service Bus** | Emulador local / Cadena de conexión | Passwordless (`FQDN` + Entra ID) | Passwordless (`FQDN` + Entra ID) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Cosmos DB** | Emulador local (`COSMOS_KEY`) | Passwordless (`TokenCredential`) | Passwordless (`TokenCredential`) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **PostgreSQL Flexible** | DSN local (`psycopg`) | Token dinámico Entra ID + TLS | Token dinámico Entra ID + TLS | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Redis** | `redis://127.0.0.1:6379/0` | Seam Azure Managed Redis (TLS) | Seam Azure Managed Redis (TLS) | `PASSWORDLESS_REDIS=PARTIAL` (`READY_TO_VALIDATE`) |
| **Proveedor LLM** | `FoundryLocalProvider` (host) | `AzureFoundryProvider` (Entra ID) | `AzureFoundryProvider` (Entra ID) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Host del Agente** | CLI + MCP stdio + API local | Hosted FastAPI (`/api/v1/agent/run`) | Hosted FastAPI (`/api/v1/agent/run`) | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Autenticación Agente** | Identidad sintética (`CUST-0001`) | Bearer Token obligatorio | Bearer Token obligatorio | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Frontera Core Banking** | DB SQLite local o HTTP API | Exclusivamente HTTP API con auth | Exclusivamente HTTP API con auth | `IMPLEMENTED_CLOUD_PATH` (`READY_TO_VALIDATE`) |
| **Acceso Directo a DB** | Permitido para tests unitarios locales | **BLOQUEADO** (falla cerrado) | **BLOQUEADO** (falla cerrado) | `IMPLEMENTED_CLOUD_PATH` |
| **Infraestructura IaC** | `docker-compose.yml` | Bicep (`Container Apps`) | Bicep (`Container Apps`) | `IMPLEMENTED_CLOUD_PATH` (`VALIDATED_STATICALLY`) |
| **Pipeline CI/CD** | Tests locales + Fast Quality Gate | GitHub Actions OIDC (manual) | Deshabilitado / Manual | `IMPLEMENTED_CLOUD_PATH` (`CONFIGURED_NOT_EXECUTED`) |

---

## 2. Catálogo de Claves de App Configuration

En entornos de Azure Staging y Producción, la configuración no secreta se obtiene de Azure App Configuration mediante `AppConfigurationCloudProvider` filtrando por label de entorno (`staging` o `production`):

| Clave | Tipo | Valor / Formato en Staging | Propósito |
|---|---|---|---|
| `aegisbank:agent:model_alias` | String | `phi-4-mini` | Nombre del despliegue de modelo en Azure AI Foundry. |
| `aegisbank:agent:max_tool_rounds` | Integer | `3` | Límite determinista de iteraciones de herramientas. |
| `aegisbank:agent:timeout_seconds` | Float | `45.0` | Timeout máximo para inferencia y orquestación. |
| `aegisbank:core_banking:base_url` | String (URL) | `http://aegisbank-staging-core-banking` | Endpoint interno de la API HTTP de Mock Core Banking. |
| `aegisbank:servicebus:fqdn` | String (FQDN) | `aegisbank-staging-sb.servicebus.windows.net` | Fully Qualified Namespace de Azure Service Bus. |
| `aegisbank:servicebus:queue` | String | `aegisbank-events` | Nombre de la cola de eventos y solicitudes bancarias. |
| `aegisbank:cosmos:endpoint` | String (URL) | `https://aegisbank-staging-cosmos.documents.azure.com:443/` | Endpoint de la cuenta NoSQL de Cosmos DB. |
| `aegisbank:cosmos:database` | String | `aegisbank-db` | Base de datos particionada para sesiones y eventos. |
| `aegisbank:cosmos:container` | String | `agent-sessions` | Contenedor de persistencia del estado del agente. |
| `aegisbank:rag:postgres_host` | String | `aegisbank-staging-psql.postgres.database.azure.com` | Host de Azure Database for PostgreSQL Flexible Server. |
| `aegisbank:rag:postgres_db` | String | `aegisbank_rag` | Base de datos vectorial con extensión pgvector. |
| `aegisbank:rag:postgres_user` | String | `aegis_workload_identity` | Principal de base de datos vinculado a la Managed Identity. |
| `aegisbank:rag:redis_host` | String | `aegisbank-staging-cache.redis.cache.windows.net` | Host de Azure Managed Redis con TLS habilitado. |
| `aegisbank:rag:redis_port` | Integer | `6380` | Puerto seguro SSL/TLS de Azure Managed Redis. |
| `aegisbank:observability:service_name` | String | `aegisbank-agent` | Nombre de servicio en trazas OpenTelemetry. |
| `aegisbank:observability:sample_ratio` | Float | `1.0` | Razón de muestreo de trazas distribuidas. |

---

## 3. Catálogo de Nombres de Secretos en Key Vault

> **Regla Invariable:** No se documentan ni registran valores secretos reales ni sintéticos en este catálogo. Solo se especifican los identificadores de secretos requeridos por el resolvedor `KeyVaultReferenceResolver`:

| Nombre del Secreto en Key Vault | Versión | Propósito Operativo |
|---|---|---|
| `aegisbank-jwt-signing-secret` | Opcional | Clave simétrica o pública para validación de tokens de prueba de staging. |
| `aegisbank-external-partner-key` | Opcional | Clave de autenticación para integraciones de prueba con burós sintéticos. |

---

## 4. Matriz de Roles y Asignaciones RBAC

Definida declarativamente en [deploy/azure/main.bicep](file:///C:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/deploy/azure/main.bicep):

| Recurso | Rol RBAC | ID de Definición | Identidad Asignada |
|---|---|---|---|
| **App Configuration** | `App Configuration Data Reader` | `516239f1-63e1-4d78-a4de-a74fb236a071` | `id-aegisbank-staging-workload` |
| **Key Vault** | `Key Vault Secrets User` | `4633458b-17de-408a-b874-0445c86b69ea` | `id-aegisbank-staging-workload` |
| **Service Bus** | `Azure Service Bus Data Sender` | `69a216fc-b8fb-44d8-bc22-1f3c2cd27a39` | `id-aegisbank-staging-workload` |
| **Service Bus** | `Azure Service Bus Data Receiver` | `4f6d3a01-5356-424a-9274-02e06e644125` | `id-aegisbank-staging-workload` |
| **Azure AI Foundry** | `Cognitive Services OpenAI User` | `5e6ce059-de30-45e8-b8e7-e898950d9990` | `id-aegisbank-staging-workload` |

---

## 5. Procedimientos Operativos y Runbooks Vinculados

- [Guía de Diagnóstico de Identidad](IDENTITY-TROUBLESHOOTING.md) — resolución de errores IMDS, RBAC 403, audiencias Entra ID y certificados.
- [Matriz de Mínimo Privilegio RBAC](RBAC-LEAST-PRIVILEGE-MATRIX.md) — análisis de seguridad de roles y revocación de emergencia.
- [Runbook de Aceptación en Staging](STAGING-ACCEPTANCE-RUNBOOK.md) — batería de pruebas E2E a ejecutar tras el aprovisionamiento de staging.
- [Runbook de Despliegue y Rollback en Producción](PRODUCTION-DEPLOYMENT-RUNBOOK.md) — procedimiento de promoción inmutable y reversión de revisiones en Container Apps.

---

## 6. Evidencia de Validación de Cierre del Milestone

1. **Pruebas Automatizadas:** 55 pruebas unitarias de configuración, guardias de producción, API del agente, base de datos bloqueada, Key Vault versionado, fábricas de PostgreSQL y Redis ejecutadas y aprobadas (`55 passed in 3.09s`).
2. **Pyright Whole-Source:** `0 errors, 0 warnings, 0 informations`.
3. **Ruff Check y Format:** Aprobados sin infracciones ni advertencias de formato (`All checks passed! 437 files formatted`).
4. **Validación Bicep:** `az bicep build --file deploy/azure/main.bicep` compila limpiamente sin advertencias de sintaxis.
5. **Cero Secretos en Git:** Verificación de archivos staged sin tokens, claves privadas, ni connection strings.
