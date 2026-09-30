# Configuración cloud e identidad de workload

> **Estado:** `AZURE_DEPLOYMENT_PARTIALLY_PREPARED` · `CLOUD_UNVALIDATED`.
> La aplicación sigue siendo un laboratorio bancario sintético, no un banco real.

## Decisión operativa

La frontera canónica es `aegisbank_agent.configuration`. Se mantiene el contrato
existente `ConfigurationProvider` para valores no secretos y `SecretProvider`
para secretos inevitables. Ningún runtime local requiere Azure.

```text
local / test / development
  proceso -> .env.local opcional -> emuladores o proveedores sintéticos

staging / production
  bootstrap mínimo -> Managed Identity -> App Configuration -> Key Vault references
```

`AEGISBANK_ENV` acepta `local`, `test`, `development`, `staging` y
`production`. Los valores históricos `container` y `kubernetes-local` se
conservan como alias explícitos de `local` para no romper Compose ni Kubernetes
de laboratorio. Cualquier otro valor falla, nunca se interpreta silenciosamente
como local.

## Precedencia y clasificación

| Clase | Ejemplos | Regla |
| --- | --- | --- |
| `BOOTSTRAP_ENV` | `AEGISBANK_ENV`, `AZURE_APPCONFIG_ENDPOINT`, `AZURE_KEY_VAULT_URL` | Solo localiza la fuente de configuración y no contiene secretos. |
| `APP_CONFIGURATION` | límites del Agent, timeout, URLs no secretas, nombres de colas y modelos | Se lee con `DefaultAzureCredential` y label del entorno. |
| `KEY_VAULT` | credencial externa inevitable | Se resuelve con `AzureKeyVaultSecretProvider`; nunca se registra el valor. |
| `MANAGED_IDENTITY_ELIMINATES_SECRET` | App Configuration, Key Vault, Service Bus, Cosmos | Usar token Entra antes que connection string o key. |
| `LOCAL_ONLY` | Foundry Local, SQLite, emuladores Service Bus/Cosmos/App Config | Prohibido en staging y producción. |
| `CODE_CONSTANT` | formatos de eventos, defaults no sensibles | No debe transportar configuración por entorno. |

En cloud, el proveedor carga primero valores sin label y después el label del
entorno: la capa específica reemplaza el valor común. App Configuration usa
`DefaultAzureCredential` y usa la misma credencial para referencias de Key
Vault. El refresh es dirigido por llamadas al proveedor; no se creó un hilo de
background.

## Guardias de producción

`validate_runtime_configuration` rechaza en staging/producción emulador de App
Configuration, Service Bus Emulator, endpoints loopback de dependencias externas
y bootstrap incompleto de producción. Los errores muestran solo el nombre de la
clave, nunca su valor. `SecretProvider` no puede degradar a secretos sintéticos
en cloud: requiere `AZURE_KEY_VAULT_URL` HTTPS.

`.env.local` es la única convención dotenv soportada para desarrollo. Está
ignorado. Los procesos cloud no lo cargan; no existe ni se requiere
`.env.production`.

## Matriz passwordless

| Dependencia | Estado de código | Límite antes de staging |
| --- | --- | --- |
| App Configuration | `PASSWORDLESS_IMPLEMENTED` | Asignar `App Configuration Data Reader`. |
| Key Vault | `PASSWORDLESS_IMPLEMENTED` | Asignar `Key Vault Secrets User`; probar referencias y rotación. |
| Service Bus | `PASSWORDLESS_ADAPTER_READY` | Configurar namespace y `Azure Service Bus Data Sender/Receiver` según el flujo. |
| Cosmos DB NoSQL | `PASSWORDLESS_ADAPTER_READY` | Conceder rol de datos mínimo y probar particiones/TTL/change feed. |
| PostgreSQL | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | El checkout usa DSN/psycopg, sin adaptador de token Entra seguro. |
| Redis | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | El checkout usa URL redis; validar soporte del servicio y cliente elegido. |
| Foundry/LLM cloud | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Solo existe Foundry Local; falta provider cloud separado y prueba de deployment. |
| Azure Monitor | `PASSWORDLESS_REQUIRES_FUTURE_CLOUD_VALIDATION` | Solo existe telemetría in-memory. |

El Core Banking local sigue siendo un mock con SQLite. El Agent no obtiene acceso
directo a su base de datos: cualquier integración cloud debe mantener el contrato
HTTP, propiedad de recursos, trazas y aprobación humana para escrituras.

## RBAC mínimo previsto

| Principal | Scope | Rol |
| --- | --- | --- |
| Identidad asignada de workload | App Configuration del entorno | App Configuration Data Reader |
| Identidad asignada de workload | Key Vault del entorno | Key Vault Secrets User |
| Identidad de Agent/Functions | Namespace o entidad Service Bus | Data Sender/Receiver mínimo por flujo |
| Identidad de Agent/Functions | Cosmos DB NoSQL | Rol de datos mínimo definido por operación |

Las asignaciones de Service Bus y Cosmos no se codifican todavía porque sus
recursos, topología y permisos de consumidor no están aprobados ni validados.

## Infraestructura declarativa y CI

[`deploy/azure/main.bicep`](../../deploy/azure/main.bicep) prepara una identidad
asignada, App Configuration con autenticación local deshabilitada, Key Vault con
RBAC y protección contra purge, y dos asignaciones RBAC. No aprovisiona Container
Apps, datos, colas ni modelos. El workflow
[`azure-validate.yml`](../../.github/workflows/azure-validate.yml) solo compila
Bicep; declara `id-token: write` para un workflow de despliegue futuro aprobado,
pero no inicia sesión, no crea recursos y no consulta secretos.

## Evidencia local requerida

```powershell
az bicep build --file deploy/azure/main.bicep --stdout > $null
.\.venv\Scripts\python.exe -m pytest -c ai/agent/pyproject.toml ai/agent/tests/unit/configuration ai/agent/tests/unit/reliability/test_azure_identity_adapters.py -q
```

La compilación no reemplaza una ejecución contra Azure. Antes de desplegar a
staging se debe revisar [el runbook](../operations/AZURE-STAGING-RUNBOOK.md).
