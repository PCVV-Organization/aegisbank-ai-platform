# Matriz de Privilegio Mínimo RBAC (Microsoft Entra ID / Azure)

> **Estado:** `DOCUMENTED_LEAST_PRIVILEGE` · `CLOUD_UNVALIDATED`.
> **Ámbito:** Runtimes de Azure Staging y Producción para AegisBank AI Platform.
> En desarrollo local y pruebas automatizadas, rige confianza local o emuladores sin Azure RBAC.

---

## 1. Principio Fundamental de Segregación

1. **Separación Estricta:** La identidad de despliegue (CI/CD GitHub Actions) y las identidades de ejecución (Workload Managed Identities) son identidades completamente independientes.
2. **Prohibición de Roles Genéricos:** Ningún runtime de aplicación recibe roles amplios como `Owner`, `Contributor`, o `User Access Administrator`.
3. **Passwordless por Defecto:** Se priorizan roles de plano de datos (`Data Reader`, `Data Receiver/Sender`, `Secrets User`) sobre credenciales fijas o cadenas de conexión.

---

## 2. Inventario de Identidades de Carga de Trabajo

| Identidad | Tipo | Propósito | Responsabilidad |
| --- | --- | --- | --- |
| `id-aegisbank-<env>-workload` | User-Assigned Managed Identity | Identidad principal de Container Apps (Agent / API). | Acceso a configuración, secretos inevitables y mensajería. |
| `id-aegisbank-<env>-functions` | User-Assigned Managed Identity | Identidad para Azure Functions (consumidor de eventos). | Consumo de Service Bus, persistencia de idempotencia y outbox. |
| `id-aegisbank-<env>-corebanking` | User-Assigned Managed Identity | Identidad de servicio Mock Core Banking (si se aloja en cloud). | Aislamiento de base de datos bancaria mock y endpoints seguros. |
| `id-aegisbank-<env>-deployer` | Microsoft Entra App / Federated OIDC | Pipeline de GitHub Actions vía OpenID Connect. | Despliegue declarativo de infraestructura y actualización de Container Apps. |

---

## 3. Matriz Detallada de Asignación de Roles por Recurso

| Identidad Runtime | Recurso Azure | Rol RBAC | Acceso | Justificación de Mínimo Privilegio |
| --- | --- | --- | --- | --- |
| **Agent Workload** | Azure App Configuration | `App Configuration Data Reader` (`516239f1-63e1-4d78-a4de-a74fb236a071`) | Read-Only | Lectura de parámetros de runtime (modelos, timeouts, URLs, feature flags) filtrados por label. Sin permiso de escritura. |
| **Agent Workload** | Azure Key Vault | `Key Vault Secrets User` (`4633458b-17de-408a-b874-0445c86b69ea`) | Read-Only | Resolución de referencias a secretos indispensables (ej. API keys de terceros o certificados). Cero permisos sobre llaves criptográficas o certificados. |
| **Agent Workload** | Azure Service Bus | `Azure Service Bus Data Sender` (`69a216fc-b8fb-44d8-bc22-1f3c2cd27a39`) | Write-Only | Emisión de eventos de auditoría y solicitudes de servicio aprobadas por HITL hacia tópicos/colas autorizados. |
| **Agent Workload** | Azure Cosmos DB | `Cosmos DB Built-in Data Reader` (Plano de datos NoSQL) | Read-Only | Consulta particionada de estados de sesión y eventos del agente. |
| **Agent Workload** | Azure AI Foundry / Azure OpenAI | `Cognitive Services OpenAI User` (`5e6ce059-de30-45e8-b8e7-e898950d9990`) | Execute | Inferencia de chat completions grounded (`phi-4-mini`) mediante tokens Entra sin API keys fijas. |
| **Functions Consumer** | Azure Service Bus | `Azure Service Bus Data Receiver` (`4f6d3a01-b2a5-4e24-9d14-70f80761a4c6`) | Read + Settle | Recepción, liquidación (complete/abandon) y dead-lettering de eventos de servicio. |
| **Functions Consumer** | Azure Key Vault | `Key Vault Secrets User` | Read-Only | Lectura de secretos requeridos por integraciones externas de eventos. |
| **GitHub Actions Deployer** | Grupo de Recursos (`rg-aegisbank-<env>`) | Rol acotado de despliegue (`Deployment Operator` / ARM deployment) | Control Plane | Creación/actualización de recursos ARM/Bicep y publicación de revisiones en Container Apps. Cero acceso a datos bancarios o secretos. |

---

## 4. Auditoría de Identidad y Revocación

1. **Sin Secretos en Git:** Las identidades asignadas no tienen contraseñas ni client secrets persistidos.
2. **Federación OIDC:** GitHub Actions utiliza autenticación federada temporal con subject restringido a la rama autorizada:
   `repo:VegaValverde/aegisbank-ai-platform:environment:staging`
3. **Procedimiento de Emergencia:** Ante cualquier sospecha de compromiso, la asignación de rol se retira inmediatamente en Azure Portal / CLI sin afectar el código base ni requerir recompilación:
   ```bash
   az role assignment delete --assignee <principal-id> --role "Key Vault Secrets User" --scope <vault-id>
   ```
