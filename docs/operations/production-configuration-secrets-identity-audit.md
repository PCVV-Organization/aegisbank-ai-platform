# Auditoría de configuración, secretos e identidad de producción

> **Clasificación:** `AUDIT-RESULT` · `READ-ONLY` · `CLOUD-PENDING`
>
> **Fecha de evidencia:** 2026-09-30. **Repositorio auditado:** `aegisbank-ai-platform` en `master`, `HEAD c89b18f`, último tag semántico `v1.0.8`.
>
> **Regla de lectura:** `READY` significa que el código o contrato local existe; no significa que Azure haya sido aprovisionado ni validado. `UNKNOWN` significa que el repositorio no aporta evidencia suficiente. Los valores secretos no se imprimen.

## Resumen ejecutivo

AegisBank tiene una frontera canónica bien diseñada para configuración y secretos (`ConfigurationProvider`, `SecretProvider`, `KeyVaultReferenceResolver`), un emulador local de App Configuration y un adaptador inyectable de Key Vault. Sin embargo, esa frontera no es todavía la única ruta de runtime: Agent, RAG, Core Banking, Cosmos, Redis, Service Bus, Functions y scripts leen variables de entorno directamente.

La nube es **diseño, no ejecución**: no existe IaC de Azure, despliegue de Container Apps, identidad administrada validada, App Configuration cloud validada, Key Vault real ni CI cloud ejecutado. La siguiente fase debe partir de esta radiografía y no de migrar valores a ciegas.

### Flujo actual observado

```text
.env (solo Foundry Local mediante python-dotenv) ─┐
variables de proceso ────────────────────────────┼─> módulos con os.getenv/os.environ
App Configuration Emulator ─> ConfigurationProvider ─> fallback EnvironmentConfigurationProvider
SecretProvider local sintético ──────────────────┘
AzureKeyVaultSecretProvider ─> contrato inyectable; cloud no configurada
```

### Decisión objetivo recomendada, aún no implementada

```text
Container Apps bootstrap env (nombre de entorno, URI de App Config/Key Vault)
  -> Managed Identity
  -> Azure App Configuration: valores no secretos, labels y feature flags
  -> Key Vault: secretos inevitables
  -> Entra ID: sustituir claves/connection strings cuando el SDK lo permita
```

## Inventario de variables y rutas directas

| Clave | Lectura / dueño | Default o fallback | Clase actual | Destino cloud recomendado |
|---|---|---|---|---|
| `AEGISBANK_ENV` | Core Banking `config.py:23` | `development` | configuración directa | App Configuration o env no secreto |
| `AEGISBANK_DATABASE_URL` | Core Banking, tools, MCP | SQLite local | configuración/DSN | App Config + identidad de DB; secreto solo si inevitable |
| `AEGISBANK_CONFIG_LABEL` | `configuration/config.py:150,381,384` | `local` | configuración | bootstrap env + App Config label |
| `AEGISBANK_USE_APPCONFIG_EMULATOR` | `configuration/config.py:379` | `true` | local-only | eliminar/denegar en producción |
| `AEGISBANK_APPCONFIG_EMULATOR_URL` | `configuration/config.py:383` | `http://127.0.0.1:8483` | local-only | no aplica; usar endpoint de App Config |
| `AEGISBANK_FOUNDRY_LOCAL_BASE_URL` | `rag/foundry_local.py:17,65` | descubrimiento CLI | local-only | endpoint/deployment cloud separado |
| `AEGISBANK_FOUNDRY_TIMEOUT_SECONDS` | `agent.py:187` | `45` | configuración | App Configuration |
| `AEGISBANK_FOUNDRY_MAX_RETRIES` | `agent.py:188` | `2` | configuración | App Configuration |
| `AEGISBANK_FOUNDRY_BUSY_MAX_RETRIES` | `agent.py:265` | `5` | configuración | App Configuration |
| `AEGISBANK_FOUNDRY_BUSY_RETRY_BASE_SECONDS` | `agent.py:266` | `2` | configuración | App Configuration |
| `AEGISBANK_SESSION_DB_PATH` | `session_store.py:42` | `data/sessions.db` | local state | managed durable store / App Config name |
| `AEGISBANK_PGVECTOR_URL` | `pgvector_retriever.py:34` | local PostgreSQL default | DSN, sensible | Entra token path; otherwise Key Vault |
| `REDIS_URL` | `cache.py:23`, `redis_retriever.py:26` | `redis://127.0.0.1:6379/0` | endpoint/possible credential | App Config endpoint; identity or Key Vault credential |
| `COSMOS_ENDPOINT` | `cosmos.py:20` | local emulator URL | endpoint | App Configuration |
| `COSMOS_KEY` | `cosmos.py:21` | emulator credential | secret-like | Managed Identity; otherwise Key Vault |
| `AEGISBANK_SERVICEBUS_CONN_STR` | `azure_servicebus_adapter.py:40` | emulator connection string | secret | Managed Identity; otherwise Key Vault |
| `AEGISBANK_CORE_BANKING_URL` / `CORE_BANKING_URL` | `banking_tools.py:376` | no default | endpoint | App Configuration / internal service discovery |
| `AEGISBANK_FUNCTION_IDEMPOTENCY_DATABASE_URL` | Functions handler `service_request_handler.py:92` | SQLite memory | local state/DSN | managed durable DB identity path |
| `AEGISBANK_APPROVAL_FILE` / `AEGISBANK_CUSTOMER_ID` | `mcp_server.py:20,35` | optional / `CUST-0001` | local MCP/testing | not a production identity model |
| `MLFLOW_DISABLE_AGENT_HINT` | `mlops/tracker.py:18` | assigned `1` | local process switch | runtime config if retained |
| `POSTGRES_PASSWORD`, `MSSQL_SA_PASSWORD` | local Compose | required shell values | local secrets | never reuse; managed identity/Key Vault as applicable |
| `POSTGRES_PORT`, `REDIS_PORT`, `COSMOS_PORT_*`, `SERVICEBUS_PORT`, `APPCONFIG_PORT` | local Compose | ports shown in manifest | local-only | no aplica |
| `FUNCTIONS_WORKER_RUNTIME`, `AZURE_FUNCTIONS_ENVIRONMENT`, `AzureWebJobsStorage`, `FUNCTIONS_SECRETS_PATH` | Functions local image/settings | development/local defaults | local Functions bootstrap | cloud Functions/ACA design required |

## Respuestas completas al cuestionario

### A. Bootstrap y configuración

1. CLI: `python -m aegisbank_agent.cli` (`ai/agent/src/aegisbank_agent/cli.py`).
2. API hospedada del agente: **UNKNOWN**; no se encontró HTTP API del agente.
3. El agente expone CLI y MCP stdio; el HTTP API presente es Core Banking FastAPI, no Agent API.
4. `AEGISBANK_ENV` selecciona Core Banking; `AEGISBANK_CONFIG_LABEL` selecciona el label de configuración. No hay selector único de entorno.
5. No hay objeto único: coexisten provider canónico y lecturas directas.
6. Sí: `EnvironmentConfigurationProvider` copia `os.environ`.
7. Sí: `AppConfigurationEmulatorProvider` usa `/kv` local.
8. No se encontró `AppConfigurationCloudProvider` operativo; la documentación lo declara `CLOUD-PENDING`.
9. Labels: sí en proveedor/emulador (`AEGISBANK_CONFIG_LABEL`).
10. Refresh: el emulador implementa `refresh`; no hay watcher cloud validado.
11. Feature flags: emulador implementa `set_feature_flag`; consumo runtime de flags: **UNKNOWN**.
12. Bootstrap mínimo: flag de emulador, endpoint y label; todos tienen defaults locales.
13. No hay ciclo de bootstrap en código actual porque Key Vault no se activa como provider por defecto.
14. No hay namespace uniforme `AegisBank:*`; predominan variables planas.
15. Hardcoded candidatos: URLs/puertos locales, retry/timeout, nombres de cola e índices, modelos, defaults de Redis/pgvector.

### B. `.env`

16. Existen `.env.example` raíz y `ai/agent/.env.example`; `.env*` está ignorado salvo ejemplos.
17. Sí, pero solo `ai/rag/.../foundry_local.py` intenta `load_dotenv()`.
18. Precedencia Foundry: `AEGISBANK_FOUNDRY_LOCAL_BASE_URL` del entorno/.env; si falta, `foundry server status`; otros módulos no cargan dotenv.
19. `.env` no es requisito de pruebas; es conveniencia local.
20. No: los ejemplos cubren Foundry/sesiones, no el inventario completo de Compose, Functions ni adaptadores.
21. Ejemplos raíz no contienen secreto real conocido; Dockerfile Functions contiene claves locales estáticas sintéticas y debe permanecer local.
22. Sí potencialmente para Foundry, porque dotenv carga valores de `.env`; no hay guardia de producción.
23. Precedencia global: **UNKNOWN/no unificada**. Se observan argumentos, `os.environ`, dotenv solo Foundry, emulador/fallback y defaults por módulo.

### C. SecretProvider

24. Contrato: `get`, `get_optional`, `require`, `describe` y atributo `name` (`secrets.py:47`).
25. Implementaciones: `LocalSyntheticSecretProvider` y `AzureKeyVaultSecretProvider`.
26. Local guarda valores sintéticos en memoria.
27. Sí, adapter de `SecretClient`; no hay instancia cloud compuesta por producción.
28. Contract-tested; cloud real pendiente.
29. Sí, importa `azure.keyvault.secrets.SecretClient` de forma lazy.
30. Sí, usa `DefaultAzureCredential` cuando recibe `vault_url`.
31. Solo la cadena interna de `DefaultAzureCredential`; no se codifican credenciales alternativas explícitas.
32. No se encontró `ClientSecretCredential` en runtime.
33. Los providers no registran valores; errores sí incluyen nombre y pueden incluir el texto de excepción externa.
34. Redacción cubre `api_key`, password, secret, token, authorization, bearer, CVV, PIN y access token; no es una garantía universal para toda forma de DSN.
35. `KeyVaultReferenceResolver` parsea URI/JSON y llama a `SecretProvider.require`; puede resolver con provider inyectado.
36. Espera `https://<vault>/secrets/<name>[/<version>]` o JSON `{ "uri": ... }`.
37. Sí, parsea y expone versión; el provider llama `get_secret(name)` sin pasar la versión: pinning efectivo **NO**.
38. Sin cliente: `SecretError`; denegado/no encontrado: excepción explícita. No se observó fallback inseguro.
39. No hay caché de secretos en el adapter.
40. Para secretos requeridos falla cerrado; otras rutas directas con defaults de emulador son una brecha de producción.

### D. Managed Identity / Entra

41. Solo `AzureKeyVaultSecretProvider` invoca `DefaultAzureCredential`.
42. Service Bus usa connection string; Cosmos usa key; PostgreSQL y Redis usan URL/DSN.
43. Cosmos y Service Bus actuales sí dependen de key/connection string para sus adapters.
44. No: adapter Service Bus solo usa `from_connection_string`.
45. No: `CosmosRepository` toma credencial string.
46. **UNKNOWN**: driver/URL actual no implementa token Entra.
47. No: Redis usa URL y cliente Redis estándar.
48. El diseño lo contempla, runtime cloud no lo implementa.
49. Sí en adapter Key Vault, pendiente de identidad/RBAC reales.
50. Functions local usa `AzureWebJobsStorage=""`; producción no está modelada.
51. Event Grid production: **UNKNOWN**; actual trigger es local/container.
52. Service Bus, Cosmos, Key Vault y potencialmente PostgreSQL son oportunidades passwordless; Redis y Functions requieren diseño adicional.

### E. Agent, LLM y Foundry

53. Variables `AEGISBANK_FOUNDRY_LOCAL_BASE_URL`, timeout, retries, busy max retries y busy base seconds.
54. Sí: discovery llama `foundry server status -o json`.
55. Reemplazo cloud: **UNKNOWN**; ADR-010 es provider-agnóstico, pero no hay provider remoto implementado.
56. Existe protocolo `LLMProvider`; solo Foundry Local fue evidenciado.
57. Cliente OpenAI-compatible usa API key placeholder `none` para Local.
58. Modelo y URL están separados; modelo por defecto `phi-4-mini`, configuración del alias por variable solo en scripts live.
59. Configurables: base URL, timeout y retries; max rounds es constante/contructor; tokens/temperature/top-p no expuestos.
60. Timeouts, retries, modelo y límites van a App Configuration; credenciales cloud a identidad/Key Vault si fueran inevitables.
61. Prompt se carga desde archivo JSON versionado.
62. No se observó refresh dinámico de prompt.
63. Límites, retries, timeout, modelo y política de herramientas requieren valores de producción; la política determinista no debe externalizarse sin control de cambios.

### F. Core Banking

64. `AEGISBANK_CORE_BANKING_URL`; además `AEGISBANK_DATABASE_URL` en mock Core Banking.
65. No: Agent también usa datos/DB local en tools.
66. No se encontró autenticación Agent→Core Banking.
67. Confianza local: datos sintéticos y sesión `customer_id` controlada por aplicación.
68. TLS no es impuesto por el adapter; URL puede ser HTTP.
69. Mecanismo apropiado: identidad de workload/OAuth2 o mTLS; implementación exacta **UNKNOWN**.
70. El agente puede leer `AEGISBANK_DATABASE_URL` en tools, por tanto sí puede usar DB local directa.
71. Retries/timeouts HTTP: **UNKNOWN/no configuración evidenciada**.
72. Observabilidad contiene correlation/trace en el proceso; propagación HTTP explícita no fue evidenciada.
73. Sí, hay contratos/OpenAPI de Core Banking bajo `contracts/` y servicio FastAPI.

### G. SQLite / PostgreSQL

74. `AEGISBANK_DATABASE_URL`, `AEGISBANK_PGVECTOR_URL`, Function idempotency DSN, MLflow SQLite URI.
75. SQLite de Core Banking, sesiones, Functions y MLflow son locales.
76. Core Banking, Agent session store, Functions handler y MLflow poseen sus stores respectivamente.
77. Mock Core Banking soporta SQLite; PostgreSQL para Core Banking: **UNKNOWN/no adapter evidenciado**.
78. Alembic en startup: **UNKNOWN/no evidencia de wiring**.
79. pgvector actual consume URL; passwordless no está implementado.
80. pgvector usa `psycopg`; Core Banking usa SQLAlchemy.
81. SSL mode configurable: solo si se incluye en URL; no se fuerza.
82. Pool de PostgreSQL no configurable; abre conexión por operación.
83. Timeouts DB no configurables en adapter.
84. pgvector inicializa esquema/índices desde código idempotente.
85. Migraciones separadas de startup: **UNKNOWN**.
86. Entra PostgreSQL requeriría adapter de token; no existe aún.
87. Si Entra se adopta, se eliminan password/DSN secreto; endpoint y DB name permanecen configuración.

### H. Redis

88. Solo `REDIS_URL`; default local sin contraseña.
89. `rediss://` sería aceptado por `from_url`, pero no hay validación específica.
90. URL puede contener credenciales, no existe clave separada.
91. Entra no soportado explícitamente.
92. Cachea entradas RAG/vectoriales; reglas de datos prohibidos: **UNKNOWN** en código auditado.
93. TTL configurable: **UNKNOWN**.
94. Redis es opcional para el camino local híbrido; no es requisito de arranque del Agent básico.
95. El retriever devuelve lista vacía ante `ResponseError`.
96. Degrada en búsqueda Redis; no hay prueba de startup cloud.
97. URL, index, prefijo, dimensión y conexiones deben ser configuración.

### I. Cosmos DB

98. `COSMOS_ENDPOINT`, `COSMOS_KEY`; DB/container se obtienen por constructor/defaults de módulo.
99. Usa endpoint + key/emulador; no `DefaultAzureCredential`.
100. Partition key es de esquema/configuración de repository; cambio runtime: **UNKNOWN**.
101. Consistency level: **UNKNOWN**.
102. Retry: SDK/default, no política explícita evidenciada.
103. Passwordless con MI requiere cambio de adapter: `MAJOR_GAP`.
104. Endpoint localhost, key de emulador y puertos son exclusivamente locales.

### J. Service Bus y mensajería

105. `AEGISBANK_SERVICEBUS_CONN_STR`; queue default `service-requests` hardcoded/constructor.
106. No acepta `fully_qualified_namespace` + credential.
107. Sí, requiere connection string actualmente.
108. MI puede eliminar el secreto en diseño, no en adapter actual.
109. Queue/topic/subscription deben vivir en App Configuration.
110. Retry/DLQ: adaptador y broker local; configuración broker cloud **UNKNOWN**.
111. Consumer actual: Functions Event Grid handler; Service Bus consumer cloud no evidenciado.
112. Escalado: Container Apps es decisión futura; KEDA no configurado.
113. Compose usa `MSSQL_SA_PASSWORD` solo para emulador; no mezclar con cloud.

### K. Azure Functions / Event Grid

114. Settings enumerados en inventario; `local.settings.example.json` es plantilla segura local.
115. Todo `local.settings`, secret storage Files, SQLite memory y claves horneadas es local-only.
116. Sí existe `local.settings.json` y está ignorado.
117. Sí, `local.settings.example.json`.
118. Storage cloud: **UNKNOWN/no configuración de producción**.
119. Identity-based bindings: **UNKNOWN/no binding cloud configurado**.
120. Event Grid inbound usa trigger/host local; autenticación cloud no demostrada.
121. Sí: CloudEvent schema/contratos versionados e independientes de config.

### L. Observabilidad

122. No se encontraron `OTEL_*` ni Application Insights variables de runtime; hay OTel SDK in-memory.
123. No soporta OTLP endpoint/exporter en código actual.
124. No requiere telemetry connection string local.
125. Azure Monitor con MI: diseño no implementado; `MAJOR_GAP`.
126. Servicio/nombre de tracer configurables por argumento; atributos de entorno no centralizados.
127. Sí, logs JSON estructurados.
128. Sí, redacción por claves/patrones antes de logs/audit; cobertura completa de PII: **UNKNOWN**.
129. Nivel de log runtime: **UNKNOWN**.
130. Sampling configurable: no; exporter in-memory simple.
131. Nunca prompts crudos, secretos, tokens, contraseñas, credenciales ni payloads bancarios ilimitados.

### M. MLflow / GenAIOps

132. Solo `MLFLOW_DISABLE_AGENT_HINT`; `tracking_uri` y experiment name son argumentos.
133. Sí, SQLite local por defecto en `reports/mlruns`.
134. Backend productivo: **UNKNOWN**.
135. Credenciales no se asumen en adapter local.
136. Sí captura parámetros/métricas/artefactos; la política de versions no es secreto.
137. URI y nombre de experimento deben ir a App Configuration.

### N. Contenedores / despliegue

138. Core Banking Docker ejecuta Uvicorn; Functions image ejecuta host Functions; RAG/Agent no tienen imagen de producción propia.
139. Core Banking 8000; Functions 80; Compose expone emuladores locales.
140. Public ingress cloud: **UNKNOWN**; Core Banking debe ser interno salvo API explícita.
141. Datos/mensajería/config deben ser internos.
142. Root filesystem read-only: no se evidencia para Core Banking/Functions.
143. Core Banking corre non-root UID 10001; Functions image no demuestra non-root final.
144. Core Banking `/app/data`, volúmenes Compose PostgreSQL/Core Banking; Functions secret files locales.
145. Datos durables Azure: diseño pendiente.
146. Core Banking tiene `/health/live`; readiness cloud completa: **UNKNOWN**.
147. Healthchecks Compose prueban procesos locales; dependencia vs liveness no está uniformada.
148. Fallo de configuración a readiness: **UNKNOWN**.
149. Graceful shutdown/SIGTERM: **UNKNOWN**.
150. CPU/mem limits: no encontrados.
151. Autoscaling/KEDA: no configurado.
152. Algunas imágenes Compose están digest-pinned, otras usan `latest`; deployment cloud no tiene tags inmutables.
153. ACR target: **UNKNOWN/no IaC**.
154. Container Apps es objetivo de diseño; no despliegue.

### O. Red y seguridad

155. Outbound real necesario: dependencias Azure futuras; local Foundry/Compose usa loopback/red bridge.
156. Private endpoints: diseño recomendado, no configurado.
157. VNet integration: no existe.
158. Sí: múltiples `localhost`/`127.0.0.1` y DNS Compose locales.
159. Hardcoded relevantes: 8000, 8081/8080/1234 Cosmos, 6379 Redis, 8483 App Config, 5672 Service Bus, SQLite paths.
160. Cosmos healthcheck usa `curl -k`; no se vio desactivación TLS en clientes de producción.
161. Emulador Cosmos implica excepción local de TLS en healthcheck.
162. No hay guardia que impida esa configuración en producción: `MAJOR_GAP`.
163. CORS: no encontrado.
164. Inbound auth del Core Banking: no encontrado.

### P. CI/CD

165. `.github/workflows/ci.yml` lint, tests, Bandit, pip-audit, SBOM y secret gate.
166. No usa secretos de repositorio en workflow actual.
167. Secretos Azure de despliegue: no definidos porque no hay despliegue.
168. OIDC GitHub→Azure: posible como diseño, no implementado.
169. Environments/aprobaciones: no configurados.
170. Sí genera SBOM CycloneDX.
171. Sí SAST, SCA y secret scan; image scan no evidenciado.
172. Migraciones separadas: **UNKNOWN**.
173. Rollback está documentado como runbook, no validado cloud.
174. Cambios Azure IaC-driven: no; no hay IaC Azure.
175. IaC productivo actual: ninguno encontrado.

### Q. Datos y seguridad

176. Config local contiene identificadores sintéticos y endpoints; no se halló PII real como configuración.
177. `snapshot_for_audit` limita claves; no se observó serialización global de env, salvo MCP boundary que hereda entorno para subprocess.
178. Algunos errores externos se interpolan; valores secretos no se pasan deliberadamente, pero sanitización de excepciones completas no es universal.
179. Salud/diagnóstico no exponen secretos en código inspeccionado; cobertura completa: **UNKNOWN**.
180. Config/Key Vault no se incluyen en audit snapshots, salvo descriptor de origen.
181. Rotación explícita: no.
182. Rotación sin restart: no demostrada.
183. Refresh del emulador existe; propagación dinámica runtime no demostrada.
184. No hay guardia explícito que bloquee emuladores/defaults inseguros para `production`.
185. No hay validador global contra localhost/default credentials en producción.

### R. Modelo de entornos de producción

186. El repo define local/development/container/kubernetes-local; no modelo DEV/STAGING/PROD completo.
187. Recursos por entorno: actualmente **diseño pendiente**; deben aislarse App Config, Key Vault, datos, Service Bus, observabilidad y compute.
188. Diferirían endpoints, labels, nombres de recursos, límites, model deployment, top-k, timeouts, colas y sampling.
189. Los nombres de secretos por entorno no están definidos.
190. Key Vaults separados por entorno: compatible con adapter (`vault_url`), no desplegado.
191. App Config stores separados o labels: labels están soportados localmente; stores separados cloud no implementados.

## Inventario de secretos (redactado)

| Material | Ubicación actual | Riesgo / estado | Acción posterior |
|---|---|---|---|
| PostgreSQL password | shell de Compose | local, no versionado | no migrar; usar identidad o Key Vault |
| MSSQL emulator password | shell de Compose | local, no versionado | no migrar; eliminar con emulador |
| Cosmos key | env/default emulador | adapter basado en clave | reemplazar por credential Entra |
| Service Bus connection string | env/default emulador | adapter basado en secreto | `ServiceBusClient(fully_qualified_namespace, credential)` |
| Function keys locales | Dockerfile Functions | sintéticas pero horneadas | excluir de imagen cloud |
| Foundry Local key | placeholder `none` | no secreto real | provider cloud separado |
| DB/Redis URLs con credencial embebible | env | sensible si contienen `@` | Key Vault o token/MI |

## Readiness resumido

| Área | Estado | Fundamento |
|---|---|---|
| App Configuration labels/emulador | `READY-LOCAL` | provider + tests locales |
| App Configuration cloud | `MAJOR_GAP` | no provider cloud/composición/MI validada |
| Key Vault contract | `READY-CONTRACT` | adapter `SecretClient` + URI parser |
| Key Vault cloud | `SMALL_GAP` de código / `MAJOR_GAP` de infraestructura | faltan composición, vault, MI, RBAC y evidencia |
| Managed Identity | `MAJOR_GAP` | solo invocada implícitamente por Key Vault adapter |
| Service Bus passwordless | `MAJOR_GAP` | adapter connection-string-only |
| Cosmos passwordless | `MAJOR_GAP` | credential string-only |
| PostgreSQL passwordless | `MAJOR_GAP` | DSN-only |
| Redis passwordless | `MAJOR_GAP` | URL-only |
| Container Apps | `MAJOR_GAP` | ADR de diseño; sin IaC/deploy |
| CI federated identity | `MAJOR_GAP` | CI de calidad sin workflow de despliegue |
| Observabilidad cloud | `MAJOR_GAP` | OTel in-memory, sin OTLP/Azure Monitor |

## Plan de corrección posterior (no ejecutado)

1. Convertir esta auditoría en una especificación cloud aprobada, con DEV/STAGING/PROD y ownership de cada clave.
2. Centralizar lecturas directas tras proveedores/adaptadores sin cambiar políticas deterministas ni HITL.
3. Implementar autenticación passwordless por adapter antes de crear secretos nuevos.
4. Añadir guardia de arranque que rechace localhost, emuladores y credenciales de desarrollo en `production`.
5. Crear IaC y despliegue cloud aprobados; después ejecutar evidencia separada y actualizar el estado desde `CLOUD-PENDING`.

## Evidencia principal

- `ai/agent/src/aegisbank_agent/configuration/config.py`
- `ai/agent/src/aegisbank_agent/configuration/secrets.py`
- `ai/agent/src/aegisbank_agent/agent.py`
- `ai/rag/src/aegisbank_rag/foundry_local.py`
- `ai/agent/src/aegisbank_agent/reliability/azure_servicebus_adapter.py`
- `ai/agent/src/aegisbank_agent/cosmos.py`
- `ai/rag/src/aegisbank_rag/{pgvector_retriever,redis_retriever}.py`
- `deploy/local/docker-compose.yml`, `functions/aegisbank-events/`, `.github/workflows/ci.yml`
- `docs/architecture/adr/ADR-029-configuration-secrets-identity-boundary.md`
