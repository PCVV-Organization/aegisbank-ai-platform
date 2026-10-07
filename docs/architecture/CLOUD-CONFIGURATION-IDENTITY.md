# Configuración Cloud, Identidad de Workload y Fronteras de Despliegue

> **Estado:** `AZURE_DEPLOYMENT_PREPARED` · `CLOUD_UNVALIDATED`.
> **Misión:** AegisBank AI Platform es un laboratorio educativo de banca con IA seguro y reproducible; no es un banco comercial ni procesa transacciones financieras reales.

---

## Contrato de entrega: Local-first antes de Azure

El orden de entrega es obligatorio: **local reproducible → contrato cloud versionado → staging autorizado → evidencia de aceptación**. Ninguna configuración, imagen, plantilla Bicep o workflow declara por sí mismo una ejecución cloud satisfactoria.

- El entorno local es la referencia de desarrollo, regresión y depuración con datos sintéticos.
- Azure reutiliza los mismos contratos de aplicación; solo reemplaza adaptadores de infraestructura.
- Staging exige autorización explícita para aprovisionar recursos y evidencia de sus pruebas.
- Producción solo puede promover el artefacto inmutable aceptado en staging.

## 1. Decisión Operativa y Modelo de Doble Vía (Local-First vs Cloud)

La frontera canónica de configuración reside en `aegisbank_agent.configuration`. Se preserva de forma estricta e inquebrantable el entorno local existente:

```text
LOCAL (SQLite / Foundry Local / Redis local / pgvector Docker / emuladores)
  │
  │ MISMOS CONTRATOS, INTERFACES Y COMPORTAMIENTO DETERMINISTA
  ▼
PRODUCTION (Managed Identity / App Configuration / Key Vault / Servicios Gestionados Azure)
```

### Precedencia de Configuración

- **LOCAL:**
  `Overrides explícitos de test > Variables de proceso > .env.local opcional (desarrollo) > Proveedor local / Emuladores`
- **AZURE (Staging / Producción):**
  `Bootstrap mínimo de contenedor > Azure App Configuration (vía Entra ID) > Referencias Key Vault para secretos > Constantes de código`

`AEGISBANK_ENV` acepta exclusivamente: `local`, `test`, `development`, `staging`, `production` (y los alias históricos locales `container` y `kubernetes-local`). Cualquier valor desconocido o inválido **falla cerrado** de forma inmediata (`EnvironmentSelectionError`).

---

## 2. Tabla de Verdad de Capacidades: LOCAL vs AZURE TARGET

Cada celda cloud se clasifica rigurosamente de forma individual sin afirmaciones genéricas ni prematuras:

| Capacidad | LOCAL (Preservado 100%) | AZURE TARGET | Estado Cloud | Límite Técnico Antes de Despliegue Real |
| --- | --- | --- | --- | --- |
| **LLM Inferencia** | Foundry Local (`http://127.0.0.1:5272/v1`, `phi-4-mini`) | Azure AI Foundry / Azure OpenAI (`AzureFoundryProvider`) | `PASSWORDLESS_ADAPTER_READY` | Requiere recurso Azure OpenAI aprovisionado y RBAC `Cognitive Services OpenAI User`. |
| **Core Banking** | FastAPI mock local con SQLite embebido | Frontera externa / Microservicio hospedado | `DOCUMENTED_ONLY` | En staging se mantiene el mock aislado. El Agent nunca accede directamente a la BD de Core Banking. |
| **RAG Embeddings / Vector** | PostgreSQL + pgvector Docker (`vector(32)`, HNSW) | Azure Database for PostgreSQL Flexible Server | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Conexión actual vía psycopg DSN. Autenticación Entra token para PostgreSQL requiere prueba cloud. |
| **Caché & Vector Search** | Docker Redis local (standalone) | Azure Managed Redis | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Redis local preservado. Autenticación Entra para Redis requiere configuración específica de Azure Managed Redis. |
| **Mensajería & Eventos** | Azure Service Bus Emulator local (AMQP) | Azure Service Bus Namespace | `PASSWORDLESS_ADAPTER_READY` | `AzureServiceBusMessageBus` implementa `DefaultAzureCredential` passwordless cuando se provee el namespace. |
| **Almacenamiento NoSQL** | Azure Cosmos DB Emulator (puerto 8081) | Azure Cosmos DB NoSQL | `PASSWORDLESS_ADAPTER_READY` | `CosmosRepository` implementa `DefaultAzureCredential` passwordless en entornos cloud. |
| **Configuración No Secreta** | App Configuration Emulator / Env fallback | Azure App Configuration (con label) | `PASSWORDLESS_IMPLEMENTED` | `AppConfigurationCloudProvider` con `DefaultAzureCredential` e hidratación sin label + label del entorno. |
| **Secretos Inevitables** | `LocalSyntheticSecretProvider` (in-memory) | Azure Key Vault (`AzureKeyVaultSecretProvider`) | `PASSWORDLESS_IMPLEMENTED` | `KeyVaultReferenceResolver` resuelve referencias `@Microsoft.KeyVault(...)` usando `DefaultAzureCredential`. |
| **Identidad / Autenticación** | Confianza local de red / synthetic | User-Assigned Managed Identity (`Microsoft Entra ID`) | `PASSWORDLESS_IMPLEMENTED` | Declarada en Bicep con roles de privilegio mínimo asignados a la identidad del workload. |
| **Telemetría & Trazas** | OpenTelemetry In-Memory / Consola local | Azure Monitor / Application Insights | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Instrumentación OTel neutra y W3C traceparent listos. Exporter Azure Monitor requiere validación en staging. |

---

## 3. Política Estricta de Secretos y `.env`

1. **Sin `.env.production`:** Queda categóricamente prohibido crear o requerir archivos `.env.production` en el repositorio o en contenedores cloud.
2. **`.env.local` solo para Desarrollo:** Es la única convención dotenv permitida para desarrolladores locales. Está listada en `.gitignore` y `.dockerignore`.
3. **Guardia Fail-Closed:** `load_local_dotenv()` solo considera `.env.local` cuando el proceso ya está en un entorno local. En `staging` y `production` no carga archivos. `foundry_local.py` tampoco carga dotenv al importarse.
4. **Validación de Producción (`validate_runtime_configuration`):**
   - Rechaza emuladores de App Configuration, Service Bus y Cosmos.
   - Rechaza endpoints loopback (`127.0.0.1`, `localhost`).
   - Rechaza claves por defecto de emulador.
   - Rechaza flags de `DEBUG` o bypass de autenticación.
   - Exige endpoints HTTPS válidos para App Configuration y Key Vault.
   - **Nunca imprime valores de secretos o endpoints en los mensajes de error.**

---

## 4. Infraestructura Declarativa (IaC) y CI/CD OIDC

1. **Plantilla Bicep:** [`deploy/azure/main.bicep`](../../deploy/azure/main.bicep) define la fundación completa de identidad y configuración:
   - Identidad gestionada asignada por usuario.
   - Almacén de Azure App Configuration con autenticación local desactivada (`disableLocalAuth: true`).
   - Azure Key Vault con autorización RBAC estricta (`enableRbacAuthorization: true`) y purge protection.
   - Asignaciones de roles de mínimo privilegio:
     - `App Configuration Data Reader` (`516239f1-63e1-4d78-a4de-a74fb236a071`)
     - `Key Vault Secrets User` (`4633458b-17de-408a-b874-0445c86b69ea`)
2. **Parámetros de Despliegue:**
   - [`deploy/azure/parameters.staging.json`](../../deploy/azure/parameters.staging.json)
   - [`deploy/azure/parameters.production.json`](../../deploy/azure/parameters.production.json)
   (Ambos declarativos, sin secretos ni valores sensibles).
3. **Validación Estática Local:**
   ```powershell
   az bicep build --file deploy/azure/main.bicep --stdout > $null
   ```
4. **CI/CD OIDC:** Pipeline de GitHub Actions ([`deploy-staging.yml`](../../.github/workflows/deploy-staging.yml)) configurado con `azure/login@v2` para federación OIDC passwordless (sin `AZURE_CLIENT_SECRET`).

---

## 5. Documentación de Operaciones Asociada

- [Matriz de Privilegio Mínimo RBAC](../operations/RBAC-LEAST-PRIVILEGE-MATRIX.md)
- [Runbook y Contrato de Aceptación Staging](../operations/STAGING-ACCEPTANCE-RUNBOOK.md)
- [Runbook de Operaciones y Promoción a Producción](../operations/PRODUCTION-DEPLOYMENT-RUNBOOK.md)
