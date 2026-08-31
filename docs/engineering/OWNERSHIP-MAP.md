# AegisBank — Ownership Map

> **Propósito:** Delimitar formalmente la responsabilidad de cada subsistema y componente en AegisBank AI Platform.
> **Principio:** Cada archivo y responsabilidad del repositorio tiene un dominio bien definido para evitar solapamientos arquitectónicos y colisiones entre sesiones de desarrollo.

---

## 1. Mapa de Responsabilidades por Componente

| Dominio Arquitectónico | Rutas Autorizadas | Responsabilidad Principal |
|---|---|---|
| **Core Banking (Mock)** | `services/mock-core-banking/**` | Simulación determinista de Core Banking: clientes, préstamos, cronogramas de pago, solicitudes de servicio, persistencia SQLite, outbox transaccional y OpenAPI 3.1. |
| **Intent Classifier (ML)** | `ml/intent-classifier/**` | Clasificación de intenciones del usuario mediante TF-IDF y Logistic Regression con dataset sintético reproducible y métricas congeladas. |
| **RAG Knowledge Base** | `ai/rag/**` | Ingesta, chunking canónico, retrieval híbrido léxico/denso (RRF k=60), evaluación de citas y abstención ante falta de contexto. |
| **Agent Orchestration** | `ai/agent/src/aegisbank_agent/agent.py`, `ai/agent/src/aegisbank_agent/knowledge_routing.py`, `ai/agent/src/aegisbank_agent/tools/**` | Orquestación conversacional, políticas de enrutamiento bancario y de conocimiento, prompts inmutables y ejecución de herramientas de lectura. |
| **MCP & HITL Boundary** | `ai/agent/src/aegisbank_agent/hitl.py`, `ai/agent/src/aegisbank_agent/mcp_boundary.py`, `ai/agent/src/aegisbank_agent/mcp_server.py`, `contracts/mcp-tools.schema.json` | Protocolo MCP stdio oficial (`2026-07-28`), gestión del ciclo de vida de `ApprovalRequest`, aprobación obligatoria humana para escrituras, validación anti-tampering por hash. |
| **Reliability & Messaging** | `ai/agent/src/aegisbank_agent/reliability/**` | Resiliencia operativa: `IdempotencyGuard`, `RetryPolicy` con backoff y jitter, `CircuitBreaker` (FSM 3 estados), timeouts, `LocalMessageBus`, `OutboxProcessor`, `IdempotentConsumer` y `DeadLetterQueue (DLQ)`. |
| **Observability & AgentOps** | `ai/agent/src/aegisbank_agent/observability/**` | Telemetría OpenTelemetry (spans, tracer), logs estructurados con redacción de datos sensibles, métricas operativas (`OperationalMetrics`), registro de auditoría (`AuditLogger`) y supervisión HOTL (`HOTLSupervisor`). |
| **Quality & DevSecOps** | `scripts/**`, `.github/workflows/**`, `docs/quality/**`, `docs/security/**`, `contracts/**` | Compuertas deterministas de calidad (`quality_gate.py`), coordinación cross-session (`session_guard.py`), escaneo SAST (Bandit), auditoría SCA (pip-audit), SBOM CycloneDX y suite de contratos/E2E. |
| **Teaching & Governance** | `docs/learning/**`, `docs/architecture/**`, `docs/requirements/**`, `docs/chatgpt-prompts/**` | Material pedagógico nivel Maestría (Teaching Contract, glosario, notas), matriz de cobertura frente a Mibanco 2026, y ADRs inmutables. |

---

## 2. Política sobre `.github/CODEOWNERS`

* **Estado:** **DIFERIDO** hasta la formalización de equipos remotos en GitHub.
* **Justificación:** GitHub `CODEOWNERS` requiere identificadores de usuarios u organizaciones reales de GitHub (e.g. `@aegisbank/core-team`). Inventar identificadores ficticios provocaría errores de sintaxis en el linter de GitHub o bloquearía revisiones de Pull Requests.
* **Diferenciación Técnica:**
  - `CODEOWNERS` opera a nivel de pull request y revisión en la plataforma remota de GitHub.
  - `session_guard.py` opera a nivel de working tree local para impedir condiciones de carrera entre múltiples sesiones/agentes locales.
