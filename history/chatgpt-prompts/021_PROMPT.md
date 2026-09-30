# 021 — AegisBank v0.12.2 Redis Cache + Vector/Search Semantics

Actúa estrictamente como ORCHESTRATOR principal del milestone.

Tu función NO es escribir código indiscriminadamente. Debes:
- reconciliar el estado real del repositorio;
- adquirir coordinación single-writer;
- inspeccionar componentes canónicos antes de crear nada;
- dividir el trabajo en subtareas pequeñas;
- delegar solo investigación READ-ONLY cuando aporte valor;
- permitir UN SOLO WRITER;
- validar cada integración antes de avanzar;
- detenerte ante colisiones, ambigüedad o regresiones;
- consolidar únicamente evidencia verificable;
- explicar todo como una clase de Maestría en Inteligencia Artificial.

Continúa exclusivamente:
`v0.12.2 — Redis Cache + Vector/Search Semantics`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Estado reportado:
- Cosmos previo: `d95baeb`
- Corrective R1 posterior: `c526982`
- working tree reportado limpio

NO asumir baseline hasta verificarlo.

NO iniciar:
- v0.13
- Event Grid
- Azure Functions
- Azure cloud
- Azure CLI
- MLOps
- nuevas operaciones bancarias WRITE
- nuevos agentes
- nuevos sistemas RAG

Guardar este prompt como:
`docs/chatgpt-prompts/021_PROMPT.md`

==================================================
0. TEACHING CONTRACT
==================================================
Leer primero:
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/OWNERSHIP-MAP.md`
- `docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md`
- `docs/security/DATA-LAYER-SECURITY.md`
- documentación v0.12 PostgreSQL/pgvector
- documentación v0.12.1 Cosmos DB
- documentación v0.12.0-R1 Grounded Response Consistency

Aplicar:
`ONE WRITER, MANY READERS`
`DISCOVER BEFORE CREATE`

Toda creación debe clasificarse como:
- `REUSE`
- `EXTEND`
- `NEW_COMPONENT_JUSTIFIED`

Antes de crear módulo/clase/helper:
- buscar con `rg`;
- revisar CANONICAL-COMPONENTS;
- revisar imports/callers;
- decidir REUSE/EXTEND/NEW;
- justificar cualquier NEW.

Explica desde cero:
Redis, in-memory database, key-value store, cache, cache-aside, cache hit, cache miss, hit ratio, TTL, expiration, invalidation, stale data, cache key, namespace/prefix, serialization, cache stampede, thundering herd, single-flight, distributed lock, eviction policy, LRU, LFU, no-eviction, persistence, RDB, AOF, Redis Search, vector index, KNN, HNSW, semantic cache, similarity threshold, false positive, Redis connection pool, Azure Managed Redis, RediSearch, local emulator y cloud parity.

Para cada concepto:
1. nombre/sigla;
2. traducción;
3. significado;
4. problema que resuelve;
5. funcionamiento interno;
6. por qué existe;
7. por qué AegisBank lo necesita;
8. ejemplo;
9. alternativa/cuándo NO usarlo;
10. riesgos;
11. relación Mibanco;
12. relación AI-103/AI-200;
13. maturity status.

==================================================
1. RECONCILIAR GIT — READ ONLY
==================================================
Ejecutar:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -8 --oneline
git show --stat --oneline d95baeb
git show --stat --oneline c526982
git merge-base --is-ancestor d95baeb c526982
git diff --name-status d95baeb c526982
```
Confirmar:
c526982 es HEAD canónico;
contiene/desciende del trabajo Cosmos d95baeb;
working tree limpio.

Si no puede probarse:
AEGISBANK_V0.12_2_BASELINE_AMBIGUOUS
y STOP.

NO reset/rebase/amend/push.

==================================================
2. SESSION GUARD
==================================================
Adquirir SessionGuard con session-id único.
Allowed paths:
ai/**,deploy/local/**,contracts/**,docs/**,scripts/**,.github/**,README.md,.gitignore

Si existe writer:
AEGISBANK_CROSS_SESSION_WRITER_ACTIVE
y STOP.

Luna puede delegar investigación READ-ONLY, pero solo UNA sesión puede escribir.

Antes de cambios estructurales, staging y commit:
session_guard check.

==================================================
3. VERIFICAR DOCUMENTACIÓN OFICIAL ACTUAL
==================================================
Confirmar antes de implementar:
- Azure Managed Redis NO tiene emulador local oficial.
- Microsoft recomienda Redis local/Open Source para desarrollo similar.
- AI-200 exige caching, expiration, invalidation y vector indexing.
- Azure Managed Redis usa Redis Search/RediSearch para vector search.
- Redis Open Source 8 integra Redis Search.

Target cloud conceptual:
Azure Managed Redis

Target local:
Redis Open Source

NO afirmar paridad total.

==================================================
4. SELECCIÓN DE REDIS LOCAL
==================================================
Usar Docker Linux containers.
Verificar imagen oficial actual de Redis Open Source.
Preferir GA estable con fixes de seguridad actuales.

NO usar:
- RC
- beta
- latest
sin justificación.

Registrar:
- Redis version
- Docker image tag
- image ID
- RepoDigest cuando exista

No push de imagen.
No instalar Redis globalmente en Windows.

==================================================
5. OBJETIVO ARQUITECTÓNICO
==================================================
Redis NO reemplaza:
- PostgreSQL/pgvector como vector persistence canónica;
- Cosmos DB como document/change-feed store;
- Service Bus como broker;
- Outbox;
- Core Banking;
- RAG canónico.

Redis añade dos capacidades:
A. cache de baja latencia;
B. vector/search semantics como laboratorio AI-200.

Arquitectura:
Source of truth
(PostgreSQL / Core / authorized corpus)
|
v
Cache-aside policy
|
+--> Redis HIT -> return
|
+--> Redis MISS
|
v
canonical source
|
v
cache SET + TTL

Separadamente:
authorized chunks/embeddings
|
v
Redis Search vector index
|
v
retriever adapter experimental

No crear otro RAG engine.

==================================================
6. DISCOVER BEFORE CREATE — CACHE OWNERSHIP
==================================================
Buscar:
cache
ttl
redis
memo
retriever
embedding
connection pool

Determinar si existe abstracción reutilizable.

Si NO existe cache abstraction:
NEW_COMPONENT_JUSTIFIED
puede ser válido porque cache es una responsabilidad nueva.

NO crear:
- otro retry;
- otro circuit breaker;
- otro metrics system;
- otro tracing system;
- otro idempotency engine.

REUSE los componentes existentes.

==================================================
7. CACHE POLICY
==================================================
Definir policy explícita.
Por defecto, NO cachear datos financieros customer-specific sensibles o muy dinámicos:
- saldo de préstamo;
- próxima cuota;
- estado transaccional;
salvo justificación explícita de consistencia/staleness.

Primer scope seguro:
- resultados de retrieval de conocimiento autorizado;
- metadatos de corpus;
- resultados costosos no sensibles;
- opcionalmente "not found" con TTL muy corto y justificado.

Crear:
`docs/architecture/REDIS-CACHE-POLICY.md`

La decisión cacheable/non-cacheable NO depende del LLM.

==================================================
8. CACHE-ASIDE
==================================================
Implementar:
- construir key canónica;
- GET;
- HIT -> devolver;
- MISS -> consultar source of truth;
- serializar;
- SET con TTL;
- devolver.

No write-through/write-behind salvo justificación.

Métricas:
- cache_hit_count
- cache_miss_count
- cache_hit_ratio
- cache_set_count
- cache_invalidation_count
- cache_error_count
- cache_latency_ms

EXTEND OperationalMetrics.
No crear métricas paralelas.

==================================================
9. CACHE KEY DESIGN
==================================================
Diseñar keys versionadas y namespaced.
Ejemplo conceptual:
`aegisbank:rag:v1:<corpus_version>:<query_digest>`

No usar raw prompts completos.
No incluir PII.
Evitar colisiones.

Si cambia serialization contract:
cambiar key version.

==================================================
10. TTL + EXPIRATION
==================================================
Demostrar:
SET + TTL
→ HIT
→ expira
→ MISS

TTL corto solo en acceptance tests.

Explicar tradeoff:
TTL corto = menos stale / menos hit ratio.
TTL largo = más hits / mayor riesgo stale.

No fijar TTL "productivo" arbitrario.

==================================================
11. INVALIDATION
==================================================
Cuando cambia la fuente autorizada:
INVALIDAR cache.

Demostrar:
- cache result;
- version bump de corpus;
- invalidar namespace/key;
- siguiente read = MISS;
- recargar source actual.

No invalidar todo Redis si puede hacerse por namespace/version.

==================================================
12. STALE DATA
==================================================
Acceptance:
- entrada vieja existe;
- corpus_version cambia;
- policy impide servir entrada vieja.

Para políticas bancarias:
stale policy = riesgo operativo/compliance.

==================================================
13. CACHE STAMPEDE
==================================================
Simular N requests concurrentes a una key ausente.

Sin protección:
N requests -> N source loads.

Con single-flight:
N requests -> 1 source load.

No reutilizar SessionGuard:
CACHE_LOCK != SESSION_GUARD.

Si lock Redis:
- token único;
- TTL;
- liberar solo si token coincide.

==================================================
14. REDIS FAILURE POLICY
==================================================
Redis cache NO debe convertirse en single point of failure para READ cacheables.

Si Redis cae:
cache failure
→ observabilidad
→ fallback source of truth
→ respuesta correcta.

Acceptance obligatorio.

==================================================
15. CONNECTION POOL
==================================================
Usar redis-py estable y compatible con Python 3.14.
Configurar connection pool reutilizable.

No conexión nueva por cada GET/SET.
No pool ilimitado.
No tuning productivo inventado.

==================================================
16. SERIALIZATION
==================================================
Formato simple, explícito y versionado.
Preferir JSON cuando baste.
NO pickle para datos no confiables.

Tests:
- serialize/deserialize;
- schema version;
- malformed cached value;
- incompatible version -> MISS/error controlado.

==================================================
17. EVICTION POLICY
==================================================
Enseñar:
- noeviction
- allkeys-lru
- allkeys-lfu
- volatile-*

No afirmar equivalencia automática con Azure Managed Redis.
Documentar que Azure Managed Redis con Redis Search requiere planificación específica de eviction/capacity.

==================================================
18. PERSISTENCE
==================================================
Enseñar:
RDB = snapshots.
AOF = Append Only File.

Pero Redis sigue siendo cache:
CACHE DATA CAN BE REBUILT.

No convertirlo en system of record.

==================================================
19. VECTOR SEARCH — REDIS SEARCH
==================================================
AI-200 exige vector indexing.
Usar Redis Search local.

REUSE:
`LocalDenseEmbeddingModel`

No crear otro embedding model.

REUSE:
- corpus
- chunking
- qrels
- Retriever interface

Crear solo adapter Redis vectorial si encaja.
NO nuevo RAG.

==================================================
20. VECTOR SCHEMA
==================================================
Índice con:
- chunk_id
- document_id
- version
- status
- topic
- content/referencia
- embedding
- embedding_model_id

Preferir HNSW estable.
No usar Vector Set beta como baseline bancario.

==================================================
21. VECTOR SEARCH + FILTERS
==================================================
Demostrar:
- KNN/vector similarity;
- status=active;
- topic filtering;
- embedding model/version filter;
- superseded excluded.

Autorización/vigencia NO depende del LLM.

==================================================
22. REDIS VECTOR vs PGVECTOR
==================================================
Comparar adapters:
`PgVectorRetriever` vs `RedisVectorRetriever`

Mismos:
- corpus
- embeddings
- qrels
- top_k
- metrics

Evaluar:
- nDCG@5
- MRR@5
- Precision@5
- Recall@5
- local latency

No afirmar "Redis mejor" solo por latencia.
PostgreSQL sigue como persistent vector store canónico salvo ADR futura.

==================================================
23. SEMANTIC CACHE — SOLO SI ES SEGURO
==================================================
Opcional.
NO cachear respuestas finales LLM en este milestone.

Si se demuestra semantic caching:
cachear retrieval result/reference, no final banking answer.

Threshold conservador.
Medir false positives.

Si no hay evidencia suficiente:
`SEMANTIC_CACHE_DEFERRED_FOR_SAFETY`
es resultado válido.

==================================================
24. OBSERVABILITY
==================================================
REUSE OTel/logging/metrics.

Instrumentar:
- cache.get
- cache.set
- cache.invalidate
- cache.fallback
- redis.vector.search

Atributos:
- hit/miss
- namespace
- TTL class
- latency
- error
- vector top_k

No raw customer data ni prompts completos.

==================================================
25. SECURITY
==================================================
Actualizar:
`docs/security/DATA-LAYER-SECURITY.md`

Local:
- loopback/container network;
- synthetic data;
- no passwords hardcoded;
- no public exposure innecesaria;
- no PII real.

Cloud pending:
- Entra ID/Managed Identity;
- TLS;
- private networking;
- RBAC;
- geo replication;
- SLA;
- managed clustering.

==================================================
26. ACCEPTANCE TESTS — CACHE
==================================================
Cubrir:
- MISS -> source load -> SET.
- second read -> HIT.
- TTL expiry -> MISS.
- invalidation -> MISS.
- version change -> old cache not served.
- malformed cache -> fallback.
- Redis unavailable -> source fallback.
- stampede -> one logical source load.
- namespace collision prevented.
- sensitive customer query -> NOT cached.
- metrics HIT/MISS correct.
- tracing present.

==================================================
27. ACCEPTANCE TESTS — VECTOR
==================================================
Cubrir:
- index created.
- canonical model/dimension.
- KNN ranked hits.
- active filter.
- superseded excluded.
- topic filter.
- dimension mismatch rejected.
- duplicate ingest idempotent.
- malformed vector rejected.
- same qrels preserved.
- PgVector regression preserved.
- no new WRITE tool exposed.

==================================================
28. LOCAL vs AZURE PARITY
==================================================
`LOCAL-REDIS-COVERED` solo:
- GET/SET
- cache-aside
- TTL
- expiration
- invalidation
- connection pooling
- failure fallback
- stampede protection
- Redis Search vector index
- local KNN/filter semantics

`AZURE-MANAGED-REDIS-CLOUD-PENDING`:
- provisioning tiers;
- cluster policy;
- Managed Identity;
- private networking;
- Azure monitoring;
- production scaling;
- enterprise SLA;
- managed RediSearch provisioning;
- cloud capacity/performance.

==================================================
29. QUALITY GATE
==================================================
Añadir:
`redis/integration gate`

Los tests rápidos NO deben requerir Redis Docker.

Gate:
- levantar Redis;
- esperar PING;
- cache acceptance;
- vector acceptance;
- guardar evidencia;
- bajar Redis incluso si falla.

==================================================
30. DUPLICATION + ARCHITECTURE AUDIT
==================================================
Ejecutar Pylint R0801.

Revisar:
- no segundo Retriever interface;
- no segundo embedding model;
- no segundo metrics system;
- no segundo retry engine;
- no framework de connection-management duplicado;
- no nuevo source of truth.

Mantener:
`NEW TRUE_DUPLICATION = 0`

==================================================
31. AI-200 COVERAGE
==================================================
Actualizar:
- `docs/learning/GLOSSARY.md`
- `docs/learning/MASTERS-NOTES.md`
- `docs/requirements/COVERAGE-MATRIX.md`

Marcar:
`LOCAL-REDIS-COVERED`
- caching
- cache-aside
- expiration/TTL
- invalidation
- vector indexing
- vector similarity
- metadata filters
- connection pool
- failure fallback

Marcar:
`AZURE-MANAGED-REDIS-CLOUD-PENDING`
para capacidades Azure no ejecutadas.

==================================================
32. VALIDACIÓN FINAL
==================================================
Ejecutar:
- Redis integration tests;
- suite completa;
- agent;
- RAG;
- Core Banking;
- ML;
- PostgreSQL regressions;
- Cosmos regressions;
- contracts;
- E2E;
- fast quality gate;
- Ruff;
- format;
- compileall;
- Bandit;
- pip-audit;
- secret scan;
- Pylint R0801;
- git diff --check.

No levantar Kubernetes/Service Bus si no es necesario.

==================================================
33. CLEANUP
==================================================
Al finalizar:
- Redis apagado;
- no port-forward;
- PostgreSQL/Cosmos apagados si se levantaron;
- Kubernetes intacto;
- no borrar imágenes/cache globales;
- SessionGuard se libera después del commit.

==================================================
34. GIT
==================================================
Antes de staging:
session_guard check

Ejecutar:
```powershell
git rev-parse HEAD
git status --porcelain=v2
git diff --name-status
git diff --check
```

PROHIBIDO:
worktrees
git add .
git add -A
reset
rebase
amend
push

Stage SOLO v0.12.2.

Revisar:
```powershell
git diff --cached --name-only
git diff --cached --stat
git diff --cached
```

Repetir session_guard check.

Si TODO pasa crear:
`feat(v0.12): establish Redis cache and vector search foundation`

NO push.
Liberar SessionGuard.

==================================================
35. INFORME FINAL DEL ORCHESTRATOR
==================================================
Reportar según schema oficial.

Finalizar únicamente con:
AEGISBANK_V0.12_REDIS_CACHE_VECTOR_READY
y STOP.

NO iniciar v0.13.
