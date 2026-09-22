# AegisBank AI Platform — Briefing completo auto-contenido para ChatGPT

> Revisión de baseline 2026-09-21: este briefing conserva contexto histórico.
> No acredita una release ni una nueva ejecución live. El informe de Phase 2.2
> del 2026-09-12 se identifica como R2, pero la aceptación R2 sigue parcial.
> Para estado, defectos, pruebas actuales y plan de commits, prevalece el
> [informe de cierre](../quality/LOCAL-BASELINE-CLOSURE-20260921.md).

> **Propósito:** Este documento entrega a un LLM externo (p.ej. ChatGPT, Claude, agentes de evaluación y auditoría) toda la información necesaria para entender, navegar y auditar AegisBank AI Platform sin requerir acceso físico previo al repositorio.
> **Versiones:** Repo `v1.0.6` (base técnica y defensas de routing) · Documentación `v1.0.6` (Information Architecture, Evaluation Taxonomy, Coder Navigation Stack & Post-Generation Interceptors).
> **Estado:** `LOCAL-COVERED` para lo que está implementado y verificado en laboratorio. `CLOUD-PENDING` para todo lo que requiere Azure real. `PROD-UNPROVEN` para cualquier afirmación de capacidad productiva.
> **No afiliación:** AegisBank NO está afiliado a Mibanco, Microsoft, la SBS (Perú), NIST ni a ninguna institución financiera o regulatoria. Todo el proyecto es estrictamente educativo, sintético y de portafolio.
> **Precedencia de evidencia:** Este briefing es un snapshot narrativo canónico y autocontenido para lectores externos. La evidencia ejecutable del repositorio tiene precedencia sobre este documento; las cifras y estados pueden quedar obsoletos.
> **Tamaño observado de este snapshot:** 2,945 líneas y 260,206 bytes en la revisión actual; este dato es descriptivo, no una garantía permanente.

---

## Tabla de contenidos

1. [Resumen ejecutivo](#1-resumen-ejecutivo)
2. [Identidad, misión y reglas permanentes](#2-identidad-misión-y-reglas-permanentes)
3. [¿Qué hace? Capacidades observables](#3-qué-hace-capacidades-observables)
4. [Topología física del repositorio](#4-topología-física-del-repositorio)
5. [Stack tecnológico](#5-stack-tecnológico)
6. [Arquitectura canónica, planos de aislamiento y stack de navegación](#6-arquitectura-canónica-planos-de-aislamiento-y-stack-de-navegación)
   - 6.1 [Arquitectura de los tres planos: Coder Tooling vs. Runtime MCP vs. Core Bancario](#61-arquitectura-de-los-tres-planos-coder-tooling-vs-runtime-mcp-vs-core-bancario)
   - 6.2 [Stack de navegación, descubrimiento e inspección del Coder](#62-stack-de-navegación-descubrimiento-e-inspección-del-coder)
   - 6.3 [Las 24 responsabilidades canónicas](#63-las-24-responsabilidades-canónicas-extracto-de-canonical-componentsmd)
   - 6.4 [Las 5 trust boundaries (modelo STRIDE del proyecto)](#64-las-5-trust-boundaries-modelo-stride-del-proyecto)
   - 6.5 [Flujo end-to-end (read path)](#65-flujo-end-to-end-read-path)
   - 6.6 [Las 15 Invariantes Canónicas del Sistema (Formal Logic & Verification Map)](#66-las-15-invariantes-canónicas-del-sistema-formal-logic--verification-map)
7. [Paradigma LOCAL-FIRST + PRODUCTION-MIGRATABLE](#7-paradigma-local-first--production-migratable)
8. [Cómo maneja Docker](#8-cómo-maneja-docker)
9. [Cómo maneja Foundry Local](#9-cómo-maneja-foundry-local)
10. [Cómo maneja Azure (y qué está emulado vs. qué es cloud real)](#10-cómo-maneja-azure-y-qué-está-emulado-vs-qué-es-cloud-real)
11. [Cómo maneja las bases de datos](#11-cómo-maneja-las-bases-de-datos)
12. [El agente Aegis: orquestador, herramientas, HITL, HOTL, MCP](#12-el-agente-aegis-orquestador-herramientas-hitl-hotl-mcp)
    - 12.1 [AgentOrchestrator — agent.py (v1.0.6)](#121-agentorchestrator--aiagentsrcaegisbank_agentagentpy-1190-líneas)
    - 12.1.1 [Almacén de sesión durable SQLite](#1211-almacén-de-sesión-durable-sqlite-aiagentsrcaegisbank_agentsession_storepy)
    - 12.1.2 [Invariante canónico 'Zero Account Fakery' y defensas post-generación (v1.0.6)](#1212-invariante-canónico-zero-account-fakery-y-defensas-post-generación-v106)
    - 12.1.3 [Plan comparativo determinista multicuenta (v1.0.6)](#1213-plan-comparativo-determinista-multicuenta-v106)
    - 12.2 [Tool Registry](#122-tool-registry--aiagentsrcaegisbank_agenttools)
    - 12.3 [HITL State Machine](#123-hitl-state-machine--aiagentsrcaegisbank_agenthitlpy-244-líneas)
    - 12.4 [HOTL Supervisor](#124-hotl-supervisor--aiagentsrcaegisbank_agentobservabilityhotlpy)
    - 12.5 [MCP Boundary — Producto vs Coder Tooling](#125-mcp-boundary--aiagentsrcaegisbank_agentmcp_boundarypy--mcpserverpy)
13. [El sistema RAG: retrieval híbrido, generación con citas, abstención](#13-el-sistema-rag-retrieval-híbrido-generación-con-citas-abstención)
14. [El clasificador de intención (clásico ML)](#14-el-clasificador-de-intención-clásico-ml)
15. [Workflows principales: los 8 journeys bancarios A–H](#15-workflows-principales-los-8-journeys-bancarios-ah)
   - 15.1 [Matriz Resumen de los 8 Journeys](#151-matriz-resumen-de-los-8-journeys)
   - 15.2 [Trazabilidad Técnica Detallada Paso a Paso](#152-trazabilidad-técnica-detallada-paso-a-paso)
16. [Workflows de desarrollo: la cadena de prompts 000–026](#16-workflows-de-desarrollo-la-cadena-de-prompts-000026)
   - 16.1 [El patrón de los prompts](#161-el-patrón-de-los-prompts)
   - 16.2 [Catálogo Genealógico de los 28 Prompts del Proyecto](#162-catálogo-genealógico-de-los-28-prompts-del-proyecto)
   - 16.3 [La regla ONE WRITER, MANY READERS](#163-la-regla-one-writer-many-readers)
   - 16.4 [La regla DISCOVER BEFORE CREATE](#164-la-regla-discover-before-create)
17. [Workflows de testing: pirámide, contratos, evaluación](#17-workflows-de-testing-pirámide-contratos-evaluación)
18. [Workflows de release: gates, evidencia, taxonomía de claims](#18-workflows-de-release-gates-evidencia-taxonomía-de-claims)
19. [Workflows de operaciones: runbooks, HOTL, rollback](#19-workflows-de-operaciones-runbooks-hotl-rollback)
20. [Seguridad: STRIDE, contenedor, datos, serverless, DevSecOps](#20-seguridad-stride-contenedor-datos-serverless-devsecops)
21. [Alineación con certificaciones Microsoft de IA](#21-alineación-con-certificaciones-microsoft-de-ia)
22. [Maestría de IA: 7 capas de evaluación, MLOps, drift](#22-maestría-de-ia-7-capas-de-evaluación-mlops-drift)
   - 22.1 [La taxonomía de evaluación y formulación matemática formal](#221-la-taxonomía-de-evaluación-y-formulación-matemática-formal)
   - 22.2 [MLOps: Arquitectura de Tracking y Detección de Drift](#222-mlops-arquitectura-de-tracking-y-detección-de-drift)
   - 22.3 [Evaluación Comparativa AB y Rigor Estadístico](#223-evaluación-comparativa-ab-y-rigor-estadístico)
   - 22.4 [Tabla Exhaustiva de Métricas de Promoción v0.15 / v1.0.1](#224-tabla-exhaustiva-de-métricas-de-promoción-v015--v101)
   - 22.5 [Reconciliación Histórica de Procedencia: v012_retrieval_comparison.json](#225-reconciliación-histórica-de-procedencia-v012_retrieval_comparisonjson)
   - 22.6 [Principio de Desacoplamiento: Métricas ≠ Milestones](#226-principio-de-desacoplamiento-métricas--milestones)
   - 22.7 [Reproducibilidad Científica e Inmutabilidad](#227-reproducibilidad-científica-e-inmutabilidad)
23. [Fortalezas del proyecto](#23-fortalezas-del-proyecto)
24. [Debilidades, riesgos abiertos y huecos](#24-debilidades-riesgos-abiertos-y-huecos)
25. [Errores conocidos y post-mortems](#25-errores-conocidos-y-post-mortems)
26. [Glosario bilingüe (ES / EN)](#26-glosario-bilingüe-es--en)
27. [Mapa de fuentes del repositorio (para auditoría)](#27-mapa-de-fuentes-del-repositorio-para-auditoría)
28. [Limitaciones de este briefing](#28-limitaciones-de-este-briefing)

---

## 1. Resumen ejecutivo

**AegisBank AI Platform** es un laboratorio educativo y de portafolio que demuestra cómo construir un asistente de IA bancario ficticio llamado **Aegis**, con tres capacidades bajo control determinista:

1. **Conocimiento** — Responde preguntas sobre productos bancarios usando RAG sobre un corpus sintético en español, citando siempre las fuentes o absteniéndose explícitamente.
2. **Lectura** — Consulta datos sintéticos de préstamos y cuotas del cliente autenticado usando herramientas de sólo-lectura filtradas por `customer_id`.
3. **Escritura** — Propone la creación de un "reclamo / solicitud de servicio" que **nunca se ejecuta** sin aprobación humana explícita (HITL) **y** sin que el operador (HOTL) haya habilitado las escrituras.

**Filosofía rectora:** *"El LLM interpreta y propone; la identidad, política, autorización, validación y reglas de negocio deterministas deciden."* En otras palabras: el LLM **nunca** tiene poder directo de escritura; sólo produce propuestas estructuradas que pasan por tres valles de control antes de tocar datos.

El proyecto está construido como **monolito modular** (no microservicios), arranca como **un solo agente**, vive primero en **local** y luego migra a Azure sin reescritura. Tiene **24 componentes canónicos**, **30 ADRs** (architecture decision records), **una pirámide de tests de ~221 tests automatizados** y **4 runbooks de operaciones**. La versión actual es `v1.0.x`, congelada en tags Git `v1.0.0` y `v1.0.1` (corrección de integridad de evidencia).

---

## 2. Identidad, misión y reglas permanentes

### 2.1 Identidad y misión
- **No es un banco real** ni un core bancario productivo. Es un laboratorio.
- **Todos los datos son sintéticos y reproducibles**. Ningún DNI, RUC, número de tarjeta, cuenta real, credencial o transacción real aparece en el repositorio.
- **No usa tenants reales** de Microsoft Entra ID, AWS, GCP ni servicios pagos de Azure sin aprobación explícita.
- **Tres audiencias declaradas:** (1) reclutadores y gerentes de contratación que evalúan el portafolio, (2) arquitectos senior / tech leads que auditan diseño, (3) ingenieros que estudian la cadena histórica de construcción.

### 2.2 Las 13 reglas permanentes
Estas reglas están duplicadas en `AGENTS.md` (raíz del repo) y son inmutables salvo decisión explícita:

| # | Regla |
|---|---|
| 1 | Modificar archivos **solo** dentro de `C:\aegisbank-ai-platform`. |
| 2 | Usar **solo** datos sintéticos y reproducibles. Nunca datos personales, bancarios ni confidenciales reales. |
| 3 | Trabajar **primero local**, luego Docker, luego CI, luego Azure — en ese orden estricto. |
| 4 | **No crear recursos Azure de pago** ni correr deployments sin aprobación explícita. |
| 5 | Arrancar con **un agente y un monolito modular**. No introducir microservicios, AKS ni multi-agente tempranamente. |
| 6 | El LLM puede **interpretar y proponer**; la identidad, política, autorización, validación y reglas de negocio **deterministas deciden**. |
| 7 | **HITL obligatorio** para toda operación que cambie estado. |
| 8 | **Nunca commitear secretos.** Mantener `.env` ignorado y publicar placeholders solo en `.env.example`. |
| 9 | **Minimizar y redactar** contenido sensible en logs, prompts, registros de auditoría y telemetría. |
| 10 | Añadir una dependencia o tecnología **solo** si resuelve un requerimiento, reduce un riesgo o demuestra una competencia definida. |
| 11 | Mantener cambios dentro del **milestone autorizado**. Expandir alcance requiere decisión explícita. |
| 12 | **Preservar los artefactos de bootstrap** de OpenCode pre-existentes, salvo que una tarea los ataque explícitamente. |
| 13 | Promover **solo conocimiento verificado y durable** a `.intelligence/`. |

### 2.3 Las 7 reglas de calidad
1. Agregar tests apropiados a cada cambio de implementación.
2. **Separar** preocupaciones unit, integration, contract, end-to-end y AI evaluation.
3. **Validar comportamiento ejecutado** antes de reportar `PASS`. Nunca sustituir comportamiento esperado por evidencia ejecutada.
4. Las escrituras deben ser **idempotentes** antes de habilitar cualquier política de reintentos.
5. Usar reintentos **acotados** solo para fallos transitorios conocidos y circuit breakers para fallos persistentes.
6. **Propagar correlation_id y trace_id** (W3C `traceparent`) por cada límite de ejecución.
7. **No reclamar** certificación legal, regulatoria, NIST, Microsoft o bancaria.

### 2.4 Métricas de éxito (extracto del charter)
- 100% de pase en journeys críticos (UC-002 lectura, UC-003 detalle, UC-004 escritura con HITL, UC-006 dependencia degradada).
- 0 secretos verificados en Git.
- 0 escrituras no autorizadas.
- Toda escritura con `idempotency-key` y replay = 1 solo registro.
- Cada flujo lleva `correlation_id` + `trace_id` y el caso UC-004 es reconstruible desde telemetría sin captura irrestricta de payload.
- Baseline de ML clásico (TF-IDF + Logistic Regression) corrido con accuracy, F1, matriz de confusión, latencia y seed registrados.
- Protocolo de comparación usa held-out sets; umbrales **no afinados** sobre el held-out.

---

## 3. ¿Qué hace? Capacidades observables

El asistente **Aegis** expone tres capacidades de cara al cliente y dos capacidades operativas:

### 3.1 Capacidades de cliente (cara al usuario)
| Capacidad | Cómo se implementa | Evidencia |
|---|---|---|
| **Knowledge Q&A** (preguntas sobre productos) | Pipeline RAG: `query → retrieval (TF-IDF + SVD + RRF k=60, o pgvector HNSW, o RediSearch KNN) → context builder → LLM (Foundry Local phi-4-mini) → grounded answer + citations`. Si evidencia insuficiente → abstiene. | `ai/rag/src/aegisbank_rag/generation.py`, prompt `prompts/rag-answer-v001.json` |
| **Read inquiries** (consultar mis préstamos / próxima cuota) | Tool registry: `get_my_loans`, `get_loan_details`, `get_next_installment`. Cada tool valida `customer_id` contra `AgentContext.session_customer_id`. | `ai/agent/src/aegisbank_agent/tools/banking_tools.py`, tests en `tests/unit/tools/` |
| **Write con HITL** (crear reclamo / solicitud de servicio) | Tool `create_service_request` exige cadena `LLM propone → HOTL kill-switch check → HITL create_request → approval_callback → HITL approve → execute con IdempotencyGuard → verify_and_mark_executed`. | `ai/agent/src/aegisbank_agent/hitl.py`, journey E, journey F |

### 3.2 Capacidades operativas (cara al SRE / ingeniero)
| Capacidad | Cómo se implementa |
|---|---|
| **Observabilidad** | OpenTelemetry tracing (W3C `traceparent`) + structured logging con redaction + OperationalMetrics (p50/p95/p99) + AuditLogger WORM (append-only) + AgentOpsSummary |
| **Reliability** | IdempotencyGuard + RetryPolicy (backoff exponencial + jitter, acotado, solo transitorios) + CircuitBreaker FSM (CLOSED/OPEN/HALF_OPEN) + with_timeout |
| **MLOps** | MLflowTracker (SQLite local) + DriftDetector (PSI, Wasserstein, JSD) + ABExperimentHarness (McNemar + bootstrap CI) |
| **Config & Secrets boundary** | `ConfigurationProvider` (App Configuration emulator) + `SecretProvider` (sintético local con contract adapter hacia Azure Key Vault real) + KeyVaultReferenceResolver (RFC 3986 + regex) |
| **Outbox + messaging** | OutboxRepository (transaccional) + LocalMessageBus + IdempotentConsumer + DeadLetterQueue + Azure Service Bus emulator adapter |

### 3.3 Lo que **NO** hace
- No mueve dinero, no procesa pagos, no hace transferencias ni desembolsos.
- No aprueba créditos, no ejecuta scoring de fraude productivo, no da asesoría financiera.
- No usa biometría, omnicanalidad, app móvil ni WhatsApp/SMS/voz reales.
- No se autodefine como compatible con ISO 27001, NIST 800-53, PCI-DSS, SBS Perú, EBA, OCC SR 11-7 u otra certificación.
- No afirma producción, SLA, capacidad de carga ni multi-región.

---

## 4. Topología física del repositorio

Hay **dos capas** anidadas que es importante distinguir:

### 4.1 Capa externa: entorno AI (`C:\aegisbank-ai-platform\`)
- `AGENTS.md` — instrucciones permanentes para agentes IA.
- `opencode.json` — config de OpenCode (perfil `minimax-plus`, agentes `plan` y `build`, MCP servers, permisos, retrieval policy).
- `README.md` — landing page.
- `.ai-env/retrieval-policy.json` — política de retrieval adoptada por el proyecto.
- `.intelligence/` — knowledge store durable (graph, index, manifest, smoke evidence).
- `.opencode/` — material del entorno IA: MCP servers (Node), scripts (`smoke-mcp.mjs`), package.json, pyright LSP.

### 4.2 Capa interna: el proyecto real (`C:\aegisbank-ai-platform\aegisbank-ai-platform\`)
```
aegisbank-ai-platform/
├── README.md                       # Landing page del proyecto
├── .gitignore
├── .github/workflows/ci.yml        # CI: static-analysis + test-suite + devsecops (CI-CONFIGURED/RUNNER-PENDING)
├── ai/
│   ├── agent/                      # Orquestador, MCP stdio, HITL state machine, observability, MLOps
│   └── rag/                        # Retrieval (TF-IDF/SVD/pgvector/RediSearch) + grounded generation
├── contracts/                      # 10 JSON Schemas 2020-12 (OpenAPI, CloudEvents, Outbox, MCP, Cosmos, etc.)
├── docs/                           # Suite de documentación (charter, ADRs, runbooks, learning, releases, evaluation)
├── functions/
│   └── aegisbank-events/           # Azure Functions Python v2 (Event Grid trigger / CloudEvents 1.0)
├── ml/intent-classifier/           # Baseline clásico TF-IDF + Logistic Regression (frozen v0.3)
├── scripts/                        # Quality gate, session guard, performance, evaluation, sbom, acceptances
├── services/
│   └── mock-core-banking/          # FastAPI modular monolith (Accounts/Loans/Cards/Outbox)
├── deploy/
│   ├── local/docker-compose.yml    # Stack emulado (mock-core-banking + mssql + Service Bus + pgvector + Cosmos + Redis + App Config)
│   └── kubernetes/                 # deployment.yaml, service.yaml, configmap.yaml, namespace.yaml
├── data/                           # sessions.db, evaluation holdouts
├── artifacts/quality/              # bandit.json, coverage.json, pip-audit.json, sbom.cdx.json, secret-scan.json
└── mlruns/                         # MLflow SQLite (drift + experiment runs)
```

### 4.3 Estructura interna de los servicios
- `ai/agent/src/aegisbank_agent/` (38 archivos `.py`): `agent.py` (968 líneas), `cli.py`, `hitl.py`, `mcp_boundary.py`, `mcp_server.py`, `mcp/server.py`, `knowledge_routing.py`, `cosmos.py`, `session_store.py`, `tools/{base,registry,banking_tools,knowledge_tools}.py`, `reliability/{idempotency,retry,circuit_breaker,timeout,messaging,azure_servicebus_adapter}.py`, `observability/{tracer,audit,hotl,metrics,telemetry,logging,agentops}.py`, `mlops/{drift,tracker}.py`, `evaluation/{evaluators,ab_testing}.py`, `configuration/{config,secrets}.py`, `prompts/agent-system-v{001,002,003}.json`.
- `ai/rag/src/aegisbank_rag/` (16 archivos `.py`): `retriever.py`, `hybrid.py`, `lexical.py`, `dense_local.py`, `embedding.py`, `foundry_local.py`, `pgvector_retriever.py`, `redis_retriever.py`, `cache.py`, `generation.py`, `generation_evaluation.py`, `prompting.py`, `corpus.py`, `chunking.py`, `evaluation.py`, `cli.py`.
- `services/mock-core-banking/src/mock_core_banking/`: `main.py`, `config.py`, `correlation.py`, `error_handlers.py`, `api/{customers,loans,service_requests,health,dependencies}.py`, `domain/{money,enums,errors,next_installment}.py`, `persistence/{base,database,models,repositories,seed,types}.py`, `schemas/models.py`.
- `functions/aegisbank-events/`: `function_app.py`, `service_request_handler.py`, `cloud_event.py`, `Dockerfile`, `host.json`, `requirements.txt`, `local.settings.example.json`, `samples/service-request-created.cloudevent.json`.

---

## 5. Stack tecnológico

### 5.1 Lenguaje y runtime
- **Python 3.14** (target). El proyecto usa tipado estricto (`dict[str, Any]`, `StrEnum`, `Protocol`).
- **Node.js 20+** solo para la capa `.opencode/` (MCP servers vía `pnpm`/`node`).
- **PowerShell 7+** como shell de operación en Windows.
- **Docker** (con `docker-compose` v2 profiles) para los servicios emulados.

### 5.2 Dependencias clave de Python (versiones pinneadas en `pyproject.toml`)
| Librería | Uso | Versión |
|---|---|---|
| `fastapi` | HTTP framework (mock-core-banking) | 0.141.1 |
| `pydantic` | Schemas y validación | 2.13.4 |
| `sqlalchemy` | ORM | 2.0.52 |
| `starlette` | Middleware ASGI | 1.6.0 |
| `uvicorn` | ASGI server | 0.52.4 |
| `openai` | Cliente OpenAI (también usado contra Foundry Local) | 3.5.0 |
| `mcp` | Model Context Protocol SDK (v2) | 2.1.1 |
| `opentelemetry` | Tracing + spans + W3C propagation | 1.44 |
| `azure-servicebus` | Adapter hacia Service Bus emulator | 7.14 |
| `azure-cosmos` | Cosmos DB NoSQL + change feed | ≥4.16 |
| `redis` | Cliente Redis (cache + RediSearch) | ≥5 |
| `azure-appconfiguration-provider` | Configuración (con emulator) | 2.5 |
| `azure-identity` | DefaultAzureCredential | 1.25 |
| `azure-keyvault-secrets` | Adapter hacia Key Vault (CLOUD-PENDING) | 4.11 |
| `mlflow` | Tracking de experimentos | ≥3.16 |
| `alembic` | Migraciones | ≥1.19 |
| `httpx` | Cliente HTTP para tests | 2.12.0 |
| `pytest` | Test runner | 9.1.1 |
| `ruff` | Linter + formatter | 0.16.4 |

### 5.3 Dependencias de Node (capa `.opencode/`)
- `@modelcontextprotocol/server-sequential-thinking@2020.x`
- `@modelcontextprotocol/server-filesystem@2026.7.10` (scoped a `C:/aegisbank-ai-platform`)
- `@cyanheads/git-mcp-server@2.15.3` (sustituto de `@modelcontextprotocol/server-git`)
- `@modelcontextprotocol/server-everything@2026.8.18` (smoke target)
- `@upstash/context7-mcp@4.0.3` (inert hasta rotar `CONTEXT7_API_KEY`)
- `pyright@1.1.413` (LSP Python)

### 5.4 Stack de Azure contemplado (LOCAL emulado vs CLOUD real)
| Servicio Azure | Equivalente local | Estado |
|---|---|---|
| Azure OpenAI / Foundry | **Foundry Local** (`foundry` CLI) con modelo `phi-4-mini` | `LAB-COVERED` |
| Azure Functions | `azure-functions-core-tools@4.14.0` (Python v2 worker) | `LAB-COVERED` en Linux container, `BLOCKED` en Windows nativo (cygrpc MAX_PATH) |
| Azure Service Bus | `mcr.microsoft.com/azure-messaging/servicebus-emulator:latest` + MSSQL | `LAB-COVERED` |
| Azure Cosmos DB | `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest` | `LAB-COVERED` |
| Azure Database for PostgreSQL + pgvector | `pgvector/pgvector:0.8.0-pg17` | `LAB-COVERED` |
| Azure Cache for Redis | `redis:8.10.1-trixie@sha256:...` (digest pinned) | `LAB-COVERED` |
| Azure App Configuration | `mcr.microsoft.com/azure-app-configuration/app-configuration-emulator:1.2.0@sha256:...` | `LAB-COVERED` (v0.14.0) |
| Azure Key Vault | Implementación sintética + adapter contract-tested | `CLOUD-KEYVAULT-PENDING` |
| Managed Identity / Entra ID | `DefaultAzureCredential` documentado con fallback a `AzureCliCredential` / `EnvironmentCredential` | `CLOUD-PENDING` |
| Azure Container Apps | `deploy/kubernetes/*.yaml` listo + scripts de acceptance | `CLOUD-PENDING` |
| Azure Kubernetes Service | Diferido explícitamente a v1.1 | `SAFETY-DEFERRED` (para v1.0) |
| Azure Container Registry | Sin tag pinneado aún (v0.11 emite imágenes `aegisbank/mock-core-banking:0.11.0`) | `CLOUD-PENDING` |
| Azure Event Grid | `mcr.microsoft.com/azure-messaging/servicebus-emulator` + `event_grid_trigger` decorator | `LAB-COVERED` |
| Azure SQL / Immutable Ledger | MSSQL emulator + `AuditEvent` model | `LAB-COVERED` |

---

## 6. Arquitectura canónica, planos de aislamiento y stack de navegación

### 6.1 Arquitectura de los tres planos: Coder Tooling vs. Runtime MCP vs. Core Bancario

> **Regla de oro para LLMs y evaluadores:** NUNCA confundir las herramientas de ingeniería que usa el developer/agente de código (OpenCode / Antigravity) para construir el software, con los contratos y herramientas que el producto AegisBank expone a sus usuarios o clientes bancarios.

```
┌──────────────────────────────────────────────────────────────────────────────────┐
│ PLANO 1: ENGINEERING & CODER TOOLING (Desarrollo, Navegación y Auditoría)         │
│ Utilizado por: Ingeniero de software, OpenCode, Antigravity Agent, CI Runner     │
│ Propósito: Inspeccionar código, consultar docs, razonar cambios y ejecutar tests │
│ ├── codebase-memory-mcp  → Knowledge Graph de código (search_graph, trace_path)  │
│ ├── MCP filesystem       → Inspección acotada a C:\aegisbank-ai-platform         │
│ ├── MCP git              → Diff, blame, status, reflog (push bloqueado)          │
│ ├── MCP sequential-think → Descomposición analítica multi-paso para HITL/planes  │
│ ├── MCP context7         → Documentación viva de librerías en tiempo de sesión   │
│ ├── MCP everything       → Target de smoke test de transporte MCP host           │
│ ├── Skills del Coder     → antigravity-guide, agy-customizations, e2e-patterns   │
│ ├── Retrieval Policy     → .ai-env/retrieval-policy.json (exact/symbol/knowledge)│
│ └── Slash Commands       → /smoke-mcp, /check-contracts, /lint-adr-links         │
└──────────────────────────────────────────────────────────────────────────────────┘
                                         │ (construye, valida, verifica)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ PLANO 2: PRODUCT RUNTIME & MCP BOUNDARY (Frontera del Asistente Aegis)            │
│ Expuesto por: ai/agent/src/aegisbank_agent/mcp_boundary.py + mcp/server.py       │
│ Protocolo: MCP version 2026-07-28 sobre stdio sandboxed                          │
│ ├── 4 Tools READ: search_knowledge, get_my_loans, get_loan_details, next_install│
│ ├── 1 Tool WRITE: create_service_request (encapsulada en IdempotencyGuard)       │
│ ├── HITL Boundary: ApprovalRequest inmutable con hash SHA-256 de argumentos      │
│ └── HOTL Boundary: Kill-switch atómico en memoria / feature flag                 │
└──────────────────────────────────────────────────────────────────────────────────┘
                                         │ (ejecuta de forma determinista)
                                         ▼
┌──────────────────────────────────────────────────────────────────────────────────┐
│ PLANO 3: DETERMINISTIC CORE BANKING & GOVERNANCE (Capa Bancaria Determinista)     │
│ Implementado en: services/mock-core-banking, reliability, security, audit_logger │
│ ├── Mock Core Banking: SQLite / SQLAlchemy models (Customer, Loan, Installment)  │
│ ├── Ownership Enforcement: loan.customer_id == session_customer_id (Fail-Closed) │
│ ├── Transactional Outbox + Idempotent Consumer + Dead Letter Queue               │
│ └── Immutable Audit Logger: Eventos append-only WORM con trace_id y correlation_id│
└──────────────────────────────────────────────────────────────────────────────────┘
```

#### Matriz de contraste entre planos para ingesta por LLMs

| Dimensión | Plano 1: Coder Tooling | Plano 2: Product MCP Boundary | Plano 3: Deterministic Core |
|---|---|---|---|
| **Actor principal** | Developer / OpenCode / Antigravity | Asistente de IA (Aegis) / Cliente MCP | Motor bancario transaccional |
| **Ubicación de código** | `.opencode/`, `.agents/`, `.ai-env/` | `ai/agent/`, `mcp/` | `services/mock-core-banking/` |
| **Transporte** | Stdio local / In-process IDE | Stdio subproceso MCP | HTTP REST (`:8001`) / ORM directo |
| **Herramientas representativas** | `search_graph`, `read_file`, `git_diff` | `get_my_loans`, `create_service_request` | `LoanRepository`, `OutboxRepository` |
| **Manejo de estado** | Efímero por sesión de edición | Durable en `session_store.py` (SQLite) | ACID en `aegisbank-dev.db` (SQLite) |
| **Peligro si se confunde** | El LLM intentaría llamar a git en producción | El agente expondría APIs privadas sin auth | Inconsistencia de saldos o evasión HITL |

---

### 6.2 Stack de navegación, descubrimiento e inspección del Coder

Para cualquier agente o máquina que deba navegar o auditar este repositorio, el protocolo de navegación se rige por la regla canónica **DISCOVER BEFORE CREATE** y cuenta con un stack de herramientas estructurado:

#### 6.2.1 Orden de prioridad para descubrimiento de código
1. **Knowledge Graph (`codebase-memory-mcp`)**: Se invoca prioritariamente para localizar clases, métodos, esquemas y relaciones:
   - `search_graph(name_pattern)`: Búsqueda de símbolos estructurados.
   - `trace_path(function_name, direction="inbound"|"outbound")`: Traza quién invoca o a quién llama una función.
   - `get_code_snippet(qualified_name)`: Inspección precisa del AST sin leer archivos masivos.
   - `query_graph(cypher_query)`: Consultas topológicas complejas.
   - `get_architecture()`: Resumen arquitectónico de alto nivel.
2. **LSP Server (`pyright@1.1.413`)**: Provee resolución exacta de símbolos Python (`symbol`, `architecture`).
3. **MCP Filesystem (`@modelcontextprotocol/server-filesystem@2026.7.10`)**: Lectura y recorrido acotado estrictamente dentro de `C:\aegisbank-ai-platform`. Bloquea accesos fuera de la raíz del proyecto.
4. **MCP Git (`@cyanheads/git-mcp-server@2.15.1`) & Ripgrep**:
   - `git` para inspección de diffs, historia de commits, branches y tracking de modificaciones.
   - Ripgrep (`exact` en retrieval policy) reservado para strings literales, configuraciones, mensajes de error y archivos no-Python (YAML, Dockerfile, scripts).
5. **Sequential Thinking MCP (`@modelcontextprotocol/server-sequential-thinking@2026.7.4`)**: Empleado para razonamiento multi-paso previo a refactorizaciones críticas o diseño de contratos HITL.
6. **Context7 MCP (`@upstash/context7-mcp@4.0.3`)**: Acceso a documentación viva de librerías oficiales (inerte hasta aprovisionar `CONTEXT7_API_KEY`).
7. **MCP Everything (`@modelcontextprotocol/server-everything@2026.8.18`)**: Smoke target de referencia Anthropic para testear el canal MCP stdio (`scripts/smoke-mcp.mjs`).

#### 6.2.2 Skills para navegación y patrones de ingeniería
- **`antigravity-guide`**: Manual y sitemap del entorno Antigravity IDE, CLI, comandos slash, atajos y arquitectura de plugins.
- **`agy-customizations`**: Guía canónica para declarar y mantener skills, rules (`rules/`), hooks y configuraciones MCP.
- **`e2e-testing-patterns`** (instalada en `~/.agents/skills/`): Patrones de resiliencia, aislamiento y pruebas E2E a nivel HTTP (`httpx` + `pytest-httpx` + `respx`) aplicables a APIs sin UI gráfica.

#### 6.2.3 Política de Recuperación (`.ai-env/retrieval-policy.json`)
La política de enrutamiento de consultas desacopla el método de búsqueda según el tipo de necesidad:
```json
{
  "exact": "ripgrep",
  "symbol": "lsp:pyright",
  "architecture": "lsp:pyright",
  "knowledge": {
    "provider": "filesystem",
    "paths": ["AGENTS.md", ".ai-env/**", "docs/**", "specs/**", "docs/architecture/adr/**", "README*", "CHANGELOG*", "PROGRESS.md", "MIGRATION_CONTROL*", "HANDOFF_NEXT_RUN*"]
  },
  "semantic": "disabled"
}
```

#### 6.2.4 Comandos Slash de solo-lectura (`opencode.json`)
- `/smoke-mcp`: Ejecuta `.opencode/scripts/smoke-mcp.mjs` y reporta conectividad y herramientas de cada servidor MCP.
- `/check-contracts`: Valida sintácticamente que todos los esquemas en `contracts/*.schema.json` cumplan con JSON Schema 2020-12.
- `/lint-adr-links`: Verifica que cada enlace markdown entre ADRs resuelva a un archivo existente en el disco.
- `/charter-summary`: Emite un resumen de los cinco documentos del charter, el límite del producto y las reglas permanentes.

#### 6.2.5 Modelo de permisos de shell (Defensa en profundidad en el IDE)
- **ALLOW (Seguro/Solo lectura):** `git status`, `git log*`, `git diff*`, `git show*`, `git branch*`, `pnpm *`, `python *`, `pytest *`, `ruff *`, `Get-ChildItem *`, `Get-Content *`.
- **ASK (Catch-all y red):** Comandos no categorizados, `curl *`, `Invoke-WebRequest *`, `wget *`, `git switch *`.
- **DENY (Operaciones irreversibles prohibidas):** `git push*`, `git reset --hard*`, `git clean*`, `git filter-branch*`, `git update-ref*`.
- **External Directory:** Bloqueado (`*` DENY); permitido exclusivamente sobre `~/projects/aegisbank*` y `~/config/opencode`.

---

### 6.3 Las 24 responsabilidades canónicas (extracto de `CANONICAL-COMPONENTS.md`)
La regla **DISCOVER BEFORE CREATE** obliga a reutilizar o extender estos componentes antes de crear nuevos:

1. **AgentOrchestrator** (`ai/agent/src/aegisbank_agent/agent.py`) — `run(prompt, customer_id, correlation_id, approval_callback) -> AgentExecutionResult`
2. **ToolRegistry** (`tools/registry.py`) — register/get/list/export_openai_tools
3. **Banking Routing Policy** (`agent.py::requires_account_data`, `requires_banking_read`) — gating determinista antes del LLM
4. **RAG Retrieval** (`ai/rag/src/aegisbank_rag/` + `tools/knowledge_tools.py::SearchKnowledgeTool`)
5. **LLM Provider Adapter** (`agent.py::OpenAIClient` + `ai/rag/foundry_local.py::FoundryLocalProvider`)
6. **HITL** (`hitl.py::HITLApprovalManager`) — `create_request → approve → verify_and_mark_executed`
7. **MCP Server & Boundary** (`mcp_boundary.py::create_mcp_server`, `mcp/server.py::MCPServer`) — stdio, mcp==2.1.1, protocol `2026-07-28`
8. **IdempotencyGuard** (`reliability/idempotency.py`) — `execute(key, op) -> (Any, bool)`
9. **RetryPolicy** (`reliability/retry.py`) — backoff exponencial + jitter, acotado, transient-only
10. **CircuitBreaker** (`reliability/circuit_breaker.py`) — FSM CLOSED/OPEN/HALF_OPEN
11. **TimeoutGuard** (`reliability/timeout.py`) — `@with_timeout(seconds)` y `execute_with_timeout`
12. **Transactional Outbox** (`mock_core_banking/persistence/repositories.py::OutboxRepository`, `models.py::OutboxEvent`)
13. **Message Bus & Consumer** (`reliability/messaging.py::LocalMessageBus`, `IdempotentConsumer`, `DeadLetterQueue`)
14. **OpenTelemetry Tracing** (`observability/tracer.py::TracerProvider`, `trace_span` ctx mgr)
15. **Structured Logging** (`observability/logging.py::StructuredLogger`, `RedactionFilter`)
16. **Operational Metrics** (`observability/metrics.py::OperationalMetrics`) — p50/p95/p99
17. **Immutable Audit Logger** (`observability/audit.py::AuditLogger`, `AuditEventType` enum)
18. **HOTL Supervisor** (`observability/hotl.py::HOTLSupervisor`) — `engage_kill_switch`, `is_write_allowed`
19. **Quality Gate Runner** (`scripts/quality_gate.py::run_quality_gates`)
20. **Cosmos NoSQL & Change Feed** (`cosmos.py::CosmosRepository`, `CosmosChangeFeedProcessor`)
21. **Redis Cache & Vector Search** (`ai/rag/src/aegisbank_rag/cache.py::RedisCacheManager`, `redis_retriever.py::RedisVectorRetriever`)
22. **Serverless Function App** (`functions/aegisbank-events/function_app.py`, `service_request_handler.py`)
23. **Configuration & Secrets Boundary** (`configuration/config.py::ConfigurationProvider`, `secrets.py::SecretProvider`, `KeyVaultReferenceResolver`)
24. **Local AI Evaluation & MLOps** (`evaluation/evaluators.py::FoundryEvaluators`, `mlops/tracker.py::MLflowTracker`, `mlops/drift.py::DriftDetector`, `evaluation/ab_testing.py::ABExperimentHarness`)

### 6.4 Las 5 trust boundaries (modelo STRIDE del proyecto)
1. **User prompt → Agent**: input no confiable. La política determinista decide si se puede acceder a datos bancarios privados.
2. **Retrieved documents → Answer**: evidencia no confiable. Citation + groundedness checks deciden responder o abstener.
3. **LLM → Tools/MCP**: el LLM **propone** un tool call; el registry + autorización + ownership + validación + HITL + HOTL + idempotencia + reglas de negocio **ejecutan**.
4. **WRITE path → Core banking repo**: no llega al repo sin aprobación explícita atada al SHA-256 del payload + estado vivo de HOTL.
5. **Outbox → broker**: frontera transaccional; consumers idempotentes; veneno → DLQ.

### 6.5 Flujo end-to-end (read path)
```
User prompt
  → AgentOrchestrator.run(prompt, customer_id, correlation_id)
    → SessionStore.get_or_create(session_id, customer_id)            [cross-customer → OwnershipViolationError]
    → Routing determinista: requires_account_data / requires_authorized_knowledge
    → Resolución anafórica de contexto previo:
        Si pregunta por "último préstamo" y session.last_loan_id existe → get_loan_details directo (0 rondas LLM)
    → Plan comparativo determinista:
        Si consulta superlativa ("más saldo pendiente") → get_my_loans → max(balance) → get_next_installment (0 rondas, 2 tools)
    → Si requiere cuenta simple: pre-fetch get_my_loans, inyectar resultados como system message
    → Si requiere conocimiento: pre-fetch search_knowledge, inyectar evidencia
      → Insuficiencia → audit AGENT_RUN_COMPLETED{status:ABSTAIN} → abstención canónica
    → Loop LLM (max 3 rondas, bounded):
        → _call_completions(messages, tools, tool_choice)
          [span llm.chat con gen_ai.system=openai, gen_ai.model, round]
        → Sin tool_calls + texto mimickando función → PSEUDO_TOOL_CALL audit + fallo
        → Con tool_calls:
            → HOTLSupervisor.is_write_allowed check
            → Si WRITE: HITLApprovalManager.create_request → audit HITL_REQUESTED
                       → approval_callback(req) → True → approve → execute → verify_and_mark_executed
                       → False → audit HITL_REJECTED → fallo
            → Si READ: ToolRegistry.execute(name, args, context)
                       → cada tool valida session_customer_id
                       → span tool.<name>
        → Audit TOOL_EXECUTED + telemetry completa
    → Interceptores post-generación (Invariante "Zero Account Fakery" v1.0.6):
        → PLACEHOLDER_LEAK detectado? → intercepta y reemplaza con negativa canónica
        → PROCESS_HALLUCINATION detectado? → intercepta y audita PROCESS_HALLUCINATION
        → FALSE_TOOL_EXECUTION_CLAIM detectado? → intercepta y audita FALSE_TOOL_EXECUTION_CLAIM
        → UNGROUNDED_ACCOUNT_RESPONSE (datos de cuenta sin tools ejecutadas)? → abstención de seguridad
  → AgentExecutionResult (answer / abstain / failure)
```

### 6.4 Flujo end-to-end (write path)
```
LLM propone create_service_request(category, description)
  → HOTL kill-switch check (atomic flag)
    → Si engaged → audit TOOL_DENIED{actor:HOTL_SUPERVISOR} → fast-fail
    → Si allowed:
       → HITLApprovalManager.create_request(approval_id = "APPR-XXXXXXXX", status=PENDING)
       → audit HITL_REQUESTED
       → approval_callback(req) [CLI: "¿APPROVE? [y/N]"]
       → Si False: status=REJECTED → audit HITL_REJECTED → return failure (no side effects)
       → Si True:
          → approve(approval_id, customer_id) → status=APPROVED
          → ToolRegistry.execute(create_service_request, args, context)
              → IdempotencyGuard.execute_idempotent(key, op) si args trae idempotency_key
              → HTTP POST a services/mock-core-banking/api/v1/service-requests
                 → ServiceRequestRepository.create() en transacción:
                    INSERT ServiceRequest + INSERT OutboxEvent(event_type=ServiceRequestCreated, payload=...)
                    COMMIT atómico (no dual-write hazard)
              → audit TOOL_EXECUTED
          → verify_and_mark_executed(approval_id, customer_id, args, result)
              → Re-valida customer match
              → Re-valida canonical-JSON hash de arguments == approved hash
              → Si altered args → ArgumentTamperingError → status=REJECTED{reason:"Argumentos alterados"}
       → Mensaje final al usuario con confirmation
```

### 6.5 Diagrama lógico (resumido)
```
+---------------------+       +----------------------+
| User prompt (CLI)   |  -->  | AgentOrchestrator    |
+---------------------+       |  (max 3 rounds)      |
                              +----------+-----------+
                                         |
                  +----------------------+----------------------+
                  v                      v                      v
        +------------------+   +-------------------+   +------------------+
        | Tool Registry    |   | RAG Retriever     |   | MCP stdio server |
        | (5 tools)        |   | (hybrid RRF)      |   | (mcp==2.1.1)     |
        +--------+---------+   +---------+---------+   +---------+--------+
                 |                       |                       |
                 v                       v                       v
        +------------------+   +-------------------+   +------------------+
        | Mock Core Bank   |   | Foundry Local     |   | Foundry Local    |
        | (FastAPI+SQLite) |   | phi-4-mini        |   | phi-4-mini       |
        +--------+---------+   +-------------------+   +------------------+
                 |
                 v
        +------------------+
        | OutboxEvent      |   --> LocalMessageBus / Service Bus emulator
        +------------------+                          |
                                                      v
                                            +------------------+
                                            | IdempotentConsumer
                                            |    + DLQ          |
                                            +------------------+
                                                      |
                                                      v
                                            +------------------+
                                            | Function App     |
                                            | (Event Grid tri.)|
                                            +------------------+
```

### 6.6 Las 15 Invariantes Canónicas del Sistema (Formal Logic & Verification Map)

El diseño de AegisBank AI Platform se fundamenta en un conjunto finito de **15 invariantes no negociables**. Ningún modelo de lenguaje, optimización heurística o solicitud de usuario puede sobrepasar o relajar estas reglas. Se expresan a continuación en lógica de predicados formal, con su traducción operativa, punto de enforcement en el código y test de verificación automatizado:

| ID | Nombre Canónico | Expresión en Lógica Formal / Álgebra Relacional | Significado Operativo | Módulo y Clase de Enforcement | Test de Verificación Canónico |
|---|---|---|---|---|---|
| **$I_1$** | **Zero Account Fakery** | $\forall c \in \text{Claims}(R), \text{IsFinancialData}(c) \implies \exists t \in \text{ExecutedTools}(T) : t.\text{status} = \text{SUCCESS} \land c \in t.\text{data}$ | Si el LLM emite saldos, estados o números de préstamo, estos deben provenir estrictamente de una herramienta ejecutada con éxito en el turno actual. | [agent.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/agent.py) (`_intercept_post_generation_claims`) | `tests/unit/test_account_fakery_defense.py` |
| **$I_2$** | **Mandatory HITL for Writes** | $\forall op \in \text{StateMutations}, \text{Execute}(op) \implies \text{HITLProposal}(op).\text{status} = \text{APPROVED} \land \text{SHA256}(op.\text{args}) = \text{Proposal}.\text{args\_hash}$ | Ninguna escritura bancaria (crear reclamo/solicitud) muta la base de datos sin confirmación humana explícita y verificación de hash anti-tampering. | [hitl.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/hitl.py) (`HITLApprovalManager.verify_and_transition`) | `tests/integration/mcp/test_mcp_hitl_acceptance.py` (Journey E & F) |
| **$I_3$** | **HOTL Supervisory Kill-Switch** | $\forall op \in \text{StateMutations}, \text{Execute}(op) \implies \text{HOTLSupervisor}.\text{is\_write\_allowed}() = \text{True}$ | El operador humano tiene un interruptor maestro que desactiva inmediatamente toda mutación en el sistema, rechazando propuestas antes del HITL. | [hotl.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/observability/hotl.py) (`HOTLSupervisor.assert_write_allowed`) | `tests/integration/observability/test_hotl_kill_switch.py` (Journey G) |
| **$I_4$** | **Customer IDOR Isolation** | $\forall req \in \text{Queries}, \forall r \in \text{ReturnedRecords}(req) : r.\text{customer\_id} = \text{Session}.\text{customer\_id}$ | Un cliente autenticado únicamente puede ver, consultar o solicitar operaciones sobre sus propios datos. Intentos de acceder a otros clientes se bloquean en Round 0. | [agent.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/agent.py) (`_precheck_prompt_for_unauthorized_customer`) | `tests/unit/test_idor_customer_isolation.py` |
| **$I_5$** | **Transactional Outbox Atomicity** | $\forall sr \in \text{ServiceRequests}, \Delta \text{DB}(sr) \iff \Delta \text{DB}(\text{OutboxEvent}(sr)) \text{ within same ACID transaction}$ | La entidad de negocio y el evento de mensajería se persisten en una única transacción SQLite/SQL atómica. Se prohíbe el dual-write asíncrono no transaccional. | [persistence/repository.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/services/mock-core-banking/src/mock_core_banking/persistence/repository.py) | `tests/integration/test_outbox_atomicity.py` |
| **$I_6$** | **Idempotency Precedes Retries** | $\forall op \in \text{RetriedOperations}, \text{EnableRetryPolicy}(op) \implies \text{HasIdempotencyKey}(op) = \text{True}$ | Ninguna política de reintento transitorio se activa sobre mutaciones si la operación no cuenta con una clave de idempotencia verificada contra duplicados. | [reliability/retry.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/reliability/retry.py) & [repository.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/services/mock-core-banking/src/mock_core_banking/persistence/repository.py) | `tests/unit/reliability/test_idempotency.py` (Journey H) |
| **$I_7$** | **Active Corpus Grounding** | $\forall c \in \text{Citations}(R), \text{Corpus}[c].\text{status} = \text{'active'} \land \text{Corpus}[c].\text{document\_id} \in \text{AuthorizedDocs}$ | Cada cita en respuestas RAG debe pertenecer a un chunk activo y no obsoleto en el catálogo de políticas bancarias vigentes. | [generator.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/rag/src/aegisbank_rag/generator.py) (`validate_citations`) | `tests/unit/test_grounded_generation.py` (Journey C & D) |
| **$I_8$** | **Telemetry Data Minimization** | $\forall ev \in \text{TelemetryEvents}, ev.\text{payload} \cap \{\text{PAN}, \text{CVV}, \text{SecretKey}, \text{RawPII}\} = \emptyset$ | Registros de logs, eventos OTel y auditoría estructurada deben pasar por funciones deterministas de enmascaramiento antes de su emisión. | [observability/audit.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/observability/audit.py) (`redact_pii`) | `tests/unit/observability/test_audit_redaction.py` |
| **$I_9$** | **Zero Paid Cloud Deployment** | $\text{DeployTarget} = \text{AzureCloud} \implies \text{HumanExplicitApproval} = \text{True} \land \text{BudgetVerification} = \text{PASS}$ | Prohibición absoluta de desplegar recursos de pago o aprovisionar clústeres productivos en Azure sin autorización explícita previa del operador humano. | [AGENTS.md](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/AGENTS.md) & [session_guard.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/scripts/session_guard.py) | Verificación estática de repositorios y pipelines |
| **$I_{10}$** | **Zero Balance Caching** | $\text{CacheTTL}(\text{CoreBanking}.\text{AccountBalances}) = 0\text{ seconds}$ | Los saldos y deudas exigibles nunca se almacenan en cachés con tiempo de vida positivo. Siempre se consultan directamente al Core Banking en tiempo real. | [caching.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/cache/caching.py) | `tests/unit/cache/test_cache_policy.py` |
| **$I_{11}$** | **Circuit Breaker Fault Isolation** | $\text{ConsecutiveFailures}(dep) \ge \theta_{\text{threshold}} \implies \text{State}(dep) = \text{OPEN} \land \text{FastFailCalls}(dep)$ | Dependencias externas caídas o degradadas se aíslan inmediatamente para proteger el hilo de ejecución principal y evitar consumo de recursos en cascada. | [circuit_breaker.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/reliability/circuit_breaker.py) | `tests/unit/reliability/test_circuit_breaker.py` (Journey H) |
| **$I_{12}$** | **Single-Agent Monolith Boundary** | $\text{Count}(\text{AutonomousAgents}) = 1 \land \text{SubagentDepth} \le 1$ | Prohibición de arquitecturas multi-agente complejas o enjambres no supervisados antes de consolidar el monolito modular y las garantías de gobierno. | [agent.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/agent/src/aegisbank_agent/agent.py) & [opencode.json](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/opencode.json) | `tests/unit/test_orchestrator_bounds.py` |
| **$I_{13}$** | **Strict Contract-First Validation** | $\forall payload \in \text{IOBoundaries}, \text{ValidateJSONSchema}(payload, \text{Draft2020-12}) = \text{True}$ | Todo payload JSON intercambiado entre agente, herramientas MCP, eventos de mensajería y APIs cumple rigurosamente con su contrato JSON Schema 2020-12. | [contracts/](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/contracts/) & [contract_verifier.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/scripts/contract_verifier.py) | `scripts/check_contracts.py` |
| **$I_{14}$** | **Tamper-Evident Append-Only Audit** | $\forall ev \in \text{AuditLogs}, \text{CanUpdate}(ev) = \text{False} \land \text{CanDelete}(ev) = \text{False} \land ev.\text{id} \text{ strictly monotonic}$ | Los registros de auditoría se insertan en tablas append-only (WORM) con marcas de tiempo UTC estrictas y correlation IDs no modificables. | [persistence/models.py](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/services/mock-core-banking/src/mock_core_banking/persistence/models.py) (`AuditEvent`) | `tests/integration/test_audit_persistence.py` |
| **$I_{15}$** | **Synthetic Data Exclusivity** | $\forall record \in \text{DataStores}, \text{IsSynthetic}(record) = \text{True} \land \text{RealCustomerData}(record) = \text{False}$ | Todo número de documento, préstamo, cuota, nombre o teléfono es generado matemáticamente y reproducido mediante scripts declarativos controlados. | [fixtures/](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/services/mock-core-banking/fixtures/) & [data/](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/ai/rag/data/) | Quality Gate: `test_no_real_data.py` |

---

## 7. Paradigma LOCAL-FIRST + PRODUCTION-MIGRATABLE

Este es el corazón del proyecto y merece explicación detallada porque es no trivial.

### 7.1 Qué significa LOCAL-FIRST
- **Todo se ejecuta primero en tu laptop**: SQLite (mock-core-banking), Foundry Local (LLM), Service Bus emulator, Cosmos emulator, pgvector container, Redis container, App Configuration emulator, Functions Core Tools, todos los mocks y herramientas.
- **No necesitas internet** para correr la suite de tests, la calidad de los journeys A–H ni los scripts de acceptance.
- **Los datos nunca salen de tu máquina**. No hay tenants reales de Azure, no hay APIs externas pagadas, no hay telemetría hacia la nube.
- **El feedback loop es de segundos**: el ciclo `edit → run tests → fix → commit` ocurre sin Docker pulls ni despliegues lentos.

### 7.2 Qué significa PRODUCTION-MIGRATABLE
- **El código local y el código cloud comparten la misma forma**. Cada componente tiene un **adapter** o **provider abstraction** que se enchufa contra un servicio real cuando llega el momento:
  - `LocalMessageBus` ↔ `azure_servicebus_adapter.py` (Service Bus emulator ahora, real después)
  - `FoundryLocalProvider` (localhost:port) ↔ Azure OpenAI SDK (cloud)
  - `ConfigurationProvider` local (env + dict) ↔ App Configuration real + `@Microsoft.KeyVault(SecretUri=...)`
  - `SecretProvider` sintético ↔ Azure Key Vault con `DefaultAzureCredential`
  - `RedisCacheManager` standalone ↔ Azure Managed Redis con RediSearch
  - `PgVectorRetriever` ↔ Azure Database for PostgreSQL Flexible Server con Microsoft Entra ID
  - `CosmosRepository` ↔ Azure Cosmos DB real
  - `mock-core-banking` Docker ↔ Azure Container Apps o AKS (AKS diferido a v1.1)
- **El contrato es lo que migra, no la implementación**. Las herramientas exponen una interfaz; el provider concreto cambia.
- **Los JSON Schemas (`contracts/*.schema.json`) son la fuente de verdad de la compatibilidad**. Mientras los mensajes outbox ↔ consumer cumplan `cloudevents/service-request-created-v1.schema.json` y `service-request-created.schema.json`, el back-end puede cambiar de SQLite a PostgreSQL sin tocar el agente.
- **El patrón Outbox garantiza atomicidad DB↔broker**. No hay "dual-write hazard" — si la entidad commit, el evento también; si falla, ninguno.

### 7.3 La regla del orden de promoción
Cada nuevo capability sigue esta secuencia canónica (regla 3 de las permanentes):
1. **Local**: implementar contra mocks/emuladores, escribir tests unit + integration + contract.
2. **Docker**: contenerizar y verificar `docker-compose up` + health checks + scripts de acceptance.
3. **CI**: agregar el gate correspondiente a `scripts/quality_gate.py` y al workflow `.github/workflows/ci.yml`.
4. **Azure (cuando hay aprobación explícita)**: deploy a Container Apps / Functions / Service Bus / etc.

### 7.4 La capa de contratos (lo que realmente migra)
10 JSON Schemas en `contracts/` con `"$schema": "https://json-schema.org/draft/2020-12/schema"` y `additionalProperties:false` en su mayoría. Cualquier mensaje que cruce un límite debe poder validarse contra uno:

| Schema | Valida |
|---|---|
| `bootstrap-manifest.schema.json` | Registro de bootstrap (`/init` output) |
| `core-banking-openapi.schema.json` | El `openapi.json` que produce mock-core-banking |
| `cloudevents/service-request-created-v1.schema.json` | Envelope CloudEvents 1.0 publicado por el outbox |
| `cosmos-event-item.schema.json` | Items escritos a Cosmos DB NoSQL |
| `graph.schema.json` | NDJSON lines de `.intelligence/graph.jsonl` |
| `index.schema.json` | Resumen `.intelligence/index.json` |
| `manifest.schema.json` | `.intelligence/manifest.json` |
| `mcp-tools.schema.json` | Exports del MCP tool registry |
| `service-request-created.schema.json` | Payload del outbox (NO el CloudEvent) |
| `session.schema.json` | NDJSON lines en `.intelligence/sessions/<id>.jsonl` |

### 7.5 Lo que NO migra (todavía)
- **Multi-agent orchestration** — diferido a v1.2.
- **AKS** — diferido a v1.1.
- **Azure AI Search** — diferido (la búsqueda se hace con pgvector local primero).
- **Semantic cache LLM** — `SAFETY-DEFERRED` (dos queries con alta cosine similarity pueden requerir respuestas radicalmente distintas en banca).
- **Production SLO/SLA, multi-región HA, alta TPS** — `PROD-UNPROVEN` por diseño.

---

## 8. Cómo maneja Docker

### 8.1 El stack local (`deploy/local/docker-compose.yml`)
- **Nombre del compose:** `aegisbank-local`.
- **Red:** bridge `aegisbank-net` (todos los servicios en la misma red privada).
- **Volúmenes nombrados:** `aegisbank-core-banking-data`, `aegisbank-pgvector-data`.
- **Perfiles** (compositor por defecto arranca solo mock-core-banking + mssql + servicebus-emulator):
  - `data` → agrega `postgres-pgvector` + opcionalmente cosmos y redis
  - `cosmos` → agrega `cosmos-emulator`
  - `redis` → agrega `redis` (digest pinned)
  - `config` → agrega `app-configuration-emulator`
  - `all` → activa todo

### 8.2 Servicios y seguridad
| Servicio | Imagen (digest pinned donde crítico) | Puerto | Hardening |
|---|---|---|---|
| `mock-core-banking` | build local → `aegisbank/mock-core-banking:0.11.0` | 8000 | `read_only: true`, `tmpfs /tmp 16m`, `cap_drop: [ALL]`, `no-new-privileges`, `user 10001:10001` no-root, healthcheck `python urllib /health/ready` |
| `mssql` | `mcr.microsoft.com/mssql/server:2022-latest` | (interno) | `ACCEPT_EULA=Y`, password via env `MSSQL_SA_PASSWORD` |
| `servicebus-emulator` | `mcr.microsoft.com/azure-messaging/servicebus-emulator:latest` | 5672 | depende de mssql healthy, `Config.json` montado read-only |
| `postgres-pgvector` | `pgvector/pgvector:0.8.0-pg17` (perfil `data`) | 5432 | db `aegisbank_rag`, user `aegisuser` |
| `cosmos-emulator` | `mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest` (perfil `cosmos`/`data`) | 8081/8080/1234 | `PARTITION_COUNT=4`, data explorer enabled |
| `redis` | `redis:8.10.1-trixie@sha256:298e5b3bc566bade82f46ad5511777a4a07a294097ce16ada2f6a42be5239df5` (perfil `redis`/`data`) | 127.0.0.1:6379 (loopback only) | `--save 60 1`, healthcheck `redis-cli ping` |
| `app-configuration-emulator` | `mcr.microsoft.com/azure-app-configuration/app-configuration-emulator:1.2.0@sha256:f84ca52fcf51aab3bad8a0363198c161e8a79eb41712d27779f6e0eb777c7000` (perfil `config`/`all`) | 127.0.0.1:8483→8082 | AnonymousAuthEnabled para local |

### 8.3 Foundry Local NO está en Docker
- El comando `foundry` corre en el host (porque necesita acceso directo a GPU/CPU optimizations).
- `host.docker.internal` queda reservado para futura comunicación contenedor ↔ Foundry Local.
- El cliente OpenAI del agente apunta a `AEGISBANK_FOUNDRY_LOCAL_BASE_URL` (env) o autodetecta con `foundry server status -o json`.

### 8.4 Scripts de acceptance
- `scripts/container_acceptance.py` — verifica que `mock-core-banking` levante en Docker con `/health/live` y `/health/ready` en HTTP 200.
- `scripts/appconfig_emulator_acceptance.py` — verifica keys/values/labels/refrescos/versionado contra App Config emulator.
- `scripts/functions_runtime_acceptance.py` — verifica el arranque de Azure Functions host con `func start`.
- `scripts/capture_pgvector_query_plans.py` — captura `EXPLAIN ANALYZE` para `rag_chunks`.
- `scripts/evaluate_retrievers_v012.py` — re-ejecuta protocolo v0.4 contra pgvector.

### 8.5 Kubernetes (`deploy/kubernetes/`)
- 4 manifests: `namespace.yaml`, `deployment.yaml`, `service.yaml`, `configmap.yaml`.
- Diseñados para `kubectl apply -f deploy/kubernetes/`.
- El acceptance local de K8s está documentado en `docs/operations/KUBERNETES-TROUBLESHOOTING.md` (decision tree para `Pending`, `ImagePullBackOff`, `CrashLoopBackOff`, `OOMKilled`, etc.).

---

## 9. Cómo maneja Foundry Local

### 9.1 Qué es Foundry Local en este proyecto
- **Foundry Local** es un runtime que sirve modelos ONNX/OpenVINO optimizados localmente, expuesto como un endpoint OpenAI-compatible (típicamente `http://127.0.0.1:5272/v1` o el puerto que asigne).
- El modelo pinneado para este proyecto: **`phi-4-mini`** (alias) → **`phi-4-mini-instruct-openvino-gpu`** (modelo real) en Foundry Local **0.10.3**.

### 9.2 Cómo se descubre el endpoint
En `ai/rag/src/aegisbank_rag/foundry_local.py`:
1. Lee `AEGISBANK_FOUNDRY_LOCAL_BASE_URL` del environment.
2. Si no, ejecuta `foundry server status -o json` (subproceso) y extrae el puerto.
3. Si nada funciona → fail-fast con mensaje claro (nunca hardcodea el puerto).

### 9.3 Cómo se usa desde el agente
```python
# ai/agent/src/aegisbank_agent/agent.py
from openai import OpenAI
from ai.rag.foundry_local import DEFAULT_MODEL_ALIAS, resolve_foundry_base_url

client = OpenAI(
    base_url=resolve_foundry_base_url(),
    api_key="not-used-locally",
    max_retries=int(os.getenv("AEGISBANK_FOUNDRY_MAX_RETRIES", "2")),
    timeout=float(os.getenv("AEGISBANK_FOUNDRY_TIMEOUT_SECONDS", "30.0")),
)
# client.chat.completions.create(model=DEFAULT_MODEL_ALIAS, messages=..., tools=..., tool_choice=...)
```

### 9.4 Provider-neutrality (regla 10 de ADRs)
- `LLMProvider` Protocol vive en `ai/rag/src/aegisbank_rag/provider.py`.
- `FoundryLocalProvider` implementa el Protocol.
- Cuando llegue el momento de migrar a Azure OpenAI, se agrega `AzureOpenAIProvider` que cumple el mismo Protocol; los consumidores (`AgentOrchestrator`, evaluadores) **no cambian**.
- Nunca se mezcla HTTP directo con endpoints de inferencia (regla CANONICAL #5).

### 9.5 Plan de recuperación cuando Foundry Local falla
Documentado en `docs/experiments/v0.5-foundry-local-recovery-plan.md` (en español):
1. Tests deterministas + Ruff.
2. `foundry server status -o json` debe responder healthy.
3. `GET /v1/models` debe listar `phi-4-mini`.
4. **Una sola invocación smoke** (sin held-out completo).
5. Si smoke pasa → correr las 6 held-out cases una vez.
6. Re-correr regresiones v0.2/0.3/0.4/0.5 + Ruff + format + compileall + secret scan + `git diff --check`.
7. **No commit** hasta que todos los gates pasen con evidencia ejecutada. **No push**.

### 9.6 Por qué `phi-4-mini`
- Es chico (puede correr en laptop CPU) y rápido.
- Soporta **native tool calling** estructurado (verificado en v0.6.1) — devuelve `message.tool_calls` con nombre y JSON args.
- Suficientemente capaz para responder grounded con citas en español.
- Compatible con `tool_choice="required"` y `tool_choice={"type":"function","function":{"name":"..."}}`.

---

## 10. Cómo maneja Azure (y qué está emulado vs qué es cloud real)

### 10.1 Principio: la nube es la última parada
Por la regla permanente #4, **ningún recurso Azure de pago se crea sin aprobación explícita**. Hasta `v1.0.1`, todos los servicios Azure están emulados localmente. El "go-cloud" ocurriría solo en milestones autorizados con presupuesto explícito.

### 10.2 Estado por servicio
| Servicio Azure | Estado | Notas |
|---|---|---|
| **Azure Container Apps (ACA)** | `CLOUD-PENDING` (diseño + K8s manifests listos) | Decisión documentada en ADR-027 (vs AKS): ACA gana por escala-to-zero, KEDA built-in, menor ops overhead. AKS queda como opcional v1.1. |
| **Azure Kubernetes Service (AKS)** | `SAFETY-DEFERRED` para v1.0 | Diferido explícitamente para v1.1. Razón: monolito modular no necesita aún la complejidad. |
| **Azure Container Registry (ACR)** | `CLOUD-PENDING` | Tag local `aegisbank/mock-core-banking:0.11.0` ya emitido (LAB-COVERED). Migración a ACR pendiente de aprobación. |
| **Azure Functions** | `LAB-COVERED` en Linux container, `BLOCKED` en Windows nativo | Functions Core Tools v4.14.0 (Python v2). Windows: falla por `cygrpc` + Win32 MAX_PATH. Workaround: contenedor oficial `mcr.microsoft.com/azure-functions/python:4-python3.14`. |
| **Azure Service Bus** | `LAB-COVERED` | Emulator + MSSQL backing. Adapter en `reliability/azure_servicebus_adapter.py`. |
| **Azure Event Grid** | `LAB-COVERED` (con Service Bus emulator) | Decorator `@app.event_grid_trigger` valida CloudEvents 1.0 contra `cloudevents/service-request-created-v1.schema.json`. |
| **Azure Cosmos DB** | `LAB-COVERED` (emulator) | `CosmosRepository` + `CosmosChangeFeedProcessor`. Partition key `/customer_id`. |
| **Azure Database for PostgreSQL Flexible Server + pgvector** | `LAB-COVERED` (`pgvector/pgvector:0.8.0-pg17`) | Migración a Flexible Server con Entra ID + Private Endpoints + TDE Customer-Managed Keys = `CLOUD-PENDING`. |
| **Azure Cache for Redis / Azure Managed Redis** | `LAB-COVERED` (`redis:8.10.1-trixie`) | Cache-aside + single-flight stampede protection. RediSearch KNN opcional. |
| **Azure App Configuration** | `LAB-COVERED` (emulator v1.2.0 con digest pinned) | `ConfigurationProvider` con keys/values/labels/locks/refrescos/versionado/fail-fast. |
| **Azure Key Vault** | `CLOUD-KEYVAULT-PENDING` | Implementación local sintética + adapter contract-tested. URI parsing RFC 3986-compliant con regex `^[a-zA-Z0-9-]+$`. |
| **Microsoft Entra ID / Managed Identity** | `CLOUD-MANAGED-IDENTITY-PENDING` | `DefaultAzureCredential` documentado con fallback a `AzureCliCredential` / `EnvironmentCredential`. |
| **Azure AI Search** | Diferido | Sustituido por pgvector + RediSearch. |
| **Azure AI Foundry** | `CLOUD-PENDING` | Evaluators locales (`evaluation/evaluators.py`) hoy. Migración a Foundry Evaluators + Azure ML pendiente. |
| **Azure Monitor / Application Insights** | `CLOUD-PENDING` | OTel tracer preparado (vendor-neutral). Exportadores hacia Azure Monitor aún no cableados. |

### 10.3 Tres ADRs críticas para el camino a la nube
- **ADR-024** (`ci-cd-pipeline-and-devsecops-shift-left-gates.md`): define el pipeline CI con Bandit SAST, pip-audit SCA, pip-audit CycloneDX SBOM, secret scan.
- **ADR-025** (`local-containers-and-service-bus-adapter.md`): contenedorización + Service Bus emulator adapter como base para Service Bus real.
- **ADR-027** (`container-platform-decision-container-apps-vs-aks.md`): decisión documentada ACA vs AKS — gana ACA para v1.0, AKS opcional para v1.1.
- **ADR-029** (`configuration-secrets-identity-boundary.md`): separación CONFIG≠SECRET, App Configuration + Key Vault References.

### 10.4 El camino crítico a producción (cuando se apruebe)
1. Crear resource group + App Configuration + Key Vault (con purge protection).
2. Configurar Managed Identity para el Container App.
3. Asignar roles RBAC: `App Configuration Data Reader`, `Key Vault Secrets User`.
4. Crear Container Registry + push de imágenes con digest pinning.
5. Crear Container Apps Environment + Container App + KEDA scaler contra Service Bus queue length.
6. Crear Service Bus namespace + topics/subscriptions + DLQ.
7. Crear Azure Database for PostgreSQL Flexible Server + pgvector + Entra ID auth.
8. Crear Azure Cache for Redis (o Managed Redis con RediSearch).
9. Crear Cosmos DB account + database + containers con partition key `/customer_id`.
10. Wire OTel exporter hacia Application Insights.
11. Ejecutar acceptance contra `infra/` + runbooks de `docs/operations/runbooks/`.
12. Solo entonces: claim `CLOUD-COVERED` para el componente (nunca `PROD-COVERED`).

---

## 11. Cómo maneja las bases de datos

### 11.1 Inventario de datastores
| Datastore | Local | Cloud target | Patrón de uso |
|---|---|---|---|
| **SQLite** (`services/mock-core-banking/data/local/aegisbank-dev.db`) | archivo file-based | (solo local) | Core banking mock: customers, loans, installments, service_requests, idempotency_records, outbox_events, audit_events. Bind `127.0.0.1:8001` en dev. |
| **PostgreSQL + pgvector** | `pgvector/pgvector:0.8.0-pg17` container | Azure DB for PostgreSQL Flexible Server | RAG: tabla `rag_chunks` con `vector(32)` + L2 unit norm + HNSW index. SQL parametrizado 100% (psycopg `register_vector`). |
| **Azure Cosmos DB NoSQL** | `azure-cosmos-emulator:vnext-latest` | Azure Cosmos DB | Event items (audit cross-region), partition key `/customer_id`, change feed processor. |
| **Azure Cache for Redis** | `redis:8.10.1-trixie` (digest pinned) | Azure Managed Redis | Cache-aside de retrieval results (TTL 300s), corpus metadata (TTL 600s), vector KNN session-persistent. Single-flight stampede protection con token + safety TTL. |

### 11.2 Reglas duras del data layer
1. **0 string concatenation** en SQL. Todo via `%(param)s::type` parametrizado.
2. **Least privilege DB user.** Para pgvector: `aegisuser` solo sobre db `aegisbank_rag` y tabla `rag_chunks`.
3. **Vector dimension validation at engine.** `vector(32)` rechaza mismatches sin pasar por el código Python.
4. **Cosine operator parameterization.** Vectores via binary + `register_vector(conn)`, no strings.
5. **Cosmos DB partition isolation.** Partition key `/customer_id` evita cross-partition queries en paths críticos; idempotent consumer con `id:etag` dedup.
6. **Superseded documents deterministically excluded.** Vector queries SIEMPRE incluyen `WHERE status='active'`. La similitud semántica **nunca** overridea validez legal/banco.
7. **Encryption.** Local: bridge network. Cloud target: TLS 1.2/1.3 + TDE con Customer-Managed Keys.
8. **Secrets via env var, nunca en Git.** `${POSTGRES_PASSWORD}` o `DefaultAzureCredential` para Key Vault.

### 11.3 Esquemas de Base de Datos y DDL Completo (Machine-Readable)

A continuación se detalla el DDL SQL ejecutable exacto y las restricciones de integridad relacional y vectorial de los almacenes del sistema.

#### 11.3.1 DDL SQL Completo — SQLite Mock Core Banking (`services/mock-core-banking/`)
Datastore local: `services/mock-core-banking/data/local/aegisbank-dev.db`

```sql
-- Tabla: customers (Clientes sintéticos de laboratorio)
CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(20) PRIMARY KEY,
    display_name VARCHAR(200) NOT NULL,
    segment VARCHAR(32) NOT NULL CHECK (segment IN ('RETAIL', 'PREMIER', 'BUSINESS')),
    status VARCHAR(32) NOT NULL CHECK (status IN ('ACTIVE', 'INACTIVE', 'BLOCKED')),
    created_at TIMESTAMP NOT NULL
);

-- Tabla: loans (Préstamos con invariantes de saldo no negativo)
CREATE TABLE IF NOT EXISTS loans (
    loan_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    product_code VARCHAR(32) NOT NULL,
    currency VARCHAR(3) NOT NULL CHECK (currency IN ('PEN', 'USD')),
    principal_amount NUMERIC(18, 2) NOT NULL,
    outstanding_balance NUMERIC(18, 2) NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('ACTIVE', 'PAID_OFF', 'DEFAULTED')),
    opened_at DATE NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT ck_loan_principal_nonnegative CHECK (principal_amount >= 0),
    CONSTRAINT ck_loan_outstanding_nonnegative CHECK (outstanding_balance >= 0),
    CONSTRAINT ck_loan_outstanding_not_above_principal CHECK (outstanding_balance <= principal_amount)
);
CREATE INDEX IF NOT EXISTS ix_loans_customer_id ON loans(customer_id);

-- Tabla: installments (Cronograma de cuotas y componentes financieros)
CREATE TABLE IF NOT EXISTS installments (
    installment_id VARCHAR(20) PRIMARY KEY,
    loan_id VARCHAR(20) NOT NULL,
    installment_number INTEGER NOT NULL,
    due_date DATE NOT NULL,
    principal_due NUMERIC(18, 2) NOT NULL,
    interest_due NUMERIC(18, 2) NOT NULL,
    fees_due NUMERIC(18, 2) NOT NULL DEFAULT 0.00,
    total_due NUMERIC(18, 2) NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('PENDING', 'PAID', 'OVERDUE')),
    FOREIGN KEY (loan_id) REFERENCES loans(loan_id),
    CONSTRAINT uq_installment_loan_number UNIQUE (loan_id, installment_number),
    CONSTRAINT ck_installment_number_positive CHECK (installment_number > 0),
    CONSTRAINT ck_installment_principal_nonnegative CHECK (principal_due >= 0),
    CONSTRAINT ck_installment_interest_nonnegative CHECK (interest_due >= 0),
    CONSTRAINT ck_installment_fees_nonnegative CHECK (fees_due >= 0),
    CONSTRAINT ck_installment_total_matches_components CHECK (total_due = principal_due + interest_due + fees_due)
);
CREATE INDEX IF NOT EXISTS ix_installments_loan_id ON installments(loan_id);

-- Tabla: service_requests (Reclamos / Solicitudes mutadas bajo HITL)
CREATE TABLE IF NOT EXISTS service_requests (
    service_request_id VARCHAR(20) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    category VARCHAR(32) NOT NULL CHECK (category IN ('CLAIM', 'INQUIRY', 'LIMIT_CHANGE', 'DISPUTE')),
    description VARCHAR(1000) NOT NULL,
    status VARCHAR(32) NOT NULL CHECK (status IN ('PENDING_REVIEW', 'APPROVED', 'REJECTED', 'RESOLVED')),
    created_at TIMESTAMP NOT NULL,
    FOREIGN KEY (customer_id) REFERENCES customers(customer_id),
    CONSTRAINT ck_service_request_description CHECK (length(trim(description)) > 0)
);
CREATE INDEX IF NOT EXISTS ix_service_requests_customer_id ON service_requests(customer_id);

-- Tabla: idempotency_records (Registro de descarte de duplicados)
CREATE TABLE IF NOT EXISTS idempotency_records (
    idempotency_key VARCHAR(128) PRIMARY KEY,
    customer_id VARCHAR(20) NOT NULL,
    resource_id VARCHAR(64) NOT NULL,
    request_hash VARCHAR(64) NOT NULL,
    response_data VARCHAR(4000) NOT NULL,
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_idempotency_customer_id ON idempotency_records(customer_id);

-- Tabla: outbox_events (Patrón Transactional Outbox para mensajería confiable)
CREATE TABLE IF NOT EXISTS outbox_events (
    event_id VARCHAR(64) PRIMARY KEY,
    event_type VARCHAR(64) NOT NULL,
    aggregate_type VARCHAR(64) NOT NULL,
    aggregate_id VARCHAR(64) NOT NULL,
    payload VARCHAR(4000) NOT NULL,
    status VARCHAR(20) NOT NULL DEFAULT 'PENDING',
    created_at TIMESTAMP NOT NULL,
    published_at TIMESTAMP NULL
);
CREATE INDEX IF NOT EXISTS ix_outbox_events_status ON outbox_events(status);
CREATE INDEX IF NOT EXISTS ix_outbox_events_event_type ON outbox_events(event_type);
CREATE INDEX IF NOT EXISTS ix_outbox_events_aggregate_id ON outbox_events(aggregate_id);

-- Tabla: audit_events (Log de auditoría append-only WORM)
CREATE TABLE IF NOT EXISTS audit_events (
    event_id VARCHAR(64) PRIMARY KEY,
    event_name VARCHAR(64) NOT NULL,
    correlation_id VARCHAR(64) NOT NULL,
    trace_id VARCHAR(64) NOT NULL,
    session_id VARCHAR(64) NOT NULL,
    synthetic_customer_id VARCHAR(20) NULL,
    tool_name VARCHAR(64) NULL,
    approval_status VARCHAR(20) NULL,
    execution_status VARCHAR(20) NULL,
    latency_ms NUMERIC(12, 3) NULL,
    error_code VARCHAR(64) NULL,
    details_json VARCHAR(4000) NOT NULL DEFAULT '{}',
    created_at TIMESTAMP NOT NULL
);
CREATE INDEX IF NOT EXISTS ix_audit_events_event_name ON audit_events(event_name);
CREATE INDEX IF NOT EXISTS ix_audit_events_correlation_id ON audit_events(correlation_id);
CREATE INDEX IF NOT EXISTS ix_audit_events_trace_id ON audit_events(trace_id);
```

#### 11.3.2 DDL SQL Completo — SQLite Almacén de Sesiones Durables (`data/sessions.db`)
Datastore: `ai/agent/src/aegisbank_agent/session_store.py`

```sql
CREATE TABLE IF NOT EXISTS agent_sessions (
    session_id TEXT PRIMARY KEY,
    customer_id TEXT NOT NULL,
    last_loan_id TEXT,
    last_account_id TEXT,
    last_intent TEXT,
    metadata_json TEXT,
    created_at TEXT NOT NULL,
    updated_at TEXT NOT NULL
);
CREATE INDEX IF NOT EXISTS idx_agent_sessions_customer ON agent_sessions(customer_id);
```

#### 11.3.3 DDL SQL Completo — PostgreSQL 17 + pgvector 0.8.0 (`ai/rag/src/aegisbank_rag/pgvector_retriever.py`)
Datastore: `pgvector/pgvector:0.8.0-pg17` / Azure Database for PostgreSQL Flexible Server

```sql
-- Extensión vectorial obligatoria
CREATE EXTENSION IF NOT EXISTS vector;

-- Tabla: rag_chunks (Segmentos de conocimiento bancario con embeddings)
CREATE TABLE IF NOT EXISTS rag_chunks (
    chunk_id VARCHAR(64) PRIMARY KEY,
    document_id VARCHAR(64) NOT NULL,
    document_version VARCHAR(32) NOT NULL,
    status VARCHAR(32) NOT NULL,
    effective_from DATE NOT NULL,
    effective_to DATE,
    source VARCHAR(255) NOT NULL,
    topic VARCHAR(64) NOT NULL,
    title VARCHAR(255) NOT NULL,
    content TEXT NOT NULL,
    metadata JSONB NOT NULL DEFAULT '{}'::jsonb,
    embedding vector(32) NOT NULL,
    embedding_model_id VARCHAR(64) NOT NULL,
    created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
    updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

-- Índices relacionales para filtrado de documentos activos y versiones
CREATE INDEX IF NOT EXISTS idx_rag_chunks_status_topic ON rag_chunks (status, topic);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc_ver ON rag_chunks (document_id, document_version);
CREATE INDEX IF NOT EXISTS idx_rag_chunks_model ON rag_chunks (embedding_model_id);

-- Índice vectorial HNSW (Hierarchical Navigable Small World) para distancia coseno (<=>)
CREATE INDEX IF NOT EXISTS idx_rag_chunks_hnsw
ON rag_chunks USING hnsw (embedding vector_cosine_ops)
WITH (m = 16, ef_construction = 64);
```

#### 11.3.4 Esquema Documental NoSQL — Azure Cosmos DB (`ai/agent/src/aegisbank_agent/cosmos.py`)
- **Partition Key:** `/customer_id` (garantiza point-reads eficientes en $O(1)$ sin cross-partition query en paths transaccionales).
- **Esquema de Documento (`contracts/cosmos-event-item.schema.json`):**
```json
{
  "id": "EVT-000001",
  "customer_id": "CUST-0001",
  "event_type": "ServiceRequestCreated",
  "aggregate_type": "ServiceRequest",
  "aggregate_id": "SR-000001",
  "payload": {
    "category": "CLAIM",
    "description": "Cargo de comisión no reconocido en cuota 2"
  },
  "_etag": "\"00002f00-0000-0800-0000-60b8b8f20000\"",
  "_ts": 1726059600
}
```
- **Change Feed Processor:** Emplea el lease container para registrar el progreso mediante checkpoints. El consumidor idempotente descarta reprocesamientos validando la tupla `(id, _etag)`.

#### 11.3.5 Topología de Llaves y Expiración — Azure Cache for Redis (`ai/rag/src/aegisbank_rag/cache.py`)
- **Namespaces y TTL:**
  - `rag:retrieval:{sha256(query_norm)}` — Resultados de recuperación híbrida (TTL = 300 segundos).
  - `rag:corpus:{topic}:{document_id}:{version}` — Chunks y metadatos de políticas bancarias (TTL = 600 segundos).
  - `rag:lock:{sha256(query_norm)}` — Mutex distribuido para **Single-Flight Stampede Protection** (TTL = 10 segundos).
- **Regla Inviolable de Seguridad de Datos:** **PROHIBIDO cachear en Redis saldos, cuotas, nombres de clientes o propuestas HITL**. Los datos bancarios transaccionales tienen TTL = 0s (consulta directa forzada al motor core).

### 11.4 Outbox + Idempotent Consumer (lo más importante)
Cuando `POST /api/v1/service-requests` se ejecuta:
1. SQLAlchemy `session.begin()`.
2. INSERT `ServiceRequest`.
3. INSERT `OutboxEvent(event_id="EVT-000001", event_type="ServiceRequestCreated", payload=JSON)`.
4. COMMIT (atómico).
5. Background publisher drena `OutboxEvent(status='PENDING')` → `LocalMessageBus.publish(topic, msg)`.
6. Adapter traduce a Azure Service Bus AMQP si `azure_servicebus_adapter` está cableado.
7. `IdempotentConsumer.handle(msg)` valida `id:etag` (Cosmos) o `(event_id, payload_hash)` (local) — duplicados se descartan silenciosamente.
8. Veneno → `DeadLetterQueue`.

### 11.5 Lo que NO está permitido cachear
- Saldos de cuenta.
- Próximas cuotas.
- Estado HITL transaccional.
- Datos privados del cliente.

El cache es solo para **public knowledge + corpus vectors + retrieval results**. TTL 0s (siempre direct query) para todo lo demás.

---

## 12. El agente Aegis: orquestador, herramientas, HITL, HOTL, MCP

### 12.1 AgentOrchestrator — `ai/agent/src/aegisbank_agent/agent.py` (~1,190 líneas)
- **Firma:** `run(user_message, *, customer_id, session_id=None, correlation_id=None, approval_callback=None) -> AgentExecutionResult`.
- **Init:** carga system prompt versionado (`agent-system-v003`), construye `OpenAI` client con `base_url=resolve_foundry_base_url()`, `timeout=float(os.getenv("AEGISBANK_FOUNDRY_TIMEOUT_SECONDS", "30.0"))`, `max_retries=int(os.getenv("AEGISBANK_FOUNDRY_MAX_RETRIES", "2"))`.
- **Multi-turn:** max 3 rondas de tool calling.
- **Routing determinista (gating):**
  - `requires_account_data(user_message) → True` ⇒ `account_required=True`.
  - `is_greeting(user_message) → True` ⇒ `tools=[]` (sin tools ofrecidas al LLM, respuesta directa rápida).
  - Si `account_required`: filtra tools a `account_tool_allowlist(user_message) ∪ WRITE_TOOLS`; si queda exactamente 1 tool ⇒ fuerza `tool_choice={"type":"function","function":{"name":"..."}}`.
  - Else: todas las tools disponibles.
- **Forced deterministic path & anáfora:**
  - Si `extract_loan_id()` es None pero `is_last_loan_reference()` ⇒ recupera `session.last_loan_id` de `SessionStore`.
  - Si `account_required && forced_loan_id && allowlist==["get_loan_details"]` ⇒ ejecuta `get_loan_details` directo, formatea answer, actualiza `record_loan_access`, retorna en **0 rondas LLM** y **1 tool**.
- **Pseudo-tool-call detection** (anti-mimicking):
  - Si LLM devuelve texto mimickeando firma de función (`get_loan_details(LOAN-0001)` como texto plano) sin emitir structured tool_calls, con regex `\b(get_loan_details|get_my_loans|get_next_installment)\s*\(` y `account_required=True` ⇒ incrementa `pseudo_tool_call_count`, audita `TOOL_DENIED{reason:PSEUDO_TOOL_CALL}`, retorna fallo controlado.

### 12.1.1 Almacén de sesión durable SQLite — `ai/agent/src/aegisbank_agent/session_store.py`
Para resolver la amnesia en CLI entre ejecuciones independientes de procesos (`python -m aegisbank_agent.cli run`):
- **Datastore:** SQLite embebido local (`data/sessions.db`), serverless, zero-cloud.
- **Tabla:** `agent_sessions(session_id TEXT PRIMARY KEY, customer_id TEXT NOT NULL, last_loan_id TEXT, last_account_id TEXT, last_intent TEXT, metadata_json TEXT, created_at TEXT, updated_at TEXT)`.
- **Invariante de frontera de cliente (Anti-IDOR):**
  `get_session(session_id, customer_id)` verifica estrictamente `stored.customer_id == customer_id`. Si `CUST-0002` intenta cargar una sesión creada por `CUST-0001`, levanta `OwnershipViolationError` inmediatamente.
- **Resolución anafórica:** Permite resolver consultas como `"¿cuál fue el último préstamo por el que te consulté?"` o `"¿cuánto debo del anterior?"` leyendo `session.last_loan_id` sin invocar al LLM.

### 12.1.2 Invariante canónico 'Zero Account Fakery' y defensas post-generación (v1.0.6)
> **Invariante canónico:** `AccountDataClaim => SuccessfulAuthorizedToolCall`.
> Ninguna respuesta puede entregar o simular datos bancarios privados de un cliente si no existe evidencia verificable de una herramienta autorizada ejecutada exitosamente en el mismo turno.

Para hacer cumplir este invariante, el orquestador implementa cuatro interceptores post-generación:
1. **`PLACEHOLDER_LEAK`**: Detecta filtración de plantillas sintéticas emitidas por el LLM cuando no sabe qué responder (p.ej. `[Nombre del Préstamo]`, `[Fecha de Pago 1]`, `[Monto]`, `[Número de Cuotas]`). Intercepta y sustituye la respuesta por la negativa canónica.
2. **`PROCESS_HALLUCINATION`**: Detecta cuando el modelo simula pausas o esperas de ejecución en texto plano (p.ej. `[Breve pausa mientras el asistente realiza la consulta]`, `[Consultando al sistema central...]`). Audita el evento bajo `PROCESS_HALLUCINATION` y aborta la respuesta espuria.
3. **`FALSE_TOOL_EXECUTION_CLAIM`**: Detecta afirmaciones en las que el LLM dice haber consultado información (p.ej. `"He consultado tus préstamos..."`, `"He encontrado los detalles de tu cuenta..."`) cuando en realidad `tools_executed == 0`.
4. **`UNGROUNDED_ACCOUNT_RESPONSE`**: Si el mensaje del usuario requería datos de cuenta pero ninguna herramienta devolvió éxito, y el LLM emite afirmaciones factuales sobre productos, se aplica abstención estricta:
   `"No pude consultar la información verificada de tus cuentas en este momento. Por favor, indícame el número de préstamo específico (por ejemplo, LOAN-0001) para consultarlo directamente."`

### 12.1.3 Plan comparativo determinista multicuenta (v1.0.6)
Para consultas analíticas o superlativas complejas (p.ej. `"¿dime cual es el prestamo con más saldo pendiente que tengo y que fechas de pago tengo??"`):
1. **Detección de intención comparativa:** Se detecta que el usuario solicita el extremo (`más saldo pendiente`, `mayor deuda`) junto con detalle de cuotas.
2. **Fase 1 (Recuperación y agregación determinista):** Invoca `get_my_loans(customer_id)`. Extrae la lista de préstamos activos y calcula `max(outstanding_balance)` usando aritmética determinista en Python (`float(item['outstanding_balance'])`).
3. **Fase 2 (Enlace y persistencia):** Identifica el préstamo de mayor saldo (p.ej. `LOAN-0001`) y actualiza `session_store.record_loan_access`.
4. **Fase 3 (Sub-consulta encadenada):** Invoca `get_next_installment(loan_id="LOAN-0001", customer_id)`.
5. **Resultado:** Devuelve una respuesta 100% aterrizada y exacta en **0 rondas LLM** y **2 tools ejecutadas**, con latencia < 50ms y cero riesgo de alucinación.

### 12.2 Tool Registry — `ai/agent/src/aegisbank_agent/tools/`
- **5 tools canónicas** (4 read + 1 write):
  1. `SearchKnowledgeTool` — `execute(query, top_k) -> [RetrievalHit]` → RAG.
  2. `GetMyLoansTool` — `execute(customer_id)` → `LoanRepository.list_by_customer(customer_id)`.
  3. `GetLoanDetailsTool` — `execute(loan_id, customer_id)` → valida `loan.customer_id == session_customer_id`, sino `ToolResult(success=False, error="Acceso denegado: …")`.
  4. `GetNextInstallmentTool` — `execute(loan_id, customer_id)` → ownership check + `InstallmentRepository.list_by_loan(loan_id)` + `select_next_installment(...)`.
  5. `CreateServiceRequestTool` (WRITE, only when `include_write_tools=True`) — `execute(category, description, customer_id, idempotency_key?)` → wrapped in `IdempotencyGuard.execute_idempotent(...)`.
- **WRITE_TOOLS = {"create_service_request"}** constante.
- **Authorization enforcement** = tres valles independientes:
  1. **HOTL kill-switch** (atomic flag) antes de ejecutar.
  2. **HITL state machine** con canonical-JSON argument hashing.
  3. **Tool allowlist** determinista basado en `account_tool_allowlist(query)`.
- **Per-tool ownership check** dentro de cada tool (fail-closed).
- **OpenAI schema export**: cada `FunctionTool.to_openai_tool()` → `{"type":"function","function":{"name","description","parameters"}}`.
- **MCP export**: `mcp/server.py::MCPServer` con `ToolAnnotations(read_only_hint, destructive_hint)`.

### 12.3 HITL State Machine — `ai/agent/src/aegisbank_agent/hitl.py` (244 líneas)
- **Estados:** `PENDING` → `APPROVED` → `EXECUTED` (success path), o `PENDING` → `REJECTED` (denied), o `PENDING/APPROVED` → `REJECTED` con `rejection_reason="Argumentos alterados…"` (tampering).
- **Anti-tampering:** canonical-JSON hash de los argumentos aprobados + customer_id binding. `verify_and_mark_executed` re-valida customer match y hash equality.
- **Approval ID format:** `APPR-XXXXXXXX`.
- **Inmutabilidad:** una vez `EXECUTED` no se puede re-aprobar; intentos adicionales son denegados.

### 12.4 HOTL Supervisor — `ai/agent/src/aegisbank_agent/observability/hotl.py`
- Variable atómica thread-safe (`is_write_allowed`).
- Check antes de cada WRITE. Si engaged → audit `TOOL_DENIED{actor:HOTL_SUPERVISOR}` + fast-fail.
- **Local:** variable en memoria (testeable via CLI / test fixture).
- **Cloud target:** Azure App Configuration Feature Flag dinámico (sin redeployment).
- Engagement flow: Client → Agent → [HOTL: ACTIVE?] → si NO (allowed) ejecuta tool con HITL; si YES → FAST-FAIL con mensaje "Escrituras suspendidas por supervisión".

### 12.5 MCP Boundary — `ai/agent/src/aegisbank_agent/mcp_boundary.py` + `mcp/server.py`
- **Protocol:** mcp==2.1.1, MCP protocol version `2026-07-28`.
- **Transporte:** stdio (process-level sandboxing; no port conflicts; no unauthorized network).
- **Distinción canónica entre MCP de Producto y MCPs del Coder:**
  - **AegisBank Product MCP (`mcp/server.py`):** Es la frontera funcional del asistente bancario hacia clientes externos o frontends compatibles con Model Context Protocol. Expone estrictamente lógica de negocio bancario y hace cumplir los límites HITL/HOTL.
  - **Coder Tooling MCPs (`.opencode/`):** (`filesystem`, `git`, `sequential-thinking`, `context7`, `codebase-memory`) son herramientas que utiliza el desarrollador en el IDE para inspeccionar el repo y no existen ni se despliegan en el runtime de producción de AegisBank.
- **Tools expuestas al cliente MCP:**
  - READ (4): `search_knowledge`, `get_my_loans`, `get_loan_details`, `get_next_installment` con `readOnlyHint=true`.
  - WRITE (1): `create_service_request` con `readOnlyHint=false, destructiveHint=false`.
- **HITL boundary enforced in MCP:** el server crea `ApprovalRequest` inmutable desde la propuesta normalizada usando el `AgentContext` customer del runtime. CLI muestra tool/category/description/customer; solo un `y` explícito flips PENDING→APPROVED. Cualquier otra respuesta → denied. Server verifica tool identity, customer ownership, approval state y **exact arguments** antes de llamar al deterministic Core Banking tool.
- **Subprocess entrypoint:** `mcp_server.py` (47 líneas) arranca stdio loop.

### 12.6 Reliability Layer (resumen)
- **IdempotencyGuard:** `execute(key, op) -> (Any, bool)` — key basado en SHA-256(payload) + event_id. Re-aparición con mismo content → cached response; con diferente content → `IdempotencyConflictError`.
- **RetryPolicy:** exponential backoff + jitter, bounded, `transient_classifier` filtra excepciones transitorios (timeout, connection reset, 5xx) vs permanentes (4xx, validation).
- **CircuitBreaker:** FSM CLOSED→OPEN (tras N fallos consecutivos) →HALF_OPEN (tras cooldown) →CLOSED (tras éxito de prueba) o OPEN (si falla la prueba).
- **TimeoutGuard:** `@with_timeout(seconds)` y `execute_with_timeout(fn, seconds)` para llamadas LLM y DB.
- **LocalMessageBus / IdempotentConsumer / DLQ:** desacoplan productores y consumidores; mensajes venenosos terminan en DLQ con `dlq_envelope` + reason.

### 12.7 Observability Layer (resumen)
- **TracerProvider:** OTel SDK + `trace_span()` context manager. W3C `traceparent` propagation. Spans: `agent.run`, `llm.chat`, `tool.<name>`, `outbox.publish`, `consumer.handle`, `db.query`.
- **StructuredLogger + RedactionFilter:** redacta API keys, passwords, bearer tokens, PII. PROHIBIDO usar `logging.basicConfig` sin el filtro.
- **OperationalMetrics:** counters, histograms, percentiles p50/p95/p99.
- **AuditLogger:** append-only WORM-style con `AuditEventType` enum. Separation audit vs ops logs.
- **Telemetry:** persistencia por corrida (DB + audit).
- **AgentOpsSummary:** reporte de salud post-run.

### 12.8 MLOps Layer (resumen)
- **MLflowTracker:** backend SQLite local en `reports/mlruns/mlflow.db`, experimento `aegisbank-v015-agent-evaluation`, registra run_id + params + 9 métricas Foundry + artifacts.
- **DriftDetector:** PSI (Population Stability Index) sobre categóricas, Wasserstein para continuas, JSD (Jensen-Shannon Divergence) para predictions. **Status v0.15:** DATA_DRIFT `STABLE` (PSI=0.0000), PREDICTION_DRIFT `STABLE` (JSD=0.0000), MODEL_PERFORMANCE_DRIFT `STABLE`.
- **ABExperimentHarness:** McNemar paired test + bootstrap CI. **Status v0.15:** p=0.248213, CI [0.0000, 0.1714] → `STATISTICAL_SUPERIORITY_NOT_ESTABLISHED`. Promoción bajo política operacional: threshold + safety invariants + zero regression.

---

## 13. El sistema RAG: retrieval híbrido, generación con citas, abstención

### 13.1 Componentes
- **Corpus sintético:** 12 documentos en `ai/rag/data/corpus/`, 6 topics (`comisiones`, `creditos`, `cuotas`, `politicas`, `productos`, `reclamos`). 11 activos + 1 superseded (`creditos_producto_general` v1 superseded por v2 `effective2026-07-01`).
- **Manifest:** `ai/rag/data/corpus-manifest.json` con per-document `{document_id, version, topic, status, effective_from, effective_to}` + corpus SHA-256 fingerprint.
- **Chunking:** sentence-boundary `_SENTENCE_SPLIT = re.compile(r"(?<=[\.\?\!])\s+(?=[A-ZÁÉÍÓÚÑ¿¡])")`, packed en chunks de 50–300 chars. IDs `chk_{document_id}__{version}__c{n:03d}_{digest12}`.

### 13.2 Retrievers disponibles
| Retriever | Backend | Notas |
|---|---|---|
| `lexical_tfidf` | TF-IDF | Baseline. |
| `dense_local_lsa` | TF-IDF + `TruncatedSVD(n_components=64, random_state=42)` + L2 | Sin GPU, 100% local. |
| `hybrid_rrf` | lexical + dense via Reciprocal Rank Fusion k=60 | Frozen para v0.4. Gana todas las métricas. |
| `pgvector` | `pgvector/pgvector:0.8.0-pg17` HNSW | Metadata filtering + cosine `<=>`. |
| `redis` | RediSearch KNN | Single-flight stampede protection. |

### 13.3 Foundry Local integration
- `ai/rag/src/aegisbank_rag/foundry_local.py::FoundryLocalProvider` implementa el Protocol `LLMProvider` (definido en `provider.py`).
- Mismo adapter usado por `AgentOrchestrator` (single source of truth).
- `MAX_RETRIES=2`, `TIMEOUT=30.0s` por default (elevado en v1.0.6 tras post-mortem de socket abort en Kestrel a 10s).

### 13.4 Generation pipeline
1. `query → retrieval (hybrid_rrf o pgvector) → context builder → LLMProvider → grounded answer + citations`.
2. Prompt: `prompts/rag-answer-v001.json` (versionado, frozen).
3. Output estricto JSON: `{answer, citations[], abstained}`.
4. Citations deben ser `chunk_id`s exactos.
5. Retrieved content sospechoso → tratado como untrusted evidence (defense vs indirect prompt injection en retrieval).

### 13.5 Abstención (regla de oro)
- Si la evidencia es insuficiente, contradictoria, obsoleta (superseded), o out-of-domain → **abstain** (no fabricar).
- Mensaje canónico: "No encuentro información suficiente en la base de conocimiento autorizada para confirmar ese dato."
- Métrica tracked: `abstention_correctness` en `evaluation.py::metrics`.

### 13.6 Evaluación
- Frozen queries: `ai/rag/data/queries.jsonl` (18 queries) + `qrels.json` (ground truth).
- 4 categorías: direct, paraphrase, version, out-of-domain.
- Métricas: Precision@5, Recall@5, MRR@5, nDCG@5.
- **v0.4 resultado (frozen):** hybrid_rrf gana las 4 métricas.
- **v0.12 re-ejecución:** protocolo v0.4 corrido contra pgvector para verificar no-degradación → `HISTORICAL_BENCHMARK_PRESERVED`.

### 13.7 Red-team Phase-2 (estado actual)
- La suite fija `test_adversarial_red_team.py` demuestra `ASR = 0% on the frozen fixed adversarial suite`; no demuestra resistencia universal a prompt injection.
- Las fixtures Phase-2 cubren indirect RAG prompt injection, tool-output injection y separación entre seguridad y utilidad. Evidencia: `docs/security/PHASE2-LOCAL-RED-TEAM-EVIDENCE.md`.
- El briefing no es la máxima fuente de verdad. Código, tests, runtime, Git y documentación de arquitectura ejecutable prevalecen sobre este snapshot.
- **Reconciliación de utilidad:** el reporte live registrado contiene tres controles benignos. Bajo el oráculo corregido compartido, `benign_task_success_rate = 3/3 = 1.0` y `false_refusal_rate = 0/3 = 0.0`; el reporte previo `1.0` / `0.6667` usaba criterios asimétricos y quedó reconciliado.
- **Cobertura live (Phase 2.1 & 2.2):** la suite en vivo cubre DIRECT, MISINFORMATION, MULTI_TURN y MUTATION (`reports/red_team_phase2.json`, ASR = 0/8 = 0.0%), y en Phase 2.2 evalúa en vivo indirect RAG/XPIA contra pgvector y tool-output injection contra Foundry Local (`reports/red_team_phase22.json`, ASR = 0/2 = 0.0%, benign_task_success = 2/2 = 1.0, false_refusal = 0/2 = 0.0%). Red teaming en nube y resiliencia en producción permanecen CLOUD-PENDING y PROD-UNPROVEN.

---

## 14. El clasificador de intención (clásico ML)

### 14.1 Pipeline (`ml/intent-classifier/src/aegisbank_intent_classifier/pipeline.py`)
- TF-IDF: `TfidfVectorizer(lowercase=True, ngram_range=(1,2), min_df=1, max_df=1.0, sublinear_tf=True, norm="l2", token_pattern=r"(?u)\b\w\w+\b")`.
- Classifier: `LogisticRegression(C=1.0, l1_ratio=0.0, solver="lbfgs", max_iter=1000, tol=1e-4, random_state=42)`.
- Dummy baseline: `DummyClassifier(strategy="most_frequent")` para tener floor.

### 14.2 Dataset sintético
- 5 labels: `informational`, `account_query`, `service_request`, `sensitive_action`, `unsupported`.
- Generación: 25 topic groups × 4 variations × 5 classes = **500 records**.
- Split: 20 grupos train (400) + 5 grupos holdout (100) por label.
- StratifiedGroupKFold(n_splits=5) con `template_group_id` como groups (no leakage).
- **Frozen SHA-256:** `db250b5993e892610d29a2cc53bdafcff08d085df29deecf9a53515a13308664`.

### 14.3 Resultados frozen (v0.3)
- Dummy macro-F1 = 0.0667.
- Model CV mean = 0.9975 ± 0.0050.
- Holdout macro-F1 = 1.000 (diagonal confusion matrix).
- **Caveat del README:** "near-perfect result likely reflects the balanced, template-generated language. It is not evidence of performance on real users."

### 14.4 CLI (`cli.py`)
- `generate` — regenera dataset + manifest.
- `validate` — corre invariants.
- `evaluate` — CV + one-shot holdout → `reports/baseline-metrics.json` + `reports/baseline-report.md`.
- `predict <text>` — retrain on TRAIN each call (no persisted model).

### 14.5 Por qué clásico ML (no LLM)
- Reproducibilidad total (seed=42, SHA-256 pinned).
- Latencia sub-milisegundo en CPU.
- Foundation para comparar contra LLM classifiers con el mismo protocolo de evaluación.
- Cumple el competency "classical ML intent baseline" del AI-103 / AI-102.

---

## 15. Workflows principales: los 8 journeys bancarios A–H

Definidos formalmente en `docs/quality/E2E-MATRIX.md` y verificados mediante tests de integración y extremo a extremo en `ai/agent/tests/e2e/test_critical_journeys.py`. Los 8 workflows demuestran que las políticas deterministas de seguridad bancaria, aislamiento IDOR, Human-in-the-Loop, outbox transaccional y resiliencia de fallos operan con precisión absoluta.

### 15.1 Matriz Resumen de los 8 Journeys

| Journey | Nombre y Flujo | Capacidad Validada | Módulos Clave Involucrados | Evidencia Primaria en Tests |
|---|---|---|---|---|
| **A** | **Single-Step READ Account Routing**<br>`get_my_loans` → Respuesta | Enrutamiento determinista de cuentas propias sin exponer datos ajenos. | `AgentOrchestrator`, `GetMyLoansTool`, SQLite Core Banking | `test_critical_journeys.py::test_journey_a_read_account_policy_routes_real_tool` |
| **B** | **Multi-Step READ Account Composition**<br>`get_my_loans` → `get_next_installment` | Encadenamiento multi-turno con extracción contextual y correlation_id compartido. | `AgentOrchestrator`, `GetNextInstallmentTool`, SQLite Core Banking | `test_critical_journeys.py::test_journey_b_multistep_read_routes_next_installment` |
| **C** | **RAG Knowledge Available + Grounding**<br>`search_knowledge` → Respuesta citada | Retrieval híbrido RRF ($k=60$) y validación estricta post-generación de citas `[chunk_id]`. | `SearchKnowledgeTool`, `HybridRetriever`, `GroundedGenerator` | `test_critical_journeys.py::test_journey_c_rag_knowledge_available_with_grounding` |
| **D** | **RAG Knowledge Gap + Abstención**<br>Gap de política → Abstención UC-005 | Detección determinista de falta de evidencia; cero alucinación sobre temas no cubiertos. | `SearchKnowledgeTool`, `OperationalMetrics`, `AgentOrchestrator` | `test_critical_journeys.py::test_journey_d_rag_knowledge_gap_abstains_before_generation` |
| **E** | **WRITE via MCP con HITL REJECT**<br>Propuesta → Rechazo operador → 0 efectos | Interceptación de mutación; el rechazo humano garantiza cero inserciones en base de datos. | `CreateServiceRequestTool`, `HITLApprovalManager`, Core Banking SQLite | `test_critical_journeys.py::test_journey_e_write_hitl_reject_zero_side_effects` |
| **F** | **WRITE con HITL APPROVE + Outbox + Consumer**<br>Aprobación → SQLite → Outbox → Bus → Func | Flujo transaccional completo: verificación anti-tampering, ACID Outbox, deduplicación CloudEvent. | `HITLApprovalManager`, `OutboxProcessor`, `LocalMessageBus`, `IdempotentConsumer` | `test_critical_journeys.py::test_journey_f_write_hitl_approve_idempotent_outbox_consumer` |
| **G** | **HOTL Supervisory Kill-Switch**<br>Activación parada → Bloqueo preventivo | Interruptor maestro de seguridad que anula escrituras en milisegundos sin reiniciar servicios. | `HOTLSupervisor`, `AuditLogger`, `AgentOrchestrator` | `test_critical_journeys.py::test_journey_g_hotl_kill_switch_blocks_write` |
| **H** | **Reliability: Retries, Circuit Breaker & DLQ**<br>Fallo transitorio → FSM CB → Mensaje a DLQ | Mitigación de fallas: backoff exponencial, aislamiento por Circuit Breaker y aislamiento de mensajes venenosos. | `RetryPolicy`, `CircuitBreaker`, `DeadLetterQueue`, `IdempotentConsumer` | `test_critical_journeys.py::test_journey_h_reliability_retries_circuit_breaker_dlq` |

---

### 15.2 Trazabilidad Técnica Detallada Paso a Paso

#### Journey A: Consulta de Préstamos del Cliente Autenticado (Single-Step READ)
```
[1. User Prompt]        : "¿Cuáles son mis préstamos activos?" (--customer-id CUST-0001)
[2. Route Policy Gating]: AgentOrchestrator._route_policy detecta patrón de cuenta propia (requires_account_data=True).
                          Allowlist de herramientas se restringe a ["get_my_loans"].
[3. Tool Execution]     : Invocación determinista GetMyLoansTool.run({"customer_id": "CUST-0001"}).
                          Query SQLite: SELECT * FROM loans WHERE customer_id = 'CUST-0001' AND status = 'ACTIVE'.
                          Datos retornados: [{"loan_id": "LOAN-0001", "principal": 10000.0, "balance": 4500.0, "currency": "PEN"}, ...]
[4. Post-Gen Defense]   : Interceptor verifica que los números de préstamo y montos en el texto final del LLM
                          coincidan estrictamente con el JSON retornado por la herramienta (Invariante I_1: Zero Account Fakery).
[5. Audit Event]        : AuditLogger emite TOOL_EXECUTED {customer_id: "CUST-0001", tool: "get_my_loans", status: "SUCCESS"}.
[6. Final Answer]       : "Tienes 2 préstamos activos: LOAN-0001 (saldo PEN 4,500.00) y LOAN-0002 (saldo PEN 1,750.00)."
```

#### Journey B: Encadenamiento Multi-Paso Préstamo → Próxima Cuota (Multi-Step READ)
```
[1. User Prompt]        : "¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?" (--customer-id CUST-0001)
[2. Round 1 Execution]  : Ejecuta get_my_loans({"customer_id": "CUST-0001"}).
                          Recupera préstamos activos; persiste en AgentSessionStore last_loan_id = "LOAN-0002".
[3. Round 2 Execution]  : LLM emite llamada estructurada a get_next_installment({"loan_id": "LOAN-0002"}).
                          Query SQLite: SELECT * FROM installments WHERE loan_id = 'LOAN-0002' AND status = 'PENDING'
                          ORDER BY due_date ASC LIMIT 1.
                          Datos retornados: {"installment_number": 3, "amount": 450.00, "due_date": "2026-09-25", "currency": "PEN"}.
[4. Correlation Sync]   : Ambas llamadas comparten el mismo correlation_id ("CORR-...") y traceparent W3C.
[5. Final Answer]       : "Tus préstamos son LOAN-0001 y LOAN-0002. Para tu préstamo LOAN-0002, tu próxima cuota es la N.° 3 por PEN 450.00 con vencimiento el 25/09/2026."
```

#### Journey C: Búsqueda de Políticas con Citas de Evidencia (RAG Grounded)
```
[1. User Prompt]        : "¿Cuáles son los plazos y requisitos para un crédito personal?" (--customer-id CUST-0001)
[2. Route Policy Gating]: Gating clasifica como consulta general de conocimiento normativo (requires_account_data=False).
                          Allowlist de herramientas selecciona SearchKnowledgeTool.
[3. Hybrid Retrieval]   : Invocación SearchKnowledgeTool.run({"query": "plazos requisitos crédito personal"}).
                          Ejecución híbrida Reciprocal Rank Fusion (RRF k=60):
                          - Lexical BM25 ranking + Dense SVD cosine similarity ranking.
                          - Chunks recuperados: DOC-POL-001#c01 y DOC-POL-001#c02 (status = 'active').
[4. Grounded Gen & Eval]: Inyección en el prompt activo únicamente de los fragmentos recuperados.
                          LLM genera texto incluyendo la referencia explícita: "[DOC-POL-001#c01]".
                          validate_citations() corrobora que la cita existe, está activa y previene citas fantasma.
[5. Final Answer]       : "El crédito personal ofrece plazos de 6 a 60 meses según la política vigente [DOC-POL-001#c01]."
```

#### Journey D: Detección de Gap de Conocimiento y Abstención Determinista (RAG Gap UC-005)
```
[1. User Prompt]        : "¿Cuál es el plazo máximo para un crédito vehicular?" (--customer-id CUST-0001)
[2. Hybrid Retrieval]   : SearchKnowledgeTool ejecuta búsqueda sobre el catálogo sintético de políticas bancarias.
                          Resultado: Cero coincidencias con score superior al umbral de relevancia (hits = []).
[3. Deterministic Halt] : Al detectar hits vacíos, el orquestador aborta la llamada generativa probabilística del LLM.
                          Emite la respuesta canónica de abstención determinista:
                          "No encuentro información suficiente en las políticas vigentes para responder a tu consulta sobre crédito vehicular."
[4. Operational Metric] : Se incrementa el contador determinista knowledge_abstention_count (métrica = 1). Cero alucinación.
```

#### Journey E: Intento de Mutación Rechazado por el Usuario (WRITE + HITL REJECT)
```
[1. User Prompt]        : "Quiero presentar un reclamo formal por un cobro indebido de comisión." (--customer-id CUST-0001)
[2. Tool Proposal]      : LLM genera llamada a herramienta de escritura:
                          create_service_request({"category": "CLAIM", "description": "Cobro indebido de comisión", "idempotency_key": "IDEMP-E2E-REJECT"})
[3. HITL Interception]  : HITLApprovalManager intercepta la llamada (readOnlyHint=False).
                          Calcula args_hash = SHA256(canonical_json(args)).
                          Crea registro en memoria con estado PROPOSED.
[4. Operator Callback]  : CLI presenta la propuesta al usuario con detalles y solicita confirmación: "¿Desea autorizar? [y/N]".
                          El usuario responde "n" (Rechazar).
[5. State Transition]   : Estado cambia a REJECTED {reason: "Rechazado por el operador"}.
[6. Zero Side Effects]  : La herramienta aborta inmediatamente. SELECT COUNT(*) FROM service_requests WHERE description LIKE '%comisión%' retorna 0.
[7. Final Answer]       : "La operación de registro de reclamo ha sido cancelada por el usuario. No se ha realizado ninguna modificación en el sistema."
```

#### Journey F: Mutación Aprobada con Transacción Outbox y Procesamiento Serverless (WRITE + HITL APPROVE)
```
[1. User Prompt]        : "Crea una solicitud formal para reprogramar mi préstamo." (--customer-id CUST-0001)
[2. Tool Proposal]      : create_service_request({"category": "LOAN", "description": "Reprogramación de deuda", "idempotency_key": "IDEMP-E2E-APPROVE-001"})
[3. Operator Callback]  : HITLApprovalManager intercepta en estado PROPOSED; el operador responde "y" (Aprobar).
[4. Anti-Tampering]     : Se re-calcula SHA256(args) antes de persistir y se valida idéntico al hash aprobado (Invariante I_2).
[5. ACID Dual-Persist]  : En una única transacción SQLite atómica en mock-core-banking:
                          a) INSERT INTO service_requests (id, customer_id, category, description, status) VALUES ('SR-...', ...);
                          b) INSERT INTO idempotency_records (idempotency_key, response_payload, created_at) VALUES (...);
                          c) INSERT INTO outbox_events (event_id, event_type, payload, status) VALUES ('EVT-...', 'ServiceRequestCreated', ..., 'PENDING');
                          (Invariante I_5: Eliminación total del riesgo de Dual-Write).
[6. Outbox Dispatch]    : OutboxProcessor.process_pending() lee eventos PENDING, los emite al MessageBus (Azure Service Bus emulator / LocalMessageBus)
                          y actualiza outbox_events.status = 'PROCESSED'.
[7. Idempotent Consume] : IdempotentConsumer recibe el evento envuelto en CloudEvents 1.0 (service-request-created-v1.schema.json).
                          Verifica deduplicación por event_id; si es nuevo, procesa y confirma; si es repetido, descarta sin re-ejecución.
```

#### Journey G: Bloqueo Preventivo Mediante Interruptor de Supervisión (HOTL Kill-Switch)
```
[1. Supervisor Action]  : El administrador ejecuta HOTLSupervisor.engage_kill_switch("Mantenimiento operativo de emergencia").
[2. User Prompt]        : "Crea una solicitud urgente de revisión de cuenta." (--customer-id CUST-0001)
[3. Immediate Intercept]: El orquestador intenta evaluar create_service_request.
                          HOTLSupervisor.assert_write_allowed() detecta kill_switch_engaged=True.
[4. Block Outcome]      : Bloqueo automático en menos de 1 milisegundo sin consultar al usuario ni evaluar HITL:
                          ToolResult(success=False, error="HOTL supervisory kill-switch active: Mantenimiento operativo de emergencia").
[5. Audit Telemetry]    : Se registra el evento de seguridad HOTL_KILL_SWITCH_BLOCKED_WRITE en la tabla WORM audit_events.
[6. Final Answer]       : "En este momento las operaciones de registro y modificación están suspendidas por mantenimiento operativo del banco. Por favor intenta más tarde."
```

#### Journey H: Resiliencia ante Fallos de Dependencias (Retries, Circuit Breaker y Dead-Letter Queue)
```
[1. Scenario 1: Retries Transitorios]
    - Llamada a Core Banking falla con ConnectionError transitorio (intentos 1 y 2).
    - RetryPolicy(max_retries=3, base_delay=0.01s) intercepta la excepción.
    - Aplica backoff exponencial sin agotar hilos.
    - Intento 3 responde exitosamente -> Estado recuperado transparentemente sin error para el usuario.

[2. Scenario 2: Circuit Breaker ante Falla Persistente]
    - Servicio externo caído responde sostenidamente con HTTP 503 / Crash.
    - CircuitBreaker registra 2 fallos consecutivos (failure_threshold=2).
    - La máquina de estados transiciona FSM: CLOSED -> OPEN.
    - Llamadas posteriores lanzan CircuitBreakerOpenError inmediatamente (fast-fail, latencia <0.1ms), protegiendo el pool de conexiones del agente.
    - Tras recovery_timeout (ej. 30s), transiciona a HALF_OPEN para sondear una única petición de prueba.

[3. Scenario 3: Mensajes Venenosos y Dead-Letter Queue (DLQ)]
    - Un evento con payload corrupto o schema inválido llega a la cola de mensajería (CorruptedPayloadEvent).
    - Intento 1 de IdempotentConsumer falla por error de deserialización y re-lanza para permitir redelivery de la infraestructura.
    - Intento 2 alcanza max_delivery_attempts = 2.
    - IdempotentConsumer aísla el mensaje venoso encolándolo en DeadLetterQueue (DLQ).
    - Retorna False; el bus no se bloquea y los mensajes válidos subsiguientes continúan procesándose con normalidad.
```

---

## 16. Workflows de desarrollo: la cadena de prompts 000–026

### 16.1 El patrón de los prompts
Cada prompt (excepto el maestro `000`) sigue el patrón:

1. **Heading:** `### N — AegisBank vX.Y [<name>]` (formato `### N` para numeración ancla).
2. **Working directory absoluto:** `Continúa exclusivamente vX.Y — <name> en C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`.
3. **Baseline verification:** `git rev-parse HEAD`, árbol limpio, `SessionGuard.acquire`.
4. **Operating posture:** `ONE WRITER MANY READERS`, `DISCOVER BEFORE CREATE`, `REUSE/EXTEND`.
5. **Authorized extras:** agentes, skills, env vars, imágenes con digest pinned.
6. **Permanent boundary restated** (lo no-negociable del milestone).
7. **Subtasks / acceptance gates** pre-listadas.
8. **Closing readiness marker:** `AEGISBANK_VX.Y_<...>_READY` (solo cuando cada gate ejecutó con evidencia real).

### 16.2 Catálogo Genealógico de los 28 Prompts del Proyecto

| # | Archivo de Prompt | Milestone | Objetivo y Componentes Desarrollados | Artefactos y Código Producido | Comando / Evidencia de Validación |
|---|---|---|---|---|---|
| **000** | `000_PROMPT.md` | `v0.1.0` | **Charter Maestro**: Standing instructions globales, anti-scope-creep, Definition of Done, 7 reglas permanentes y roadmap $v0.1 \to v1.0$. | `docs/charter/*`, `AGENTS.md`, `opencode.json` | `git diff --check`, `/charter-summary` |
| **001** | `001_PROMPT.md` | `v0.2.0` | **Mock Core Banking**: API REST con FastAPI, base de datos SQLite determinista, modelos de préstamo/cuotas y tabla outbox transaccional. | `services/mock-core-banking/`, `persistence/models.py` | `pytest services/mock-core-banking` |
| **002** | `002_PROMPT.md` | `v0.2.0` | **Cierre Limpio v0.2**: Autorización de excepción para limitar `ruff format` exclusivamente a `services/mock-core-banking`. | Scripts de verificación y commit limpio | `.venv\Scripts\python -m ruff format --check services/mock-core-banking` |
| **003** | `003_PROMPT.md` | `v0.5.0` | **Grounded Generation & Eval**: Interfaz neutral para LLMs, inyección de contexto activo y validación de citas obligatorias. | `ai/rag/src/aegisbank_rag/generator.py` | `pytest ai/rag/tests/unit/test_grounded_generation.py` |
| **004** | `004_PROMPT.md` | `v0.5.0` | **Detección de LLM Autorizado**: Script de diagnóstico y descubrimiento en tiempo de ejecución de Foundry Local (`phi-4-mini`) y fallback a OpenAI. | `scripts/test_foundry_connection.py` | Ejecución de probe HTTP hacia `GET /openai/status` |
| **005** | `005_PROMPT.md` | `v0.5.0` | **Live LLM Evaluation**: Evaluación de los 6 casos de prueba congelados contra el endpoint en vivo de Foundry Local / OpenAI. | `docs/experiments/v0.5-grounded-generation-evaluation.md` | `python scripts/run_frozen_experiment.py` |
| **006** | `006_PROMPT.md` | `v0.5.0` | **Recuperación de Foundry Local**: Plan de diagnóstico ante socket abort y configuración dinámica de puertos para `phi-4-mini`. | Procedimiento de reinicio y healthcheck CLI | `foundry server status`, `foundry model run` |
| **007** | `007_PROMPT.md` | `v0.5.0` | **Cierre y Staging v0.5**: Verificación integral de calidad de RAG y commit de baseline generativo en repositorio local. | Tags de madurez y reporte de laboratorio | `AEGISBANK_V0.5_READY`, `git commit` |
| **008** | `008_PROMPT.md` | `v0.6.0` | **Single Agent + Read Tools**: Primer `AgentOrchestrator` con límite estricto de 3 rounds y herramientas de solo lectura bancarias. | `ai/agent/src/aegisbank_agent/agent.py`, `tools/` | `pytest ai/agent/tests/unit/test_orchestrator.py` |
| **009** | `009_PROMPT.md` | `v0.6.1` | **Tool Calling Acceptance**: Validación de la invocación nativa de funciones estructuradas en `phi-4-mini` bajo formato OpenAI functions. | `tests/integration/test_tool_calling_acceptance.py` | `pytest tests/integration/test_tool_calling_acceptance.py` |
| **010** | `010_PROMPT.md` | `v0.7.0` | **MCP + HITL Foundation**: Servidor MCP stdio con `mcp==2.1.1` y máquina de estados formal Human-in-the-Loop con hash SHA-256. | `mcp/server.py`, `hitl.py`, `contracts/mcp-tools.schema.json` | `pytest ai/agent/tests/integration/mcp/` (32 tests) |
| **011** | `011_PROMPT.md` | `v0.8.0` | **Reliability & Messaging**: Primitivas de resiliencia: verificación de idempotencia, `RetryPolicy`, 3-state `CircuitBreaker` y `DeadLetterQueue`. | `reliability/retry.py`, `circuit_breaker.py`, `messaging.py` | `pytest ai/agent/tests/unit/reliability/` |
| **012** | `012_PROMPT.md` | `v0.9.0` | **Observability & Audit**: OpenTelemetry con propagación W3C `traceparent`, logger estructurado JSON y tabla WORM `audit_events`. | `observability/audit.py`, `telemetry.py`, `correlation.py` | `pytest ai/agent/tests/unit/observability/` |
| **013** | `013_PROMPT.md` | `v0.9.1` | **Knowledge Tool Routing**: Integración de `SearchKnowledgeTool` en el orquestador y enrutamiento híbrido RAG. | `tools/knowledge_tools.py`, `test_knowledge_tool_routing.py` | `pytest tests/integration/v09/test_knowledge_tool_routing.py` |
| **014** | `014_PROMPT.md` | `v0.9.2` | **Banking Tool IDOR Defense**: Aislamiento estricto de propiedad por `customer_id` y almacenamiento de sesión multi-turno en memoria. | `agent.py` (`_precheck_prompt...`), `test_ownership.py` | `pytest tests/integration/v09/test_ownership.py` |
| **015** | `015_PROMPT.md` | `v0.10.0` | **DevSecOps & CI/CD**: Pipeline GitHub Actions shift-left con Bandit (SAST), pip-audit (SCA), CycloneDX (SBOM) y escaneo de secretos. | `.github/workflows/ci.yml`, `docs/security/sbom.json` | `python scripts/quality_gate.py --fast` |
| **016** | `016_PROMPT.md` | `v0.10.1` | **Cross-Session Coordination**: Mecanismo `SessionGuard` (ONE WRITER MANY READERS), catálogo `CANONICAL-COMPONENTS.md` y auditoría de ADRs. | `scripts/session_guard.py`, `CANONICAL-COMPONENTS.md` | `python scripts/session_guard.py acquire / release` |
| **017** | `017_PROMPT.md` | `v0.11.0` | **Containerization**: Entorno local Docker Compose con emulador oficial Microsoft Azure Service Bus y adaptador de mensajería AMQP. | `deploy/local/docker-compose.yml`, `azure_service_bus.py` | `docker compose -f deploy/local/docker-compose.yml up` |
| **018** | `018_PROMPT.md` | `v0.11.1` | **Kubernetes Runtime**: Manifiestos K8s declarativos (`deploy/k8s/`), probes de salud (liveness/readiness) y políticas de recursos para Pods. | `deploy/k8s/*.yaml`, `test_k8s_manifests.py` | Validación sintáctica y de recursos de manifests K8s |
| **019** | `019_PROMPT.md` | `v0.12.0` | **PostgreSQL + pgvector**: Datastore vectorial empresarial en contenedor con índice HNSW cosine y script de benchmark de query plans. | `ai/rag/src/aegisbank_rag/vector_store.py`, `scripts/evaluate_retrievers_v012.py` | Reconciliación de planes HNSW vs. Seq Scan en postgres |
| **020** | `020_PROMPT.md` | `v0.12.1` | **Cosmos DB NoSQL Emulator**: Contenedor emulador Azure Cosmos DB, partition key `/customer_id` y Change Feed Processor con deduplicación `id:etag`. | `cosmos.py`, `docs/architecture/COSMOS-PARTITION-DESIGN.md` | Tests de Change Feed y checkpointing de leases |
| **020A** | `020A_PROMPT.md` | `v0.12.0-R1` | **Grounded Consistency & Provenance**: Reconciliación histórica de `v012_retrieval_comparison.json` (protocolo v0.4.0 ejecutado en v0.12). | `docs/evaluation/EVALUATION-CATALOG.md` (§2) | Verificación de inmutabilidad y metadatos de benchmarks |
| **021** | `021_PROMPT.md` | `v0.12.2` | **Redis Cache & Single-Flight**: Integración de Azure Cache for Redis emulator, estrategia cache-aside para RAG y single-flight stampede protection. | `ai/agent/src/aegisbank_agent/cache/caching.py` | `pytest tests/unit/cache/test_single_flight.py` |
| **022A** | `022A_PROMPT.md` | `v0.12.2-R1` | **Redis Evidence Hardening**: Verificación de TTL determinista (300s / 600s), pruebas de aislamiento de namespaces y benchmark hit/miss. | Reportes de latencia y tests de concurrencia de caché | `pytest tests/integration/test_redis_resilience.py` |
| **023** | `023_PROMPT.md` | `v0.13.0` | **Azure Functions + Event Grid**: Arquitectura serverless local con Python v2 programming model y webhook trigger para CloudEvents 1.0. | `functions/event_consumer/function_app.py`, `host.json` | `func start`, `pytest tests/integration/test_functions_local.py` |
| **024** | `024_PROMPT.md` | `v0.13.0-R2` | **Test Suite Rationalization**: Optimización de la pirámide de pruebas, eliminando 25% de deuda de tests redundantes manteniendo 15 invariantes. | `docs/quality/TEST-SUITE-RATIONALIZATION.md` | Ejecución de FAST gate en <30 segundos |
| **025** | `025_PROMPT.md` | `v0.13.1` | **Functions Live Runtime E2E**: Ejecución extremo a extremo del consumidor serverless procesando eventos de outbox vía Core Tools. | Traza E2E documentada con CloudEvent delivery | `pytest tests/e2e/test_serverless_event_flow.py` |
| **026** | `026_PROMPT.md` | `v0.14.0` | **App Config & Secrets Boundary**: Emulador de Azure App Configuration, referencias de Key Vault y fallback transparente `DefaultAzureCredential`. | `services/config/app_config.py`, `contracts/config.schema.json` | `pytest tests/unit/config/test_secrets_boundary.py` |

---

### 16.3 La regla ONE WRITER, MANY READERS
- Antes de editar: `python scripts/session_guard.py acquire` (lock atómico sobre el repo).
- Después de commit: `python scripts/session_guard.py release`.
- Previene race conditions cuando múltiples sub-agentes IA editan concurrentemente.
- Si el lock falla → espera a que el otro libere.

### 16.4 La regla DISCOVER BEFORE CREATE
1. Buscar (grep / rg) sobre nombres de clases y responsabilidades.
2. Consultar `docs/architecture/CANONICAL-COMPONENTS.md`.
3. Decidir: `REUSE` / `EXTEND` / `NEW_COMPONENT_JUSTIFIED` (justificar en el PR/commit).

---

## 17. Workflows de testing: pirámide, contratos, evaluación

### 17.1 La pirámide (estado v1.0)
```
        /\
       /  \          E2E (Critical User Journeys A-H)
      / E2E \         11 tests
     /──────\
    / Contract\      JSON Schema, MCP, Outbox events
   /──────────\       21 tests
  /Integration\     Components connected (DB + RAG + Bus + Cosmos)
 /──────────────\    51 tests
/     Unit       \   Single piece, no I/O or stubs
/──────────────────\  138 tests
```
**Total agent tests:** 248 passed (`tests/e2e/test_critical_journeys.py` + resto).
**Infra tests:** 46 passed, 12 skipped (Docker daemon no estaba corriendo en el último release local).
**Total v1.0 release:** 14/14 PASS en gates DevSecOps + ruff/format/compileall + bandit + pip-audit + secret scan + performance baseline (25-iter, 0% errors, p95 < 5ms).

### 17.2 Cinco tipos de tests separados
1. **Unit** (`tests/unit/`) — un solo componente, sin I/O o con stubs.
2. **Integration** (`tests/integration/`) — DB + RAG + bus + cosmos conectados.
3. **Contract** (`tests/contracts/`) — JSON Schema validation, MCP contracts, outbox events.
4. **E2E** (`tests/e2e/`) — journeys A-H, críticos de usuario.
5. **AI Evaluation** (`scripts/evaluation_gate.py`) — Foundry evaluators sobre holdout frozen.

### 17.3 Contratos de Interoperabilidad: Los 10 JSON Schemas 2020-12 (Estructura y Validación)

Todos los esquemas residen en `contracts/`, utilizan **JSON Schema Draft 2020-12** y son validados mediante `/check-contracts` y en el quality gate (`tests/contracts/test_contract_schemas.py`). Constituyen la frontera contractual inmutable entre servicios y lenguajes.

#### 1. `contracts/cloudevents/service-request-created-v1.schema.json`
- **URI:** `urn:aegisbank:contracts:cloudevents:service-request-created:v1`
- **Propósito:** Mapeo estricto del estándar **CNCF CloudEvents 1.0** para el evento de dominio `ServiceRequestCreated`.
- **Estructura del Contrato:**
```json
{
  "required": ["specversion", "id", "source", "type", "subject", "time", "datacontenttype", "dataschema", "correlationid", "data"],
  "properties": {
    "specversion": { "const": "1.0" },
    "id": { "type": "string", "minLength": 1, "maxLength": 128 },
    "source": { "const": "urn:aegisbank:mock-core-banking" },
    "type": { "const": "com.aegisbank.service-request.created.v1" },
    "subject": { "type": "string", "pattern": "^/service-requests/[A-Za-z0-9._-]+$" },
    "time": { "type": "string", "format": "date-time" },
    "datacontenttype": { "const": "application/json" },
    "dataschema": { "const": "urn:aegisbank:contracts:service-request-created:v1" },
    "correlationid": { "type": "string", "minLength": 1, "maxLength": 128 },
    "traceparent": { "type": "string", "pattern": "^[0-9a-f]{2}-[0-9a-f]{32}-[0-9a-f]{16}-[0-9a-f]{2}$" },
    "data": {
      "type": "object",
      "required": ["service_request_id", "customer_id", "category", "status"],
      "properties": {
        "service_request_id": { "type": "string", "maxLength": 64 },
        "customer_id": { "type": "string", "pattern": "^CUST-[0-9]{4}$" },
        "category": { "enum": ["CLAIM", "INQUIRY", "LIMIT_CHANGE", "DISPUTE"] },
        "status": { "enum": ["PENDING_REVIEW", "APPROVED", "REJECTED", "RESOLVED"] },
        "description": { "type": "string", "maxLength": 1000 }
      }
    }
  }
}
```

#### 2. `contracts/service-request-created.schema.json`
- **URI:** `urn:aegisbank:contracts:service-request-created:v1`
- **Propósito:** Valida el payload atómico que se persiste en la tabla `outbox_events` de SQLite antes de transformarse en CloudEvent.
- **Campos obligatorios:** `event_id`, `event_type` (`"ServiceRequestCreated"`), `aggregate_type` (`"ServiceRequest"`), `aggregate_id`, `customer_id`, `occurred_at`, `payload`.

#### 3. `contracts/core-banking-openapi.schema.json`
- **URI:** `urn:aegisbank:contracts:core-banking-openapi:v1`
- **Propósito:** Valida que el `openapi.json` generado por FastAPI contenga los 8 endpoints canónicos y las 6 entidades de datos sin desviaciones de firma.
- **Endpoints requeridos:**
  - `GET /api/v1/customers/{customer_id}`
  - `GET /api/v1/customers/{customer_id}/loans`
  - `GET /api/v1/loans/{loan_id}`
  - `GET /api/v1/loans/{loan_id}/installments/next`
  - `POST /api/v1/service-requests` (con idempotency-key header opcional)
  - `GET /api/v1/service-requests/{service_request_id}`
  - `GET /health/live`
  - `GET /health/ready`

#### 4. `contracts/cosmos-event-item.schema.json`
- **URI:** `urn:aegisbank:contracts:cosmos-event-item:v1`
- **Propósito:** Valida los ítems persistidos en Azure Cosmos DB NoSQL.
- **Campos requeridos:** `id`, `customer_id` (Partition Key obligatoria), `event_type`, `aggregate_type`, `aggregate_id`, `payload`, `created_at`.

#### 5. `contracts/mcp-tools.schema.json`
- **URI:** `urn:aegisbank:contracts:mcp-tools:v1`
- **Propósito:** Valida la exportación de herramientas del servidor MCP (`mcp/server.py`).
- **Restricciones de Anotaciones:**
  - `search_knowledge`: `readOnlyHint: true, destructiveHint: false`
  - `get_my_loans`: `readOnlyHint: true, destructiveHint: false`
  - `get_loan_details`: `readOnlyHint: true, destructiveHint: false`
  - `get_next_installment`: `readOnlyHint: true, destructiveHint: false`
  - `create_service_request`: `readOnlyHint: false, destructiveHint: false`

#### 6. `contracts/session.schema.json`
- **URI:** `urn:opencode-global:contracts:session:v1`
- **Propósito:** Valida el registro NDJSON de eventos en sesión conversacional.

#### 7–10. Esquemas de Gobernanza e Integridad (`contracts/`)
- `graph.schema.json` (`urn:opencode-global:contracts:graph:v1`): Valida nodos y aristas del Knowledge Graph `.intelligence/graph.jsonl`.
- `index.schema.json` (`urn:opencode-global:contracts:index:v1`): Valida el archivo de índices y conteos de símbolos `.intelligence/index.json`.
- `manifest.schema.json` (`urn:opencode-global:contracts:manifest:v1`): Valida las versiones de esquemas y hashes criptográficos SHA-256 en `.intelligence/manifest.json`.
- `bootstrap-manifest.schema.json` (`urn:opencode-global:contracts:bootstrap-manifest:v1`): Valida el manifiesto de inicialización del entorno OpenCode.

---

### 17.4 AI Evaluation: 7 capas
| Capa | Evalúa | Métricas | Origen |
|---|---|---|---|
| 1. Intent/ML | Clásico NLP antes de delegación generativa | Accuracy, Macro-F1, Brier, ECE, PSI Drift | v0.3 (500 samples) |
| 2. Retrieval | Chunk retrieval autorizado | Precision@K, Recall@K, MRR, nDCG@K | v0.4 (TF-IDF/SVD/RRF), v0.12 (pgvector) |
| 3. Generation | Respuesta grounded sin alucinación | Groundedness, Relevance, Citation Precision/Recall, Abstention Rate | v0.5 (active-context filtering) |
| 4. Agent | Multi-turn, tool routing, completion | Intent Resolution Rate, Tool Selection Accuracy, Tool Input Accuracy, Tool Call Success, Task Completion | v0.6 (native tool calling), v0.15 (35 traces) |
| 5. Safety | Banking risk boundaries deterministas | Ownership Isolation Rate (100%), No-Write Direct Mutation (0%), HITL State Machine, Idempotency Replay, HOTL Kill-Switch | v0.7, v0.15, v1.0 |
| 6. System E2E | Stack distribuido | 8 Journeys Pass Rate (100%), traceparent propagation (100%), Audit Log Completeness | v1.0 |
| 7. Performance | Latency, concurrency, reliability | p50/p95/p99, Error Rate, SLI/SLO Compliance | v1.0 (25-iteration baseline) |

### 17.5 Holdouts frozen (NO modificar)
- `ml/intent-classifier/data/intent_dataset.jsonl` SHA-256 pinned.
- `ai/rag/data/queries.jsonl` + `qrels.json` (v0.4 frozen).
- `data/evaluation/v015_eval_suite.jsonl` (35 multi-turn traces v0.15).
- `ai/rag/data/corpus-manifest.json` corpus SHA-256.

### 17.6 Scripts de acceptance (test riguroso, no solo pytest)
- `scripts/quality_gate.py --fast` — 13 automated checks.
- `scripts/quality_gate.py --gate-secrets-only` — solo secret scan.
- `scripts/container_acceptance.py` — Docker compose up + health checks.
- `scripts/appconfig_emulator_acceptance.py` — App Config emulator CRUD + labels + refresh.
- `scripts/functions_runtime_acceptance.py` — Functions Core Tools host start.
- `scripts/capture_pgvector_query_plans.py` — EXPLAIN ANALYZE para vector queries.
- `scripts/evaluate_retrievers_v012.py` — re-corre protocolo v0.4 contra pgvector.
- `scripts/performance_baseline.py` — 25-iter local lab baseline.
- `scripts/evaluation_gate.py` — v0.15 evaluation gate (McNemar + bootstrap CI + drift).
- `scripts/generate_sbom.py` — CycloneDX SBOM desde pip-audit.
- `scripts/session_guard.py` — atomic lock acquire/check/release.

---

## 18. Workflows de release: gates, evidencia, taxonomía de claims

### 18.1 Release gates (v1.0.0 release)
| Gate | Estado |
|---|---|
| SessionGuard | `TESTED-LOCAL` |
| Agent critical E2E (73 tests passed) | `TESTED-LOCAL` |
| v0.15 evaluation gate | `TESTED-LOCAL` |
| Performance baseline (25-iter, 0% errors, p95 < 5ms) | `LOCAL-LAB-PERFORMANCE-BASELINE` |
| Ruff/format/compileall | `PASS` |
| Bandit/pip-audit/secrets | **14/14 PASS** |
| Agent non-infra (248 passed) | `TESTED-LOCAL` |
| Infra suite (46 passed, 12 skipped) | `BLOCKED` (Docker daemon no activo) |
| Windows Functions worker | `BLOCKED` (cygrpc MAX_PATH) |

**Capability Decision:** Sin claim de capacidades blocked o cloud-pending en producción.

### 18.2 Taxonomía de claims (lo que SÍ se puede decir)
- `LAB-COVERED` — implementado, probado, verificado completamente en laboratorio local con tests automatizados reproducibles.
- `TESTED-LOCAL` — ejecutado reproduciblemente contra componentes sintéticos locales.
- `CI-CONFIGURED` / `RUNNER-PENDING` — pipeline creado sintácticamente, pendiente ejecución en runner remoto verificable.
- `LOCAL-LAB-PERFORMANCE-BASELINE` — medición local acotada (no extrapolable a producción).
- `LOCAL-COVERED` / `LOCAL-APPCONFIG-COVERED` / `LOCAL-SECRETS-COVERED` — variante específica.

### 18.3 Taxonomía de claims (lo que NO se puede decir)
- `PROD-COVERED`, `PRODUCTION-READY`, `PRODUCTION-COVERED`, `PROD-PARTIAL`.
- `CERTIFIED`, `COMPLIANT`, `MIBANCO-APPROVED`, `MICROSOFT-CERTIFIED`, `NIST-CERTIFIED`.
- `CLOUD-COVERED` (sin haber corrido contra el cloud real).
- "Statistical superiority" sin p-value < 0.05 + CI que no toca zero.
- `LAB-COVERED → certificación bancaria` (no es válido cruzar el dominio).

### 18.4 Claims intermedios (transición)
- `CLOUD-PENDING` — formalmente planeado para futuras fases cloud.
- `SAFETY-DEFERRED` — decisión arquitectural de diferir (semantic cache LLM, AKS, multi-agente).
- `PROD-UNPROVEN` — capacidad de producción, SLA, certificación, conclusiones regulatorias intencionalmente fuera de la evidencia.

### 18.5 Pipeline CI (`.github/workflows/ci.yml`)
- 3 jobs: `static-analysis` (Ruff check + format check + compileall), `test-suite` (pytest por servicio), `devsecops` (Bandit + pip-audit + CycloneDX SBOM + secret scan).
- Estado: `CI-CONFIGURED / RUNNER-PENDING` (sintaxis correcta, no ejecutado en runner real con logs verificables).

---

## 19. Workflows de operaciones: runbooks, HOTL, rollback

### 19.1 Cuatro runbooks canónicos (`docs/operations/runbooks/`)
1. **incident-response.md** — protocolo de respuesta a incidentes (severity matrix, escalation paths, comms templates).
2. **rollback.md** — procedimientos de rollback (inversion de deploy + DB migration rollback + feature flag toggle).
3. **dependency-outage.md** — cuando Cosmos / Service Bus / pgvector están caídos: degraded mode con telemetry + circuit breakers engaged.
4. **dlq-and-kill-switch.md** — cuando la DLQ crece más allá del threshold o el HOTL kill-switch debe activarse.

### 19.2 Kubernetes troubleshooting (decision tree documentado)
| Pod status | Causa probable | Solución |
|---|---|---|
| `Pending` | Scheduler no puede colocar | Reducir `resources.requests.cpu/memory` |
| `ImagePullBackOff` / `ErrImagePull` | Node no descarga la imagen | Usar imagen local; `imagePullPolicy: IfNotPresent` |
| `CrashLoopBackOff` | Process exits non-zero | Fix imports/deps/env vars; check `USER 10001` permissions |
| `Running but 0/1 Ready` | Readiness probe failure | Validar deps (SQLite/SQL Server) |
| `OOMKilled` | Memory > `resources.limits.memory` (exit 137) | Increase limit o investigar memory leaks |

### 19.3 Disaster recovery approach
- **Backup local:** `pg_dump` logical + Docker volume backups.
- **Cloud target:** continuous WAL backups, 35-day retention, geo-redundancy.
- **Outbox recovery:** pending events remain recoverable in DB; idempotent consumer replays safely.
- **State persistence:** audit logs in SQLite `audit_logs` (local); cloud target Azure SQL Immutable Ledger / Cosmos DB WORM.
- **Immutable artifacts:** container image digests pinned (no floating tags).

### 19.4 HOTL Kill-Switch flow
- **Distinction:** HITL = per-action microscopic human approval; HOTL = macroscopic supervisory control over system capability.
- Variable atómica thread-safe (`is_write_allowed`) checked BEFORE every WRITE.
- Flip via: in-memory (local lab) o Azure App Configuration Feature Flag (cloud target, dynamic, no redeploy).
- Engagement flow: Client → Agent → [HOTL: ACTIVE?] → if NO (allowed) execute tool (requires HITL); if YES → FAST-FAIL con mensaje "Escrituras suspendidas por supervisión".

### 19.5 Scripts operativos
- `scripts/session_guard.py {acquire|check|release}` — atomic single-writer lock.
- `scripts/performance_baseline.py` — mide p50/p95/p99 + error rate sobre N iteraciones.
- `scripts/generate_sbom.py` — CycloneDX SBOM inventory.
- `scripts/evaluation_gate.py` — frozen-holdout AI evaluation.

---

## 20. Seguridad: STRIDE, contenedor, datos, serverless, DevSecOps

### 20.1 STRIDE Threat Model (resumen)
| Categoría | Boundary | Amenazas | Controles | Estado |
|---|---|---|---|---|
| **S — Spoofing** | User → Agent | Prompt injection, sensitive input | Structured prompts, deterministic policy, redaction | Local covered |
| **S — Spoofing** | Agent → Tools/MCP | Unauthorized tool, malformed args | Canonical registry, schemas, ownership policy, MCP contracts | `TESTED-LOCAL` |
| **T — Tampering** | HITL → WRITE | Approval tampering, replay | Payload digest (SHA-256), expiry, actor/action binding, idempotency | `TESTED-LOCAL` |
| **R — Repudiation** | Audit / OTel records | Pérdida de no-repudio | WORM immutable audit, OTel spans | Local covered |
| **I — Information Disclosure** | App → Config/Secrets | Secret disclosure, config drift | Separated providers, fail-fast validation, no secret logging | Local; Key Vault identity `CLOUD-PENDING` |
| **I — Info Disclosure** | Data Stores | Cross-customer access | Ownership filters + authorization tests | `TESTED-LOCAL` |
| **D — DoS** | Runtime | Outage, timeout, resource exhaustion | Bounded retries, timeout, circuit breaker | Local; capacity `PROD-UNPROVEN` |
| **E — EoP** | HOTL → WRITE | Unsafe operator state | Kill-switch antes de cada WRITE | `TESTED-LOCAL` |
| **Mixed** | App → Messaging | Duplicate, loss, poison event | Transactional outbox, idempotent consumer, DLQ | `TESTED-LOCAL` |
| **Mixed** | RAG → Answer | Poisoned/stale evidence | Trust labeling, citation validation, abstention | `TESTED-LOCAL` |

### 20.2 Amenazas específicas mitigadas
- **Indirect Prompt Injection:** defense-in-depth. LLM tiene read-only tools por default. Cada acción state-changing requiere `ApprovalRequest` validado contra SHA-256 payload digest bound to authenticated customer ID + out-of-band human sign-off. "Attack surface constrained by code, not prompt compliance."
- **Estado de evidencia:** el runner local Phase-2 registra ASR, utilidad, bypasses y claims no soportados. El resultado `0%` se limita a la suite fija ejecutada; no es una afirmación universal. El contenido RAG y las salidas de tools se etiquetan como datos no confiables, pero el etiquetado por sí solo no garantiza obediencia del modelo; la autorización efectiva depende de la defensa en profundidad determinista.
- **IDOR / cross-customer data leakage:** deterministic ownership policy via `AgentContext.session_customer_id`; LLM **no puede** suplir customer_id. Testeado con 6+ combinaciones parametrizadas en `tests/unit/tools/test_ownership_enforcement.py`. Cross-customer access siempre denied.
- **Replay attacks:** `IdempotencyGuard` keyed on `event-grid:{event_id}` con SHA-256 payload hash. Reaparición con mismo content → cached response; con different content → `IdempotencyConflictError`.
- **PII sanitization:** `RedactionFilter` strips API keys, passwords, tokens, PII from all telemetry. Audit/telemetry contain solo synthetic IDs, latencies, tool names, approval status.
- **Pseudo-Tool-Call vulnerability:** cuando LLM output `get_loan_details(LOAN-0001)` como plain text en vez de structured tool_call, se registra como `PSEUDO_TOOL_CALL`/`ROUTING_FAILURE` y NO se ejecuta. Mitigación: canonical entity extraction (regex `\bLOAN-[0-9]{4}\b`) + deterministic short-circuit cuando entity present.
- **Dual-write hazard:** prevenido por Transactional Outbox — entity change + domain event escrito en mismo atomic SQL transaction.

### 20.3 Container security baseline
- **Non-root:** `USER 10001:10001` en Dockerfile de mock-core-banking.
- **Minimal base:** `python:3.14-slim`.
- **Toolchain isolation:** solo runtime wheel instalado; no tests/caches copiados.
- **Secret exclusion:** `.dockerignore` exhaustivo (excluye `.git`, `.venv`, `.env*`, `*.db`).
- **Network isolation:** explícito `aegisbank-net` bridge con port mapping estricto.
- **Healthcheck automation:** `HEALTHCHECK` directive + Compose readiness probes.
- **Minimal filesystem perms:** read-only root FS con solo `/app/data` writable.
- **PROHIBITED:** `--privileged`, `CAP_SYS_ADMIN`, `/var/run/docker.sock` mounting.
- **Defense-in-depth layers:** Bandit SAST → pip-audit SCA → Non-root container → Pydantic schemas → HITL → WORM audit.

### 20.4 Data layer security
- **SQL injection prevention:** 100% parameterized queries via `psycopg` (`%(param)s::type`); 0 string concatenation.
- **Least privilege:** non-root `aegisuser` restricted to `aegisbank_rag` db + `rag_chunks` table.
- **Secrets:** dynamic injection via `${POSTGRES_PASSWORD}` env var; 0 credentials in Git.
- **Encryption:** local bridge network; cloud target TLS 1.2/1.3 + TDE with Customer-Managed Keys.
- **Vector dimension validation:** `vector(32)` rechaza mismatched dimensions at engine level.
- **Cosmos DB isolation:** partition key `/customer_id`; idempotent consumer con `id:etag` dedup.
- **Redis security:** NO balances / quota / PII cached — only public knowledge + corpus vectors; Lua `RELEASE_LOCK_LUA` para atomic single-flight stampede protection.

### 20.5 Serverless security (local lab v0.13)
- **Secrets isolation:** `local.settings.json` gitignored; only `.example` template versioned.
- **Strictly synthetic data:** test events usan solo `SR-2026-0001`, `CUST-0001`; real financial data prohibited.
- **Schema validation:** cada CloudEvent validado contra JSON Schema 2020-12 (`service-request-created-v1.schema.json`) con `additionalProperties: false` — previene payload poisoning.
- **Least privilege handler:** `service_request_event_handler` es read-only consumer; `NEW_BANKING_WRITES = 0`.
- **Cloud controls (CLOUD-PENDING):** System-Assigned Managed Identity, Azure Key Vault con `@Microsoft.KeyVault(...)`, VNet/Private Endpoints, Event Grid `ValidationCode`/`ValidationResponse` + HMAC tokens, RBAC (Event Grid Data Receiver, Key Vault Secrets User).

### 20.6 DevSecOps gates (`.github/workflows/ci.yml::devsecops`)
| Gate | Tool | Failure meaning |
|---|---|---|
| Lint/format | Ruff | Code quality / import defect |
| Tests/contracts/E2E | pytest | Behavior/compatibility defect |
| **SAST** | **Bandit** (`-ll -r src/`) | AST pattern review; fail on medium/high |
| **SCA** | **pip-audit** | Known dependency advisory; blocked ≠ PASS |
| **SBOM** | **pip-audit CycloneDX JSON** | Dependency inventory (artifact) |
| Secrets | Tracked-file scanner | Credential exposure; must fail on match |

### 20.7 SBOM
- Generado via `pip-audit -f cyclonedx-json -o docs/security/sbom.json`.
- Es un inventory, no un vulnerability scan.
- Soporta Mibanco secure delivery y AI-103/AI-200 safeguards.
- `LAB-COVERED` ≠ banking certification.

### 20.8 Policy explícita de claims prohibidos
- Legal, regulatory, NIST, Microsoft, o banking certification/compliance.
- Production SLO/SLA from local lab measurements.
- Statistical superiority sin proper p-values/CIs.
- "LAB-COVERED" → banking certification.
- Cloud deployment from local tests sin cloud evidence.

---

## 21. Alineación con certificaciones Microsoft de IA

### 21.1 Mapa de certificaciones
| Cert | Status en el proyecto | Artefactos que cubren el syllabus |
|---|---|---|
| **AI-900** (Azure AI Fundamentals) | **Subsyllabus cubierto** por construcción. No se rinde el examen dentro del repo. | Foundry Local + phi-4-mini (intro to generative AI), pgvector embeddings, RAG (knowledge mining), Core Banking + Cosmos (data + NoSQL), Functions (compute), MLOps basics |
| **AI-102** (Azure AI Engineer Associate) | **Strong alignment**. Diseñado deliberadamente para cubrir el syllabus. | Agent SDK via OpenAI/MCP, Foundry Local embeddings, RAG with citations, prompt engineering, evaluators, MLflow + drift, App Configuration + Key Vault boundary, Functions + Event Grid |
| **AI-200** (Azure data + cloud dev) | **Strong alignment**. Containers + Service Bus + Azure data + identity. | Docker + Compose, Service Bus emulator + adapter, K8s manifests, ACA vs AKS decision ADR-027, pgvector + Cosmos + Redis, App Config + Key Vault, DefaultAzureCredential |

### 21.2 Mapeo skill-rubric → milestone (extracto del gap analysis)
| Skill | Demostrado en repo | Evidencia |
|---|---|---|
| Prompting strategy & quality | v0.5 | `ai/rag/prompts/rag-answer-v001.json` (versioned) |
| LLM evaluation harness | v0.5, v0.6.1, v0.15 | `reports/v015_evaluation_evidence.json`, frozen holdouts |
| RAG design (chunking, retrieval, grounding, provenance) | v0.4 | `docs/experiments/v0.4-rag-retrieval-foundation.md`, corpus manifest |
| Guard rails (HITL, ownership, no-write) | v0.6, v0.7 | `evaluate_no_write_compliance`, `evaluate_ownership_enforcement`, `IdempotencyGuard`, `hitl.py` |
| Tool integration via MCP | v0.7 | `functions/aegisbank-events/` (MCP v2 server, stdio, SDK 2.1.1) |
| Observability (correlation_id, trace_id, audit) | v0.5, v0.13 | `correlation.py`, `audit_events` table, OTel spans |
| Idempotency | v0.5, v0.7, v0.13 | `IdempotencyRepository`, `IdempotencyGuard`, outbox+dedupe |
| Reliability: retries, circuit breaker | v0.8 | `reliability/retry.py`, `reliability/circuit_breaker.py` |
| Docker / local Azure messaging | v0.11 | `deploy/local/docker-compose.yml` + `scripts/container_acceptance.py` |
| Kubernetes | v0.11.1 | `deploy/kubernetes/*.yaml` |
| Azure data services (Cosmos, pgvector, Redis) | v0.12.x | `scripts/capture_pgvector_query_plans.py`, `evaluate_retrievers_v012.py` |
| Serverless Functions + Event Grid | v0.13.0, v0.13.1 | `functions/aegisbank-events/` + `scripts/functions_runtime_acceptance.py` |
| App Config + identity/secrets boundary | v0.14 | `scripts/appconfig_emulator_acceptance.py` |
| Quality, CI/CD, secret scan | v0.10 | `scripts/quality_gate.py`, `scripts/generate_sbom.py` |
| Classical ML baseline | v0.3 | `docs/experiments/v0.3-intent-classification-baseline.md` |

### 21.3 Areas de AI-103/AI-102 fuera de scope (gaps declarados)
- **Computer Vision** (image classification, OCR, object detection) — no implementado.
- **Text Analytics** (NER, sentiment, key phrase extraction) — no implementado.
- **Document Intelligence / Form Recognizer** — no implementado.
- **Custom Vision / Custom Speech** — no implementado.
- **Azure AI Search** (reemplazado por pgvector + RediSearch localmente).

### 21.4 Mapa runbook + ADR → dominio cloud
- Incident Response runbook ↔ Azure incident response + status page.
- Rollback runbook ↔ ACA revisions rollback + DB migration down.
- Dependency Outage runbook ↔ Service Bus failover + Cosmos multi-region write.
- DLQ + Kill-Switch runbook ↔ Service Bus DLQ + App Configuration feature flag dynamic toggle.

---

## 22. Maestría de IA: 7 capas de evaluación, MLOps, drift

### 22.1 La taxonomía de evaluación y formulación matemática formal
El proyecto implementa las **7 capas de evaluación** del estándar Microsoft AI Foundry + MLflow, formalizando cada métrica con rigor matemático reproducible:

```
+-----------------------------------------------------------------------------+
|               TAXONOMÍA DE EVALUACIÓN DE 7 CAPAS (AEGISBANK)                |
+-----------------------------------------------------------------------------+
| 1. Intent / ML      : Accuracy, Macro-F1, Brier Score, ECE, PSI Data Drift  |
| 2. Retrieval        : Precision@K, Recall@K, MRR, nDCG@K, RRF Fusion       |
| 3. Generation       : Groundedness, Citation Precision, Abstention Rate     |
| 4. Agent Tooling    : Tool Selection Accuracy, Routing Adherence, Arguments |
| 5. Safety Invariants: Ownership Isolation (IDOR), No-Write, HITL Hash Check |
| 6. System E2E       : 8 Critical Journeys Pass Rate, Outbox Dual-Write Zero  |
| 7. Performance/Ops  : Latency (p50/p95/p99), Throughput, Error Rate, SLI/SLO |
+-----------------------------------------------------------------------------+
```

#### Formulación Matemática por Capa:

1. **Capa 1: Intención y Clasificación Clásica (ML Baseline)**
   - **Accuracy**:
     $$\text{Accuracy} = \frac{\text{TP} + \text{TN}}{\text{TP} + \text{TN} + \text{FP} + \text{FN}}$$
   - **Macro-F1** (promedio no ponderado para penalizar debilidad en clases minoritarias):
     $$\text{Macro-F1} = \frac{1}{|C|} \sum_{c \in C} \frac{2 \cdot P_c \cdot R_c}{P_c + R_c}$$
   - **Brier Score** (calibración cuadrática de la distribución de probabilidad multiclase):
     $$\text{Brier} = \frac{1}{N} \sum_{i=1}^N \sum_{k=1}^K (f_{ik} - o_{ik})^2 \quad (v0.3 = 0.052, v0.15 = 0.0152)$$
   - **Expected Calibration Error (ECE)** sobre $M=5$ bins de probabilidad:
     $$\text{ECE} = \sum_{m=1}^M \frac{|B_m|}{N} \left| \text{acc}(B_m) - \text{conf}(B_m) \right| \quad (v0.3 = 0.041, v0.15 = 0.1137)$$

2. **Capa 2: Recuperación de Información (Ranked Retrieval RAG)**
   - **Precision@K**:
     $$\text{Precision}@K = \frac{|\text{Retrieved}_K \cap \text{Relevant}|}{K}$$
   - **Recall@K**:
     $$\text{Recall}@K = \frac{|\text{Retrieved}_K \cap \text{Relevant}|}{|\text{Relevant}|} \quad (\text{Recall}@5 = 0.8333)$$
   - **Mean Reciprocal Rank (MRR)**:
     $$\text{MRR} = \frac{1}{|Q|} \sum_{i=1}^{|Q|} \frac{1}{\text{rank}_i} \quad (\text{MRR} = 0.7778)$$
   - **Normalized Discounted Cumulative Gain (nDCG@K)**:
     $$\text{DCG}@K = \sum_{i=1}^K \frac{2^{rel_i} - 1}{\log_2(i + 1)}, \quad \text{nDCG}@K = \frac{\text{DCG}@K}{\text{IDCG}@K} \quad (\text{nDCG}@5 = 0.8107)$$
   - **Reciprocal Rank Fusion (RRF)** con parámetro de suavizado congelado $k = 60$:
     $$\text{RRF Score}(d) = \sum_{m \in M} \frac{1}{k + r_m(d)}$$

3. **Capa 3: Generación Grounded y Citas**
   - **Groundedness**: Proporción de afirmaciones verificables en la respuesta que están explícitamente soportadas por los chunks activos inyectados ($= 1.0000$).
   - **Citation Precision**: Proporción de citas emitidas `[chunk_id]` que corresponden a documentos autorizados vigentes ($= 1.0000$).
   - **Abstention Rate**: Proporción de consultas ambiguas o fuera de dominio que disparan una negativa explícita antes de la llamada generativa ($= 1.0000$).

4. **Capa 4 & 5: Agent Tooling y Safety Invariants**
   - **Tool Selection Accuracy**: Exactitud en la elección del conjunto de herramientas bancarias ($34/35 = 0.9714$).
   - **Ownership Isolation Rate**:
     $$\text{Isolation} = 1.0 - \frac{\text{IDOR Violations}}{\text{Total Queries}} = 1.0000 \quad (\text{Invariante } I_4)$$
   - **No-Write Direct Mutation**:
     $$\text{No-Write} = \mathbb{I}(\text{DirectWritesWithoutHITL} = 0) = 1.0000 \quad (\text{Invariante } I_2)$$

5. **Capa 6: Integración del Sistema E2E**
   - **Critical Journeys Pass Rate**: $8/8 \text{ workflows (100\%) passing}$ en `tests/e2e/test_critical_journeys.py`.
   - **Dual-Write Hazard Rate**: $0.0\%$ (verificado mediante el patrón Transactional Outbox, Invariante $I_5$).

6. **Capa 7: Rendimiento Operativo y SLI/SLO**
   - Percentiles de latencia en laboratorio local ($N=25$ ejecuciones secuenciales):
     $$\text{p50} = 14.2\text{ms}, \quad \text{p95} = 19.8\text{ms}, \quad \text{p99} = 24.1\text{ms}, \quad \text{Error Rate} = 0.0\%$$

---

### 22.2 MLOps: Arquitectura de Tracking y Detección de Drift
Implementado en `ai/agent/src/aegisbank_agent/mlops/`:
- **MLflowTracker**:
  - Backend SQLite local ubicado en `reports/mlruns/mlflow.db`.
  - Experimento formal: `aegisbank-v015-agent-evaluation`.
  - Registra por cada corrida: `run_id`, `git_commit`, parámetros (`dataset_sha256`, `evaluator_version`, `model_id`), las 9 dimensiones de Microsoft Foundry, métricas de invariantes de seguridad y artefactos JSON de salida.
  - Dependencias mínimas: `mlflow-skinny` y `alembic` (sin interfaz web pesada).
- **DriftDetector**:
  - **Covariate Shift (Data Drift)**: Monitoreo de cambios en la distribución de entrada mediante Population Stability Index (PSI) y distancia de Wasserstein:
    $$\text{PSI} = \sum_{i=1}^B (A_i - E_i) \cdot \ln\left(\frac{A_i}{E_i}\right)$$
    - Criterio estándar: $\text{PSI} < 0.1 \implies \text{STABLE}$; $0.1 \le \text{PSI} \le 0.2 \implies \text{MODERATE}$; $\text{PSI} > 0.2 \implies \text{SIGNIFICANT\_DRIFT}$.
  - **Concept Shift (Prediction Drift)**: Divergencia de Jensen-Shannon (JSD) sobre probabilidades de salida:
    $$\text{JSD}(P \parallel Q) = \frac{1}{2} D_{\text{KL}}(P \parallel M) + \frac{1}{2} D_{\text{KL}}(Q \parallel M), \quad \text{donde } M = \frac{1}{2}(P + Q)$$
  - **Resultados v0.15:** Data Drift `STABLE` ($\text{PSI} = 0.0000$), Prediction Drift `STABLE` ($\text{JSD} = 0.0000$), Model Performance Drift `STABLE`.

---

### 22.3 Evaluación Comparativa AB y Rigor Estadístico
Implementado en `ai/agent/src/aegisbank_agent/evaluation/ab_testing.py`:

#### Prueba de Hipótesis Pareada de McNemar
Para comparar la versión Baseline ($v0.14$) frente a la Candidata ($v0.15$) sobre las $N=35$ trazas multi-turno congeladas, se aplica el test no paramétrico de McNemar con la corrección de continuidad de Edwards:
$$\chi^2 = \frac{(|b - c| - 1)^2}{b + c}$$
donde:
- $a = 31$: Aciertos en ambos modelos.
- $b = 3$: Fallos en baseline corregidos en el candidato (e.g. pseudo-tool call routing).
- $c = 0$: Aciertos en baseline que fallaron en el candidato (cero regresiones).
- $d = 1$: Fallos en ambos modelos.

$$\chi^2 = \frac{(|3 - 0| - 1)^2}{3 + 0} = \frac{4}{3} \approx 1.3333 \implies p\text{-value} = 0.248213$$

Dado que $p = 0.248213 > 0.05$, la hipótesis nula no puede rechazarse con significancia estadística formal al 95%. Se declara con honestidad técnica:
`STATISTICAL_SUPERIORITY_NOT_ESTABLISHED`.

#### Tamaño del Efecto y Bootstrap Confidence Interval
- **Tamaño del efecto de Cohen's $h$ para proporciones**:
  $$h = 2 \cdot \arcsin(\sqrt{p_1}) - 2 \cdot \arcsin(\sqrt{p_2}) = 2 \cdot \arcsin(\sqrt{0.9714}) - 2 \cdot \arcsin(\sqrt{0.8857}) = 0.3478$$
  (Efecto práctico pequeño a mediano en la mejora operativa).
- **Intervalo de Confianza Bootstrap al 95%** ($B=1000$ remuestreos con reemplazo):
  $$\Delta \text{Accuracy} = +0.0857 \quad (\text{95\% CI: } [0.0000, 0.1714])$$
  El intervalo toca el 0.0000 en el límite inferior debido al tamaño de muestra acotado ($N=35$).

#### Veredicto de Promoción
La versión candidata fue promovida a producción de laboratorio bajo la regla:
`PROMOTED [PASS] (Safety + Engineering Threshold Policy)`:
1. Superó el umbral ingenieril determinista ($\ge 95\%$ en task completion y tool routing).
2. Presentó **cero regresiones** en invariantes de seguridad ($I_1$ a $I_{15}$).
3. Resolvió los bugs de pseudo-tool-calling identificados en pruebas anteriores.

---

### 22.4 Tabla Exhaustiva de Métricas de Promoción v0.15 / v1.0.1

| Dimensión Evaluada | Baseline (v0.14) | Candidato (v0.15) | Delta Observado | Método / Test | p-value / Criterio | Estado |
|---|---|---|---|---|---|---|
| **Task Completion Rate** | 0.8857 (31/35) | 0.9714 (34/35) | +0.0857 (+8.6 pp) | McNemar (Edwards) | $p = 0.248213$ | `PASS (Threshold)` |
| **Tool Selection Accuracy** | 0.9143 (32/35) | 1.0000 (35/35) | +0.0857 (+8.6 pp) | McNemar (Edwards) | $p = 0.248213$ | `PASS (Threshold)` |
| **Tool Input Accuracy** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante JSON Schema | Contrato 2020-12 | `PASS (Invariant)` |
| **Tool Call Success Rate** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante de Ejecución | Cero fallos no controlados | `PASS (Invariant)` |
| **Relevance (No Tool Leaks)** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante de Redacción | Sin fuga de datos internos | `PASS (Invariant)` |
| **Groundedness Score** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante de Citas | Cero alucinaciones bancarias | `PASS (Invariant)` |
| **Abstention on Gaps** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante UC-005 | Cero falsas respuestas | `PASS (Invariant)` |
| **Ownership Isolation** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante IDOR ($I_4$) | Cero fugas cross-customer | `PASS (Hard Gate)` |
| **No-Write Direct Mutation** | 1.0000 (35/35) | 1.0000 (35/35) | 0.0000 | Invariante HITL ($I_2$) | Cero escrituras autónomas | `PASS (Hard Gate)` |

---

### 22.5 Reconciliación Histórica de Procedencia: `v012_retrieval_comparison.json`

Un hallazgo crítico de auditoría documental es la aparente discrepancia de nombres en el archivo [v012_retrieval_comparison.json](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/docs/evaluation/v012_retrieval_comparison.json):

- **Nombre físico del archivo:** `v012_retrieval_comparison.json`
- **Metadatos internos del JSON:**
  ```json
  {
    "experiment_name": "aegisbank-synthetic-spanish-rag-retrieval",
    "experiment_version": "0.4.0",
    "primary_metric": "ndcg_at_5",
    "queries_evaluated": 18,
    "qrels_evaluated": 18,
    "top_k": 5
  }
  ```

#### Causa Raíz y Razón de Ingeniería:
1. **El protocolo y dataset (`0.4.0`):** El banco de 18 consultas sintéticas en español bancario y su matriz de relevancia juicio-humano (`qrels.json`) fueron fijados, validados y congelados durante el milestone `v0.4.0`.
2. **El hito de ejecución (`v0.12`):** En el milestone `v0.12`, se introdujo la infraestructura de base de datos vectorial PostgreSQL + `pgvector`. Para demostrar que `pgvector` con indexación HNSW no degradaba la calidad de recuperación frente a los baselines previos, el script `scripts/evaluate_retrievers_v012.py` ejecutó el **protocolo congelado v0.4.0** contra el contenedor PostgreSQL.
3. **Resolución de Gobernanza:** En cumplimiento de la regla de **inmutabilidad de benchmarks (WORM)**, el archivo JSON original no fue modificado retroactivamente para cambiar su metadato de versión. Se documenta formalmente aquí: el archivo representa la **ejecución en v0.12 del protocolo benchmark v0.4.0**, catalogado como `HISTORICAL_BENCHMARK_PRESERVED`.

---

### 22.6 Principio de Desacoplamiento: Métricas ≠ Milestones
- **Una métrica** cuantifica una dimensión de rendimiento técnico observable (e.g. `nDCG@5`, `Macro-F1`).
- **Un milestone** designa la procedencia temporal, el commit y el snapshot del repositorio en el que se corrió el experimento.
- Confundir métricas con milestones lleva a re-escribir evidencias históricas. En AegisBank, la procedencia se rastrea mediante hashes SHA-256 inmutables de los datasets.

---

### 22.7 Reproducibilidad Científica e Inmutabilidad
- **Semilla fija universal:** `RANDOM_STATE = 42` definido en `aegisbank_rag.constants` para todos los algoritmos de embeddings, descomposición SVD y splits de validación.
- **Integridad de Corpus:** `data/corpus-manifest.json` contiene los hashes SHA-256 de cada archivo normativo.
- **Integridad de Datasets:** `ml/intent-classifier/data/dataset-manifest.json` fija el hash `db250b59...` para el clasificador de intención.
- **Políticas de congelamiento:** Flags obligatorios `evaluated_once_after_configuration_freeze = True` y `post_holdout_tuning = False` en `run_frozen_experiment`.
- **Estratificación agrupada:** `StratifiedGroupKFold(n_splits=5)` por `template_group_id` para eliminar cualquier fuga sintáctica entre entrenamiento y evaluación.

---

## 23. Fortalezas del proyecto

Las siguientes 25 fortalezas son observables, no aspiracionales. Cada una referencia al menos un artefacto verificable.

### 23.1 Disciplina arquitectónica
1. **24 componentes canónicos con regla DISCOVER BEFORE CREATE** (`docs/architecture/CANONICAL-COMPONENTS.md`) — evita duplicación, garantiza single-writer principle.
2. **30 ADRs append-only** (`docs/architecture/adr/`) — decisiones documentadas, ninguna re-escrita.
3. **Monolito modular deliberado** (`ADR-001`) — sin microservices prematuros, sin AKS, sin multi-agente en v1.0.
4. **Single-agent orchestrator** (`ADR-012`) — un Aegis, max 3 rondas, bounded loop.
5. **Provider-neutral LLM boundary** (`ADR-010`) — Foundry Local → Azure OpenAI sin cambiar consumidores.

### 23.2 Autorización determinista (tres valles)
6. **HOTL kill-switch** antes de cada WRITE.
7. **HITL state machine** con SHA-256 payload digest binding + actor/action binding.
8. **Tool allowlist determinista** basado en `account_tool_allowlist(query)` — LLM nunca elige libremente acceder a datos bancarios.
9. **Customer-id ownership filter** en cada tool banking (fail-closed).
10. **WRITE_TOOLS constant** — única write tool es `create_service_request`, sin excepciones silenciosas.

### 23.3 Seguridad
11. **STRIDE threat model explícito** (`docs/security/V1.0-THREAT-MODEL.md`) con mitigaciones por boundary.
12. **Pseudo-tool-call vulnerability mitigada** (regex + deterministic short-circuit) — bug real encontrado y resuelto.
13. **Indirect prompt injection mitigation** defense-in-depth (código, no prompt compliance).
14. **Container hardening** (non-root UID 10001, read-only FS, cap_drop ALL, no-new-privileges, digest-pinned images).
15. **DevSecOps gates** (Bandit SAST + pip-audit SCA + CycloneDX SBOM + secret scan).

### 23.4 Reliability
16. **Transactional outbox** (no dual-write hazard) — entity change + domain event en mismo SQL tx.
17. **IdempotencyGuard** en cada WRITE (replay = 1 solo registro).
18. **Bounded retry + circuit breaker FSM** (CLOSED/OPEN/HALF_OPEN).
19. **DLQ + idempotent consumer** — mensajes venenosos no bloquean.

### 23.5 Testing
20. **Pirámide de tests completa** (138 unit + 51 integration + 21 contract + 11 E2E = 221+ en mock-core-banking/agent).
21. **Contract-first** — 10 JSON Schemas 2020-12 (`contracts/*.schema.json`).
22. **Frozen holdouts** con SHA-256 pinned — no se modifican, se re-ejecutan.
23. **AI evaluation de 7 capas** con Foundry evaluators + MLflow + drift detection.

### 23.6 Honestidad y gobernanza
24. **Taxonomía de claims explícita** (`LAB-COVERED`, `TESTED-LOCAL`, `CLOUD-PENDING`, `PROD-UNPROVEN`) — prohíbe claims inflados.
25. **28 prompts históricos auditables** (`docs/chatgpt-prompts/000-026`) — construcción reproducible.

### 23.7 Otras fortalezas técnicas
- **Reproducibilidad científica total** (seed=42, SHA-256, frozen prompts).
- **Deterministic routing** (`requires_account_data`, `is_greeting`, `extract_loan_id`) — LLM solo donde el LLM aporta.
- **W3C `traceparent` propagation** end-to-end.
- **WORM audit log** separado de operational logs.
- **Cache-aside con strict data classification** — nunca cachea datos bancarios privados.
- **Single-flight stampede protection** en Redis.
- **Cross-session integrity** via SessionGuard (atomic lock).

---

## 24. Debilidades, riesgos abiertos y huecos

### 24.1 Riesgos BLOCKED (no funcionan ahora)
1. **Windows Functions worker** — `cygrpc.cp314-win_amd64.pyd` + Win32 MAX_PATH (Error 206). Resolución: Linux container `mcr.microsoft.com/azure-functions/python:4-python3.14`. Si el developer usa Windows nativo, **no funciona**.
2. **Docker daemon no activo en último release local** — 12 infra tests skipped. Re-correr `scripts/container_acceptance.py` requiere Docker desktop en ejecución.
3. **Context7 MCP API key es placeholder** — `opencode.json` lo trae como env var no rotada. Hasta que el usuario la rote con su secret store, Context7 responde "Request timed out".

### 24.2 Riesgos CLOUD-PENDING (no implementados)
4. **Azure Key Vault real** — `CLOUD-KEYVAULT-PENDING`. Solo implementación local sintética + adapter.
5. **Microsoft Entra ID / Managed Identity** — `CLOUD-MANAGED-IDENTITY-PENDING`. Solo `DefaultAzureCredential` documentado con fallback.
6. **Azure Container Apps deployment** — manifests K8s listos, no deployado contra ACA real.
7. **Azure Service Bus real** — emulator funciona, adapter listo, no production-tested.
9. **Azure Cosmos DB real** — emulator, partition design documentado, no production-tested.
10. **Azure Database for PostgreSQL Flexible Server + Entra ID + Private Endpoints** — todo el stack de seguridad cloud pendiente.
11. **Azure App Insights / OTel exporter** — vendor-neutral tracer preparado, exportador no cableado.

### 24.3 Riesgos PROD-UNPROVEN (declarado intencionalmente)
12. **Multi-region HA** — no implementado.
13. **Alta TPS / capacidad de carga** — solo 25-iteration baseline local (p95 < 5ms).
14. **SLA / SLO productivo** — no hay.
15. **Certificaciones** — ISO 27001, NIST, PCI-DSS, SBS, EBA, OCC SR 11-7 todas **NO**.

### 24.4 Gaps de scope explícitos
16. **Multi-agent orchestration** — diferido a v1.2 (intencional).
17. **AKS** — diferido a v1.1 (intencional, decisión ADR-027).
18. **Azure AI Search** — no introducido (pgvector + RediSearch lo cubren localmente).
19. **Semantic cache LLM** — `SAFETY-DEFERRED` (riesgo banking).
20. **AI-103 areas fuera de scope** — Computer Vision, Text Analytics, Document Intelligence, Custom Vision/Speech.

### 24.5 Limitaciones de la evaluación
21. **Statistical superiority NOT established** en v0.15 (McNemar p=0.248213). Promoción bajo política operacional, no bajo rigor estadístico.
22. **Intent classifier "near-perfect"** (holdout macro-F1=1.0) pero el README advierte: "likely reflects the balanced, template-generated language. It is not evidence of performance on real users."
23. **CI runner no verificado** — `.github/workflows/ci.yml` está `CI-CONFIGURED / RUNNER-PENDING` (sintaxis OK, no ejecutado en runner real con logs).
24. **Sin live cloud deployment evidence** — todos los claims `TESTED-LOCAL` o `LOCAL-LAB-PERFORMANCE-BASELINE`.

### 24.6 Gaps de negocio
25. **Sin brief / SIPOC / business case real** — el repo usa caso educativo sintético. Para Mibanco se necesitaría proceso real con valor medible.
26. **Sin employer collaboration** — single-developer, no co-design con producto.

---

## 25. Errores conocidos y post-mortems

### 25.1 Post-mortem #1: Windows NT Dynamic Linker Failure on `cygrpc`
- **Síntoma:** `ImportError: DLL load failed while importing cygrpc: El nombre del archivo o la extensión es demasiado largo`.
- **Root cause:** Win32 Error 206 (0xCE). Python 3.14 worker `LoadLibraryExW` de `cygrpc.cp314-win_amd64.pyd` + dependency paths exceeded 260-char MAX_PATH.
- **Resolución:** Adopt OCI container isolation (`mcr.microsoft.com/azure-functions/python:4-python3.14`); Linux `dlopen` no está sujeto a Win32 path limits.
- **Status:** Windows clasificado `BLOCKED`, Linux verificado `PASS`.

### 25.2 Post-mortem #2: Metamorphic Routing Loss & "Pseudo-Tool-Call" Vulnerability
- **Síntoma A:** `"Dame detalle de mi prestamo LOAN-0001"` → correctamente ejecutó `get_loan_details(loan_id="LOAN-0001")`.
- **Síntoma B:** `"Dame detalle de mi LOAN-0001"` → 0 tools ejecutados; LLM output raw text `get_loan_details(LOAN-0001)`.
- **Root cause:** naive lexical search (`if "prestamo" in text`); omitir noun rompió `requires_account_data`; `tool_choice="auto"` sin mandatory allowlist permitió hallucinated function signature como text.
- **Resolución:**
  1. Canonical entity extraction via regex `\bLOAN-[0-9]{4}\b`.
  2. Deterministic short-circuit cuando explicit entity present.
  3. Metamorphic testing suite con 7+ parametrized linguistic variations.
- **Status:** Resuelto + regresión bloqueada por test suite.

### 25.3 Post-mortem #3: App Configuration Key Vault Reference URI Parsing
- **Síntoma:** invalid URI errors en `{"uri": "https://aegisbank-kv.vault.azure.net/secrets/db-password"}` con optional version suffixes.
- **Root cause:** reference resolver asumía standard HTTP URL formatting; fallaba en `/secrets/{name}/{version}` paths.
- **Resolución:** RFC 3986-compliant URI parsing, strict schema validation (`https://`), domain verification (`*.vault.azure.net`), regex validation of secret identifiers (`^[a-zA-Z0-9-]+$`).
- **Status:** Resuelto.

### 25.4 Post-mortem #4: Inferencia Local Kestrel Socket Abort por Timeout Prematuro de Cliente HTTP (10s vs 10,153ms)
- **Síntoma:** En turnos conversacionales con reasoning pesado en Foundry Local (`phi-4-mini`), el cliente emitía:
  `{"event_name": "llm_call_failed", "error_code": "LLM_COMMUNICATION_ERROR", "details": {"error": "Connection error."}}`
- **Forensic RCA:** A las 05:19:32 UTC, la llamada de inferencia tardó 10,153.93 ms en el host local. El cliente `OpenAI` tenía configurado un timeout por defecto de 10.0 segundos (`AEGISBANK_FOUNDRY_TIMEOUT_SECONDS=10`). Al cumplirse los 10,000 ms exactos, el cliente cerró el socket TCP prematuramente mientras el servidor web ASP.NET Kestrel de Foundry Local aún generaba tokens. Kestrel abortó la conexión con `System.OperationCanceledException: The operation was canceled` en el pipeline de ASP.NET Core (`Microsoft.AspNetCore.Server.Kestrel.Core.Internal.Http.HttpProtocol.ProcessRequests`).
- **Resolución:** Elevación del timeout por defecto a `30.0` segundos (`AEGISBANK_FOUNDRY_TIMEOUT_SECONDS=30.0`) y configuración de política de degradación que informa al usuario que puede consultar por identificador estructurado (`LOAN-XXXX`) si el LLM excede el umbral.
- **Status:** Resuelto y validado en v1.0.6.

### 25.5 Post-mortem #5: Infiltración de Placeholders y Alucinación de Espera en Respuestas de Cuenta (Zero Account Fakery)
- **Síntoma A:** Al consultar saldos o fechas de préstamos sin pasar un `LOAN-ID` explícito, el LLM generaba respuestas sintéticas filtrando nombres de variables como texto final: `[Nombre del Préstamo]`, `[Fecha de Pago 1]`, `[Monto]`.
- **Síntoma B:** El LLM insertaba textos de simulación de espera: `[Breve pausa mientras el asistente realiza la consulta]`, pretendiendo haber interactuado con el backend cuando en realidad `tools_executed == 0`.
- **Root cause:** Ausencia de un guardrail determinista post-generación. Los modelos pequeños instructivos (`phi-4-mini`) en ausencia de datos en el contexto intentan completar plantillas aprendidas en pre-entrenamiento.
- **Resolución:** Formalización del invariante canónico **`NO ACCOUNT FACTS WITHOUT AUTHORIZED TOOL EVIDENCE`** (`AccountDataClaim => SuccessfulAuthorizedToolCall`). Implementación de 4 interceptores post-generación en `AgentOrchestrator`:
  1. `PLACEHOLDER_LEAK` regex interceptor.
  2. `PROCESS_HALLUCINATION` regex interceptor.
  3. `FALSE_TOOL_EXECUTION_CLAIM` interceptor.
  4. `UNGROUNDED_ACCOUNT_RESPONSE` (sustitución por negativa canónica si hay claims sin tools).
  5. Implementación del **Deterministic Comparative Read Plan** (`get_my_loans` $\to$ `max(saldo)` $\to$ `get_next_installment`) en 0 rondas LLM para resolver preguntas comparativas sin riesgo generativo.
- **Status:** Resuelto y protegido por 26 tests de robustez en `ai/agent/tests/unit/routing/test_intent_robustness.py` (81/81 tests de routing pasando).

### 25.6 Otros issues conocidos
- **Riesgo de sobre-claim:** la frase "496 automated tests, 100% pass" en el master summary es engañosa sin contexto: 12 infra tests están skipped (Docker daemon no activo) y Windows Functions worker está BLOCKED. El estado honesto es **"248 agent non-infra tests passed + 46 infra passed + 12 skipped"**.
- **Foundry Local version-sensitive:** los tests asumen Foundry Local 0.10.3. Cambios de versión requieren re-validación del recovery plan v0.5.
- **RAG corpus solo en español** — el intent classifier + corpus están construidos sobre banking en español. Extensión a otros idiomas requiere regenerar corpus + re-entrenar.

---

## 26. Glosario bilingüe (ES / EN)

### 26.1 Banking / Finance
- **account query** / consulta de cuenta
- **customer isolation** / aislamiento de cliente
- **ownership** / propiedad (customer_id ownership)
- **tool allowlist** / lista de herramientas permitidas

### 26.2 AI / ML
- **LLM** / Large Language Model
- **prompt / prompting** / instrucción
- **RAG** / Retrieval Augmented Generation
- **retrieval** / recuperación
- **chunking** / fragmentación
- **grounding** / anclaje a evidencia
- **citations** / citas
- **MCP** / Model Context Protocol
- **tool calling / function calling** / llamada a herramienta

### 26.3 Agentic
- **HITL** / Human-in-the-Loop (microscopic per-action approval)
- **HOTL** / Human-on-the-Loop (macroscopic supervisory control)

### 26.4 Reliability
- **idempotency / idempotency-key** / idempotencia
- **retry / backoff / jitter** / reintento
- **circuit breaker** / cortacircuitos
- **timeout** / tiempo máximo
- **transactional outbox** / outbox transaccional
- **message bus / queues** / bus de mensajes
- **idempotent consumer** / consumidor idempotente
- **DLQ** / Dead-Letter Queue

### 26.5 Observability
- **OTel** / OpenTelemetry
- **trace / span** / traza / segmento
- **correlation ID vs trace ID** / identificadores de correlación vs de traza
- **structured logging** / logging estructurado
- **redaction** / redacción
- **operational metrics (p50/p95/p99)** / métricas operacionales
- **AgentOps** / operaciones del agente
- **audit log** / registro de auditoría
- **KQL** / Kusto Query Language
- **ADR** / Architecture Decision Record

### 26.6 Container / Infra
- **container, image, Dockerfile, Compose, registry, OCI, port mapping, network, health check, readiness/liveness, env var, secret, volume**
- **AMQP** (Azure Service Bus protocol)
- **KEDA** (Kubernetes Event-Driven Autoscaling)
- **Container Apps** (Azure serverless containers)
- **Kubernetes / AKS**

### 26.7 Data
- **DBMS / RDBMS**
- **PostgreSQL, SQL, schema, table, row, PK/FK, transaction, ACID, index, EXPLAIN, ANALYZE, connection pool**

### 26.8 Vector
- **embedding, vector, vector database, pgvector**
- **cosine similarity, L2/Euclidean, inner product**
- **exact NN, ANN, HNSW, IVFFlat**
- **metadata filtering**
- **recall, latency, throughput**

### 26.9 Cosmos
- **NoSQL, document database, Azure Cosmos DB**
- **partition key (logical/physical), cardinality, hot partition**
- **point read, cross-partition query, TTL**
- **change feed, processor, checkpoint, lease**
- **at-least-once, consistency level, RU, indexing policy, emulator**

### 26.10 Reproducibility
- **reproducible build, immutable artifact**
- **Docker tag (vs floating), image digest sha256**
- **supply-chain risk, SemVer**
- **maturity levels (LAB-COVERED, CI-CONFIGURED, RUNNER-PENDING, PROD-PARTIAL, CLOUD-PENDING, SAFETY-DEFERRED)**

### 26.11 Quality
- **QA, CI, SAST, SCA, SBOM**

### 26.12 Cross-session
- **DRY, code duplication, code smell, technical debt, refactoring, cohesion, coupling, canonical component, single-writer principle, concurrency, race condition, ownership, lease/lock, HEAD, working tree, staging/index, CI concurrency, CODEOWNERS**

### 26.13 Serverless
- **serverless, FaaS, Azure Functions, Functions Host, Core Tools, trigger, binding (input/output), Python v2 model, stateless, cold/warm start, event-driven, Event Grid, CloudEvents 1.0, topic/subscription, dead-letter destination, at-least-once, idempotent event handler**

### 26.14 Microsoft AI
- **Foundry, Foundry Local, AI Foundry**
- **phi-4-mini**
- **Azure OpenAI, Azure AI Search, Azure AI Document Intelligence, Azure AI Vision, Azure AI Language**

### 26.15 Certificaciones
- **AI-900** — Azure AI Fundamentals
- **AI-102** — Azure AI Engineer Associate (antes AI-103)
- **AI-200** — Build and modernize AI Apps with Azure services (data + cloud dev)

### 26.16 Coder Tooling & Navigation Stack
- **codebase-memory-mcp**: Servidor MCP que indexa el grafo de conocimiento del código (`search_graph`, `trace_path`, `get_code_snippet`, `query_graph`).
- **sequential-thinking**: Servidor MCP de razonamiento deliberativo paso a paso para descomponer problemas complejos e invariantes.
- **context7**: Servidor MCP para consultar documentación actualizada de librerías en tiempo de desarrollo.
- **antigravity-guide / agy-customizations**: Skills que documentan las capacidades del entorno IDE y la creación de extensiones.
- **e2e-testing-patterns**: Skill de patrones de pruebas end-to-end e integración para APIs HTTP en sistemas sin UI gráfica.
- **retrieval policy**: Política determinista (`.ai-env/retrieval-policy.json`) que rige cómo se resuelve la búsqueda de código (exact, symbol, architecture, knowledge).
- **zero account fakery**: Invariante bancario que prohíbe emitir o simular hechos sobre cuentas sin ejecución autorizada y exitosa de herramientas.

---

## 27. Mapa de fuentes del repositorio (para auditoría)

Si un auditor quiere verificar cada claim de este briefing, estos son los archivos primarios.

### 27.1 Charter y misión
- `docs/charter/01-vision.md`
- `docs/charter/02-scope.md`
- `docs/charter/03-use-cases.md`
- `docs/charter/04-non-goals.md`
- `docs/charter/05-success-criteria.md`

### 27.2 Tooling de desarrollo e inspección
- `AGENTS.md` (reglas permanentes, permisos de bash, stack de MCPs y skills del coder)
- `opencode.json` (configuración del IDE, slash commands, LSP pyright, subagents)
- `.ai-env/retrieval-policy.json` (política de enrutamiento de consultas de código)
- `.opencode/scripts/smoke-mcp.mjs` (script de smoke-test de transporte MCP)
- `.intelligence/smoke/mcp-smoke.json` (evidencia verificable de handshake de MCP servers)

### 27.3 Arquitectura
- `docs/architecture/CANONICAL-COMPONENTS.md` (24 componentes)
- `docs/architecture/E2E-FINAL-ARCHITECTURE.md`
- `docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md`
- `docs/architecture/CONTAINER-PLATFORM-DECISION.md` (ACA vs AKS)
- `docs/architecture/COSMOS-PARTITION-DESIGN.md`
- `docs/architecture/REDIS-CACHE-POLICY.md`
- `docs/architecture/EVENT-GRID-CLOUD-DESIGN.md`
- `docs/architecture/EVENT-GRID-VS-SERVICE-BUS.md`
- `docs/architecture/adr/ADR-001` a `ADR-030` (30 ADRs)

### 27.4 Seguridad y calidad
- `docs/security/V1.0-THREAT-MODEL.md`
- `docs/security/DEVSECOPS-GATES.md`
- `docs/security/CONTAINER-SECURITY.md`
- `docs/security/DATA-LAYER-SECURITY.md`
- `docs/security/SERVERLESS-SECURITY.md`
- `docs/security/sbom.json` (CycloneDX)
- `docs/quality/TEST-STRATEGY.md`
- `docs/quality/E2E-MATRIX.md` (journeys A-H)
- `docs/quality/TEST-SUITE-RATIONALIZATION.md`
- `docs/quality/V1.0-PERFORMANCE-EVIDENCE.md`
- `docs/quality/V1.0-SLI-SLO-LAB-REPORT.md`
- `docs/quality/V0131-RUNTIME-EVIDENCE.md`
- `docs/quality/V0140-APPCONFIG-IDENTITY-EVIDENCE.md`
- `docs/quality/V0150-EVALUATION-MLOPS-EVIDENCE.md`

### 27.5 Operaciones y releases
- `docs/operations/runbooks/incident-response.md`
- `docs/operations/runbooks/rollback.md`
- `docs/operations/runbooks/dependency-outage.md`
- `docs/operations/runbooks/dlq-and-kill-switch.md`
- `docs/operations/KUBERNETES-TROUBLESHOOTING.md`
- `docs/releases/PORTFOLIO-INTERVIEW-EVIDENCE.md`
- `docs/releases/V1.0-EVIDENCE.md`

### 27.6 Evaluación y learning
- `docs/evaluation/README.md`
- `docs/evaluation/EVALUATION-CATALOG.md`
- `docs/evaluation/v015-ai-evaluation-mlops.md`
- `docs/learning/GLOSSARY.md`
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/learning/MASTERS-NOTES.md`
- `docs/learning/V1.0-MASTERS-NOTES.md`
- `docs/learning/AZURE-FUNCTIONS-TRIGGERS-BINDINGS.md`
- `docs/learning/CONTAINERS-SERVICE-BUS.md`
- `docs/learning/PGVECTOR.md`

### 27.7 Contratos (10 JSON Schemas)
- `contracts/bootstrap-manifest.schema.json`
- `contracts/core-banking-openapi.schema.json`
- `contracts/cloudevents/service-request-created-v1.schema.json`
- `contracts/cosmos-event-item.schema.json`
- `contracts/graph.schema.json`
- `contracts/index.schema.json`
- `contracts/manifest.schema.json`
- `contracts/mcp-tools.schema.json`
- `contracts/service-request-created.schema.json`
- `contracts/session.schema.json`

### 27.8 Código fuente crítico
- **Agente:** `ai/agent/src/aegisbank_agent/agent.py` (~1,190 líneas), `session_store.py` (almacén de sesiones SQLite durable), `knowledge_routing.py` (enrutamiento anafórico y planes comparativos), `hitl.py`, `mcp_boundary.py`, `mcp/server.py`, `tools/{base,registry,banking_tools,knowledge_tools}.py`, `reliability/*.py`, `observability/*.py`, `mlops/*.py`, `evaluation/*.py`, `configuration/*.py`.
- **RAG:** `ai/rag/src/aegisbank_rag/{retriever,hybrid,lexical,dense_local,embedding,foundry_local,pgvector_retriever,redis_retriever,cache,generation,prompting,corpus,chunking,evaluation}.py`.
- **Mock Core Banking:** `services/mock-core-banking/src/mock_core_banking/{main,config,correlation,error_handlers}.py` + `api/*.py` + `domain/*.py` + `persistence/*.py` + `schemas/*.py`.
- **Functions:** `functions/aegisbank-events/{function_app,service_request_handler,cloud_event}.py` + `Dockerfile` + `host.json`.
- **Intent classifier:** `ml/intent-classifier/src/aegisbank_intent_classifier/{pipeline,dataset,calibration,evaluation,cli}.py`.
- **Scripts:** `scripts/{quality_gate,session_guard,performance_baseline,evaluation_gate,generate_sbom,container_acceptance,appconfig_emulator_acceptance,functions_runtime_acceptance,capture_pgvector_query_plans,evaluate_retrievers_v012}.py`.

### 27.9 Infraestructura
- `deploy/local/docker-compose.yml` (7 servicios, 4 profiles)
- `deploy/local/Config.json` (Service Bus emulator config)
- `deploy/kubernetes/{namespace,deployment,service,configmap}.yaml`

### 27.10 Cadena de prompts (28 archivos)
- `docs/chatgpt-prompts/000_PROMPT.md` (master, 1643 líneas) a `026_PROMPT.md` (más reciente).

### 27.11 Experimentos por milestone
- `docs/experiments/v0.3-intent-classification-baseline.md`
- `docs/experiments/v0.4-rag-retrieval-foundation.md`
- `docs/experiments/v0.5-grounded-generation-evaluation.md`
- `docs/experiments/v0.5-foundry-local-recovery-plan.md`
- `docs/experiments/v0.6.1-native-tool-calling.md`
- `docs/experiments/v0.7.0-mcp-hitl.md`

### 27.11 MCP smoke evidence
- `C:\aegisbank-ai-platform\.intelligence\smoke\mcp-smoke.json` (5 servers, tool counts, initMs/listMs timing).

### 27.12 Requirements y career
- `docs/requirements/V1.0-MATURITY-MATRIX.md` (4 tiers)
- `docs/requirements/COVERAGE-MATRIX.md`
- `docs/requirements/MIBANCO-JOB-PROFILE-2026.md` (COE IA role profiles)
- `docs/career/role-profile-images-and-gap-analysis.md`

---

## 28. Limitaciones de este briefing

1. **Es un snapshot en el tiempo.** El proyecto evoluciona por milestones. La versión documentada es `v1.0.6` (base técnica y defensas de routing) / `v1.0.6` (docs, Information Architecture & Coder Navigation Stack). Cualquier cosa posterior (v1.1, v1.2 con AKS, multi-agente, AI-200 cloud) **no está cubierta**.
2. **No reemplaza al repositorio.** Para decisiones de implementación específicas (número de líneas, signatures exactas, datasets crudos) el auditor debe abrir el código. Este briefing es **narrativo**, no ejecutable.
3. **Las cifras de tests son aproximadas.** El número exacto varía según cuándo se mida (algunos infra tests quedan skipped si Docker no está activo). Los rangos dados (138 unit + 51 integration + 21 contract + 11 E2E + 248 agent non-infra + 46 infra passed + 12 skipped) son los declarados al release v1.0.0.
4. **No incluye reproducciones ejecutadas.** Este briefing describe qué existe, no ejecuta nada. Para validar PASS/FAIL de cualquier gate, abre `scripts/quality_gate.py --fast` en el repo.
5. **No incluye datos de entrenamiento ni el corpus completo.** Solo describe qué hay y por qué; el contenido de `ai/rag/data/corpus/` y `ml/intent-classifier/data/intent_dataset.jsonl` debe leerse del repo.
6. **No incluye secretos.** El proyecto tiene cero secretos en Git. No los hay para reportar.
7. **No constituye consejo legal, regulatorio, ni de cumplimiento.** El proyecto mismo prohíbe tales claims explícitamente.
8. **El briefing es bilingüe sesgo al español** porque el repositorio está escrito mayormente en español (docs/charter, docs/experiments, prompts) con código y contratos en inglés. Términos técnicos críticos se preservan en inglés.

---

## Cierre

AegisBank AI Platform es, a la fecha de este briefing, un **monolito modular de Python 3.14** que implementa un único agente (Aegis) sobre Foundry Local (phi-4-mini) y MCP stdio v2, con FastAPI mock-core-banking + outbox transaccional, RAG híbrido con abstención canónica, HITL/HOTL deterministas, reliability layer (idempotencia + retry + circuit breaker + DLQ), observability OTel + audit WORM, MLOps con MLflow + drift + A/B testing estadísticamente rigurosos, y un camino de promoción local → Docker → CI → Azure (ACA, Service Bus, Cosmos, pgvector, Redis, App Config + Key Vault) mediado por **10 JSON Schemas 2020-12** que son la fuente de verdad de la compatibilidad entre capas.

Su filosofía es **"el LLM interpreta y propone; lo determinista decide"**. Su honestidad es **"sintético, educativo, de portafolio — nunca productivo ni certificado"**. Su disciplina es **"DISCOVER BEFORE CREATE, ONE WRITER MANY READERS, DISCOVER BEFORE CREATE"** — aplicada sobre 24 componentes canónicos, 30 ADRs, 4 runbooks, y una cadena de 28 prompts históricos auditables.

Para maestría de IA, demuestra las 7 capas de evaluación (Intent / Retrieval / Generation / Agent / Safety / System E2E / Performance) con frozen holdouts y statistical rigor. Para certificaciones Microsoft AI, cubre los syllabus de AI-900, AI-102 (antes AI-103) y AI-200 con artefactos verificables. Para certificarse realmente, el developer debe **rendir los exámenes**; el repositorio no los rinde por él.

Para ChatGPT u otro LLM externo, este briefing es el manual completo. Para el developer que lo escribió, es el mapa que mantiene la cordura entre 8 milestones consecutivos.

--- APPENDIX A START ---

---

# Appendix A — Machine-Precise Data Tables

> **Purpose.** This appendix is optimized for LLM consumption. Each datum is a discrete, attributable fact. Every claim cites a concrete source path. No narrative prose. If a downstream LLM wants to query, cite, or diff against the briefing, it can extract these tables verbatim.
>
> **Format conventions.**
> - Every entry is `<KEY>: <VALUE>` or pipe-delimited (`|`) row.
> - Paths use forward slashes, repository-root-relative.
> - Line numbers reference the file at the commit specified in the commit table below.
> - Version strings match `pyproject.toml` / `requirements.txt` exactly.

## A.1 Repository Identity (machine-readable)

```
project.name                  : AegisBank AI Platform
project.landing_page          : aegisbank-ai-platform/README.md
project.root_absolute         : C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform
project.env_root_absolute     : C:\aegisbank-ai-platform-ai-env
project.inner_repo_name       : aegisbank-ai-platform
project.outer_layer_name      : opencode-bootstrap-layer
repo.docs_governance_version  : v1.0.2 (Documentation Information Architecture & Evaluation Taxonomy)
repo.base_technical_version   : v1.0.1 (evidence integrity corrective)
git.tags                      : v1.0.0, v1.0.1
git.branches                  : master, feat/v0.3-intent-baseline
git.default_branch            : master
git.total_commits             : 48
git.first_commit_date         : 2026-04 (charter v0.1)
git.last_commit_date          : 2026-09-11
project.languages_primary     : Python 3.14, Markdown, JSON, YAML, PowerShell, TypeScript
project.license_intent        : Educational, non-production, synthetic-only
project.affiliations          : NONE (explicitly disclaimed to Mibanco, Microsoft, SBS, NIST)
```
## A.2 Git Commit Timeline (48 commits, chronological ascending)

> `hash | date_utc | milestone | type | subject | files_changed | insertions`

```
hash     | date_utc              | milestone | type | subject                                                                                              | files | +/-
---------+-----------------------+-----------+------+------------------------------------------------------------------------------------------------------+-------+--------
4cee5500 | 2026-04 (approx)      | v0.1      | docs | establish AegisBank project charter                                                                  |     8 | 1367
41144561 | 2026-04 (approx)      | v0.2      | feat | implement local core banking mock                                                                    |    29 | ~1700
073f8336 | 2026-05 (approx)      | v0.3      | feat | establish ML intent classification baseline                                                          |    24 | 6459
1a26816a | 2026-05 (approx)      | v0.3      | docs | synchronize decision index                                                                            |     1 | 5
1e92a622 | 2026-05 (approx)      | v0.4      | feat | establish RAG retrieval and evaluation foundation                                                    |    35 | ~3700
ebeb3789 | 2026-06 (approx)      | v0.5      | feat | establish grounded generation and LLM evaluation                                                    |    33 | ~2400
61e30168 | 2026-06 (approx)      | v0.6      | feat | establish single-agent read-only tool orchestration                                                |    31 | ~2700
e26b2e8f | 2026-06 (approx)      | v0.6      | docs | record live local evaluation                                                                          |     5 | 294
73b7dacc | 2026-06 (approx)      | v0.6.1    | fix  | execute native Foundry Local tool calls end to end                                                   |     3 | 260
56aaa83c | 2026-07 (approx)      | v0.7      | feat | establish MCP human-approved write boundary                                                         |    25 | 1980
59f01fd5 | 2026-07 (approx)      | v0.8      | feat | establish reliability + messaging foundation (idempotency / retry / CB / outbox / DLQ)              |    29 | 2965
5862ea06 | 2026-08-21           | v0.14     | feat | add configuration and secrets identity boundary                                                     |    ~10 | ~500
90d20d8b | 2026-08-31 (approx)  | v0.14     | fix  | stabilize quality gate test runners and format acceptance script                                    |     3 | 43
72791cd8 | 2026-09-04           | v0.15     | feat | establish AI evaluation and MLOps experimentation foundation                                          |    26 | 2639
8393d88a | 2026-09-04 (approx)  | v0.15     | fix  | validate App Configuration URL schemes                                                                |     1 | 15
fa27a387 | 2026-09-09 (approx)  | v1.0      | rel  | harden AegisBank enterprise AI portfolio                                                             |    16 | 611
89faca9f | 2026-09-09 (approx)  | v1.0      | docs | harden statistical and performance evidence claims                                                   |     5 | 26
668c0b22 | 2026-09-09 (approx)  | v1.0      | docs | harden statistical and performance evidence claims (round 2)                                         |     7 | 91
6e6002c2 | 2026-09-11T04:32:37Z | v1.0.2    | docs | rationalize documentation and evaluation taxonomy                                                    |     5 | 467
268df51a | 2026-09-11T05:08:31Z | v1.0.1    | fix  | durable session state and local llm resilience                                                      |    11 | 577
```

## A.3 Author / Contribution Profile

```
author.primary    : Pablo Cesar Vega Valverde <pvegav@autonoma.edu.pe>
author.role       : single-developer project
contributors.total: 1 (sole author across all 48 commits)
remotes.configured: none (local-only repository, no origin push)
```

## A.4 File Inventory (Python source, top 30 by LOC)

```
path                                                                                                | loc  | role
---------------------------------------------------------------------------------------------------+------+-----------------------------------------------------------------
ai/agent/src/aegisbank_agent/agent.py                                                                | 1192 | AgentOrchestrator + CLI dispatch + routing policy
scripts/quality_gate.py                                                                              |  734 | Quality gate runner (lint + format + tests + SAST + SCA + secrets)
ai/agent/src/aegisbank_agent/evaluation/evaluators.py                                                 |  678 | 9 AI evaluators + aggregate computation + report writer
ml/intent-classifier/src/aegisbank_intent_classifier/dataset.py                                      |  463 | Synthetic dataset generation + StratifiedGroupKFold split
ai/rag/src/aegisbank_rag/generation_evaluation.py                                                     |  451 | Generation evaluator (groundedness, citation, abstention)
ai/agent/src/aegisbank_agent/configuration/config.py                                                  |  448 | ConfigurationProvider + App Config emulator client
ai/agent/src/aegisbank_agent/tools/banking_tools.py                                                   |  421 | 4 banking tools (get_my_loans / get_loan_details / get_next_installment / create_service_request)
ml/intent-classifier/src/aegisbank_intent_classifier/evaluation.py                                    |  418 | TF-IDF + LR frozen experiment harness
ai/agent/src/aegisbank_agent/knowledge_routing.py                                                     |  415 | Deterministic policy routing + entity extraction
scripts/evaluation_gate.py                                                                           |  366 | v0.15 AI evaluation gate (McNemar + bootstrap CI + drift)
ai/rag/src/aegisbank_rag/pgvector_retriever.py                                                        |  352 | PgVectorRetriever (HNSW + cosine + metadata filtering)
functions/aegisbank-events/service_request_handler.py                                                 |  323 | CloudEvent consumer (idempotent + audit + redaction)
ai/rag/src/aegisbank_rag/evaluation.py                                                               |  321 | Retrieval evaluator (P@K, R@K, MRR, nDCG)
ai/agent/tests/e2e/test_critical_journeys.py                                                          |  302 | 8 E2E journeys A-H
ai/rag/src/aegisbank_rag/cli.py                                                                      |  288 | RAG CLI (generate / retrieve / evaluate / generate-eval)
ai/agent/src/aegisbank_agent/mcp_boundary.py                                                          |  284 | MCP stdio server boundary
scripts/appconfig_emulator_acceptance.py                                                             |  279 | App Config emulator CRUD + labels + refresh acceptance
scripts/functions_runtime_acceptance.py                                                              |  264 | Functions Core Tools host acceptance
services/mock-core-banking/src/mock_core_banking/persistence/seed.py                                 |  261 | Seed data builder (3 customers, 4 loans, 10 installments, 2 SRs)
ai/agent/src/aegisbank_agent/mlops/drift.py                                                           |  255 | PSI / Wasserstein / JSD drift detector
ai/agent/tests/integration/hitl/test_hitl_acceptance.py                                              |  249 | HITL state machine acceptance tests
ai/agent/src/aegisbank_agent/configuration/secrets.py                                                 |  247 | SecretProvider + Key Vault reference resolver (RFC 3986)
ai/rag/src/aegisbank_rag/redis_retriever.py                                                          |  247 | RedisVectorRetriever (RediSearch KNN + single-flight)
ai/agent/src/aegisbank_agent/hitl.py                                                                 |  244 | HITLApprovalManager state machine
ai/agent/tests/infra/cosmos/test_cosmos_acceptance.py                                                |  235 | Cosmos DB emulator acceptance
scripts/session_guard.py                                                                             |  233 | Atomic single-writer lock (acquire / check / release)
services/mock-core-banking/src/mock_core_banking/persistence/repositories.py                         |  233 | 6 repositories with transactional outbox
ai/agent/src/aegisbank_agent/session_store.py                                                        |  225 | SQLiteSessionStore (durable sessions + last_loan_id)
```

## A.5 Repository Statistics

```
metric.python_files_total              : 222
metric.python_loc_total                : 25,657
metric.python_loc_source_only          : ~16,000 (excl. tests)
metric.python_loc_tests_only           : ~9,500 (incl. integration + e2e + infra + contract)
metric.markdown_files                  : ~80
metric.json_schema_files               : 10 (contracts/)
metric.docker_compose_files            : 1 (deploy/local/docker-compose.yml)
metric.kubernetes_manifests           : 4 (deploy/kubernetes/)
metric.gh_workflow_files               : 1 (.github/workflows/ci.yml)
metric.mcp_servers                     : 5 (sequential-thinking, filesystem, git, everything, context7)
metric.mcp_servers_inert               : 1 (context7: CONTEXT7_API_KEY placeholder)
metric.lsp_servers                     : 1 (pyright via .opencode/node_modules/pyright)
metric.adrs_total                      : 30 (append-only; 2 with companion drafts per README section 2)
metric.chatgpt_prompts_total           : 28 (000..026, with 020A + 022A sub-iterations)
metric.runbooks_total                  : 4 (incident-response, rollback, dependency-outage, dlq-and-kill-switch)
metric.json_schemas_draft              : 2020-12 (all contracts/*.schema.json)
metric.knowledge_graph_format          : .intelligence/graph.jsonl NDJSON (validated by contracts/graph.schema.json)
```

## A.6 Dependency Matrix (exact pins from pyproject.toml + requirements.txt)

### A.6.1 ai/agent (aegisbank-agent 0.7.0.dev0, Python >=3.14,<3.15)

```
dep.runtime.openai                          : 3.5.0
dep.runtime.mcp                             : 2.1.1
dep.runtime.opentelemetry-api               : 1.44.0
dep.runtime.opentelemetry-sdk               : 1.44.0
dep.runtime.pydantic                        : 2.13.4
dep.runtime.aegisbank-rag                   : >=0.4.0  (internal)
dep.runtime.mock-core-banking               : >=0.2.0  (internal)
dep.runtime.azure-servicebus                : 7.14.3
dep.runtime.azure-cosmos                    : >=4.16.0
dep.runtime.redis                           : >=5.0.0
dep.runtime.azure-appconfiguration-provider : 2.5.0
dep.runtime.azure-identity                  : 1.25.3
dep.runtime.azure-keyvault-secrets          : 4.11.2
dep.runtime.mlflow-skinny                   : >=3.16.0
dep.runtime.alembic                         : >=1.19.0
dep.dev.pytest                              : 9.1.1
dep.dev.ruff                                : 0.16.4
entry.aegisbank-agent                       : aegisbank_agent.cli:main
entry.aegisbank-mcp-demo                   : aegisbank_agent.hitl_cli:main
pytest.markers                              : unit | integration | contract | e2e | infra | slow
ruff.line-length                            : 100
ruff.target-version                         : py314
ruff.lint.select                            : E, F, I, N, W
```

### A.6.2 ai/rag (aegisbank-rag 0.5.0.dev0, Python >=3.14,<3.15)

```
dep.runtime.openai                          : 3.5.0
dep.runtime.scikit-learn                    : 1.9.0
dep.runtime.numpy                           : 2.5.2
dep.runtime.psycopg[binary]                 : >=3.2
dep.runtime.pgvector                        : >=0.3.0
dep.runtime.redis                           : >=5.0.0
dep.dev.pytest                              : 9.1.1
dep.dev.ruff                                : 0.16.4
entry.aegisbank-rag                         : aegisbank_rag.cli:main
```

### A.6.3 services/mock-core-banking (mock-core-banking 0.2.0, Python >=3.12)

```
dep.runtime.fastapi                         : 0.141.1
dep.runtime.pydantic                        : 2.13.4
dep.runtime.sqlalchemy                      : 2.0.52
dep.runtime.starlette                       : 1.6.0
dep.runtime.uvicorn                         : 0.52.4
dep.dev.pytest                              : 9.1.1
dep.dev.httpx2                              : 2.12.0
dep.dev.ruff                                : 0.16.4
```

### A.6.4 ml/intent-classifier (aegisbank-intent-classifier 0.3.0, Python >=3.14,<3.15)

```
dep.runtime.scikit-learn                    : 1.9.0
dep.dev.pytest                              : 9.1.1
dep.dev.ruff                                : 0.16.4
entry.aegisbank-intent                      : aegisbank_intent_classifier.cli:main
```

### A.6.5 functions/aegisbank-events (Azure Functions Python v2)

```
dep.runtime.azure-functions                 : 2.3.0
dep.runtime.jsonschema                      : 4.26.0
dep.local.-e                                : ../../services/mock-core-banking
dep.local.-e                                : ../../ai/rag
dep.local.-e                                : ../../ai/agent
```

### A.6.6 .opencode layer (Node, pnpm-only)

```
pkg.@modelcontextprotocol/server-sequential-thinking : pinned in .opencode/node_modules
pkg.@modelcontextprotocol/server-filesystem          : 2026.7.10
pkg.@cyanheads/git-mcp-server                        : 2.15.3
pkg.@modelcontextprotocol/server-everything          : 2026.8.18
pkg.@upstash/context7-mcp                           : 4.0.3  (inert: CONTEXT7_API_KEY placeholder)
pkg.pyright                                         : 1.1.413
```

## A.7 Docker Compose Services (deploy/local/docker-compose.yml, name=aegisbank-local)

```
service                     | image                                                                   | image_digest (sha256)                                                                                                | port          | profile        | security
----------------------------+-------------------------------------------------------------------------+----------------------------------------------------------------------------------------------------------------------+---------------+----------------+---------------------------
mock-core-banking           | aegisbank/mock-core-banking:0.11.0 (local build)                          | n/a                                                                                                                  | 8000          | (default)      | read_only, tmpfs, no-new-privileges, cap_drop=ALL, user=10001
mssql                       | mcr.microsoft.com/mssql/server:2022-latest                                | n/a (floating tag - known gap, see ADR-025)                                                                          | (internal)    | (default)      | ACCEPT_EULA=Y
servicebus-emulator         | mcr.microsoft.com/azure-messaging/servicebus-emulator:latest              | n/a (floating tag - known gap)                                                                                       | 5672          | (default)      | Config.json mounted RO
postgres-pgvector           | pgvector/pgvector:0.8.0-pg17                                             | n/a                                                                                                                  | 5432          | data           | POSTGRES_PASSWORD via env
cosmos-emulator             | mcr.microsoft.com/cosmosdb/linux/azure-cosmos-emulator:vnext-latest      | n/a                                                                                                                  | 8081,8080,1234 | cosmos,data    | AZURE_COSMOS_EMULATOR_PARTITION_COUNT=4
redis                       | redis:8.10.1-trixie                                                       | 298e5b3bc566bade82f46ad5511777a4a07a294097ce16ada2f6a42be5239df5                                                       | 127.0.0.1:6379| redis,data     | --save 60 1
app-configuration-emulator  | mcr.microsoft.com/azure-app-configuration/app-configuration-emulator:1.2.0| f84ca52fcf51aab3bad8a0363198c161e8a79eb41712d27779f6e0eb777c7000                                                       | 127.0.0.1:8483->host:8082 | config,all | Tenant:AnonymousAuthEnabled=true
```

Note: foundry-local is NOT containerized. Runs on host via foundry CLI (versions 0.10.3 -> public-preview-0.10.0 official per microsoft/Foundry-Local repo).

## A.8 JSON Schemas (contracts/, all draft 2020-12)

```
file                                                                                   | $id                                                       | title                                          | validates                                                        | additionalProperties
---------------------------------------------------------------------------------------+-----------------------------------------------------------+------------------------------------------------+------------------------------------------------------------------+--------------------
contracts/bootstrap-manifest.schema.json                                                | urn:opencode-global:contracts:bootstrap-manifest:v1       | BootstrapManifest                               | /init output                                                     | false
contracts/core-banking-openapi.schema.json                                             | urn:aegisbank:contracts:core-banking-openapi:v1            | CoreBankingOpenAPIContract                     | mock-core-banking openapi.json (must list 8 paths + 6 schemas)    | true
contracts/cloudevents/service-request-created-v1.schema.json                            | urn:aegisbank:contracts:cloudevents:service-request-created:v1 | ServiceRequestCreatedCloudEventContract    | CloudEvents 1.0 envelope from outbox                              | false (data only)
contracts/cosmos-event-item.schema.json                                                | urn:aegisbank:contracts:cosmos-event-item:v1                | CosmosEventItemContract                        | Cosmos DB NoSQL items                                            | true
contracts/graph.schema.json                                                            | urn:opencode-global:contracts:graph:v1                      | IntelligenceGraph                              | .intelligence/graph.jsonl NDJSON (node|edge oneOf)               | false
contracts/index.schema.json                                                            | urn:opencode-global:contracts:index:v1                     | IntelligenceIndex                              | .intelligence/index.json summary                                 | false (counts)
contracts/manifest.schema.json                                                         | urn:opencode-global:contracts:manifest:v1                  | IntelligenceManifest                           | .intelligence/manifest.json                                      | false (schema_versions)
contracts/mcp-tools.schema.json                                                        | urn:aegisbank:contracts:mcp-tools:v1                       | MCPToolsRegistryContract                       | MCP tool registry exports                                        | true
contracts/service-request-created.schema.json                                          | urn:aegisbank:contracts:service-request-created:v1         | ServiceRequestCreatedEventContract             | Transactional Outbox event payload (pre-CloudEvent)              | true
contracts/session.schema.json                                                          | urn:opencode-global:contracts:session:v1                   | SessionEvent                                   | .intelligence/sessions/<id>.jsonl NDJSON lines                   | true
```

## A.9 Scripts Inventory (scripts/*.py, 10 files)

```
script                                  | purpose                                                       | entry   | subprocess / system calls
----------------------------------------+---------------------------------------------------------------+---------+--------------------------------------------
quality_gate.py                         | runs 13+ automated checks before commit                       | main()  | git status, ruff check, ruff format, pytest, bandit, pip-audit
session_guard.py                        | atomic single-writer lock across sub-agents                  | main()  | git rev-parse HEAD, git status, file lock
performance_baseline.py                 | 25-iter local p50/p95/p99 baseline on read path              | main()  | spawns TestClient against mock-core-banking
evaluation_gate.py                      | v0.15 frozen-holdout gate (McNemar + bootstrap CI + drift)   | main()  | loads v015_eval_suite.jsonl, runs 9 evaluators, MLflow log
generate_sbom.py                        | CycloneDX SBOM via pip-audit                                 | main()  | pip-audit -f cyclonedx-json
container_acceptance.py                 | docker compose up + health check                             | main()  | docker compose up, curl /health/ready
appconfig_emulator_acceptance.py        | App Config emulator CRUD + labels + refresh                  | main()  | docker run emulator, HTTP CRUD via urllib
functions_runtime_acceptance.py         | Functions Core Tools host start                              | main()  | func start, docker run azure-functions image
capture_pgvector_query_plans.py         | EXPLAIN ANALYZE for pgvector queries                          | main()  | psql / docker exec into pgvector container
evaluate_retrievers_v012.py             | re-run v0.4 retrieval protocol against pgvector              | main()  | psycopg connect, hybrid_rrf retriever
```

Detailed script function signatures (extracted via grep):
- scripts/appconfig_emulator_acceptance.py:30: _run(*args: str), :34: ensure_emulator_container(), :74: run_acceptance_suite(), :249: main()
- scripts/capture_pgvector_query_plans.py:15: main()
- scripts/container_acceptance.py:19: _run(*args: str), :23: _health_url(), :33: _message_flow(), :65: main()
- scripts/evaluate_retrievers_v012.py:19: run_v012_evaluation()
- scripts/evaluation_gate.py:125: evaluate_variant(cases: list, variant: str), :204: run_evaluation_gate(), :329: main()
- scripts/functions_runtime_acceptance.py:27: _run(*args: str), :66: ensure_runtime_container(), :98: wait_for_host_ready(timeout_seconds: float=30.0), :116: run_acceptance()
- scripts/generate_sbom.py:10: main()
- scripts/performance_baseline.py:32: _percentile(values: list, percentile: float), :43: _measure(client, path: str, iterations: int), :64: run(iterations: int), :84: main()
- scripts/quality_gate.py:34: _run_cmd(cmd: list, cwd: Path), :45: _scan_for_secrets(repo_root: Path), :122: _check_architecture_inventory(repo_root: Path), :158: _check_redis_image_reproducibility(repo_root: Path), :199: _session_guard_result(repo_root: Path), :621: main()
- scripts/session_guard.py:23: _git(*args, cwd: Path|None=None), :34: _get_git_head(), :38: _get_git_status_files(), :54: _get_staged_paths(), :59: _matches_allowed(path: str, patterns: list), :76: _resolve_session_id(value: str|None), :198: main(argv: list|None=None)

## A.10 Top-Level Function Inventory (selected canonical modules)

```
ai/agent/src/aegisbank_agent/agent.py                                          | class AgentOrchestrator
  .run(user_message: str, *, customer_id: str, session_id: str|None=None,
       correlation_id: str|None=None,
       approval_callback: Callable[[ApprovalRequest], bool]|None=None) -> AgentExecutionResult
ai/agent/src/aegisbank_agent/hitl.py                                            | class HITLApprovalManager (per-action state machine PENDING -> APPROVED -> EXECUTED / REJECTED)
  .create_request(tool_name: str, arguments: dict, customer_id: str) -> ApprovalRequest
  .approve(approval_id: str, customer_id: str) -> None
  .reject(approval_id: str, customer_id: str, reason: str) -> None
  .verify_and_mark_executed(approval_id: str, customer_id: str, args: dict, result: Any) -> None
ai/agent/src/aegisbank_agent/reliability/idempotency.py                          | class IdempotencyGuard (keyed on (event_id, sha256(payload)))
  .execute(key: str, op: Callable, *args) -> tuple[Any, bool]
ai/agent/src/aegisbank_agent/reliability/circuit_breaker.py                     | class CircuitBreaker (FSM CLOSED/OPEN/HALF_OPEN, failure_threshold=3, recovery_timeout=2s)
ai/agent/src/aegisbank_agent/reliability/retry.py                               | class RetryPolicy (exponential backoff + jitter, transient-only)
ai/agent/src/aegisbank_agent/observability/hotl.py                              | class HOTLSupervisor (atomic flag is_write_allowed)
  .engage_kill_switch(reason: str) -> None
  .disengage_kill_switch() -> None
ai/agent/src/aegisbank_agent/observability/audit.py                              | class AuditLogger (WORM append-only AuditEvent store)
ai/agent/src/aegisbank_agent/session_store.py                                   | class SQLiteSessionStore (durable session_customer_id + last_loan_id)
  .get_or_create(session_id: str, customer_id: str) -> Session
  .record_loan_access(session_id: str, customer_id: str, loan_id: str) -> None
ai/agent/src/aegisbank_agent/mlops/drift.py                                     | class DriftDetector (PSI / Wasserstein / JSD)
ai/agent/src/aegisbank_agent/mlops/tracker.py                                   | class MLflowTracker (sqlite backend, experiment aegisbank-v015-agent-evaluation)
ai/agent/src/aegisbank_agent/evaluation/evaluators.py                           | 14 functions (eval taxonomy)
  evaluate_intent_resolution, evaluate_tool_selection, evaluate_tool_input,
  evaluate_tool_output_utilization, evaluate_tool_call_success, evaluate_relevance,
  evaluate_groundedness, evaluate_abstention, evaluate_task_completion,
  evaluate_no_write_compliance, evaluate_ownership_enforcement,
  evaluate_task_completion_proxy, compute_aggregate, evaluate_case, evaluate_agent,
  write_evaluation_reports
ai/agent/src/aegisbank_agent/evaluation/ab_testing.py                            | 2 functions: mcnemar_test, bootstrap_paired_confidence_interval
ai/agent/src/aegisbank_agent/tools/registry.py                                  | class ToolRegistry (allowlist + execute)
ai/agent/src/aegisbank_agent/tools/banking_tools.py                            | 4 classes: GetMyLoansTool, GetLoanDetailsTool, GetNextInstallmentTool, CreateServiceRequestTool
ai/agent/src/aegisbank_agent/tools/knowledge_tools.py                          | class SearchKnowledgeTool (wraps Retriever.search(query, top_k) -> [RetrievalHit])
ai/rag/src/aegisbank_rag/foundry_local.py                                       | class FoundryLocalProvider (LLMProvider Protocol)
  .generate(LLMRequest) -> str
  .resolve_foundry_base_url() -> str (env AEGISBANK_FOUNDRY_LOCAL_BASE_URL -> foundry CLI -> fail)
ai/rag/src/aegisbank_rag/hybrid.py                                              | class HybridRRFRetriever (frozen k=60, no score normalization)
ai/rag/src/aegisbank_rag/pgvector_retriever.py                                  | class PgVectorRetriever (HNSW + cosine + WHERE status=active)
ai/rag/src/aegisbank_rag/redis_retriever.py                                     | class RedisVectorRetriever (RediSearch KNN + single-flight stampede protection)
services/mock-core-banking/src/mock_core_banking/main.py                        | function create_app() (FastAPI factory + lifespan)
services/mock-core-banking/src/mock_core_banking/api/customers.py              | 2 functions: get_customer, list_customer_loans
services/mock-core-banking/src/mock_core_banking/api/loans.py                   | 2 functions: get_loan, get_next_loan_installment
services/mock-core-banking/src/mock_core_banking/api/service_requests.py        | 2 functions: create_service_request, get_service_request
services/mock-core-banking/src/mock_core_banking/persistence/repositories.py   | 6 classes: Customer, Loan, Installment, ServiceRequest, Idempotency, Outbox
ml/intent-classifier/src/aegisbank_intent_classifier/pipeline.py                | 3 functions: build_pipeline, build_dummy_classifier, train_pipeline
ml/intent-classifier/src/aegisbank_intent_classifier/dataset.py                  | 8 functions: generate_dataset, validate_dataset, split, freeze manifest
ml/intent-classifier/src/aegisbank_intent_classifier/calibration.py              | 5 functions: brier_score, expected_calibration_error, reliability_diagram_bins
ml/intent-classifier/src/aegisbank_intent_classifier/evaluation.py              | 3 functions: cross_validation_splits, run_frozen_experiment, render_baseline_report
functions/aegisbank-events/function_app.py                                       | function service_request_created (@app.event_grid_trigger)
functions/aegisbank-events/service_request_handler.py                            | class ServiceRequestEventHandler (.handle_cloud_event(event: func.CloudEvent) -> EventProcessingResult)
```

## A.11 Microsoft AI Certifications - CURRENT STATUS (verified 2026-09-11)

Source: Microsoft Learn (https://learn.microsoft.com). Status as of knowledge cutoff Jan 2026, refreshed 2026-09.

```
cert.id                  | cert.name                                            | status                | exam_id_current | skills_measured                                | weights
-------------------------+------------------------------------------------------+-----------------------+-----------------+------------------------------------------------+--------
ai-900 (renamed ai-901)  | Azure AI Fundamentals                                | ACTIVE (renamed 2026-04)| AI-901         | Identify AI concepts + Implement Foundry        | 40-45% / 55-60%
ai-102 (ex ai-103)       | Azure AI Engineer Associate                          | RETIRED (2025-12)     | n/a            | n/a                                            | n/a
ai-200                   | Build AI Apps with Azure (data + cloud dev path)     | learning path (no formal exam at v1.0.1)   | n/a | containers + Service Bus + ACA + data services | n/a
```

Critical alignment note for ChatGPT: The AegisBank docs/requirements/MIBANCO-JOB-PROFILE-2026.md and docs/career/role-profile-images-and-gap-analysis.md reference AI-103/AI-102/AI-200 as alignment targets. As of December 2025, AI-102 is RETIRED (per Microsoft Learn). The successor path is AI-901 (Fundamentals, replacing AI-900) -> Foundry-focused applied skills and the Azure AI Foundry certification track (still evolving as of Sep 2026). The repo docs/learning/V1.0-MASTERS-NOTES.md and docs/architecture/CONVERSATIONAL-RELEVANCE.md should be cross-checked against the current Microsoft certification catalog before any external claim.

## A.12 Foundry Local - CURRENT STATE (verified 2026-09-11)

Source: https://github.com/microsoft/Foundry-Local (396 commits, 2.5k stars, 366 forks).

```
foundry_local.runtime_size           : ~20 MB (lightweight)
foundry_local.engine                 : ONNX Runtime
foundry_local.protocol               : OpenAI-compatible REST + Responses API
foundry_local.transports             : stdio (in-process SDK), HTTP (optional web server)
foundry_local.cli_preview_version    : 0.10.0 (per microsoft/Foundry-Local releases/tag/cli-preview-0.10.0)
foundry_local.official_python_sdk    : pip install foundry-local-sdk
foundry_local.python_sdk_classes     : Configuration, FoundryLocalManager, catalog.get_model(), model.download(), model.load(), model.get_chat_client(), client.complete_chat(messages)
foundry_local.supported_model_families: GPT-OSS, Qwen, DeepSeek, Mistral, Phi (chat) + Whisper (audio)
```

Critical alignment note for ChatGPT: AegisBank ai/rag/src/aegisbank_rag/foundry_local.py uses the OpenAI Python client pointed at the foundry local HTTP endpoint, discovered via subprocess foundry server status -o json. The current OFFICIAL Python SDK (foundry-local-sdk, ~20MB, in-process) is NOT integrated. AegisBank approach is valid against the older CLI + HTTP-server model (pinned at version 0.10.3 in v0.5 recovery plan), but a future migration to the official foundry-local-sdk would simplify bootstrap and remove subprocess discovery. This is LAB-COVERED, not CLOUD-PENDING; both are equivalent at the application level (OpenAI-compatible).

## A.13 Phi-4-mini - Specs

Source: https://huggingface.co/microsoft/Phi-4-mini-instruct (MIT license, 828 likes, 24 languages, arxiv:2503.01743).

```
phi4mini.full_name            : microsoft/Phi-4-mini-instruct
phi4mini.params               : 3.8B (mini)
phi4mini.context_window       : 128K tokens
phi4mini.vocab                : 200K (multilingual, 24 languages incl. Spanish)
phi4mini.tasks                : text-generation, code, nlp, conversational
phi4mini.libraries            : Transformers, vLLM, SGLang, Foundry Local
phi4mini.foundry_alias        : phi-4-mini (model = phi-4-mini-instruct-openvino-gpu at Foundry 0.10.3)
phi4mini.license              : MIT
phi4mini.deployment_targets   : CPU (int4/int8), GPU, NPU
```

## A.14 MCP Python SDK - CURRENT STATE (verified 2026-09-11)

Source: https://github.com/modelcontextprotocol/python-sdk (README on main branch).

```
mcp_python_sdk.current_major   : v2
mcp_python_sdk.spec_supported : 2026-07-28 (and every earlier revision)
mcp_python_sdk.python_min     : 3.10+
mcp_python_sdk.transports     : stdio, Streamable HTTP, SSE
mcp_python_sdk.server_class   : mcp.server.MCPServer ("Demo")
mcp_python_sdk.server_decorators : @mcp.tool(), @mcp.resource("uri://{param}")
mcp_python_sdk.client_class   : mcp.Client (async context manager)
mcp_python_sdk.v1_branch      : v1.x (critical fixes only, deprecated; pin mcp<2 if not yet migrated)
```

Critical alignment note: AegisBank pins mcp==2.1.1 which is inside the v2 line and supports the 2026-07-28 spec. This is the correct, current choice. The MCP Python SDK v2 transition happened on/after the 2026-07-28 spec release. AegisBank adopted MCP in v0.7 (before v2 release), but the v2.1.1 pin reflects the post-transition SDK.

## A.15 ADRs (append-only, 30 records, machine-precise)

```
adr.id  | file                                                                                            | status   | milestone | title                                       | superseded_by
--------+-------------------------------------------------------------------------------------------------+----------+-----------+---------------------------------------------+---------------
adr-001 | docs/architecture/adr/ADR-001-modular-monolith-first.md                                          | Accepted | v0.2      | Modular Monolith First                      | -
adr-002 | docs/architecture/adr/ADR-002-local-sqlite-before-postgresql.md                                  | Accepted | v0.2      | Local SQLite Before PostgreSQL              | -
adr-003 | docs/architecture/adr/ADR-003-agent-sdk-pydantic-ai.md                                           | Accepted | v0.5      | Agent SDK (pydantic-ai)                     | -
adr-004 | docs/architecture/adr/ADR-004-vector-store-chromadb-in-process.md                                | Accepted | v0.4      | Vector Store - ChromaDB In-Process          | -
adr-005 | docs/architecture/adr/ADR-005-deferred-tooling-evaluation.md                                     | Proposed | v0.1      | Deferred Tooling Evaluation                 | -
adr-006 | docs/architecture/adr/ADR-006-classical-ml-intent-baseline.md                                    | Accepted | v0.3      | Classical ML Intent Baseline                | -
adr-007 | docs/architecture/adr/ADR-007-group-aware-synthetic-evaluation.md                                | Accepted | v0.3      | Group-Aware Synthetic Evaluation             | -
adr-008 | docs/architecture/adr/ADR-008-local-retrieval-before-azure-ai-search.md                          | Accepted | v0.4      | Local Retrieval Before Azure AI Search      | -
adr-009 | docs/architecture/adr/ADR-009-hybrid-retrieval-with-rrf.md                                      | Accepted | v0.4      | Hybrid Retrieval with RRF                   | -
adr-010 | docs/architecture/adr/ADR-010-provider-agnostic-llm-boundary.md                                  | Accepted | v0.5      | Provider-Agnostic LLM Boundary              | -
adr-011 | docs/architecture/adr/ADR-011-grounded-generation-citation-validation.md                         | Accepted | v0.5      | Grounded Generation + Citation Validation   | -
adr-012 | docs/architecture/adr/ADR-012-single-agent-orchestrator-read-only-tools.md                      | Accepted | v0.6      | Single Agent Orchestrator + Read-Only Tools | -
adr-013 | docs/architecture/adr/ADR-013-deterministic-tool-authorization-boundary.md                       | Accepted | v0.6      | Deterministic Tool Authorization             | -
adr-014 | docs/architecture/adr/ADR-014-local-mcp-boundary-stdio.md                                        | Accepted | v0.7      | Local MCP Boundary (stdio)                  | -
adr-015 | docs/architecture/adr/ADR-015-mandatory-hitl-for-banking-writes.md                               | Accepted | v0.7      | Mandatory HITL for Banking Writes           | -
adr-016 | docs/architecture/adr/ADR-016-idempotent-banking-writes-before-retries.md                        | Accepted | v0.8      | Idempotent Banking Writes Before Retries    | -
adr-017 | docs/architecture/adr/ADR-017-transactional-outbox-and-messaging-abstraction.md                  | Accepted | v0.8      | Transactional Outbox + Messaging Abstraction| -
adr-018 | docs/architecture/adr/ADR-018-circuit-breaker-policy-for-external-dependencies.md               | Accepted | v0.8      | Circuit Breaker Policy                      | -
adr-019 | docs/architecture/adr/ADR-019-opentelemetry-vendor-neutral-observability.md                     | Accepted | v0.9      | OpenTelemetry Vendor-Neutral Observability  | -
adr-020 | docs/architecture/adr/ADR-020-structured-audit-event-model.md                                    | Accepted | v0.9      | Structured Audit Event Model                | -
adr-021 | docs/architecture/adr/ADR-021-hotl-supervisory-kill-switch-for-writes.md                         | Accepted | v0.9      | HOTL Supervisory Kill-Switch                | -
adr-022 | docs/architecture/adr/ADR-022-layered-test-strategy-and-quality-gates.md                         | Accepted*| v0.10     | Layered Test Strategy + Quality Gates       | -
adr-023 | docs/architecture/adr/ADR-023-contract-first-compatibility-protection.md (canonical, 2026-08-31)| Accepted | v0.10     | Contract-First Compatibility Protection     | -
adr-024 | docs/architecture/adr/ADR-024-ci-security-gates-before-deployment.md (canonical, 2026-08-31)  | Accepted | v0.10     | CI Security Gates Before Deployment         | -
adr-025 | docs/architecture/adr/ADR-025-local-containers-and-service-bus-adapter.md                       | Accepted | v0.11     | Local Containers + Service Bus Adapter      | -
adr-026 | docs/architecture/adr/ADR-026-azure-service-bus-emulator-messaging-adapter.md                   | Accepted | v0.11     | Azure Service Bus Emulator Messaging Adapter| -
adr-027 | docs/architecture/adr/ADR-027-container-platform-decision-container-apps-vs-aks.md              | Accepted | v0.11     | ACA First, AKS Deferred                     | -
adr-028 | docs/architecture/adr/ADR-028-azure-functions-event-grid-local-serverless-foundation.md         | Accepted | v0.13     | Azure Functions + Event Grid Local          | -
adr-029 | docs/architecture/adr/ADR-029-configuration-secrets-identity-boundary.md                        | Accepted | v0.14     | Configuration/Secrets/Identity Boundary     | -
adr-030 | docs/architecture/adr/ADR-030-local-ai-evaluation-and-mlops-foundation.md                       | Accepted | v0.15     | Local AI Evaluation + MLOps Foundation      | -
```

Note: ADR-023 and ADR-024 each have a companion draft file (per docs/architecture/adr/README.md section 2). Canonical = dated file. ADR-022 has no frontmatter status line but is formally Accepted per the README.

### Matriz Exhaustiva de los 30 ADRs (Context, Decision, Discarded Alternatives & Consequences)

| ADR ID | Título y Milestone | Estado | Problema y Contexto | Decisión Canónica | Alternativas Descartadas | Consecuencias y Trade-offs |
|---|---|---|---|---|---|---|
| **ADR-001** | Modular Monolith First (`v0.2`) | Accepted | La arquitectura inicial debe permitir desacoplamiento funcional sin la sobrecarga de red, serialización y orquestación de clústeres. | Monolito modular con paquetes Python desacoplados (`mock-core-banking`, `ai/agent`, `ai/rag`) antes de introducir microservicios. | Microservicios tempranos basados en gRPC o Kubernetes. | Refactorización y tests locales inmediatos sin latencia de red; la futura migración distribuida se difiere a la fase cloud. |
| **ADR-002** | Local SQLite before PostgreSQL (`v0.2`) | Accepted | Se requiere un datastore relacional ligero y determinista para desarrollo local y ejecución rápida de suites de tests unitarios/integración. | Utilizar SQLite en memoria y basado en archivo local gestionado mediante SQLAlchemy ORM como base relacional inicial. | Exigir contenedor PostgreSQL desde el día uno (`v0.2`). | Pruebas unitarias en milisegundos sin dependencias externas de SO; PostgreSQL se difiere a `v0.12` para capacidades de `pgvector`. |
| **ADR-003** | Agent SDK Choice: Pydantic AI (`v0.5`) | Accepted | Selección de un SDK de agentes que ofrezca tipado estricto, neutralidad de proveedor y mínima sobrecarga de abstracción. | Evaluar y adoptar Pydantic AI como arnés de orquestación tipado, desacoplado de proveedores propietarios de LLM. | LangChain (demasiada complejidad y abstracciones opacas), CrewAI / AutoGen (orientados a multi-agente no supervisado). | Tipado estricto con modelos Pydantic v2; menor deuda técnica al mantener el control de las transiciones de estado. |
| **ADR-004** | Vector Store: ChromaDB In-Process (`v0.4`) | Accepted | Necesidad de un almacén vectorial local para validar el pipeline de RAG y retrieval semántico en fases tempranas. | Integrar ChromaDB en proceso como baseline vectorial local sin infraestructura adicional. | Servicios vectoriales gestionados en cloud (Azure AI Search, Pinecone, Qdrant Cloud). | Cero costo cloud y portabilidad total en desarrollo; sustituido de forma transparente por `pgvector` en `v0.12`. |
| **ADR-005** | Deferred Tooling Evaluation (`v0.1`) | Proposed | Evaluación de servidores MCP y extensiones LSP antes de incorporarlos al entorno de desarrollo del agente. | Mantener servidores MCP esenciales (`filesystem`, `sequential-thinking`), posponer LSPs pesados y dejar `context7` inerte. | Auto-instalar docenas de servidores MCP sin justificación de competencia o caso de uso. | Mínima huella de memoria y arranque instantáneo; servidores diferidos se activan solo bajo demanda explícita. |
| **ADR-006** | Classical ML Intent Baseline (`v0.3`) | Accepted | Invocar un LLM para enrutar cada consulta de usuario genera latencias inaceptables (>1000ms) y costos innecesarios. | Implementar un clasificador de intención clásico basado en TF-IDF + Logistic Regression con scikit-learn (<5ms). | Llamar a LLMs para resolver clasificaciones de intención en cada turno. | Latencia sub-milisegundo en CPU local; requiere re-entrenamiento declarativo si se expande la taxonomía de intents. |
| **ADR-007** | Group-Aware Synthetic Evaluation (`v0.3`) | Accepted | La generación sintética de datos a partir de plantillas introduce fuga de datos (data leakage) entre conjuntos de train y test. | Evaluar el clasificador mediante validación cruzada agrupada (`StratifiedGroupKFold`) sobre `template_group_id`. | División aleatoria tradicional (train_test_split simple). | Métricas de generalización científicamente rigurosas y honestas; previene sobreajuste a estructuras sintácticas repetitivas. |
| **ADR-008** | Local Retrieval before Azure AI Search (`v0.4`) | Accepted | Validar algoritmos de búsqueda y métricas de recuperación sin incurrir en latencia de red ni costos de suscripción cloud. | Construir el sustrato de recuperación combinando búsqueda léxica (BM25) y densa (SVD) localmente en Python. | Despliegue prematuro de Azure AI Search (antes Cognitive Search). | Entorno de experimentación 100% reproducible y desconectado; la interfaz queda lista para adaptación cloud futura. |
| **ADR-009** | Hybrid Retrieval via Reciprocal Rank Fusion (`v0.4`) | Accepted | La búsqueda puramente léxica ignora sinónimos; la búsqueda puramente densa falla en códigos exactos de préstamo (ej. `LOAN-0001`). | Fusión de rangos recíprocos (RRF) combinando scores léxicos y densos con constante de suavizado congelada $k = 60$. | Combinación lineal ponderada ($\alpha \cdot S_{\text{lex}} + (1-\alpha) \cdot S_{\text{dense}}$) o modelos de re-ranking pesados. | Recall@5 se eleva a 0.83 y nDCG@5 a 0.81; ordenamiento balanceado sin necesidad de normalización de puntajes dispares. |
| **ADR-010** | Provider-Agnostic LLM Boundary (`v0.5`) | Accepted | Riesgo de acoplamiento rígido a las APIs privativas de un único proveedor de modelos fundacionales. | Crear una interfaz neutral para peticiones LLM compatible con OpenAI, Azure OpenAI, Anthropic, Google y Foundry Local. | Acoplar el orquestador directamente al cliente SDK oficial de un proveedor específico. | Capacidad de conmutar entre Foundry Local (`phi-4-mini`) en local y Azure OpenAI en nube modificando solo configuración. |
| **ADR-011** | Grounded Generation + Citation Validation (`v0.5`) | Accepted | Las alucinaciones en respuestas bancarias violan normativas de protección al consumidor y confianza financiera. | Inyección de contexto activo autorizado y validación estricta post-generación de citas obligatorias (`[chunk_id]`). | Permitir respuestas libres generadas a partir del conocimiento paramétrico no verificado del LLM. | Precisión de citas del 100% y tasa de abstención del 100% ante lagunas de información o conocimiento fuera de dominio. |
| **ADR-012** | Single Agent Orchestrator + Read-Only Tools (`v0.6`) | Accepted | Los flujos multi-agente complejos y enjambres autónomos presentan comportamientos no deterministas y difíciles de auditar. | Orquestador de agente único con control determinista de turnos (máx 3 rounds) y conjunto inicial de tools de solo lectura. | Frameworks multi-agente con agentes concurrentes negociando entre sí (AutoGen, CrewAI). | Trazabilidad predecible, límites de ejecución estrictos y mitigación de bucles infinitos de razonamiento. |
| **ADR-013** | Deterministic Tool Authorization Boundary (`v0.6`) | Accepted | Las técnicas de prompt injection pueden forzar al LLM a consultar cuentas o préstamos de terceros (vulnerabilidad IDOR). | Aplicar validación de propiedad de datos fuera del prompt, inyectando de forma determinista el `customer_id` autenticado. | Confiar en que el LLM respetará las instrucciones del system prompt para no revelar datos de otros usuarios. | Protección absoluta contra IDOR; los argumentos de identificación de cliente son inmutables por la entrada del usuario. |
| **ADR-014** | Local Model Context Protocol (stdio) (`v0.7`) | Accepted | Necesidad de estandarizar la invocación de herramientas entre el modelo y el backend con aislamiento de procesos. | Implementar el protocolo abierto MCP (Anthropic SDK `mcp==2.1.1`) sobre transporte estándar de entrada/salida (stdio). | APIs REST propietarias para cada herramienta o llamadas a funciones internas acopladas en memoria. | Estandarización de capacidades, aislamiento de fallos a nivel de subproceso y compatibilidad con el ecosistema MCP. |
| **ADR-015** | Mandatory HITL for Banking Writes (`v0.7`) | Accepted | Las operaciones de mutación de estado financiero no deben ser ejecutadas de forma autónoma por un modelo de IA. | Máquina de estados Human-in-the-Loop formal: propuesta generada, aprobación humana explícita y verificación de hash. | Ejecución autónoma de escrituras basada en umbrales de confianza del modelo probabilístico. | Cero escrituras no autorizadas; el usuario o el oficial bancario retiene el control absoluto de cada mutación. |
| **ADR-016** | Idempotent Banking Writes Before Retries (`v0.8`) | Accepted | Las fallas transitorias de red pueden provocar reintentos automáticos que dupliquen transacciones y solicitudes bancarias. | Exigir `idempotency_key` suministrada por el cliente y registrarla atómicamente antes de procesar cualquier mutación. | Activar políticas de reintento automático sobre endpoints que no cuenten con verificación de idempotencia. | Resiliencia garantizada; peticiones duplicadas retornan inmediatamente la respuesta original almacenada. |
| **ADR-017** | Transactional Outbox + Messaging Abstraction (`v0.8`) | Accepted | La publicación directa en un bus de mensajería durante una transacción HTTP genera riesgo de dual-write y estados inconsistentes. | Patrón Transactional Outbox: persistir entidad y evento en la misma transacción ACID; un `OutboxProcessor` drena al bus. | Escribir en base de datos y publicar simultáneamente en Azure Service Bus mediante llamadas desacopladas. | Cero pérdida de eventos; consistencia eventual garantizada con semántica de entrega al menos una vez (*at-least-once*). |
| **ADR-018** | Circuit Breaker Policy for External Dependencies (`v0.8`) | Accepted | Dependencias externas caídas o con alta latencia pueden agotar los hilos del orquestador y causar caídas en cascada. | Implementar un Circuit Breaker de tres estados (`CLOSED`, `OPEN`, `HALF_OPEN`) con umbral de fallos y tiempo de recuperación. | Reintentos infinitos o capturas genéricas de excepciones (`try/except: pass`) sin protección de recursos. | Aislamiento inmediato de servicios degradados (*fast-fail*); protección de recursos del servidor y recuperación autónoma. |
| **ADR-019** | OpenTelemetry Vendor-Neutral Observability (`v0.9`) | Accepted | El monitoreo distribuido en arquitecturas bancarias no debe acoplarse a librerías propietarias de un único proveedor cloud. | Adoptar el estándar abierto OpenTelemetry para métricas y trazas, propagando identificadores W3C `traceparent`. | Integrar directamente SDKs privativos como Datadog, New Relic o Azure Application Insights nativo. | Portabilidad total de telemetría; correlación unificada de trazas desde el prompt del CLI hasta la base de datos. |
| **ADR-020** | Structured Audit Event Model (`v0.9`) | Accepted | Los requisitos regulatorios y de cumplimiento bancario exigen un registro inmutable y auditable de cada decisión de la IA. | Modelo de eventos de auditoría estructurado en formato JSON, persistido en una tabla append-only (WORM) en SQLite/SQL. | Registros de texto plano en archivos de log tradicionales no estructurados y de difícil análisis. | Trazabilidad forense de no-repudio; permite reconstruir con exactitud qué herramienta, usuario y LLM intervinieron. |
| **ADR-021** | HOTL Supervisory Kill-Switch for Writes (`v0.9`) | Accepted | En contingencias operativas o detección de anomalías sistémicas, los administradores requieren detener mutaciones al instante. | Supervisor Human-on-the-Loop (`HOTLSupervisor`) con interruptor de parada maestro en memoria y registro auditado. | Detener contenedores físicamente o modificar reglas de firewall de red durante una emergencia. | Desactivación inmediata de escrituras en milisegundos sin reiniciar el servicio ni interrumpir consultas de lectura. |
| **ADR-022** | Layered Test Strategy + Quality Gates (`v0.10`) | Accepted | La ejecución de suites de tests integrales pesadas en cada iteración ralentiza el feedback de los ingenieros. | Pirámide de calidad en 3 capas: Fast Gate (<30s: unitarios, lint, contratos), Integration Gate (<2m) y E2E Gate (<5m). | Ejecutar todos los tests E2E y de simulación de contenedores de forma monolítica en cada cambio menor. | Ciclos de desarrollo locales ultra-rápidos manteniendo defensas férreas antes de fusionar código a la rama principal. |
| **ADR-023** | Contract-First Compatibility Protection (`v0.10`) | Accepted | Cambios descontrolados en los esquemas de datos rompen la interoperabilidad entre microservicios, eventos y herramientas. | Adopción del estándar JSON Schema Draft 2020-12 para todos los contratos de API, herramientas y eventos de outbox. | Enfoque *code-first* donde el código Python genera dinámicamente esquemas sin control previo de compatibilidad. | Detección preventiva de incompatibilidades hacia atrás en CI; validación estricta de payloads en runtime. |
| **ADR-024** | CI Security Gates Before Deployment (`v0.10`) | Accepted | Vulnerabilidades en dependencias o credenciales expuestas representan el mayor riesgo de seguridad antes de producción. | Pipeline de seguridad shift-left obligatorio: análisis SAST (Bandit), auditoría SCA (pip-audit), SBOM (CycloneDX) y escaneo de secretos. | Realizar auditorías de seguridad manuales de forma periódica o únicamente antes del paso a producción. | Bloqueo automatizado de PRs con vulnerabilidades conocidas o claves expuestas antes de integrarse a la rama principal. |
| **ADR-025** | Local Containers + Service Bus Adapter (`v0.11`) | Accepted | Desarrollar contra mensajería empresarial sin requerir costos de suscripción cloud ni conexión permanente a internet. | Entorno local en Docker Compose con el contenedor oficial Microsoft Azure Service Bus Emulator. | Utilizar RabbitMQ local o depender exclusivamente de una suscripción activa de Azure en la nube. | Simulación fidedigna de colas y tópicos AMQP idéntica a la nube de producción sin costo económico. |
| **ADR-026** | Azure Service Bus Emulator Messaging Adapter (`v0.11`) | Accepted | Integrar el emulador de Service Bus sin que el código de dominio dependa de la librería específica de Azure. | Implementar `AzureServiceBusAdapter` bajo el protocolo abstracto `MessageBus`, conmutando transparentemente a `LocalMessageBus`. | Invocar directamente métodos del SDK de Azure Service Bus a lo largo de toda la lógica de negocio. | Desacoplamiento arquitectónico limpio; posibilidad de ejecutar en memoria en tests unitarios y con AMQP en E2E. |
| **ADR-027** | Container Platform: ACA First vs. AKS Deferred (`v0.11`) | Accepted | Determinar la plataforma de cómputo en contenedores cloud balanceando complejidad operativa y capacidades de auto-escala. | Seleccionar Azure Container Apps (ACA) con KEDA y Dapr para la primera fase cloud; diferir Azure Kubernetes Service (AKS). | Desplegar clústeres gestionados AKS desde la fase inicial de migración cloud. | Menor costo operativo, escala a cero nativa y mantenimiento mínimo de clústeres; AKS se reserva para topologías avanzadas. |
| **ADR-028** | Azure Functions + Event Grid Local Serverless (`v0.13`) | Accepted | Los consumidores de eventos de mensajería deben procesarse bajo un modelo serverless elástico y basado en eventos. | Adoptar el modelo de programación Azure Functions Python v2 con triggers HTTP / Event Grid sobre CloudEvents 1.0. | Mantener procesos demonio continuos (*long-running workers*) consumiendo colas de forma síncrona. | Elasticidad nativa en cloud y bajo costo por ejecución; se documenta limitación de entorno Windows para contenedores Linux. |
| **ADR-029** | Configuration, Secrets & Identity Boundary (`v0.14`) | Accepted | Gestión unificada de configuraciones y secretos previniendo la dispersión de variables de entorno y archivos no cifrados. | Integrar Azure App Configuration y referencias de Key Vault, utilizando `DefaultAzureCredential` con fallback local. | Almacenar secretos en texto plano en archivos `.env` o quemar cadenas de conexión en el código. | Cero secretos en repositorios Git; transición fluida a Managed Identities (Entra ID) al desplegar en infraestructura cloud. |
| **ADR-030** | Local AI Evaluation & MLOps Foundation (`v0.15`) | Accepted | La evaluación de modelos de lenguaje y detección de drift debe ser sistemática, auditable y libre de servicios SaaS de pago. | Arquetipo de evaluación local con MLflow sobre SQLite (`reports/mlruns/`), tests estadísticos de McNemar y métricas PSI/JSD. | Evaluación visual manual no estructurada o dependencia exclusiva de suites comerciales de evaluación cloud. | Rigor científico reproducible; control formal de versiones de prompts, datasets congelados y criterios de promoción. |

---

## A.16 Architectural Themes Across ADRs (machine-extractable)

```
theme.id  | theme.name                                  | supporting_adrs
----------+---------------------------------------------+-----------------------------------------------
T1        | Determinism over LLM judgement              | 011, 013, 014, 015, 030
T2        | Local-first before cloud; vendor-neutral   | 002, 004, 008, 010, 017, 019, 025, 026, 027, 028, 029, 030
T3        | HITL + HOTL layered human control          | 015, 020, 021
T4        | Reliability primitive stack                 | 016, 017, 018, 019
T5        | Contract-first versioned boundaries         | 014, 023, 028
T6        | Shift-left security + test pyramid          | 022, 024
T7        | Modular monolith + single agent + deferral  | 001, 003, 005, 006, 007, 009, 012, 027
```

## A.17 MCP Server Smoke Evidence (verified 2026-09-02)

Source: C:\aegisbank-ai-platform-ai-env\.intelligence\smoke\mcp-smoke.json.

```
mcp.name                 | version          | ok   | tool_count | initMs | listMs
-------------------------+------------------+------+------------+--------+--------
sequential-thinking      | 0.2.0            | true |          1 |    499 |     17
filesystem               | 0.2.0            | true |         14 |    441 |     21
git                      | 2.15.3           | true |         28 |    537 |     80
everything               | 2.0.0            | true |         13 |    475 |     11
context7                 | 4.0.4            | true |          2 |   4014 |      7   (inert: CONTEXT7_API_KEY placeholder)
```

## A.18 Frozen Holdouts (SHA-256 pinned, do-not-modify)

```
asset.path                                                              | sha256                                                                 | size_bytes | role
-----------------------------------------------------------------------+------------------------------------------------------------------------+------------+----------------------------------------
ml/intent-classifier/data/intent_dataset.jsonl                          | db250b5993e892610d29a2cc53bdafcff08d085df29deecf9a53515a13308664       | ~38 KB     | intent classification v0.3 (500 records)
ai/rag/data/corpus-manifest.json                                         | (computed at runtime; pinned per-corpus-document)                       |  ~2 KB     | 12-doc synthetic banking corpus manifest
ai/rag/data/queries.jsonl                                                | (frozen v0.4; 18 queries x 4 categories)                               |  ~1 KB     | retrieval eval queries
ai/rag/data/qrels.json                                                   | (frozen v0.4)                                                          |  ~6 KB     | retrieval ground truth
data/evaluation/v015_eval_suite.jsonl                                    | (frozen v0.15; 35 multi-turn traces)                                   | ~12 KB     | agent evaluation holdout
mlruns/mlflow.db (SQLite, local)                                         | n/a                                                                    | varies     | MLflow experiment tracking backend
services/mock-core-banking/data/local/aegisbank-dev.db                   | n/a                                                                    | varies     | synthetic seed data store
data/sessions.db                                                         | n/a                                                                    | varies     | agent durable sessions store
```

## A.19 CI Workflow Structure (.github/workflows/ci.yml)

```
workflow.name       : AegisBank CI Pipeline
workflow.trigger     : push to master|main, PR to master|main
workflow.permissions : contents: read
workflow.concurrency : group=${{github.workflow}}-${{github.ref}}, cancel-in-progress=true

job.static-analysis        : ubuntu-latest | actions/checkout@v4 + setup-python@v5 + ruff check + ruff format --check + compileall
job.test-suite (needs SA)  : ubuntu-latest | pip install -e 4 packages + pytest per service + --cov on agent
job.devsecops (needs SA)   : ubuntu-latest | bandit -ll -r ai/agent ai/rag ml services | pip-audit | CycloneDX SBOM | secret scan via quality_gate.py --gate-secrets-only

workflow.status : CI-CONFIGURED / RUNNER-PENDING (syntax validated; not yet executed on real GitHub runner)
```

## A.20 Drift and Known Caveats (machine-readable)

```
caveat.id  | severity | description                                                                                                  | mitigation_status
-----------+----------+--------------------------------------------------------------------------------------------------------------+-------------------------
C1         | blocker  | Windows Functions worker fails: cygrpc.cp314-win_amd64.pyd + Win32 MAX_PATH (Error 206)                       | RESOLVED via Linux container mcr.microsoft.com/azure-functions/python:4-python3.14
C2         | blocker  | 12 infra tests skipped when Docker daemon not running                                                          | RE-RUN with Docker desktop active
C3         | inert    | context7 MCP API key is placeholder; opencode logs "Request timed out"                                        | ROTATE user key via secret store
C4         | partial  | v0.15 statistical superiority NOT established (McNemar p=0.248213, CI [0.0000, 0.1714])                       | PROMOTED under safety policy, NOT under statistical rigor
C5         | warning  | ai/agent unstaged: agent.py, knowledge_routing.py, test_durable_session_routing.py                            | working-tree uncommitted changes per SessionGuard discipline
C6         | warning  | ai-102 retired December 2025; repo docs still reference AI-103/AI-102 as alignment target                       | FOLLOW-UP: cross-check docs/learning + docs/career against current MS cert catalog
C7         | warning  | foundry_local uses older CLI discovery (subprocess) vs official foundry-local-sdk package                      | LAB-COVERED either way; migration optional, not required
C8         | warning  | 100% test pass claim is misleading without context (12 skipped infra tests + Windows Functions BLOCKED)         | HONEST claim: 248 agent non-infra + 46 infra passed + 12 skipped; BLOCKED on Windows
C9         | warning  | intent classifier "near-perfect" but synthetic + template-generated (warned in ml/intent-classifier/README.md)  | LAB-COVERED; not evidence on real users
C10        | warning  | mssql + servicebus-emulator images use floating "latest" tag (no digest pin)                                  | KNOWN GAP; promote to pinned in future milestone
```

## A.21 MCP + Skills + LSP Map (for navigation)

```
server.name              | type     | version  | scope                          | tools_count | source
-------------------------+----------+----------+--------------------------------+-------------+---------------------------------
sequential-thinking      | mcp      | 0.2.0    | stdio                          |           1 | .opencode/node_modules/@modelcontextprotocol/server-sequential-thinking
filesystem               | mcp      | 0.2.0    | C:/aegisbank-ai-platform       |          14 | .opencode/node_modules/@modelcontextprotocol/server-filesystem
git                      | mcp      | 2.15.3   | C:/aegisbank-ai-platform       |          28 | .opencode/node_modules/@cyanheads/git-mcp-server
everything               | mcp      | 2.0.0    | smoke-test target              |          13 | .opencode/node_modules/@modelcontextprotocol/server-everything
context7                 | mcp      | 4.0.4    | live library docs              |           2 | .opencode/node_modules/@upstash/context7-mcp (inert)
pyright                  | lsp      | 1.1.413  | .py, .pyi                      | n/a        | .opencode/node_modules/pyright

skill.name               | location                                                                 | install_via
-------------------------+--------------------------------------------------------------------------+----------------------------------------------
e2e-testing-patterns     | C:\Users\VegaValverde\.agents\skills\e2e-testing-patterns\SKILL.md      | pnpm dlx skills@latest add wshobson/agents@e2e-testing-patterns -g
context7-mcp             | C:\Users\VegaValverde\.agents\skills\context7-mcp\SKILL.md             | (built-in)
find-docs                | C:\Users\VegaValverde\.agents\skills\find-docs\SKILL.md                | (built-in)
find-skills              | C:\Users\VegaValverde\.agents\skills\find-skills\SKILL.md              | (built-in)
loop                     | C:\Users\VegaValverde\.agents\skills\loop\SKILL.md                     | (built-in)
skill-creator            | C:\Users\VegaValverde\.agents\skills\skill-creator\SKILL.md            | (built-in)
speckit-*                | (6 speckit skills in .claude/skills and .agents/skills)               | (built-in)
customize-opencode       | (built-in via opencode CLI)                                            | (built-in)
```

## A.22 Retrieval Policy (.ai-env/retrieval-policy.json)

```
intent.exact        : ripgrep | git grep fallback
intent.symbol       : lsp (pyright)
intent.architecture : lsp (re-points codebase-memory stub to pyright LSP until real provider ships)
intent.knowledge    : filesystem | paths = AGENTS.md | .ai-env/** | docs/** | specs/** | docs/architecture/adr/** | README* | CHANGELOG* | PROGRESS.md | MIGRATION_CONTROL* | HANDOFF_NEXT_RUN*
intent.semantic     : disabled (default)
```

## A.23 Permanent Rules (verbatim, 13 rules)

```
R01  : Modify project files only inside C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform
R02  : Use only synthetic, reproducible data. Never real personal, banking, or confidential data.
R03  : Work local first, then Docker, CI, and Azure in the approved roadmap order.
R04  : Do not create paid Azure resources or run deployments without explicit approval.
R05  : Start with one agent and a modular monolith. No early microservices, AKS, or multi-agent flows.
R06  : The LLM may interpret and propose; deterministic identity, policy, authorization, validation, and business rules decide.
R07  : Require explicit HITL approval for every state-changing operation.
R08  : Never commit secrets. Keep .env ignored; publish placeholders only in .env.example when needed.
R09  : Minimize and redact sensitive content in logs, prompts, audit records, and telemetry.
R10  : Add a dependency or technology only when it resolves a requirement, reduces a risk, or demonstrates a defined competency.
R11  : Keep changes within the authorized milestone. Scope expansion requires an explicit decision.
R12  : Preserve pre-existing OpenCode bootstrap artifacts unless a task explicitly targets them.
R13  : Promote only verified, durable project knowledge to .intelligence/.
```

## A.24 Quality Rules (verbatim, 7 rules)

```
Q01  : Add tests appropriate to every implementation change.
Q02  : Separate unit, integration, contract, end-to-end, and AI evaluation concerns.
Q03  : Validate actual behavior before reporting PASS; never substitute expected behavior for executed evidence.
Q04  : Writes must be idempotent before any retry policy is enabled.
Q05  : Use bounded retries only for known transient failures and circuit breakers for persistent dependency failures.
Q06  : Propagate correlation and trace identifiers across every future execution boundary.
Q07  : Do not claim legal, regulatory, NIST, Microsoft, or banking certification/compliance.
```

## A.25 Maturity Tags (verbatim, project-defined claim taxonomy)

```
tag.LAB-COVERED              : Implemented, tested, verified completely in local lab with reproducible automated tests.
tag.TESTED-LOCAL             : Reproducibly executed against synthetic local components.
tag.LOCAL-LAB-PERFORMANCE-BASELINE : Local laboratory baseline measurement (e.g., 25-iteration p50/p95/p99).
tag.LOCAL-COVERED            : Variant: specifically local-only (e.g., LOCAL-APPCONFIG-COVERED, LOCAL-SECRETS-COVERED).
tag.CI-CONFIGURED            : Pipeline created syntactically but pending verifiable remote runner execution.
tag.RUNNER-PENDING           : Alias for CI-CONFIGURED emphasizing the runner-execution gap.
tag.PROD-PARTIAL             : Conceptually implemented locally; requires cloud services for production parity.
tag.CLOUD-PENDING            : Formally planned for future cloud deployment phases; no cloud execution claimed.
tag.SAFETY-DEFERRED          : Architectural decision to defer a technique to safeguard banking safety.
tag.PROD-UNPROVEN            : Production capacity, SLA, certification, regulatory conclusions intentionally outside evidence.
tag.STATISTICAL_SUPERIORITY_NOT_ESTABLISHED : McNemar or equivalent test failed to reject null at alpha=0.05.
tag.LOCAL-APPCONFIG-COVERED  : v0.14 App Config emulator verified.
tag.LOCAL-SECRETS-COVERED    : v0.14 SecretProvider local synthetic verified.
tag.CLOUD-APPCONFIG-PENDING  : v0.14 Azure App Config real pending.
tag.CLOUD-KEYVAULT-PENDING   : v0.14 Azure Key Vault real pending.
tag.MANAGED-IDENTITY-CLOUD-PENDING : v0.14 Managed Identity not reproducible locally.
tag.DEFAULT-AZURE-CREDENTIAL-LOCAL-COVERED : v0.14 DefaultAzureCredential documented with fallback to AzureCliCredential / EnvironmentCredential.
```

## A.26 Knowledge Sources for This Appendix

```
data.id  | source                                                                                            | fetched_via     | fetched_at
---------+---------------------------------------------------------------------------------------------------+-----------------+-----------------
D1       | 48 git commits                                                                                    | git MCP         | 2026-09-11
D2       | All 30 ADR files                                                                                   | filesystem      | 2026-09-11
D3       | ai/agent/pyproject.toml, ai/rag/pyproject.toml, mock-core-banking/pyproject.toml,
         | intent-classifier/pyproject.toml, functions/requirements.txt                                        | filesystem      | 2026-09-11
D4       | 10 contracts/*.schema.json                                                                         | filesystem      | 2026-09-11
D5       | 10 scripts/*.py function signatures                                                               | filesystem + grep | 2026-09-11
D6       | python file LOC inventory (top 30 by size)                                                         | filesystem + bash| 2026-09-11
D7       | Microsoft Learn AI-901 / AI-102-retired pages                                                     | webfetch        | 2026-09-11
D8       | github.com/microsoft/Foundry-Local README + raw README.md                                          | webfetch        | 2026-09-11
D9       | github.com/modelcontextprotocol/python-sdk raw README.md                                          | webfetch        | 2026-09-11
D10      | huggingface.co/microsoft/Phi-4-mini-instruct model card                                            | webfetch        | 2026-09-11
D11      | .intelligence/smoke/mcp-smoke.json (5 MCP servers)                                                | git MCP + FS    | 2026-09-02
```

---

# Appendix B - Footer / Verification Metadata

```
appendix.last_verified_against_repo : 2026-09-11
appendix.last_verified_commits      : 268df51 (master HEAD), 6e6002c (v1.0.2 docs), 668c0b2 (v1.0 evidence integrity)
appendix.last_verified_tags         : v1.0.0, v1.0.1
appendix.sources_verified_via       : git MCP (48 commits), filesystem (all paths), webfetch (4 sources)
appendix.format_intent              : LLM-optimized (dense tables, no narrative, every claim traceable)
appendix.lineage                    : docs/briefings/AEGISBANK-AI-PLATFORM-CHATGPT-BRIEFING.md
appendix.human_narrative_sections   : sections 1 through 28 of the main document
appendix.machine_precise_sections   : sections A.1 through A.26 of this appendix
appendix.language_note              : Per project rule: documentation default Spanish; technical identifiers (paths, class names, version strings, JSON keys) preserved verbatim in English. This applies to both human and machine sections.
```

---

# Appendix C - TL;DR for fast LLM ingestion (5 bullets)

```
T1. AegisBank AI Platform is a SINGLE-AUTHOR Python 3.14 educational/portfolio project (NOT a real bank) built as a modular monolith + single AgentOrchestrator + MCP stdio v2 + Foundry Local (phi-4-mini) + FastAPI mock-core-banking + transactional outbox + idempotency + circuit breaker + DLQ + Azure Functions Python v2 + Azure Service Bus emulator + pgvector + Cosmos DB emulator + Redis. Frozen at tags v1.0.0 (8393d88 baseline) and v1.0.1 (668c0b2 evidence-integrity corrective); documentation governance at v1.0.2.

T2. The 3 user capabilities are KNOWLEDGE (RAG over 12-doc Spanish banking corpus with citation + abstention), READ (4 banking tools filtered by session_customer_id ownership), WRITE (1 tool create_service_request gated by 3 layers: HOTL kill-switch + HITL state machine with SHA-256 payload binding + IdempotencyGuard). The 7-layer evaluation taxonomy covers Intent, Retrieval, Generation, Agent, Safety, System E2E, Performance with frozen SHA-256-pinned holdouts.

T3. Local-first / production-migratable = SQLite + in-process ChromaDB then pgvector container; Foundry Local 0.10.3 then Azure AI Foundry; docker-compose with 7 services + profiles (data/cosmos/redis/config/all) then Azure Container Apps (NOT AKS - AKS deferred to v1.1 per ADR-027). Migration boundary enforced by 10 JSON Schemas draft 2020-12 in contracts/ (OpenAPI, CloudEvents 1.0, outbox events, MCP tools, Cosmos items, etc.).

T4. Microsoft AI certification alignment (REQUIRES UPDATE due to Dec 2025 AI-102 retirement): AI-900 -> AI-901 (Azure AI Fundamentals, renamed April 2026, weights 40-45% Identify + 55-60% Implement with Foundry) is ACTIVE; AI-102 is RETIRED; AI-200 was a learning path (containers + Service Bus + ACA + data). Repo docs/requirements/MIBANCO-JOB-PROFILE-2026.md and docs/career/role-profile-images-and-gap-analysis.md still reference AI-103/AI-102 as targets - FOLLOW-UP REQUIRED.

T5. Known blockers / caveats: (a) Windows Functions worker BLOCKED (cygrpc + Win32 MAX_PATH) - use Linux container; (b) context7 MCP INERT (CONTEXT7_API_KEY placeholder); (c) Docker daemon not running = 12 infra tests SKIPPED; (d) v0.15 statistical superiority NOT ESTABLISHED (McNemar p=0.248213, CI [0.0000, 0.1714]) - promotion under safety policy NOT statistical rigor; (e) mssql + servicebus-emulator images use floating latest tag (no digest pin); (f) foundry_local uses older CLI discovery (subprocess) vs official foundry-local-sdk - LAB-COVERED either way; (g) intent classifier "near-perfect" holdout is synthetic + template-generated (warned in README).
```

End of briefing.


--- APPENDIX A END ---

---

# Appendix D — Final Implementation Addendum (added after codebase MCP cross-scope deployment)

> This addendum was added after the codebase MCP server was implemented in
> `.opencode/codebase-mcp/` and verified to cover the entire project
> (AI-env layer + inner `aegisbank-ai-platform/`) end-to-end.

## D.1 Codebase MCP server — operational status

```
package                : @aegisbank/codebase-mcp@0.1.0
path                   : C:/aegisbank-ai-platform/.opencode/codebase-mcp/
transport              : stdio (per permanent rule R12)
scope                  : CODEBASE_SCOPES=C:/aegisbank-ai-platform (default; single root that covers entire project)
index_path             : C:/aegisbank-ai-platform/.opencode/codebase-mcp/index.json
index_size             : 3.27 MB
schema_version         : 1.1 (rootMode=multi)
file_count             : 436
total_loc              : 59,853
incremental_rebuild_ms : 115
full_rebuild_ms        : 999
tools_count            : 8
```

## D.2 Verified discoverable files (cross-scope)

```
file                                                                          | size  | LOC
------------------------------------------------------------------------------+-------+------
aegisbank-ai-platform/AGENTS.md                                              | 13158 | 279
aegisbank-ai-platform/opencode.json                                          |  6604 | 184
aegisbank-ai-platform/README.md                                              |  6959 | 147
aegisbank-ai-platform/aegisbank-ai-platform/README.md                         |  7621 | 122
aegisbank-ai-platform/aegisbank-ai-platform/ai/agent/src/.../agent.py          | 56636 | 1213
aegisbank-ai-platform/aegisbank-ai-platform/ai/rag/src/.../foundry_local.py    |  4428 |  146
aegisbank-ai-platform/aegisbank-ai-platform/services/mock-core-banking/...    |  1999 |   57
aegisbank-ai-platform/aegisbank-ai-platform/docs/architecture/CANONICAL-...  | 10000 |   48
aegisbank-ai-platform/aegisbank-ai-platform/contracts/core-banking-...       |  1417 |   52
aegisbank-ai-platform/.opencode/codebase-mcp/src/server.js                    |  9645 |  304
aegisbank-ai-platform/.intelligence/codebase-mcp-inventory.json               |  2905 |   71  (promoted durable knowledge)
```

## D.3 Durable knowledge promoted to .intelligence/

```
.intelligence/
├── README.md
├── graph.jsonl
├── index.json
├── manifest.json
├── smoke/
│   └── mcp-smoke.json  (6 servers, 64 tools, 5 OK + 1 context7 timeout)
└── codebase-mcp-inventory.json  (NEW — durable inventory of codebase MCP state)
```

The `.intelligence/codebase-mcp-inventory.json` is consumed by:
- Future AI sessions opening this project for the first time
- The retrieval-policy `architecture` intent (replaces the codebase-memory stub)
- The codebase MCP server itself (re-reads on startup for cross-validation)

## D.4 Final smoke status (2026-09-11T18:42:35Z)

```
server               | tools | ok   | notes
--------------------+-------+------+------------------------------------------
sequential-thinking  |     1 | true |
filesystem           |    14 | true |
git                  |    28 | true |
everything           |    13 | true |
context7             |     2 | false| upstream timeout (placeholder API key)
codebase             |     8 | true | multi-scope (entire project)
--------------------+-------+------+------------------------------------------
total                |    66 | 5/6  | 100% of project-owned servers OK
```

## D.5 What changed vs the original briefing

The briefing (sections 1-28 + appendices A-C) describes AegisBank at v1.0.1
with `codebase-memory` as a **stub** re-pointed to pyright LSP. After this
addendum:

| Before | After |
|--------|-------|
| `codebase-memory` is a stub | `codebase-mcp` (real provider, 8 tools) |
| pyright-only symbol lookup | pyright + lexical search + symbol + outline + dependents + overview |
| Inner repo only | **Whole project**: AI-env layer + inner repo (multi-scope) |
| No project navigation map | `codebase_overview` returns top-level tree + 24 entry-points |
| No reverse dependency graph | `codebase_list_dependents` for impact analysis |
| No file inventory | `codebase_find_file` + `codebase_stats` |
| Multi-scope stub | Multi-scope schema v1.1 with `rootMode` + `scopes[]` + `perScopeStats[]` |

## D.6 Honest claim

This deployment is `LAB-COVERED`. The codebase MCP server is:

- locally installed and runnable (8 tools, stdio transport)
- exercised by `.opencode/scripts/smoke-mcp.mjs` (5/6 servers OK)
- cross-validated against real queries via `scripts/verify-and-use.mjs`
- documented in `AGENTS.md`, `.opencode/codebase-mcp/README.md`, and this briefing

It is **NOT**:
- deployed to any cloud environment
- production-scalable
- multi-machine-consistent
- Microsoft or banking certified

End of addendum.
