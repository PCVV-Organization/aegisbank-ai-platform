# 019 — AegisBank v0.12.0 PostgreSQL + pgvector Vector Data Foundation

Continúa exclusivamente:
v0.12.0 — PostgreSQL + pgvector Vector Data Foundation

Proyecto:
C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform

Baseline esperado:
- branch: master
- HEAD: 22a511a
- working tree limpio

NO iniciar v0.12.1, v0.12.2 ni v0.13.

0. TEACHING CONTRACT + INTEGRIDAD ARQUITECTÓNICA

Lee primero:
- docs/learning/TEACHING-CONTRACT.md
- docs/architecture/CANONICAL-COMPONENTS.md
- docs/engineering/OWNERSHIP-MAP.md
- docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md
- documentación RAG v0.4/v0.5 existente.

Aplica siempre:
- ONE WRITER, MANY READERS
- DISCOVER BEFORE CREATE
- decisión obligatoria REUSE / EXTEND / NEW_COMPONENT_JUSTIFIED

Antes de crear cualquier módulo/clase/helper:
- buscar con rg;
- revisar componente canónico;
- revisar imports/callers;
- decidir REUSE/EXTEND/NEW_COMPONENT_JUSTIFIED;
- documentar la justificación si es NEW.

Explica desde cero, como clase de Maestría, cada término nuevo:
DBMS, RDBMS, PostgreSQL, SQL, schema, table, row, primary key, foreign key,
transaction, ACID, index, query plan, EXPLAIN, ANALYZE, connection,
connection pool, embedding, vector, vector database, pgvector,
cosine similarity, L2/Euclidean distance, inner product,
exact nearest-neighbor search, ANN, HNSW, IVFFlat,
metadata filtering, recall, latency, throughput, RAG, vector store y migration.

Para cada concepto incluye:
- nombre completo/sigla;
- traducción;
- qué significa;
- qué problema resuelve;
- cómo funciona internamente;
- por qué AegisBank lo necesita;
- ejemplo concreto;
- alternativa y cuándo NO usarlo;
- riesgos/errores típicos;
- relación con Mibanco;
- relación con AI-103/AI-200;
- maturity status.

Guarda este prompt como:
docs/chatgpt-prompts/019_PROMPT.md

1. PREFLIGHT GIT — SOLO LECTURA

Ejecuta:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -5 --oneline
```

Si HEAD != 22a511a o working tree no está limpio:
AEGISBANK_V0.12_BASELINE_MISMATCH y STOP.

NO reset.
NO rebase.
NO amend.
NO push.

2. SESSION GUARD

Adquirir writer lock con un session-id único.

Allowed paths máximos:
ai/rag/**,deploy/local/**,contracts/**,docs/**,scripts/**,.github/**,README.md

Si existe otro writer:
AEGISBANK_CROSS_SESSION_WRITER_ACTIVE y STOP.

Antes de staging y commit:
session_guard check.

3. OBJETIVO

Agregar almacenamiento y recuperación vectorial REAL y LOCAL con:
PostgreSQL + pgvector

Arquitectura:
authorized corpus
→ chunking/versioning existente
→ embedding model local
→ PostgreSQL + pgvector
→ PgVector retriever adapter
→ RAG evaluation harness existente

NO crear un segundo sistema RAG.
NO crear RAGEngine2, RetrieverV2, VectorStore2 ni equivalentes duplicados.
NO borrar ni sustituir los retrievers v0.4.
NO modificar qrels ni métricas históricas v0.4/v0.5.

4. POSTGRESQL + PGVECTOR LOCAL

Primero revisar deploy/local/docker-compose.yml.
Preferir EXTEND del compose existente mediante profile data o equivalente mínimo.
No crear compose paralelo si no es estrictamente necesario.

Usar imagen oficial/estable de PostgreSQL con pgvector:
- verificar documentación oficial actual;
- fijar tag concreto;
- NO usar latest;
- registrar PostgreSQL version, pgvector version, tag y digest si está disponible.

NO Azure cloud.
NO push de imágenes.

5. SECRETS / CREDENTIALS

No commitear passwords.
Usar:
- variables de entorno locales;
- archivo temporal gitignored si fuera necesario;
- .env.example solo con placeholders.

Eliminar cualquier secret temporal tras aceptación.

6. INTEGRACIÓN CANÓNICA CON RAG

Inspeccionar la interfaz/retriever actual.
Objetivo:
EXTEND la abstracción existente con un adapter concreto PgVector.

El adapter NO contiene:
- lógica de chunking;
- reglas de documento vigente;
- generación;
- autorización;
- evaluación.

Esas responsabilidades deben seguir en sus componentes canónicos.
Actualizar CANONICAL-COMPONENTS.md solo si realmente aparece una responsabilidad nueva.

7. DATA MODEL

Diseñar una tabla canónica de chunks con al menos:
- chunk_id
- document_id
- document_version
- status
- effective_from
- effective_to
- source
- topic
- content
- metadata JSONB o columnas justificadas
- embedding vector(N)
- embedding_model_id
- timestamps cuando aporten valor

Preservar:
- documentos superseded excluidos;
- trazabilidad de fuente/versión;
- datos exclusivamente sintéticos/autorizados.

Definir:
- PK;
- unique constraints;
- índices relacionales;
- vector index.

8. EMBEDDINGS LOCALES

NO Azure OpenAI.
Primero comprobar si AegisBank ya tiene un modelo/provider local de embeddings.
Si existe: REUSE.

Si no:
usar un modelo de embeddings local pequeño, reproducible y compatible, documentando:
- model id;
- revisión/version cuando exista;
- licencia/procedencia;
- dimensión;
- normalización.

NO asumir que phi-4-mini sirve como embedding model.
No mezclar embeddings de distintos modelos/dimensiones en el mismo índice sin versionado explícito.

9. VECTOR SEARCH

Implementar y enseñar:
A. Exact search: Sin ANN index. Usarlo como baseline de recall.
B. HNSW: Crear índice HNSW para cosine similarity si es compatible. Explicar m, ef_construction, ef_search, memory, build time, latency, recall.
C. IVFFlat: Implementar/comparar solo si el pequeño corpus permite una prueba con significado. Explicar lists, probes, training/build behavior, tradeoff recall/latency.
NO simular DiskANN local como equivalente Azure. Marcar: DISKANN_AZURE_CLOUD_PENDING.

10. METADATA FILTERING

Demostrar vector search + filtros deterministas:
- status = active;
- topic;
- versión vigente;
- effective date cuando aplique.

La decisión de qué documento está autorizado/vigente NO depende del LLM.

11. QUERY PLANS

Ejecutar:
EXPLAIN (ANALYZE, BUFFERS)
para:
- exact search;
- HNSW;
- consulta vectorial + metadata filter.

Explicar:
- Sequential Scan;
- Index Scan;
- estimated cost;
- actual time;
- rows;
- buffers.

NO afirmar rendimiento enterprise con un corpus pequeño.

12. CONNECTION MANAGEMENT

Usar driver PostgreSQL moderno compatible con Python 3.14.
Preferir psycopg moderno / integración pgvector compatible si encaja con el stack.
Si se usa pool: explicar conexión vs connection pool, min/max size y tradeoffs.
No inventar tuning productivo.

13. INGESTIÓN IDEMPOTENTE

Garantizar:
- mismo chunk + misma versión + mismo embedding model → no duplica;
- mismo ID con contenido incompatible → conflicto claro;
- cambio de embedding model → versionado/migración explícita;
- fallo parcial → rollback;
- ejecución repetida → resultado determinista.

14. RAG EVALUATION

Reutilizar el harness actual.
Comparar:
- lexical_tfidf
- dense_local_lsa
- hybrid_rrf
- nuevo pgvector_embedding

Usar los mismos casos/qrels.
Métricas: nDCG@5, MRR@5, Precision@5, Recall@5.
Guardar NUEVA medición. NO sobrescribir históricos. NO cambiar qrels. NO afirmar que pgvector es mejor si las métricas no lo demuestran.

15. TESTS OBLIGATORIOS

Cubrir al menos:
- PostgreSQL unavailable → error controlado.
- extensión/schema missing → error claro.
- vector dimension mismatch → rechazado.
- duplicate ingestion → idempotente.
- superseded document → excluido.
- metadata filter → enforced.
- exact search → baseline reproducible.
- HNSW → ranked hits válidos.
- embedding model mismatch → rechazado/versionado.
- SQL injection attempt → consultas parametrizadas.
- connection/pool cleanup.
- no nuevas WRITE tools del agente.
- corpus/qrels históricos sin cambios.
- NEW TRUE_DUPLICATION = 0.

16. SEGURIDAD DE DATOS

Crear/actualizar:
docs/security/DATA-LAYER-SECURITY.md

Explicar:
- parameterized SQL;
- least privilege;
- secret management;
- connection security;
- encryption at rest/transit;
- backups;
- PITR = Point-In-Time Recovery;
- RLS = Row-Level Security.

Lo no implementado localmente debe quedar CLOUD-PENDING o PROD-PARTIAL.

17. AI-200 MAPPING

Actualizar:
- docs/learning/GLOSSARY.md
- docs/learning/MASTERS-NOTES.md
- docs/requirements/COVERAGE-MATRIX.md

Marcar:
LOCAL-PGVECTOR-COVERED
- connect/query PostgreSQL;
- schema/data types;
- indexes;
- embeddings;
- similarity search;
- metadata filters;
- RAG;
- connection management;
- EXPLAIN/ANALYZE.

AZURE-POSTGRESQL-CLOUD-PENDING
- Azure Database for PostgreSQL provisioning;
- compute/storage sizing productivo;
- Managed Identity / Entra ID;
- Azure networking;
- backups/PITR reales;
- Azure-specific vector capabilities;
- Azure monitoring.

No confundir PostgreSQL local con Azure Database for PostgreSQL.

18. SIGUIENTES MICRO-HITOS — SOLO DOCUMENTAR

Documentar únicamente:
- v0.12.1 — Cosmos DB NoSQL Emulator + Change Feed
- v0.12.2 — Redis Cache + Vector/Search Semantics
NO implementarlos ahora.

19. QUALITY GATES

Crear gate separado data/integration.
Los tests rápidos normales NO deben requerir PostgreSQL Docker.
Ejecutar:
data integration tests, suite completa, contracts, E2E, RAG regressions, fast quality gate, Ruff, format, compileall, Bandit, pip-audit, secret scan, Pylint R0801, git diff --check.
Mantener: NEW TRUE_DUPLICATION = 0.

20. CLEANUP

Al finalizar:
- bajar solo PostgreSQL/pgvector iniciado por este milestone;
- eliminar secret temporal;
- no borrar caches/imágenes globales;
- no alterar Kubernetes local salvo lectura necesaria;
- no dejar port-forwards.

21. GIT

Antes de staging:
- session_guard check
- git rev-parse HEAD
- git status --porcelain=v2
- git diff --name-status

PROHIBIDO: worktrees, git add ., git add -A, reset, rebase, amend, push.
Stage explícito de paths legítimos v0.12.
Antes del commit repetir session_guard check.

Si todo pasa crear:
feat(v0.12): establish PostgreSQL pgvector data foundation

Liberar SessionGuard después.
