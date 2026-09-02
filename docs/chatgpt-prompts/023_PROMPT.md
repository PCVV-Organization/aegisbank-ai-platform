# 023 — AegisBank v0.13.0 Azure Functions + Event Grid Local Serverless Foundation

Actúa estrictamente como ORCHESTRATOR principal del milestone.

Tu función NO es producir código indiscriminadamente. Debes:
- reconciliar el estado real de Git antes de escribir;
- adquirir el único writer lock del repositorio;
- leer Teaching Contract + componentes canónicos;
- aplicar DISCOVER BEFORE CREATE;
- dividir el hito en subtareas pequeñas y verificables;
- delegar únicamente investigación READ-ONLY cuando ayude;
- permitir UN SOLO WRITER sobre el working tree;
- reutilizar componentes existentes antes de crear otros;
- detenerte ante colisiones, ambigüedad, drift o regresiones;
- diferenciar siempre evidencia LOCAL, CLOUD y PRODUCTIVA;
- explicar todo como una clase de Maestría en Inteligencia Artificial.

Continúa exclusivamente:
`v0.13.0 — Azure Functions + Event Grid Local Serverless Foundation`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline reportado:
- Redis milestone: `d97eca6`
- Redis corrective: `b19c808`
- ajuste documental final: `68c443c`
- working tree reportado limpio
- SessionGuard reportado liberado

NO asumir baseline hasta verificarlo.

NO iniciar:
- v0.14 Identity/Key Vault/App Configuration
- v0.15 MLOps
- Azure cloud
- Azure CLI
- deployment a Azure
- nuevos agentes
- nuevas operaciones bancarias WRITE
- nuevo RAG
- nuevo MessageBus
- nuevo Outbox
- nueva idempotencia

Guardar este prompt como:
`docs/chatgpt-prompts/023_PROMPT.md`

==================================================
0. TEACHING CONTRACT — OBLIGATORIO
==================================================
Leer primero:
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/OWNERSHIP-MAP.md`
- `docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md`
- `docs/security/DATA-LAYER-SECURITY.md`
- ADRs actuales
- documentación v0.8 Outbox/Messaging
- documentación v0.9 Observability/Audit
- documentación v0.10 CI/DevSecOps
- documentación v0.11 Service Bus
- documentación v0.12 Data Layer

Aplicar permanentemente:
`ONE WRITER, MANY READERS`
`DISCOVER BEFORE CREATE`

Toda creación se clasifica como:
`REUSE`
`EXTEND`
`NEW_COMPONENT_JUSTIFIED`

Antes de crear archivo/clase/helper:
- buscar con rg;
- revisar CANONICAL-COMPONENTS.md;
- revisar imports/callers;
- determinar responsabilidad existente;
- decidir REUSE / EXTEND / NEW;
- justificar cualquier NEW.

Explica desde cero:
serverless, FaaS, Azure Functions, Functions Host, Azure Functions Core Tools,
trigger, binding, input binding, output binding, Python programming model v2,
decorator, stateless function, cold start, warm instance, event-driven architecture,
Azure Event Grid, event, event producer, event subscriber, event handler,
Event Grid topic, event subscription, custom event, CloudEvents, CloudEvents 1.0,
subject, event type, event id, source, data, schema version, event filtering,
retry, dead-lettering, webhook, endpoint validation, idempotent event handler,
at-least-once delivery, correlation ID, trace ID, Azurite, local runtime,
emulator y cloud parity.

Para cada concepto explicar:
- nombre completo/sigla;
- traducción;
- qué significa;
- problema que resuelve;
- cómo funciona internamente;
- por qué existe;
- por qué AegisBank lo necesita;
- ejemplo concreto;
- alternativa y cuándo NO usarlo;
- errores/riesgos;
- relación con Mibanco;
- relación con AI-103/AI-200;
- maturity status.

==================================================
1. GIT PREFLIGHT — READ ONLY
==================================================
Ejecutar:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -8 --oneline
git show --stat --oneline 68c443c
git show --stat --oneline b19c808
git merge-base --is-ancestor b19c808 68c443c
```

Continuar únicamente si:
- branch = master;
- HEAD = 68c443c;
- b19c808 es ancestro de 68c443c;
- working tree limpio.

Si no:
`AEGISBANK_V0.13_BASELINE_AMBIGUOUS`
y STOP.

PROHIBIDO:
- reset
- rebase
- amend
- force
- push

==================================================
2. SESSION GUARD
==================================================
Adquirir SessionGuard con session-id único.

Allowed paths máximos:
`functions/**,contracts/**,deploy/local/**,docs/**,scripts/**,.github/**,ai/agent/tests/serverless/**,README.md,.gitignore`

Si existe otro writer:
`AEGISBANK_CROSS_SESSION_WRITER_ACTIVE`
y STOP.

Luna puede delegar investigación READ-ONLY.
Solo UNA sesión escribe.

Antes de cambios estructurales, staging y commit:
`session_guard check`.

==================================================
3. VERIFICAR DOCUMENTACIÓN OFICIAL ACTUAL
==================================================
Consultar exclusivamente documentación oficial Microsoft para decisiones Azure.

Confirmar como mínimo:
- AI-200 actual exige Event Grid: custom events, filters, retries.
- AI-200 actual exige Azure Functions: serverless APIs, triggers y bindings.
- Azure Functions Core Tools v4 es GA.
- Azure Functions CLI v5 es Preview y NO debe ser baseline.
- Python 3.14 es GA en Azure Functions.
- Python programming model v2 es recomendado para nuevas Function Apps.
- CloudEvents 1.0 es formato recomendado por Azure Event Grid.
- NO asumir que existe emulador oficial completo de Event Grid.

Si la documentación cambió:
usar la información más reciente y documentar el cambio.

==================================================
4. PREFLIGHT LOCAL — NO INSTALAR AUTOMÁTICAMENTE
==================================================
Ejecutar READ-ONLY:
```powershell
func --version
python --version
docker version
docker compose version
```

Requisitos:
- Azure Functions Core Tools v4 GA;
- Python compatible;
- Docker disponible si Azurite fuera necesario.

NO instalar automáticamente:
- Core Tools;
- Azure CLI;
- Azurite global;
- extensiones globales.

Si func no está disponible o no es v4:
`AEGISBANK_V0.13_FUNCTIONS_CORE_TOOLS_REQUIRED`
y STOP, explicando exactamente qué prerequisito falta.

==================================================
5. OBJETIVO ARQUITECTÓNICO
==================================================
Agregar capacidad SERVERLESS EVENT-DRIVEN local SIN reemplazar capacidades existentes.

Arquitectura conceptual:
```
ServiceRequestCreated
        │
        ▼ (existing canonical domain event)
CloudEvent mapping
        │
        ▼
Azure Functions Event Grid Trigger
        │
        ▼
stateless event handler
        │
        ├──> validation
        ├──> idempotency REUSE
        ├──> audit REUSE
        ├──> OTel REUSE
        └──> operational metric REUSE
```

Service Bus continúa siendo:
command/work queue / durable messaging

Event Grid se estudia como:
event notification/routing

NO reemplazar Service Bus.

NO crear:
- segundo MessageBus;
- segundo Outbox;
- segundo AuditLogger;
- segundo metrics framework;
- segundo idempotency engine.

==================================================
6. EVENT GRID vs SERVICE BUS
==================================================
Crear:
`docs/architecture/EVENT-GRID-VS-SERVICE-BUS.md`

==================================================
7. FUNCTION APP CANÓNICA
==================================================
`functions/aegisbank-events/`
Usar Python programming model v2, `function_app.py`, decorators, requirements reproducibles, `host.json`.

==================================================
8. LOCAL SETTINGS + SECRETS
==================================================
`local.settings.json` debe estar gitignored.
Versionar `local.settings.example.json`.

==================================================
9. AZURITE
==================================================
Usarlo solo si Functions Host lo necesita en Docker Compose. Tag exacto y digest.

==================================================
10. CLOUD EVENT CONTRACT
==================================================
CloudEvents 1.0 mapping de `ServiceRequestCreated`.
Tipo: `com.aegisbank.service-request.created.v1`.

==================================================
11. SCHEMA VERSIONING
==================================================
Validación estricta de schema y versiones soportadas.

==================================================
12. AZURE FUNCTION — EVENT GRID TRIGGER
==================================================
Decorador `@app.event_grid_trigger(arg_name="event")`.
Handler fino desacoplado con idempotencia, auditoría y métricas.

==================================================
13. STATELESSNESS
==================================================
Garantía de función sin estado local permanente.

==================================================
14. IDEMPOTENT EVENT HANDLER
==================================================
REUSE `IdempotencyGuard` para deduplicación por event ID.

==================================================
15. LOCAL EVENT GRID TESTING — NO FALSEAR EMULACIÓN
==================================================
`EVENT_GRID_SERVICE_EMULATED = NO`
`EVENT_GRID_HANDLER_LOCAL = COVERED`

==================================================
16-35. VERIFICACIÓN, CALIDAD Y CIERRE
==================================================
Cierre exclusivo con `AEGISBANK_V0.13_FUNCTIONS_EVENTGRID_LOCAL_READY` y `STOP`.
