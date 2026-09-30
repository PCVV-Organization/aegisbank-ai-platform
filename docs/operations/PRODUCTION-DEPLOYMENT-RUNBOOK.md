# Runbook de Despliegue, Operación y Promoción a Producción

> **Clasificación:** `AZURE_DEPLOYMENT_PREPARED` · `CLOUD_UNVALIDATED`.
> **Alcance:** Procedimientos de despliegue, promoción inmutable, rotación, incidentes y rollback.
> **Límite Canónico:** AegisBank AI Platform es un laboratorio educativo de banca con IA; no es un banco comercial ni procesa dinero real.

---

## 1. Prerrequisitos de Plataforma

1. **Aceptación Previa en Staging:** El artefacto exacto (digest de imagen de contenedor) debe haber obtenido `STAGING_ACCEPTED` documentado bajo el [STAGING-ACCEPTANCE-RUNBOOK.md](STAGING-ACCEPTANCE-RUNBOOK.md).
2. **Grupo de Recursos Aislado:** `rg-aegisbank-production` independiente en región autorizada.
3. **Infraestructura Base Desplegada:** `deploy/azure/main.bicep` con `parameters.production.json`.
4. **Identidad Gestionada Asignada:** `id-aegisbank-production-workload` provisionada con asignaciones RBAC mínimas (ver [RBAC-LEAST-PRIVILEGE-MATRIX.md](RBAC-LEAST-PRIVILEGE-MATRIX.md)).

---

## 2. Variables Mínimas de Bootstrap (Runtime Container Apps)

En el entorno de producción en Container Apps, se configuran **únicamente** variables no secretas para localizar los recursos:

```bash
AEGISBANK_ENV=production
AEGISBANK_CONFIG_LABEL=production
AZURE_APPCONFIG_ENDPOINT=https://aegisbank-production-config.azconfig.io
AZURE_KEY_VAULT_URL=https://aegisbank-production-kv.vault.azure.net/
AEGISBANK_SERVICEBUS_NAMESPACE=aegisbank-production.servicebus.windows.net
AZURE_OPENAI_ENDPOINT=https://aegisbank-production-ai.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=phi-4-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

> **REGLA DE ORO:** Ningún secreto, password, token o clave de acceso se inyecta en variables de entorno. Todo acceso a recursos Azure se realiza mediante Entra ID (`DefaultAzureCredential`).

---

## 3. Catálogo de Claves en Azure App Configuration

Las siguientes configuraciones se gestionan centralizadamente en App Configuration con label `production`:

| Clave | Tipo | Valor Típico | Descripción |
| --- | --- | --- | --- |
| `AegisBank:Agent:MaxRounds` | int | `3` | Límite máximo de rondas de herramientas por invocación. |
| `AegisBank:Agent:TimeoutSeconds` | float | `45.0` | Timeout de invocación del agente. |
| `AegisBank:RAG:Retriever` | string | `hybrid_rrf` | Estrategia de recuperación canónica. |
| `AegisBank:RAG:TopK` | int | `3` | Documentos máximos retornados por el corpus. |
| `AegisBank:RAG:CacheTtlSeconds` | int | `3600` | TTL para caché de embeddings/documentos en Redis. |
| `AegisBank:CoreBanking:TimeoutSeconds` | float | `5.0` | Timeout para llamadas al servicio de Core Banking. |
| `AegisBank:Reliability:RetryCount` | int | `3` | Intentos acotados para fallos transitorios. |
| `AegisBank:Reliability:CircuitBreakerThreshold` | int | `5` | Fallos consecutivos antes de abrir el disyuntor. |
| `AegisBank:Observability:LogLevel` | string | `INFO` | Nivel mínimo de logging estructurado. |
| `AegisBank:Observability:SamplingRatio` | float | `0.1` | Muestreo de trazas distribuidas OpenTelemetry. |

---

## 4. Nombres de Secretos en Azure Key Vault (SIN VALORES)

Key Vault almacena **únicamente** secretos externos inevitables que no admiten Entra ID:

| Nombre del Secreto en Key Vault | Propósito | Formato |
| --- | --- | --- |
| `external-sms-gateway-api-key` | API Key para gateway de SMS / notificaciones OTP externo | Token alfanumérico |
| `legacy-vendor-webhook-signing-key` | Llave HMAC para verificar webhooks de proveedores externos | Hexadecimal 256 bits |

*(App Configuration almacena referencias `@Microsoft.KeyVault(SecretUri=...)` hacia estos nombres).*

---

## 5. Promoción Inmutable Staging -> Producción

1. **Inmutabilidad Absoluta:**
   - La imagen de producción **no se recompila**.
   - Se promueve la imagen exactamente referenciada por digest: `aegisbank-agent@sha256:...`.
2. **Actualización de Container App:**
   ```bash
   az containerapp update \
     --name ca-aegisbank-agent \
     --resource-group rg-aegisbank-production \
     --image "aegisbankacr.azurecr.io/aegisbank-agent@sha256:<ACCEPTED_DIGEST>"
   ```
3. **Verificación de Liveness y Readiness:**
   ```bash
   curl -f https://<production-endpoint>/health/live
   curl -f https://<production-endpoint>/health/ready
   ```

---

## 6. Procedimiento de Emergencia: Kill-Switch HOTL

Si se detecta una anomalía o comportamiento imprevisto del modelo en producción:

1. **Activación de HOTL (Human-On-The-Loop) Supervisory Kill Switch:**
   - Desactivar mutaciones actualizando el feature flag en App Configuration:
     `set_feature_flag("banking_mutations_enabled", False, label="production")`
   - O enviar señal de supervisor a `/api/v1/supervision/hotl/kill-switch`.
2. **Efecto Inmediato:**
   - Toda solicitud de escritura (`create_service_request`, etc.) se bloquea de inmediato a nivel de código determinista, independientemente de lo que responda el LLM.
   - Las consultas de solo lectura (`get_account_balance`, etc.) continúan operando con normalidad.

---

## 7. Procedimiento de Rollback

1. En caso de fallo en producción, revertir Container Apps a la revisión anterior conocida estable:
   ```bash
   az containerapp revision set-active \
     --name ca-aegisbank-agent \
     --resource-group rg-aegisbank-production \
     --revision <PREVIOUS_HEALTHY_REVISION>
   ```
2. Validar que la revisión anterior responde con `200 OK` en `/health/ready`.
3. Registrar el incidente en el registro de incidentes post-mortem sin divulgar datos de auditoría sensibles.

---

## 8. Rotación de Secretos e Identidades

1. **Rotación de Secretos en Key Vault:**
   - Crear una nueva versión del secreto en Azure Key Vault.
   - App Configuration puede apuntar a la versión flotante o fija.
   - Forzar refresh del proveedor en la aplicación (`ConfigurationProvider.refresh()`).
2. **Rotación de Federated Credentials (OIDC):**
   - Actualizar la credencial federada en el Service Principal de GitHub Actions en Entra ID.
   - Cero tiempo de inactividad para los runtimes de producción.

---

## 9. Limitaciones Explícitas del Sistema

- **No es un banco real:** Todos los datos son sintéticos; los clientes `CUST-0001` a `CUST-0004` son ficticios.
- **Sin dinero real:** No existe liquidación con BCRP, Cámara de Compensación Electrónica, ni SWIFT.
- **Sin Certificación SBS/PCI-DSS:** No se reclama cumplimiento regulatorio formal de banca real.
- **Cloud-Unvalidated:** El sistema está técnicamente preparado para despliegue en Azure (`AZURE_DEPLOYMENT_PREPARED`), pero la ejecución en la nube no se realiza hasta que se apruebe el aprovisionamiento real de staging.
