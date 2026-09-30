# Contrato y Runbook de Aceptación en Azure Staging

> **Estado:** `SPECIFIED_STAGING_CONTRACT` · `CLOUD_UNVALIDATED`.
> **Objetivo:** Ejecutar la suite de aceptación E2E contra el entorno de Staging en Azure
> una vez que los recursos en la nube sean aprovisionados con autorización explícita.
> **Advertencia:** Ningún comando de este runbook se ejecuta automáticamente sin infraestructura real y aprobación humana.

---

## 1. Precondiciones Técnicas

1. El despliegue de infraestructura base (`deploy/azure/main.bicep`) concluyó exitosamente en el grupo de recursos `rg-aegisbank-staging`.
2. Las variables mínimas de bootstrap están presentes en el entorno o en el contenedor de Container Apps:
   - `AEGISBANK_ENV=staging`
   - `AZURE_APPCONFIG_ENDPOINT=https://<prefix>-staging-config.azconfig.io`
   - `AZURE_KEY_VAULT_URL=https://<prefix>-staging-kv.vault.azure.net/`
   - `AEGISBANK_SERVICEBUS_NAMESPACE=<prefix>-staging.servicebus.windows.net`
   - `AZURE_OPENAI_ENDPOINT=https://<prefix>-staging-ai.cognitiveservices.azure.com/`
3. La identidad asignada (`id-aegisbank-staging-workload`) tiene los roles RBAC correspondientes (ver [RBAC-LEAST-PRIVILEGE-MATRIX.md](RBAC-LEAST-PRIVILEGE-MATRIX.md)).
4. No existe ningún archivo `.env` o `.env.local` en el contenedor o entorno de ejecución.

---

## 2. Batería de Pruebas de Aceptación Staging (14 Comprobaciones)

| Paso | Categoría | Comprobación / Prueba | Criterio de Éxito / Evidencia Esperada |
| --- | --- | --- | --- |
| **STG-01** | **Salud de Proceso** | `GET /health/live` | Retorna `200 OK`, `{"status": "alive"}`. No consulta dependencias externas. |
| **STG-02** | **Disponibilidad** | `GET /health/ready` | Retorna `200 OK`, `{"status": "ready"}`. Valida inicialización de proveedores sin filtrar secretos. |
| **STG-03** | **App Configuration** | Conexión e hidratación con label `staging` | Lee `AegisBank:Agent:MaxRounds` y feature flags. Verificado con `DefaultAzureCredential`. Cero keys locales. |
| **STG-04** | **Identidad Entra ID** | Autenticación Passwordless | No existe client secret, connection string SAS ni token persistido en variables de entorno. |
| **STG-05** | **Key Vault Reference** | Resolución de referencia sintética | Resuelve `@Microsoft.KeyVault(SecretUri=...)` para un secreto sintético de prueba (`staging-test-secret`). |
| **STG-06** | **Foundry Cloud** | Inferencia de Chat Completions | Ejecuta inferencia de prueba hacia Azure OpenAI / Foundry (`phi-4-mini`) usando token bearer de Entra ID. |
| **STG-07** | **RAG Retrieval** | Recuperación y Citaciones | Consulta bancaria sobre términos autorizados (ej. mora / `DELINQUENT`). Retorna respuesta justificada con citas `[DOC-xxx]`. |
| **STG-08** | **Abstención RAG** | Fuera de Conocimiento Bancario | Consulta no cubierta por corpus o maliciosa. El agente debe abstenerse deterministamente sin alucinar políticas. |
| **STG-09** | **Own-Customer READ** | Lectura de cuentas de cliente propio | Consulta de saldo para `CUST-0001` con credenciales de `CUST-0001`. Retorna datos correctos. |
| **STG-10** | **Prevención de IDOR** | Intento de acceso cross-customer | Intento de `CUST-0001` de consultar o mutar `CUST-0002`. Denegado categóricamente con `OwnershipViolationError` (HTTP 403). |
| **STG-11** | **HITL Rechazo WRITE** | Rechazo explícito de mutación | Solicitud de creación de servicio bancario rechazada por el supervisor humano. Cero mutaciones en base de datos (`0 rows affected`). |
| **STG-12** | **HITL Aprobado WRITE** | Aprobación explícita de mutación | Solicitud autorizada por supervisor humano. Exactamente una mutación y emisión de evento a Service Bus. |
| **STG-13** | **Idempotencia y Retry** | Repetición de solicitud de escritura | Envío idéntico del mismo `idempotency_key`. Retorna resultado anterior sin duplicar operaciones ni cargos. |
| **STG-14** | **Redacción de Secretos** | Auditoría de Telemetría | Inspección de trazas y logs de staging. 0 tokens Entra, 0 connection strings, 0 passwords, 0 números de tarjeta sin máscara. |

---

## 3. Protocolo de Ejecución de Aceptación

```powershell
# Ejecución del suite de aceptación en modo staging (ejemplo con CLI)
$env:AEGISBANK_ENV = "staging"
$env:AZURE_APPCONFIG_ENDPOINT = "https://aegisbank-staging-config.azconfig.io"
$env:AZURE_KEY_VAULT_URL = "https://aegisbank-staging-kv.vault.azure.net/"
$env:AEGISBANK_SERVICEBUS_NAMESPACE = "aegisbank-staging.servicebus.windows.net"
$env:AZURE_OPENAI_ENDPOINT = "https://aegisbank-staging-ai.cognitiveservices.azure.com/"

# 1. Verificar guardias de configuración (debe pasar sin errores de loopback)
& .\.venv\Scripts\python.exe -c "from aegisbank_agent.configuration import validate_runtime_configuration, resolve_runtime_environment; validate_runtime_configuration(resolve_runtime_environment())"

# 2. Ejecutar suite E2E de validación de contratos
& .\.venv\Scripts\python.exe -m pytest ai/agent/tests/integration/banking/test_banking_routing_e2e.py -v
```

---

## 4. Criterio de Pase / Fallo

- **APROBADO (`STAGING_ACCEPTED`):** Los 14 puntos pasan con evidencia registrada, trazas W3C correlacionadas y cero regresiones.
- **BLOQUEADO (`STAGING_REJECTED`):** Cualquier falla de IDOR, fuga de secretos en logs, o bypass de HITL bloquea inmediatamente cualquier promoción a Producción y fuerza el procedimiento de Rollback.
