# 020 — AegisBank v0.12.1 Cosmos DB NoSQL Emulator + Change Feed

Actúa como ORCHESTRATOR principal del milestone.
Tu función NO es generar código indiscriminadamente.
Tu función es:
1. reconciliar el estado real del repositorio;
2. adquirir coordinación single-writer;
3. inspeccionar arquitectura canónica;
4. dividir el trabajo en subtareas pequeñas;
5. permitir investigación READ-ONLY en paralelo cuando ayude;
6. permitir UN SOLO WRITER a la vez;
7. validar cada integración antes de avanzar;
8. detenerte ante cualquier colisión, ambigüedad o regresión;
9. consolidar únicamente evidencia verificable.

Continúa exclusivamente:
`v0.12.1 — Cosmos DB NoSQL Emulator + Change Feed`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline esperado:
- branch: `master`
- HEAD: `044de3e`
- working tree limpio

NO iniciar:
- v0.12.2 Redis
- v0.13
- Azure cloud
- Azure CLI
- nuevos agentes
- nuevas operaciones bancarias WRITE

Guardar este prompt exactamente como:
`docs/chatgpt-prompts/020_PROMPT.md`

==================================================
0. TEACHING CONTRACT — OBLIGATORIO
==================================================
Lee primero:
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/OWNERSHIP-MAP.md`
- `docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md`
- `docs/security/DATA-LAYER-SECURITY.md`
- documentación v0.12 PostgreSQL/pgvector

Mantener permanentemente:
`ONE WRITER, MANY READERS`
y:
`DISCOVER BEFORE CREATE`

Antes de crear cualquier clase/módulo/helper:
1. buscar con `rg`;
2. revisar CANONICAL-COMPONENTS;
3. revisar imports/callers;
4. clasificar obligatoriamente:
   - REUSE
   - EXTEND
   - NEW_COMPONENT_JUSTIFIED
5. si es NEW, justificar por escrito por qué no duplica una responsabilidad existente.

Explica desde cero, como profesor de Maestría en IA:
- NoSQL
- document database
- Azure Cosmos DB
- API for NoSQL
- database
- container
- item/document
- JSON
- partition key
- logical partition
- physical partition
- cardinality
- hot partition
- point read
- cross-partition query
- TTL
- Change Feed
- Change Feed Processor
- checkpoint
- lease
- at-least-once delivery
- idempotent consumer
- continuation token
- consistency level
- Request Unit / RU
- indexing policy
- gateway mode
- emulator
- cloud parity

Para CADA concepto explicar:
1. nombre completo y sigla;
2. traducción;
3. qué significa;
4. qué problema resuelve;
5. cómo funciona internamente;
6. por qué existe;
7. por qué AegisBank lo necesita;
8. ejemplo concreto del milestone;
9. alternativa y cuándo NO usarlo;
10. errores/riesgos típicos;
11. relación con Mibanco;
12. relación con AI-103/AI-200;
13. maturity status.

==================================================
1. GIT PREFLIGHT — READ ONLY
==================================================
Antes de escribir ejecutar:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -5 --oneline
```
Debe verificarse:
HEAD = 044de3e
y working tree completamente limpio.
Si no:
AEGISBANK_V0.12_1_BASELINE_MISMATCH
y STOP.

PROHIBIDO:
reset
rebase
amend
force
push

==================================================
2. SESSION GUARD
==================================================
Adquirir SessionGuard con session-id único para Luna/orchestrator.
Allowed paths máximos:
ai/**,deploy/local/**,contracts/**,docs/**,scripts/**,.github/**,README.md

Si existe writer activo:
AEGISBANK_CROSS_SESSION_WRITER_ACTIVE
y STOP.

Luna puede delegar tareas de INVESTIGACIÓN READ-ONLY a otros agentes,
pero solamente una sesión puede modificar el working tree.

Antes de:
WRITE importante
staging
commit
ejecutar:
session_guard check

Si HEAD cambia:
AEGISBANK_CROSS_SESSION_HEAD_MOVED
Si aparecen paths inesperados:
AEGISBANK_CROSS_SESSION_PATH_COLLISION
y STOP.

==================================================
3. VERIFICAR DOCUMENTACIÓN OFICIAL ACTUAL
==================================================
Antes de seleccionar imagen/SDK consulta documentación oficial Microsoft actual.
Objetivo:
Azure Cosmos DB Emulator vNext Linux
API for NoSQL
Docker
No depender de documentación antigua del emulator Windows.

Verificar explícitamente:
imagen oficial MCR actual;
feature support;
limitaciones actuales;
Python SDK estable actual.

La documentación oficial actual indica como referencia:
mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest
pero NO asumir reproducibilidad de un tag flotante.
Después del pull registrar:
image tag
image ID
RepoDigest si está disponible
No inventar una versión semántica que Microsoft no publique.

==================================================
4. LIMITACIONES DEL EMULATOR — NO FALSEAR COBERTURA
==================================================
Registrar explícitamente antes de implementar:
LOCAL EMULATOR actualmente soporta, entre otras:
API for NoSQL
Gateway mode
database/container/item CRUD
partitioned containers
TTL
Change Feed
Batch/Bulk
queries comunes

La documentación oficial actualmente indica limitaciones como:
Request Units: NOT YET IMPLEMENTED
custom indexing policy: NO-OP
collection performance changes: NOT YET IMPLEMENTED
parallel partition query: NOT YET IMPLEMENTED

Por tanto:
NO afirmar:
RU-COVERED
NO afirmar:
CUSTOM-INDEX-POLICY-COVERED
NO afirmar:
COSMOS-VECTOR-SEARCH-COVERED
si el emulator no lo demuestra realmente.

Usar estados:
LOCAL-COSMOS-COVERED
EMULATOR-LIMITATION
COSMOS-CLOUD-PENDING

==================================================
5. OBJETIVO ARQUITECTÓNICO
==================================================
Agregar Cosmos DB como NUEVA capacidad de persistencia documental/event-driven.
NO sustituir PostgreSQL/pgvector.

Responsabilidades:
PostgreSQL + pgvector
→ corpus/vector retrieval persistente

Cosmos DB
→ documentos/eventos/state NoSQL con partición y Change Feed

No crear otro RAG.

Arquitectura conceptual:
AegisBank
|
+--> PostgreSQL/pgvector
|    RAG/vector retrieval
|
+--> Cosmos DB NoSQL
     document/state/event data
     |
     +--> Change Feed
          |
          +--> idempotent consumer

Mantener separación de responsabilidades.

==================================================
6. EXTENDER DOCKER COMPOSE
==================================================
Primero inspeccionar:
deploy/local/docker-compose.yml

Preferir EXTEND del compose canónico existente.
Añadir Cosmos emulator bajo un profile dedicado, por ejemplo:
cosmos

NO crear otro compose equivalente salvo justificación.
Exponer únicamente puertos necesarios:
Cosmos gateway: 8081
health: 8080
Data Explorer 1234 solo si aporta valor al laboratorio

Usar health checks oficiales:
/alive
/ready
/status
No considerar logs como mecanismo principal de readiness.
No dejar el container corriendo tras aceptación.

==================================================
7. SDK PYTHON
==================================================
Usar SDK oficial:
azure-cosmos
Verificar primero la versión estable actual antes de pinning.
No introducir wrappers paralelos innecesarios.
Crear/EXTEND un adapter/repositorio canónico únicamente si la arquitectura existente lo justifica.
No colocar lógica de negocio dentro del SDK adapter.

==================================================
8. DATA MODEL
==================================================
Crear una base de datos local pedagógica:
aegisbank

Crear un container apropiado al caso de uso.
Elegir y JUSTIFICAR la partition key según los access patterns.
Antes de decidir, comparar explícitamente candidatos:
/customer_id
/topic
/document_id
otra opción solo con evidencia

No escoger la partition key por intuición.
Documentar:
principales writes;
point reads;
queries;
cardinalidad;
posibilidad de hot partition;
necesidad de aislamiento por customer.

La partition key debe ser:
estable;
presente;
suficientemente distribuida;
alineada con consultas dominantes.

Crear:
docs/architecture/COSMOS-PARTITION-DESIGN.md

==================================================
9. ITEMS JSON
==================================================
Diseñar schema documental mínimo y versionado.
Cada item debe incluir cuando aplique:
id
partition key
schema_version
event_type o document_type
timestamp UTC
synthetic identifiers
payload
metadata

Solo datos sintéticos.
NO PII real.
No duplicar OutboxEvent arbitrariamente.
Si Cosmos recibe eventos derivados de Outbox:
documentar claramente dónde termina la responsabilidad de Outbox
y dónde comienza Cosmos persistence/change processing.

==================================================
10. CRUD + POINT READS
==================================================
Implementar y probar:
create
point read por id + partition key
replace/update
patch si es compatible
query
delete

Explicar por qué:
point read
es diferente a:
query
y por qué conocer id + partition key permite una operación más dirigida.
No intentar medir RU reales porque emulator no las implementa actualmente.

==================================================
11. PARTITIONING
==================================================
Demostrar realmente:
creación de container particionado;
items distribuidos por múltiples partition-key values;
point reads con partition key correcta;
error/no match con partition key incorrecta;
query dirigida por partition key;
consulta que conceptualmente sería cross-partition.

Enseñar:
Logical Partition
vs
Physical Partition
pero NO afirmar distribución física real representativa de Azure cloud usando un emulator local pequeño.

==================================================
12. TTL
==================================================
TTL = Time To Live.
Implementar un container/item de laboratorio con expiración.
Demostrar:
item creado
→ visible
→ transcurre TTL controlado
→ item expira

No usar sleeps largos.
Elegir TTL pequeño y test determinista/tolerante.
Explicar aplicaciones bancarias/AgentOps apropiadas:
estados temporales
cache/state efímero
eventos de laboratorio
NO aplicar TTL a información que requiera retención/auditoría.

==================================================
13. CHANGE FEED
==================================================
Implementar Change Feed REAL contra el emulator.
Demostrar:
CREATE item
↓
Change Feed
↓
consumer
↓
evento observado

UPDATE item
↓
Change Feed
↓
consumer
↓
actualización observada

No confundir:
Cosmos Change Feed
con:
Service Bus Queue

Explicar:
Change Feed
= historial incremental de cambios del datastore
Service Bus
= broker explícito de mensajería

==================================================
14. CHANGE FEED PROCESSING
==================================================
Primero verificar capacidades reales del Python SDK + emulator.
Preferir mecanismo oficial soportado.
Debe existir:
checkpoint/continuation state cuando aplique;
idempotent processing;
restart/resume test;
no doble side effect por redelivery/re-read.

REUSE el concepto/código canónico de idempotent consumer cuando sea posible.
NO crear otra implementación de idempotencia independiente.

Si Python SDK/emulator no ofrece Change Feed Processor administrado equivalente:
NO inventarlo.
Implementar lectura incremental oficial disponible y documentar:
CHANGE_FEED_PROCESSOR_MANAGED = CLOUD/SDK-PENDING
según evidencia.

==================================================
15. CHANGE FEED + IDEMPOTENCY
==================================================
Acceptance obligatorio:
mismo cambio observado/reprocesado
→ un único efecto lógico

Usar un deterministic event/change identity.
No depender únicamente de "exactly once".
Enseñar:
at-least-once
y por qué consumidores idempotentes siguen siendo necesarios.

==================================================
16. FAILURE TESTS
==================================================
Probar:
emulator unavailable -> error controlado.
wrong database -> error claro.
wrong container -> error claro.
wrong partition key -> no acceso accidental.
duplicate create -> conflicto manejado.
idempotent upsert definido explícitamente.
TTL expiration.
Change Feed create.
Change Feed update.
resume/checkpoint.
duplicate processing -> one logical effect.
malformed document -> rejected.
connection/config missing -> fail fast.
no production secret committed.

==================================================
17. INDEXING POLICY — SOLO ENSEÑAR/LIMITACIÓN
==================================================
AI-200 exige comprender indexing policies.
Pero la documentación actual del emulator vNext indica que:
custom indexing policy = NO-OP.

Por tanto:
enseñar qué es indexing policy;
guardar ejemplo declarativo pedagógico si aporta valor;
NO usarlo para probar optimización real;
NO afirmar efecto en query performance.

Estado:
COSMOS_INDEXING_POLICY_CLOUD_PENDING

==================================================
18. REQUEST UNITS
==================================================
RU = Request Unit.
AI-200 exige comprender:
RU consumption;
optimization;
throughput.

Pero el emulator vNext actual indica:
Request Units = NOT YET IMPLEMENTED.

Por tanto:
enseñar el concepto;
explicar point read vs expensive query;
documentar cómo se mediría en cloud;
NO inventar RU values;
NO crear benchmark falso.

Estado:
COSMOS_RU_CLOUD_PENDING

==================================================
19. CONSISTENCY LEVELS
==================================================
Enseñar:
Strong
Bounded Staleness
Session
Consistent Prefix
Eventual

No afirmar que el pequeño emulator reproduce fielmente latencia/distribución multi-region.

Documentar:
CONSISTENCY_CONCEPT_COVERED
MULTI_REGION_BEHAVIOR_CLOUD_PENDING

==================================================
20. VECTOR SEARCH
==================================================
AI-200 incluye embeddings/vector search en Cosmos DB.
Pero NO implementar ni afirmar vector indexing local a menos que la documentación oficial actual del emulator confirme soporte funcional.

Si no existe soporte:
COSMOS_VECTOR_SEARCH_CLOUD_PENDING

Mantener pgvector v0.12 como vector implementation real ya demostrada.
No duplicarla artificialmente dentro de Cosmos.

==================================================
21. OBSERVABILITY
==================================================
El emulator actual soporta OpenTelemetry.
Integrar solo si se puede REUSE la observabilidad canónica sin scope creep.
Como mínimo registrar:
operation type
success/failure
latency local
correlation_id
Change Feed processed count
TTL test state

No capturar secrets ni documentos completos innecesariamente.
Si habilitar OTLP requiere infraestructura nueva significativa:
documentar y diferir.

==================================================
22. SECURITY
==================================================
Actualizar:
docs/security/DATA-LAYER-SECURITY.md

Explicar:
LOCAL:
emulator key no productiva;
synthetic data;
connection configuration;
no secret committed.

CLOUD-PENDING:
Microsoft Entra ID
Managed Identity
RBAC
private endpoints/VNet
encryption/key management
backup/restore
geo-replication

No afirmar seguridad cloud con emulator.

==================================================
23. CONTRACT TESTS
==================================================
Crear contratos para:
item schema/version;
partition-key field required;
Change Feed processed event;
no accidental new agent WRITE capability.

Los contratos deben fallar ante breaking change no versionado.

==================================================
24. QUALITY GATE
==================================================
Añadir:
cosmos/integration gate

Los tests normales rápidos NO deben requerir Docker Cosmos.
El gate Cosmos debe:
levantar emulator;
esperar /ready;
correr acceptance;
capturar evidencia;
bajar emulator aunque falle una prueba.
No dejar recursos vivos.

==================================================
25. DUPLICATION / ARCHITECTURE AUDIT
==================================================
Ejecutar:
Pylint R0801
y revisar semánticamente:
no segundo Outbox;
no segundo MessageBus;
no segundo idempotency engine;
no segundo RAG;
no segundo telemetry system;
no segundo configuration layer innecesario.

Mantener:
NEW TRUE_DUPLICATION = 0

==================================================
26. AI-200 COVERAGE
==================================================
Actualizar:
docs/learning/GLOSSARY.md
docs/learning/MASTERS-NOTES.md
docs/requirements/COVERAGE-MATRIX.md

Marcar como:
LOCAL-COSMOS-COVERED
solo:
NoSQL CRUD
partition key mechanics
partitioned container
point reads
queries
TTL
Change Feed
idempotent processing
emulator health/local lifecycle

Marcar:
COSMOS-CLOUD-PENDING
para:
RU measurements/tuning
effective custom indexing policy
vector indexing/search si emulator no lo soporta
multi-region consistency behavior
autoscale/serverless throughput
production identity/networking
backup/geo-replication

==================================================
27. NO REDIS TODAVÍA
==================================================
Solo documentar:
v0.12.2 — Redis Cache + Vector/Search Semantics
NO instalar Redis.
NO crear Redis adapter.
NO modificar roadmap fuera de documentación mínima.

==================================================
28. VALIDACIÓN FINAL
==================================================
Ejecutar:
Cosmos integration tests;
suite completa del repo;
RAG;
Agent;
ML;
Core Banking;
PostgreSQL data regressions;
contracts;
E2E;
fast quality gate;
Ruff;
format;
compileall;
Bandit;
pip-audit;
secret scan;
Pylint R0801;
git diff --check.

No ejecutar Kubernetes/container gates pesados si no son necesarios para verificar cambios de Cosmos.

==================================================
29. CLEANUP
==================================================
Al finalizar:
Cosmos emulator detenido;
Data Explorer detenido;
ningún container Cosmos activo;
no borrar imágenes Docker globales;
no borrar PostgreSQL image;
no tocar Kubernetes;
no port-forward;
SessionGuard liberado solamente después de commit.

==================================================
30. GIT
==================================================
Antes de staging:
session_guard check

Ejecutar:
git rev-parse HEAD
git status --porcelain=v2
git diff --name-status
git diff --check

PROHIBIDO:
worktrees
git add .
git add -A
reset
rebase
amend
push

Stagear SOLO paths legítimos de v0.12.1.
Revisar:
git diff --cached --name-only
git diff --cached --stat
git diff --cached

Repetir:
session_guard check
antes del commit.

Si TODO pasa crear:
feat(v0.12): establish Cosmos DB change feed foundation

NO push.
Liberar SessionGuard después.

==================================================
31. INFORME FINAL DEL ORCHESTRATOR
==================================================
Luna debe entregar un único informe consolidado y preciso.
No copiar logs enormes.
Reportar:
CANONICAL_BASELINE:
...
ORCHESTRATION:
read-only delegated tasks:
writer session:
collisions detected:
COSMOS EMULATOR:
image:
digest:
protocol:
health:
feature limitations:
SDK:
azure-cosmos version:
DATA MODEL:
database:
container:
partition key:
justification:
CRUD:
create:
read:
patch/update:
query:
delete:
PARTITIONING:
point read:
partition query:
cross-partition concept:
TTL:
PASS/FAIL
evidence:
CHANGE FEED:
create observed:
update observed:
checkpoint/resume:
idempotent processing:
INDEXING POLICY:
EMULATOR-LIMITATION / CLOUD-PENDING
REQUEST UNITS:
EMULATOR-LIMITATION / CLOUD-PENDING
CONSISTENCY:
concept coverage:
cloud behavior pending:
VECTOR SEARCH:
CLOUD-PENDING / supported evidence if documentation changed
SECURITY:
...
ARCHITECTURE:
REUSE:
EXTEND:
NEW_COMPONENT_JUSTIFIED:
new true duplication:
TESTS:
...
QUALITY GATE:
PASS/FAIL
CI STATUS:
CI-CONFIGURED / RUNNER-PENDING
WORKING TREE:
clean/dirty
PUSH:
NO

Finalizar únicamente con:
AEGISBANK_V0.12_COSMOS_CHANGE_FEED_READY
y STOP.
