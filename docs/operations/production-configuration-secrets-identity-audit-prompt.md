# Prompt de auditoría: configuración, secretos e identidad de producción

> **Clasificación:** `PLANNING-PROMPT` · `READ-ONLY` · `CLOUD-PENDING`
>
> **Propósito:** transferir a un LLM una guía completa para realizar una auditoría de descubrimiento, basada en evidencia, antes de diseñar la arquitectura de configuración, secretos e identidad de AegisBank para nube.
>
> **No es evidencia ejecutada:** este documento no afirma que Azure Key Vault, Managed Identity, Azure App Configuration ni despliegues cloud estén implementados o validados. El checkout actual y sus ADRs son la fuente de verdad.
>
> **Uso:** copiar el bloque de auditoría al LLM elegido. El LLM debe respetar sus restricciones de solo lectura y no revelar secretos reales.

---

## Contexto y prompt completo

Sí: para producción **no usaría `.env` como mecanismo principal de secretos**. En Azure, el diseño objetivo debería ser:

```text
LOCAL
.env.local / variables de entorno
        │
        └── sólo desarrollo
              ↓
ConfigurationProvider / SecretProvider
              ↑
        misma interfaz
              ↓
AZURE
Managed Identity
   ├── Azure App Configuration ── configuración NO secreta
   └── Azure Key Vault ────────── secretos
```

Esto además encaja con la arquitectura que AegisBank ya tiene: `ConfigurationProvider`, `SecretProvider` y `KeyVaultReferenceResolver`; el proyecto ya contempla `DefaultAzureCredential`, App Configuration y un adapter hacia Key Vault, pero Key Vault real y Managed Identity siguen marcados como pendientes de nube. :chatgpt-content-reference{index="0"} :chatgpt-content-reference{index="1"}

Microsoft recomienda evitar valores secretos directamente almacenados en Container Apps en producción y usar referencias a **Azure Key Vault** con **Managed Identity**; la identidad administrada puede recibir el rol `Key Vault Secrets User`. :chatgpt-content-reference{index="2"} App Configuration puede además contener referencias a Key Vault y su provider de Python puede resolverlas usando credenciales de Azure, incluidas Managed Identities. :chatgpt-content-reference{index="3"}

## Cómo dividiría las variables

No todo debe ir a Key Vault.

| Tipo | Ejemplos | Producción |
|---|---|---|
| Configuración normal | `ENVIRONMENT=production`, timeouts, feature flags, top-k, nombres de recursos | **Azure App Configuration** |
| Endpoints no secretos | URL interna Core Banking, App Configuration endpoint, OTEL endpoint | App Configuration / Container Apps env |
| Secretos | API keys, passwords, connection strings que aún existan | **Azure Key Vault** |
| Credenciales Azure | Service Bus, Cosmos, PostgreSQL, etc. | Preferir **Managed Identity / Entra ID**, evitando secretos |
| Bootstrap | App Config endpoint, Key Vault URI, environment name | Variables de Container Apps |
| Local dev | URLs localhost, passwords de emuladores, Foundry Local | `.env.local`, gitignored |
| Plantilla | nombres de variables sin valores reales | `.env.example`, versionado |

La idea más importante es:

```text
MEJOR SECRETO
= secreto que no existe
```

Si AegisBank puede autenticarse contra Service Bus, Key Vault, PostgreSQL, Cosmos, etc. mediante **Microsoft Entra ID + Managed Identity**, es mejor que almacenar connection strings en Key Vault. Key Vault queda para aquellos secretos que realmente siguen siendo necesarios.

Y tampoco quiero que terminemos con esto:

```python
os.getenv("X")
os.getenv("Y")
os.getenv("Z")
```

dispersado por cincuenta archivos. El propio diseño del proyecto ya establece que configuración y secretos deben pasar por sus fronteras canónicas. :chatgpt-content-reference{index="4"}

---

# Lo que debemos hacer primero

Antes de tocar el código quiero una **radiografía completa**.

Tenemos demasiados componentes:

```text
Agent
RAG
Core Banking
PostgreSQL/pgvector
Redis
Cosmos
Service Bus
Functions
Foundry
OpenTelemetry
MLflow
App Configuration
Key Vault
Docker
Container Apps target
```

y necesitamos saber exactamente:

```text
qué variables existen
quién las lee
cuáles son secretos
cuáles son configuración
qué tiene fallback
qué está hardcodeado
qué utiliza connection strings
qué soporta identity
qué se necesita al arrancar
```

No quiero inventar esa información.

Este es el prompt que ejecutaría ahora en Antigravity.

Perform a READ-ONLY `Production Configuration, Secrets & Identity Discovery Audit` of AegisBank. Work ONLY in application repository `C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`; the outer `C:\aegisbank-ai-platform-ai-env` repository is independent and must not be modified. DO NOT change code, create `.env`, install dependencies, modify Azure resources, commit, tag, push, rebase, reset, amend, create worktrees, start migrations, or “fix” anything in this task. The goal is to give ChatGPT a complete evidence-based map before we design the production configuration architecture.

PRECHECK and report exact evidence: repository root, branch, HEAD, latest semantic tag, `git status --short`, relevant recent commits, Python version, deployment manifests currently present (`deploy/**`, `infra/**`, `.github/workflows/**`, Dockerfiles, Compose, Kubernetes/Bicep/Terraform/ARM if any). Trust current code over historical docs.

READ FIRST: `README.md`, `AGENTS.md`, `README.LLM.md` if present, `docs/README.md`, canonical components/architecture docs, repository-boundary docs, production/cloud migration ADRs, security/threat model, configuration/secrets docs, deployment docs, `.gitignore`, every `.env.example`/`.env.*.example`, Docker Compose files, Dockerfiles, CI workflow, Functions configuration templates, and implementation of `ConfigurationProvider`, `SecretProvider`, `KeyVaultReferenceResolver`. DISCOVER BEFORE ASSUMING.

Then perform repository-wide searches for ALL configuration/secrets access mechanisms, including but not limited to: `os.getenv`, `os.environ`, `environ.get`, `load_dotenv`, `dotenv`, `BaseSettings`, Pydantic settings, `ConfigurationProvider`, `SecretProvider`, `KeyVault`, `DefaultAzureCredential`, `AzureCliCredential`, `EnvironmentCredential`, `ManagedIdentityCredential`, `ClientSecretCredential`, connection strings, passwords, tokens, API keys, SAS keys, account keys, Redis URLs, PostgreSQL DSNs, Cosmos endpoints/keys, Service Bus connection strings, Foundry endpoints/models, Core Banking URLs, OTEL exporters, MLflow URIs, App Configuration endpoints, storage accounts, Event Grid, Functions storage, Docker secrets and CI secrets. Search application source, scripts, tests, deploy/config, workflows and examples; DO NOT display actual secret values if any exist—redact them and flag exposure immediately.

Produce a COMPLETE VARIABLE INVENTORY. For every environment/config key found, answer: exact variable/key name; exact source file(s) and line(s); component owner; required/optional; current default/fallback; current local value category (never print real secret); read-at-startup or runtime refresh; secret YES/NO/UNCLEAR; sensitive YES/NO; whether the current code directly reads OS env or goes through canonical provider; whether it is used by tests only/local only/runtime; current production equivalent; whether it should eventually be `App Configuration`, `Key Vault`, `Container Apps non-secret env`, `Managed Identity eliminates it`, `runtime-generated`, or `local-only`; and any compatibility constraint if renamed. Group aliases that represent the same responsibility.

Answer these questions explicitly from CODE EVIDENCE, using `UNKNOWN` when evidence is insufficient:

A. BOOTSTRAP / CONFIGURATION
1. What is the actual entrypoint for Agent CLI?
2. What is the actual runtime entrypoint intended for a hosted API, if any?
3. Does the project currently have an HTTP API for the AI Agent or only CLI?
4. Where is the environment name selected (`local/dev/test/staging/prod`)?
5. Is there one canonical config object loaded once or configuration reads scattered across modules?
6. Does `ConfigurationProvider` currently load OS environment variables?
7. Does it load App Configuration emulator?
8. Does it support real Azure App Configuration today, or only an adapter/contract?
9. Does it support labels such as `dev`, `staging`, `prod`?
10. Does it support configuration refresh without process restart?
11. Does it support feature flags?
12. What minimum configuration must exist before `ConfigurationProvider` itself can start?
13. Is there a circular bootstrap dependency involving App Configuration/Key Vault?
14. Are namespaced keys already used (`AegisBank:Agent:*`, etc.)?
15. Which constants are hardcoded today but should plausibly be configuration?

B. `.env`
16. List every `.env*` file or template and whether Git ignores it.
17. Does application code automatically execute `load_dotenv()`?
18. If yes, where and at what precedence?
19. Are `.env` files required for tests or merely optional convenience?
20. Is there a single `.env.example` capable of documenting all local bootstrap settings?
21. Does any `.env.example` incorrectly contain secret-like realistic values?
22. Can `.env` accidentally override production configuration?
23. What is the current documented precedence between CLI args, OS env, `.env`, App Configuration, defaults and Key Vault?

C. SECRET PROVIDER
24. What is the precise `SecretProvider` interface?
25. What implementations exist?
26. What does the synthetic/local implementation do?
27. Is there already a real Azure Key Vault implementation?
28. If there is, is it complete or only contract-tested?
29. Does it use `azure-keyvault-secrets`?
30. Does it use `DefaultAzureCredential`?
31. What fallback credentials are coded?
32. Is `ClientSecretCredential` anywhere in runtime code?
33. Does code ever log secret values?
34. Does redaction cover names such as password/token/key/connection_string?
35. Does `KeyVaultReferenceResolver` resolve actual secrets or only validate/parse references?
36. What Key Vault URI/reference syntax does it expect?
37. Is secret version pinning supported?
38. What happens if Key Vault is unavailable?
39. Are secrets cached? If yes, where and for how long?
40. Does the system fail closed or silently use insecure fallbacks?

D. MANAGED IDENTITY / ENTRA ID
41. Which Azure clients currently use `DefaultAzureCredential`?
42. Which still rely on connection strings or shared keys?
43. Are any Azure account keys hard-required by current abstractions?
44. Can Service Bus use Entra/Managed Identity with the current adapter?
45. Can Cosmos use Entra/Managed Identity with current repository code?
46. Can PostgreSQL use Entra authentication with the current code/driver?
47. Can Azure Managed Redis use passwordless/Entra with the chosen client path?
48. Can App Configuration authenticate with Managed Identity?
49. Can Key Vault authenticate with Managed Identity?
50. Does Functions rely on `AzureWebJobsStorage` connection string anywhere?
51. Does Event Grid require a key in the current target design?
52. Which credentials could be completely eliminated in Azure rather than moved into Key Vault?

E. AGENT / LLM / FOUNDRY
53. Enumerate every `AEGISBANK_FOUNDRY_*` variable.
54. Is Foundry Local discovery still via CLI subprocess?
55. What would replace Foundry Local in Azure production: Azure OpenAI, Microsoft Foundry model deployment, other?
56. Does the LLM provider abstraction already support a remote/cloud provider?
57. Is an API key currently assumed by the OpenAI-compatible client even for Local?
58. Is model/deployment name configuration separate from credentials?
59. What timeouts/retries/max rounds/token/model parameters are configurable?
60. Which of these belong in App Configuration rather than Key Vault?
61. Is prompt version/config loaded from files or configuration?
62. Can prompt/version changes occur without redeployment?
63. What safety configuration needs production-specific values?

F. CORE BANKING
64. Enumerate `AEGISBANK_CORE_BANKING_*`.
65. Is the Core Banking URL the only agent-side requirement?
66. Does agent→Core Banking currently have authentication?
67. If not, what trust assumption exists locally?
68. Is TLS assumed/configured?
69. What production identity mechanism is architecturally appropriate based on existing code boundaries—Managed Identity/service identity, OAuth2 client credentials, mTLS, API key, or UNKNOWN?
70. Does the agent ever receive direct DB credentials for Core Banking?
71. Are retry/timeout settings configurable?
72. Is correlation/trace context propagated over HTTP?
73. Is there an OpenAPI contract for this boundary?

G. SQLITE / POSTGRESQL
74. Enumerate all DB URLs/DSNs.
75. Which SQLite databases are local-only?
76. Which component owns each database?
77. Does mock-core-banking support PostgreSQL or only SQLite?
78. Is Alembic actually wired into production startup?
79. For RAG PostgreSQL, is password auth currently mandatory?
80. What driver is used (`psycopg`, SQLAlchemy, async/sync)?
81. Is SSL mode configurable/enforced?
82. Is pool size configurable?
83. Are DB statement/connect timeouts configurable?
84. Does pgvector startup create schema/indexes automatically?
85. Are migrations safe to run separately from app startup?
86. Could PostgreSQL Entra authentication be inserted without leaking tokens into static config?
87. Which DB secrets would remain if Managed Identity/Entra is adopted?

H. REDIS
88. Enumerate Redis host/port/url/password/TLS variables.
89. Does code support `rediss://` / TLS?
90. Does it support credentials/password?
91. Does it support Entra authentication or only password/no-auth?
92. What data is cached and explicitly forbidden from cache?
93. Are TTLs configurable?
94. Is Redis optional or startup-critical?
95. What happens during Redis outage?
96. Does application startup fail or degrade safely?
97. Which Redis settings belong in App Configuration?

I. COSMOS DB
98. Enumerate Cosmos endpoint/database/container/key variables.
99. Does code use account keys, connection strings, `DefaultAzureCredential`, or emulator key?
100. Is partition key configurable or schema-fixed?
101. Is consistency level configured?
102. Is retry policy SDK-default or custom?
103. Can the production path be passwordless with Managed Identity?
104. What local emulator-only settings must never reach production?

J. SERVICE BUS / MESSAGING
105. Enumerate Service Bus namespace/connection-string/topic/queue/subscription variables.
106. Does the adapter accept `fully_qualified_namespace` + credential?
107. Does it currently require a connection string?
108. Can Managed Identity remove the Service Bus secret completely?
109. What queue/topic/subscription names should live in App Configuration?
110. What retry/DLQ settings are code config vs broker config?
111. Does the current message consumer run in-process, as Function, or both?
112. How does production intend to scale consumers?
113. Are there emulator-only MSSQL secrets mixed into application config?

K. AZURE FUNCTIONS / EVENT GRID
114. Enumerate Functions settings.
115. What is local-only vs cloud required?
116. Does `local.settings.json` exist and is it gitignored?
117. Is there a safe `.example`?
118. Does production deployment need storage connection strings?
119. Which bindings can use identity-based connections?
120. Does Event Grid delivery authenticate inbound calls or use native trigger infrastructure?
121. Are CloudEvent schemas versioned and independent from configuration?

L. OBSERVABILITY
122. Enumerate `OTEL_*`, Application Insights and logging variables.
123. Does the code support OTLP endpoint/config?
124. Does it require a telemetry connection string?
125. Can Azure Monitor/OpenTelemetry use Managed Identity in the intended deployment?
126. Which resource/service/environment attributes are configurable?
127. Are logs structured?
128. Are secrets/PII redacted before export?
129. Can log level be changed without redeploy?
130. Are sampling ratios configurable?
131. What must NEVER be included in traces/logs?

M. MLFLOW / GENAI OPS
132. Enumerate MLflow/tracking/artifact configuration.
133. Is SQLite tracking local-only?
134. What is the intended production tracking backend?
135. Are credentials currently assumed?
136. Are prompt/model/evaluation dataset versions captured independently from secrets?
137. Which settings belong in App Configuration?

N. CONTAINERS / DEPLOYMENT
138. What process runs inside each Docker image?
139. Which ports are exposed?
140. Which containers need public ingress?
141. Which should be internal-only?
142. Is `read_only` filesystem used?
143. Are containers non-root?
144. What writable volumes remain?
145. Where would durable data live in Azure?
146. Are health `/live` and `/ready` semantics correct for production?
147. Which health checks test dependencies and which only process liveness?
148. Does configuration failure cause readiness failure?
149. Are graceful shutdown/SIGTERM handlers present?
150. Are CPU/memory limits defined?
151. Is autoscaling/KEDA configuration present?
152. Are image tags immutable/digest-pinned?
153. Is ACR target already modeled?
154. Is Azure Container Apps actually the current target or does an ADR specify another platform?

O. NETWORK SECURITY
155. Which services need outbound internet access?
156. Which boundaries can use private endpoints?
157. Does production design include VNet integration?
158. Does any code assume `localhost` or Docker DNS names outside local adapters?
159. List every hardcoded host/port.
160. Is TLS certificate validation ever disabled?
161. Are emulator certificates bypassed?
162. Could such bypass accidentally activate in production?
163. Is CORS configured anywhere?
164. Is inbound authentication configured anywhere?

P. CI/CD
165. Which workflow builds/tests/scans containers?
166. Does CI currently use repository secrets?
167. Which secrets would be needed for Azure deployment?
168. Could GitHub→Azure use OIDC federation instead of a stored service-principal password?
169. Are environments (`dev/staging/prod`) and deployment approvals modeled?
170. Does CI publish SBOM?
171. Does it scan dependencies/images/secrets?
172. Are migrations separated from application deployment?
173. Is rollback documented?
174. Are Azure resource changes IaC-driven?
175. What production IaC actually exists today?

Q. DATA / SECURITY
176. Does any runtime config contain synthetic or real PII?
177. Are there code paths that serialize config wholesale into logs?
178. Are credentials included in exception messages?
179. Are secrets excluded from `/health`, diagnostic endpoints, metrics and AgentOpsSummary?
180. Are Key Vault/App Configuration values included in audit events?
181. Is there explicit secret rotation support?
182. Which secrets can rotate without restart?
183. Which config changes can refresh dynamically?
184. Is there an environment guard preventing emulator/insecure settings in `production`?
185. Are there fail-fast validators preventing `localhost`, default passwords or emulator credentials in production?

R. PRODUCTION ENVIRONMENT MODEL
186. Does the repo define DEV/STAGING/PROD or only LOCAL?
187. What exact resources would be duplicated per environment?
188. Which configuration keys differ per environment?
189. Which secret names differ per environment?
190. Would separate Key Vaults per environment fit current design?
191. Would separate App Configuration stores or labels fit current design?
192. Is customer-visible branding mixed with technical configuration?
193. Is technical identity (`aegisbank`) hardcoded into cloud resource naming?
194. Which settings should remain stable across rebranding?

S. REQUIRED DELIVERABLES — NO IMPLEMENTATION
Generate:
1. `EXECUTIVE SUMMARY`.
2. `CURRENT CONFIGURATION FLOW` ASCII diagram.
3. `VARIABLE INVENTORY` complete table.
4. `SECRET INVENTORY` redacted table.
5. `DIRECT os.getenv / ENV ACCESS` table with exact locations.
6. `LOCAL-ONLY SETTINGS`.
7. `PRODUCTION SETTINGS`.
8. `HARDCODED VALUES / localhost / insecure defaults`.
9. `CURRENT CONFIGURATION PRECEDENCE`.
10. `CURRENT SECRET RESOLUTION FLOW`.
11. `AZURE IDENTITY READINESS`.
12. `PASSWORDLESS OPPORTUNITIES`, classifying each as `READY / SMALL_GAP / MAJOR_GAP / NOT_APPLICABLE`.
13. `APP CONFIGURATION READINESS`.
14. `KEY VAULT READINESS`.
15. `CONTAINER APPS READINESS`.
16. `CI/CD FEDERATED IDENTITY READINESS`.
17. `PRODUCTION BLOCKERS`, severity `P0/P1/P2/P3`.
18. `PRODUCTION RISKS` with likelihood/impact.
19. `ENVIRONMENT MATRIX` local/dev/staging/prod.
20. Proposed classification for every config item: `BOOTSTRAP_ENV`, `APP_CONFIG`, `KEY_VAULT`, `MANAGED_IDENTITY_ELIMINATES_SECRET`, `LOCAL_ONLY`, `CODE_CONSTANT`.
21. Proposed `.env.example` shape containing placeholders ONLY; do not create it.
22. Proposed Azure App Configuration key hierarchy; do not create it.
23. Proposed Key Vault secret naming hierarchy; do not create it.
24. Proposed Managed Identity/RBAC matrix by runtime component.
25. `QUESTIONS STILL UNANSWERED BY CODE`.
26. `MINIMUM SAFE MIGRATION PLAN`, ordered and dependency-aware, but DO NOT IMPLEMENT.
27. `FILES THAT WOULD NEED CHANGES` with REUSE/EXTEND/NEW_COMPONENT_JUSTIFIED classification.
28. Exact current tests that protect configuration/secrets and missing tests that would be required.
29. Final `PRODUCTION_CONFIGURATION_READINESS = READY_FOR_IMPLEMENTATION / DISCOVERY_GAPS / ARCHITECTURAL_BLOCKER`.

Be extremely evidence-driven. Do not infer that a cloud adapter exists merely because a dependency is installed or a document mentions it. Differentiate `IMPLEMENTED`, `CONTRACT-TESTED`, `DOCUMENTED`, `LOCAL-EMULATED`, `CLOUD-UNVERIFIED`. Do not print secret values. Do not make code changes. End with a concise machine-readable JSON summary in addition to the human report so ChatGPT can use the result to produce the implementation prompt.

Ese es el prompt que **ejecutaría primero**, no uno que ya modifique `.env` o Key Vault.

## Qué espero encontrar

Por lo que ya sabemos del repositorio, la arquitectura final probablemente acabará así:

```text
                    AEGISBANK PRODUCTION
                           │
                 Azure Container Apps
                           │
                    Managed Identity
                           │
          ┌────────────────┼─────────────────┐
          │                │                 │
          ▼                ▼                 ▼
 App Configuration     Key Vault       Azure Services
 non-secret config      secrets         passwordless
          │                │                 │
          │                │      ┌──────────┼─────────────┐
          │                │      ▼          ▼             ▼
          │                │   ServiceBus  Cosmos      PostgreSQL
          │                │
          └────────────┬───┘
                       ▼
             ConfigurationProvider
                  SecretProvider
                       │
                       ▼
                 Application
```

El proyecto ya fue diseñado con una filosofía `LOCAL-FIRST + PRODUCTION-MIGRATABLE`, donde adapters/providers permiten sustituir emuladores por servicios reales y donde “el contrato migra, no la implementación”. :chatgpt-content-reference{index="5"}

---

## Un ejemplo de cómo NO debería quedar

No quiero terminar con:

```text
.env.production

POSTGRES_PASSWORD=...
REDIS_PASSWORD=...
COSMOS_KEY=...
SERVICEBUS_CONNECTION_STRING=...
KEYVAULT_CLIENT_SECRET=...
AZURE_CLIENT_SECRET=...
OPENAI_KEY=...
```

Eso sería trasladar deuda local a la nube.

Quiero aspirar a algo más parecido a:

```text
Container Apps bootstrap
────────────────────────
AEGISBANK_ENV=production
AZURE_APPCONFIG_ENDPOINT=https://...
AZURE_KEYVAULT_URI=https://...
OTEL_SERVICE_NAME=aegisbank-agent
```

y después:

```text
Managed Identity
   ↓
App Configuration
   ├─ Agent:MaxRounds
   ├─ RAG:TopK
   ├─ RAG:Retriever
   ├─ CoreBanking:BaseUrl
   ├─ Reliability:TimeoutSeconds
   └─ Observability:LogLevel
```

mientras secretos reales, cuando existan:

```text
Key Vault
   ├─ third-party-api-key
   ├─ unavoidable-legacy-password
   └─ external-system-secret
```

Y, mejor aún:

```text
Service Bus auth      → Managed Identity
Cosmos auth           → Managed Identity
App Config auth       → Managed Identity
Key Vault auth        → Managed Identity
Azure resource auth   → Managed Identity
```

en vez de connection strings.

---

## ¿Por qué App Configuration + Key Vault y no sólo Key Vault?

Porque son problemas diferentes.

**Configuration**:

```text
RAG TopK = 5
timeout = 10
log level = INFO
Core Banking URL = ...
feature flag = ...
```

No son secretos.

Guardarlos en Key Vault:

- encarece conceptualmente la administración;
- mezcla responsabilidades;
- dificulta refresh/feature management;
- convierte Key Vault en una pseudo-base de configuración.

**Secrets**:

```text
password
API key
private token
connection string con credenciales
```

sí corresponden a Key Vault.

Microsoft App Configuration incluso soporta referencias a Key Vault, por lo que puedes centralizar el árbol lógico de configuración manteniendo físicamente el secreto en Key Vault. :chatgpt-content-reference{index="6"}

---

## Y hay una tercera categoría: identidad

Esto es todavía mejor que Key Vault.

Supón que tenemos:

```text
SERVICE_BUS_CONNECTION_STRING
```

La estrategia clásica sería:

```text
connection string
       ↓
Key Vault
       ↓
application
```

Pero si el SDK y arquitectura soportan Entra:

```text
Container App
       ↓
Managed Identity
       ↓
Azure RBAC
       ↓
Service Bus
```

Entonces:

```text
SERVICE_BUS_CONNECTION_STRING
```

**desaparece**.

Ese es el objetivo profesional.

**RBAC = Role-Based Access Control = Control de Acceso Basado en Roles.**

En lugar de darle una llave secreta al programa, Azure sabe quién es la aplicación y qué tiene permitido hacer.

---

# El principio que quiero aplicar a AegisBank

La jerarquía será:

```text
1. ¿Podemos usar Managed Identity?
      ↓ sí
   NO SECRET

2. ¿No podemos y existe un secreto real?
      ↓
   KEY VAULT

3. ¿No es secreto?
      ↓
   APP CONFIGURATION

4. ¿Es sólo bootstrap?
      ↓
   CONTAINER APP ENV

5. ¿Es sólo desarrollo local?
      ↓
   .env.local
```

Con esto estamos aplicando de verdad conceptos de **AI-200**, seguridad cloud y Azure Well-Architected, no simplemente cambiando `localhost` por una URL Azure.

Cuando Antigravity te devuelva el reporte del prompt anterior, pégamelo completo. Con ese inventario podré darte el **segundo prompt**, ya de implementación, que será mucho más preciso: archivos exactos, qué `.env.example` crear o consolidar, qué variables eliminar, qué va a App Configuration, qué va a Key Vault, qué secretos desaparecerán mediante Managed Identity, RBAC exacto por servicio, Bicep/IaC si corresponde, validadores `production`, tests, CI/CD y Definition of Done sin inventar ningún detalle del código actual.
