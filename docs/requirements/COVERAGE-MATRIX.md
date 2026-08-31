# AegisBank — Matriz de Cobertura frente al Perfil Mibanco 2026

Este documento mapea cada competencia y requisito técnico exigido en los perfiles de Mibanco frente a la evidencia verificable construida en AegisBank AI Platform.

* **Categorías de Estado:**
  * **`LAB-COVERED`**: Implementado, probado y verificado completamente en el entorno de laboratorio local con tests reproducibles.
  * **`PROD-PARTIAL`**: Implementado conceptualmente y funcional en laboratorio, pero requiere componentes distribuidos en la nube (Kubernetes, Azure Service Bus, Cloud WORM) para producción bancaria.
  * **`CLOUD-PENDING`**: Planificado para hitos de nube e industrialización (v0.10+).

---

## 1. Conteo Oficial de Pruebas Automatizadas del Repositorio

| Paquete del Repositorio | Cantidad de Pruebas | Estado |
|---|---|---|
| `ai/agent` (Agente, Tools, MCP, HITL, Reliability, Observability, Knowledge Routing, Banking Routing) | **209 tests** | PASS |
| `ai/rag` (Chunking, Retrieval Léxico/Denso/RRF, Grounding, Evaluaciones) | **62 tests** | PASS |
| `ml/intent-classifier` (Dataset sintético, TF-IDF, Logistic Regression) | **17 tests** | PASS |
| `services/mock-core-banking` (Entidades, Restricciones, Repositorios, Outbox) | **55 tests** | PASS |
| **TOTAL GENERAL DEL REPOSITORIO** | **343 tests** | **100% PASS** |

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
| **Abstracción de Mensajería** | `LAB-COVERED` / `CLOUD-PENDING` | v0.8 | `LocalMessageBus` con publicación y suscripción desacoplada (pendiente Azure Service Bus). |
| **Consumidor Idempotente & DLQ** | `LAB-COVERED` / `CLOUD-PENDING` | v0.8 | `IdempotentConsumer` con deduplicación por `event_id` y enrutamiento a `DeadLetterQueue`. |
| **Observabilidad / OpenTelemetry** | `LAB-COVERED` / `CLOUD-PENDING` | v0.9 | `TracerProvider`, spans jerárquicos (`agent.run`, `llm.chat`, `tool.execute`, `hitl.approval`). |
| **Logs Estructurados & Redacción** | `LAB-COVERED` | v0.9 | `StructuredLogger` con filtro de redacción de secretos, tokens y prompts confidenciales. |
| **Métricas Operativas & AgentOps** | `LAB-COVERED` | v0.9 | `OperationalMetrics` (p50/p95/p99) y `AgentOpsSummary`. |
| **Registro de Auditoría Inmutable** | `LAB-COVERED` / `PROD-PARTIAL` | v0.9 | `AuditLogger` append-only para eventos críticos de seguridad y transacciones. |
| **Supervisión HOTL & Kill-Switch** | `LAB-COVERED` | v0.9 | `HOTLSupervisor` con monitoreo operativo y Kill-Switch para deshabilitar escrituras. |
| **Grounded Knowledge Tool Routing** | `LAB-COVERED` | v0.9.1 | Policy determinista ejecuta `search_knowledge` antes de preguntas bancarias, registra métricas y se abstiene ante `KNOWLEDGE_GAP`; tests de pseudo-tool text. |
| **Banking READ Tool Routing** | `LAB-COVERED` | v0.9.2 | Policy de cuenta, allowlist mínima, `tool_choice` específico, consulta multi-step y ownership determinista; sin nuevas escrituras ni cobertura cloud. |
| **CI/CD & DevSecOps** | `CLOUD-PENDING` | v0.10 | Planificado para v0.10 (GitHub Actions, SAST, SBOM, Contract testing). |
| **Contenedores / Cloud Deployment** | `CLOUD-PENDING` | v0.11 | Planificado para v0.11 (Docker, Azure Container Apps, Service Bus Emulator). |
| **MLOps & Experiment Tracking** | `CLOUD-PENDING` | v0.12 | Planificado para v0.12 (MLflow, drift de datos, calibración). |
