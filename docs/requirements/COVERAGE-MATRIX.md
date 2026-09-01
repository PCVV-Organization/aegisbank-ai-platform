# AegisBank — Matriz de Cobertura frente al Perfil Mibanco 2026

Este documento mapea cada competencia y requisito técnico exigido en los perfiles de Mibanco frente a la evidencia verificable construida en AegisBank AI Platform.

* **Categorías de Estado:**
  * **`LAB-COVERED`**: Implementado, probado y verificado completamente en el entorno de laboratorio local con tests reproducibles.
  * **`CI-CONFIGURED` / `RUNNER-PENDING`**: Pipeline o configuración automatizada creada y validada sintácticamente, pero pendiente de ejecución verificable en un runner remoto (e.g. GitHub Actions).
  * **`PROD-PARTIAL`**: Implementado conceptualmente y funcional en laboratorio, pero requiere componentes distribuidos en la nube (Kubernetes, Azure Service Bus, Cloud WORM) para producción bancaria.
  * **`CLOUD-PENDING`**: Planificado para hitos de nube e industrialización (v0.11+).

---

## 1. Conteo Oficial de Pruebas Automatizadas del Repositorio

| Paquete del Repositorio | Cantidad de Pruebas | Estado |
|---|---|---|
| `ai/agent` (Agente, Tools, MCP, HITL, Reliability, Observability, Knowledge Routing, Banking Routing, Contracts, E2E, Session Guard, Container & Service Bus Acceptance, Kubernetes Acceptance, Cosmos DB NoSQL & Change Feed Acceptance, Grounded Response Consistency & Provenance) | **262 tests** | PASS |
| `ai/rag` (Chunking, Retrieval Léxico/Denso/RRF, Grounding, Evaluaciones, PostgreSQL + pgvector Acceptance) | **69 tests** | PASS |
| `ml/intent-classifier` (Dataset sintético, TF-IDF, Logistic Regression) | **17 tests** | PASS |
| `services/mock-core-banking` (Entidades, Restricciones, Repositorios, Outbox, OpenAPI Contracts) | **58 tests** | PASS |
| **TOTAL GENERAL DEL REPOSITORIO** | **406 tests** | **100% PASS** |

---

## 2. Matriz de Competencias y Estado

| Área / Competencia | Estado de Madurez | Hito de Introducción | Evidencia Verificable en Código |
|---|---|---|---|
| **Estrategia de Prompting y Versionado** | `LAB-COVERED` | v0.5 / v0.6 / v0.7 | Prompts JSON inmutables (`rag-answer-v001`, `agent-system-v002`), esquemas JSON estrictos. |
| **Evaluación y QA de LLM** | `LAB-COVERED` | v0.5 / v0.6 | Datasets held-out congelados, métricas cuantitativas (Groundedness, Citation Validity, Selection Accuracy). |
| **RAG / Base de Conocimiento** | `LAB-COVERED` | v0.4 / v0.5 | Chunking canónico, retrieval híbrido RRF (k=60), validación de citas y abstención sin contexto. |
| **Guardrails Conversacionales** | `LAB-COVERED` | v0.5 / v0.6 | Aislamiento de clientes, defensa anti-inyección, prohibición estricta de escrituras sin HITL. |
| **Single-Agent & Tool Calling** | `LAB-COVERED` | v0.6 / v0.6.1 | Orquestador multi-turno con límite de rondas y tool calling nativo Foundry Local (`phi-4-mini`). |
| **Model Context Protocol (MCP)** | `LAB-COVERED` | v0.7 | Servidor MCP oficial (`mcp==2.1.1`, protocolo `2026-07-28`) con anotaciones y transporte `stdio`. |
| **Human-in-the-Loop (HITL)** | `LAB-COVERED` | v0.7 | Máquina de estados `ApprovalRequest`, aprobación obligatoria, anti-tampering por hash, anti-replay. |
| **Idempotencia en Escrituras** | `LAB-COVERED` / `PROD-PARTIAL` | v0.8 | `IdempotencyGuard`, tabla `idempotency_records`, detección de conflictos (requiere cluster store en prod). |
| **Reintentos (Retries) & Backoff** | `LAB-COVERED` / `PROD-PARTIAL` | v0.8 | `RetryPolicy` con exponential backoff y full jitter, acotado a fallos transitorios. |
| **Circuit Breaker (Cortacircuitos)** | `LAB-COVERED` / `PROD-PARTIAL` | v0.8 | Autómata de 3 estados (`CLOSED`, `OPEN`, `HALF_OPEN`) para contención de fallas en cascada. |
| **Timeouts Acotados** | `LAB-COVERED` | v0.8 | Decorador y wrapper `with_timeout` para evitar bloqueos indefinidos. |
| **Transactional Outbox** | `LAB-COVERED` / `PROD-PARTIAL` | v0.8 | Inserción atómica en `outbox_events` y `service_requests` bajo la misma transacción SQL. |
| **Abstracción de Mensajería** | `LAB-COVERED` / `CLOUD-PENDING` | v0.8 | `LocalMessageBus` con publicación y suscripción desacoplada. |
| **Consumidor Idempotente & DLQ** | `LAB-COVERED` / `CLOUD-PENDING` | v0.8 | `IdempotentConsumer` con deduplicación por `event_id` y enrutamiento a `DeadLetterQueue`. |
| **Observabilidad / OpenTelemetry** | `LAB-COVERED` / `CLOUD-PENDING` | v0.9 | `TracerProvider`, spans jerárquicos (`agent.run`, `llm.chat`, `tool.execute`, `hitl.approval`). |
| **Logs Estructurados & Redacción** | `LAB-COVERED` | v0.9 | `StructuredLogger` con filtro de redacción de secretos, tokens y prompts confidenciales. |
| **Métricas Operativas & AgentOps** | `LAB-COVERED` | v0.9 | `OperationalMetrics` (p50/p95/p99) y `AgentOpsSummary`. |
| **Registro de Auditoría Inmutable** | `LAB-COVERED` / `PROD-PARTIAL` | v0.9 | `AuditLogger` append-only para eventos críticos de seguridad y transacciones. |
| **Supervisión HOTL & Kill-Switch** | `LAB-COVERED` | v0.9 | `HOTLSupervisor` con monitoreo operativo y Kill-Switch para deshabilitar escrituras. |
| **Grounded Knowledge Tool Routing** | `LAB-COVERED` | v0.9.1 | Policy determinista ejecuta `search_knowledge` antes de preguntas bancarias, registra métricas y se abstiene ante `KNOWLEDGE_GAP`; tests de pseudo-tool text. |
| **Banking READ Tool Routing** | `LAB-COVERED` | v0.9.2 | Policy de cuenta, allowlist mínima, `tool_choice` específico, consulta multi-step y ownership determinista; sin nuevas escrituras ni cobertura cloud. |
| **Layered Quality Engineering** | `LAB-COVERED` / `CI-CONFIGURED` | v0.10 | Pirámide de pruebas (Unit, Integration, Contract, E2E), 8 journeys críticos A-H, y `quality_gate.py`. |
| **Contract Testing & API Tests** | `LAB-COVERED` | v0.10 | Contratos JSON Schema OpenAPI, MCP tool registry y Outbox events; colección de pruebas de API de Core Banking. |
| **DevSecOps Security Gates** | `LAB-COVERED` / `CI-CONFIGURED` | v0.10 | Bandit (SAST), pip-audit (SCA), CycloneDX SBOM y secret scanning; compuertas documentadas en `DEVSECOPS-GATES.md`. |
| **CI/CD Pipeline (GitHub Actions)** | `CI-CONFIGURED` | v0.10 | `.github/workflows/ci.yml` configurado con lint, tests, coverage, SAST, SCA, SBOM, secrets y concurrency (`RUNNER-PENDING`). |
| **Architecture Integrity & Coordination** | `LAB-COVERED` / `CI-CONFIGURED` | v0.10.1 | `session_guard.py` (Single Writer, Many Readers), catálogo `CANONICAL-COMPONENTS.md`, regla `DISCOVER BEFORE CREATE`, Pylint R0801 duplicate-code baseline (9.98/10). |
| **Contenedores y Mensajería Azure Local** | `LAB-COVERED` / `CLOUD-PENDING` | v0.11 | Docker multi-stage Linux non-root (`aegisbank/mock-core-banking:0.11.0`), Compose `aegisbank-net`, Azure Service Bus Emulator AMQP `5672`, adapter `AzureServiceBusMessageBus`, 9 journeys aceptación A-I (`test_container_e2e.py`), decisión ACA vs AKS (`CONTAINER-PLATFORM-DECISION.md`), endurecimiento (`CONTAINER-SECURITY.md`). |
| **Orquestación y Runtime Kubernetes Local** | `LOCAL-K8S-COVERED` / `AKS-CLOUD-PENDING` | v0.11.1 | Namespace `aegisbank-local`, Deployment hardened (non-root, securityContext, probes, limits), Service ClusterIP, rolling updates, rollbacks, manual horizontal scale, port-forward E2E verification, y troubleshooting guide (`KUBERNETES-TROUBLESHOOTING.md`). |
| **PostgreSQL + pgvector Vector Data Foundation** | `LOCAL-PGVECTOR-COVERED` / `AZURE-POSTGRESQL-CLOUD-PENDING` | v0.12.0 | PostgreSQL 17 + pgvector 0.8.0 local en Docker Compose, adaptador `PgVectorRetriever`, modelo de embedding local determinista (`LocalDenseEmbeddingModel`), índices HNSW/IVFFlat, filtrado relacional por metadatos, planes de ejecución `EXPLAIN ANALYZE BUFFERS`, evaluación RAG unificada (`v012_retrieval_comparison.json`) y estándar de seguridad (`DATA-LAYER-SECURITY.md`). |
| **Cosmos DB NoSQL Emulator + Change Feed** | `LOCAL-COSMOS-COVERED` / `COSMOS-CLOUD-PENDING` | v0.12.1 | Azure Cosmos DB Emulator vNext Linux en Docker Compose, adaptador `CosmosRepository`, `CosmosChangeFeedProcessor` con checkpoints y deduplicación idempotente, point reads, particionamiento por `/customer_id` (`COSMOS-PARTITION-DESIGN.md`), expiración TTL y contrato JSON Schema (`cosmos-event-item.schema.json`). |
| **Grounded Response Consistency & Provenance** | `LAB-COVERED` / `PROD-READY` | v0.12.0-R1 | Demostración formal de procedencia factual (`ServiceRequestCategory` en `mock_core_banking.domain.enums`), derivación dinámica de esquemas de tools, eliminación de frases vagas en prompts, diferenciación entre consultas de taxonomía (`Tools Executed = 0`), procedimentales (RAG), de cuenta (Core Banking) y de mutación (HITL), con 7 tests de consistencia (`test_grounded_response_consistency.py`). |
| **Redis Cache + Vector/Search Semantics** | `CLOUD-PENDING` | v0.12.2 | Planificado para v0.12.2 (Redis Community local, cache-aside, invalidación, expiración). |
| **MLOps & Experiment Tracking** | `CLOUD-PENDING` | v0.15 | Planificado para v0.15 (MLflow, drift de datos, calibración). |
