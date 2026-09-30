# 022A — AegisBank v0.12.2-R1 Redis Reproducibility + Evidence Hardening

Actúa estrictamente como ORCHESTRATOR.

Continúa exclusivamente:
`v0.12.2-R1 — Redis Reproducibility + Evidence Hardening`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Estado reportado:
- baseline previo: `c526982`
- Redis milestone: `d97eca6 feat(v0.12): establish Redis cache and vector search foundation`
- working tree limpio

NO iniciar v0.13 todavía.

==================================================
0. TEACHING CONTRACT
==================================================
Lee primero:
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/OWNERSHIP-MAP.md`
- `docs/architecture/REDIS-CACHE-POLICY.md`
- `docs/security/DATA-LAYER-SECURITY.md`
- `docs/chatgpt-prompts/021_PROMPT.md`

Aplica:
`ONE WRITER, MANY READERS`
`DISCOVER BEFORE CREATE`
`REUSE / EXTEND / NEW_COMPONENT_JUSTIFIED`

Explica desde cero: reproducible build, immutable artifact, Docker tag, floating tag, image digest, supply-chain risk, semantic version, maturity level, LAB-COVERED, PROD-PARTIAL, CLOUD-PENDING, benchmark evidence y latency percentile.

Para cada concepto: significado, por qué existe, cómo funciona, riesgo, ejemplo AegisBank y relación con Mibanco/AI-200.

Guarda este prompt como:
`docs/chatgpt-prompts/022A_PROMPT.md`

==================================================
1. GIT PREFLIGHT
==================================================
Ejecuta READ-ONLY:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -6 --oneline
git show --stat --oneline d97eca6
```

Debe verificarse:
HEAD = d97eca6
working tree limpio.

Si no:
AEGISBANK_V0.12_REDIS_R1_BASELINE_MISMATCH
y STOP.

==================================================
2. SESSIONGUARD
==================================================
Adquirir writer lock con paths mínimos:
`deploy/local/**,ai/rag/**,docs/**,scripts/**,.github/**,README.md`

Si existe writer:
AEGISBANK_CROSS_SESSION_WRITER_ACTIVE
y STOP.

==================================================
3. CAUSA DEL CORRECTIVE
==================================================
El cierre v0.12.2 contiene dos problemas de evidencia:
A. Se utilizó `redis/redis-stack-server:latest`, lo cual viola la regla de reproducibilidad.
B. Se marcaron capacidades locales como `PROD-READY` sin evidencia productiva real.

No añadir features nuevas.

==================================================
4. REDIS IMAGE CANÓNICA
==================================================
Consultar documentación oficial actual de Redis + Docker Official Image.

Seleccionar:
- Redis Open Source 8;
- GA estable;
- tag EXACTO;
- Redis Search integrado;
- compatible con FT.CREATE / FT.SEARCH / HNSW.

NO usar:
- latest
- major-only tag
- minor-only tag

Registrar:
- repository
- exact tag
- Redis server version
- image ID
- RepoDigest/manifest digest observado localmente
- license relevante

No asumir digest web; obtenerlo del pull/inspect real.

==================================================
5. MIGRACIÓN MÍNIMA
==================================================
EXTEND solo `deploy/local/docker-compose.yml`.
Migrar del Redis Stack legado a Redis Open Source 8 exacto.

NO modificar cache policy, RedisCacheManager, RedisVectorRetriever, embeddings, qrels ni RAG metrics salvo compatibilidad estrictamente necesaria.

==================================================
6. COMPATIBILITY ACCEPTANCE
==================================================
Verificar:
- PING
- server version
- FT.CREATE
- HNSW vector schema
- ingest
- KNN search
- TAG metadata filters
- GET/SET
- TTL
- invalidation
- single-flight
- Redis unavailable fallback

Todo debe PASS.

==================================================
7. REPRODUCIBILITY GATE
==================================================
Añadir check que falle si Redis usa:
- :latest
- major-only
- minor-only

Documentar por qué exact patch tag + digest observado es mejor evidencia.

==================================================
8. MATURITY CORRECTION
==================================================
Usar solo:
- LAB-COVERED
- LOCAL-REDIS-COVERED
- CI-CONFIGURED
- CLOUD-PENDING
- PROD-PARTIAL
- SAFETY-DEFERRED

PROHIBIDO PROD-READY salvo evidencia productiva real.

Corregir GLOSSARY / MASTERS-NOTES / COVERAGE-MATRIX / reportes donde aplique.

==================================================
9. BENCHMARK EVIDENCE
==================================================
El cierre afirma aproximadamente:
- Redis <2 ms
- PostgreSQL ~5-15 ms

No repetir cifras sin benchmark reproducible.

Si se mide:
- sample count
- warm-up
- p50
- p95
- p99 si aplica
- environment
- dataset size

Si no puede medirse rigurosamente:
`LATENCY_NOT_COMPARABLE_YET`.

No convertir microbenchmark local en claim productivo.

==================================================
10. RETRIEVAL METRIC RECONCILIATION
==================================================
Verificar `docs/evaluation/v012_retrieval_comparison.json`.

El cierre Redis reporta métricas pgvector distintas a cierres anteriores.

Determinar:
- dataset/query count
- evaluation set/version
- harness version
- index mode
- code changes

NO sobrescribir historia silenciosamente.

Si no puede explicarse:
`AEGISBANK_RETRIEVAL_METRIC_DRIFT_UNEXPLAINED`
y STOP antes de commit.

==================================================
11. QUALITY + ARCHITECTURE
==================================================
Ejecutar:
- Redis integration
- RAG
- Agent
- Core Banking
- ML
- PostgreSQL regressions
- Cosmos regressions
- contracts/E2E
- quality gate
- Ruff
- format
- compileall
- Bandit
- pip-audit
- secret scan
- Pylint R0801
- git diff --check

Mantener:
`NEW TRUE_DUPLICATION = 0`.

==================================================
12. GIT
==================================================
Antes de staging:
session_guard check
git rev-parse HEAD
git status --porcelain=v2
git diff --name-status
git diff --check

PROHIBIDO:
worktrees
git add .
git add -A
reset/rebase/amend
push

Stage solo corrective Redis.

Si todo pasa:
`fix(v0.12): pin Redis runtime and correct evidence maturity`

No push.
Liberar SessionGuard.

==================================================
INFORME FINAL
==================================================
Reportar:

BASELINE:
...

REDIS BEFORE:
repository:
tag:
version:

REDIS AFTER:
repository:
exact tag:
server version:
image id:
digest:
Search built-in:

REPRODUCIBILITY:
floating tag gate:

COMPATIBILITY:
cache:
HNSW:
KNN:
metadata filters:
TTL:
stampede:
fallback:

MATURITY CORRECTIONS:
...

BENCHMARK:
MEASURED / NOT-COMPARABLE
method:
p50:
p95:
p99:

RETRIEVAL METRIC RECONCILIATION:
historical pgvector:
current pgvector:
reason:

DUPLICATION:
new true duplication:

TESTS:
...

WORKING TREE:
clean/dirty

PUSH:
NO

Finalizar solo con:
AEGISBANK_V0.12_REDIS_REPRODUCIBILITY_READY
y STOP.

NO iniciar v0.13.
