# AegisBank — Matriz de Cobertura frente al Perfil Mibanco 2026

Este documento mapea cada competencia y requisito técnico exigido en los perfiles de Mibanco frente a la evidencia verificable construida en AegisBank AI Platform.

* Estados válidos:
  * **`COVERED`**: Implementado, probado y verificado con código y tests ejecutables.
  * **`PARTIAL`**: Implementado a nivel de abstracción local o con cobertura básica.
  * **`PENDING`**: Planificado para hitos posteriores (v0.9+).

---

## Matriz de Competencias y Estado

| Área / Competencia | Estado | Hito de Introducción | Evidencia Verificable en Código |
|---|---|---|---|
| **Estrategia de Prompting y Versionado** | `COVERED` | v0.5 / v0.6 / v0.7 | Prompts JSON inmutables (`rag-answer-v001`, `agent-system-v002`), esquemas JSON estrictos. |
| **Evaluación y QA de LLM** | `COVERED` | v0.5 / v0.6 | Datasets held-out congelados, métricas cuantitativas (Groundedness, Citation Validity, Selection Accuracy). |
| **RAG / Base de Conocimiento** | `COVERED` | v0.4 / v0.5 | Chunking canónico, retrieval híbrido RRF (k=60), validación de citas y abstención sin contexto. |
| **Guardrails Conversacionales** | `COVERED` | v0.5 / v0.6 | Aislamiento de clientes, defensa anti-inyección, prohibición estricta de escrituras sin HITL. |
| **Single-Agent & Tool Calling** | `COVERED` | v0.6 / v0.6.1 | Orquestador multi-turno con límite de rondas y tool calling nativo Foundry Local (`phi-4-mini`). |
| **Model Context Protocol (MCP)** | `COVERED` | v0.7 | Servidor MCP oficial (`mcp==2.1.1`, protocolo `2026-07-28`) con anotaciones y transporte `stdio`. |
| **Human-in-the-Loop (HITL)** | `COVERED` | v0.7 | Máquina de estados `ApprovalRequest`, aprobación obligatoria, anti-tampering por hash, anti-replay. |
| **Idempotencia en Escrituras** | `COVERED` | v0.8 | `IdempotencyGuard`, tabla `idempotency_records`, detección de conflictos y ejecución concurrente segura. |
| **Reintentos (Retries) & Backoff** | `COVERED` | v0.8 | `RetryPolicy` con exponential backoff y full jitter, acotado a fallos transitorios. |
| **Circuit Breaker (Cortacircuitos)** | `COVERED` | v0.8 | Autómata de 3 estados (`CLOSED`, `OPEN`, `HALF_OPEN`) para contención de fallas en cascada. |
| **Timeouts Acotados** | `COVERED` | v0.8 | Decorador y wrapper `with_timeout` para evitar bloqueos indefinidos. |
| **Transactional Outbox** | `COVERED` | v0.8 | Inserción atómica en `outbox_events` y `service_requests` bajo la misma transacción SQL. |
| **Abstracción de Mensajería** | `COVERED` | v0.8 | `LocalMessageBus` con publicación y suscripción desacoplada. |
| **Consumidor Idempotente & DLQ** | `COVERED` | v0.8 | `IdempotentConsumer` con deduplicación por `event_id` y enrutamiento a `DeadLetterQueue` tras max reintentos. |
| **Observabilidad / OpenTelemetry** | `PENDING` | v0.9 | Planificado para v0.9 (OTel, correlation IDs, métricas de latencia/tokens). |
| **CI/CD & DevSecOps** | `PENDING` | v0.10 | Planificado para v0.10 (GitHub Actions, SAST, SBOM). |
| **Contenedores / Cloud Deployment** | `PENDING` | v0.11 | Planificado para v0.11 (Docker, Azure Container Apps / AKS). |
| **MLOps & Experiment Tracking** | `PENDING` | v0.12 | Planificado para v0.12 (MLflow, drift de datos, calibración). |
