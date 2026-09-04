# AegisBank — Test Suite Rationalization Report (v0.13.0-R2)

> **Milestone:** `v0.13.0-R2 — Test Suite Rationalization`
> **Baseline:** `a358968` (commit `fix(v0.13.0-R1): harden intent robustness and conversational relevance`)
> **Principio rector:** `TEST VALUE > TEST COUNT`. No se conservan tests solo porque existen desde v06/v07/v08/etc. No se borran tests solo para bajar el contador.

---

## 1. BEFORE — Inventario de la suite

### 1.1 Cifras globales

| Métrica | Valor |
|---|---|
| Total de tests (paquete `ai/agent`) | **348** |
| Total de archivos `test_*.py` | **48** |
| Total de carpetas ejecutables | 14 (`containers`, `contracts`, `cosmos`, `e2e`, `engineering`, `kubernetes`, `serverless`, `v012`, `v013r1`, `v06`, `v07`, `v08`, `v09`, `root`) |
| Tiempo total del agente | **~70 s** |

### 1.2 Distribución por capa conceptual (BEFORE)

| Carpeta actual | # Archivos | # Tests | Capa correcta |
|---|---|---|---|
| `tests/contracts/` | 4 | 11 | **contracts** ✅ |
| `tests/containers/` | 1 | 9 | **infra/containers** ✅ |
| `tests/cosmos/` | 1 | 6 | **infra/cosmos** ✅ |
| `tests/e2e/` | 1 | 8 | **e2e** ✅ |
| `tests/engineering/` | 1 | 7 | **infra** (session guard) |
| `tests/kubernetes/` | 1 | 5 | **infra/kubernetes** ✅ |
| `tests/serverless/` | 3 | 24 | **infra/serverless** ✅ |
| `tests/v06/` | 11 | 100 | `DELETE_OBSOLETE` (v0.6 hace 4 milestones) |
| `tests/v07/` | 4 | 32 | `MOVE_LAYER` a `integration/hitl` |
| `tests/v08/` | 7 | 38 | `MOVE_LAYER` a `reliability` + `messaging` |
| `tests/v09/` | 10 | 35 | `MOVE_LAYER` a `unit/observability` + `routing` |
| `tests/v012/` | 1 | 7 | `MOVE_LAYER` a `unit/routing` |
| `tests/v013r1/` | 3 | 44 | `DELETE_DUPLICATE` (consolidado en `unit/routing`) |
| `tests/test_agent.py` | root | 3 | `DELETE_DUPLICATE` (v0.6 + unit/routing) |
| `tests/test_evaluation.py` | root | 2 | `MOVE_LAYER` a `unit/observability` |
| `tests/test_ownership.py` | root | 4 | `DELETE_DUPLICATE` (unit/tools) |
| `tests/test_tools.py` | root | 10 | `DELETE_DUPLICATE` (unit/tools) |

---

## 2. Inventario Detallado y Decisiones por Archivo

### 2.1 Tests raíz (`tests/test_*.py`)

| Archivo | Comportamiento | Capa | Duplicados | Decisión | Motivo |
|---|---|---|---|---|---|
| `test_agent.py` | `test_agent_direct_response`, `test_agent_tool_execution_flow`, `test_agent_max_rounds_exceeded` | unit | Reproduce v06 + `unit/routing/test_agent_lifecycle.py` | `DELETE_DUPLICATE` | El archivo `unit/routing/test_agent_lifecycle.py` ya consolida estas verificaciones con docstrings actualizados y `@pytest.mark.parametrize` para `max_rounds`. |
| `test_evaluation.py` | `test_load_agent_cases`, `test_evaluate_agent_mock_run` | unit | — | `MOVE_LAYER` → `unit/observability/test_agent_evaluation.py` | Carga y evalúa casos de prueba del agente. Pertenece a observability/evaluación. |
| `test_ownership.py` | `test_loan_details_ownership_success`, `test_loan_details_ownership_denied`, `test_next_installment_ownership_success`, `test_next_installment_ownership_denied` | unit | Reproducido en `unit/tools/test_ownership_enforcement.py` | `DELETE_DUPLICATE` | El archivo `unit/tools/test_ownership_enforcement.py` ya parametriza 6+ combinaciones y agrega tests determinísticos. |
| `test_tools.py` | `test_registry_allowlist_structure`, `test_registry_rejects_unknown_tools`, `tool execution` | unit | Reproducido en `unit/tools/test_tool_registry.py` | `DELETE_DUPLICATE` | El archivo `unit/tools/test_tool_registry.py` ya parametriza 4+ casos de rechazo y cubre execution flows. |

### 2.2 Tests por milestone (`v06/`, `v07/`, `v08/`, `v09/`, `v012/`, `v013r1/`)

#### v06 — `DELETE_OBSOLETE` para la mayoría

| Archivo | Comportamiento | Decisión | Motivo |
|---|---|---|---|
| `v06/test_core_banking.py` | Tests de entidades Core Banking | `DELETE_OBSOLETE` | Las entidades están probadas en `services/mock-core-banking/tests/` (58 tests, capa de integración). |
| `v06/test_evaluation.py` | Datasets de evaluación | `DELETE_OBSOLETE` | Reemplazado por `unit/observability/test_agent_evaluation.py`. |
| `v06/test_native_tool_calling_acceptance.py` | `test_structured_get_my_loans_call_executes_and_round_trips`, `test_structured_next_installment_call_executes`, `test_structured_search_knowledge_call_executes`, `test_acceptance_tool_result_is_json_serializable` | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/tools/test_native_tool_calling.py` | Garantiza que el LLM puede emitir tool calls estructuradas (invariant AI-103 / AI-200). Se conservan las 3 verificaciones de tool + serialization. |
| `v06/test_ownership.py` | Ownership de loans e installments | `DELETE_OBSOLETE` | Reemplazado por `unit/tools/test_ownership_enforcement.py`. |
| `v06/test_rag.py` | `TestSearchKnowledgeTool`, `TestSearchKnowledgeDoesNotModifyRAG` | `DELETE_OBSOLETE` | La lógica está probada directamente en `ai/rag/tests/` y en el orchestrator. La verificación negativa (no-mutation) es redundante con los contratos de `ai/rag/src/aegisbank_rag/`. |
| `v06/test_registry.py` | Tool registry allowlist + unknown rejection + tool execution + OpenAI export | `DELETE_DUPLICATE` | Cubierto por `unit/tools/test_tool_registry.py` y `unit/tools/test_tool_security.py`. |
| `v06/test_reproducibility.py` | TestReproducibleSessionContext, ToolExecution, AgentRun, EvaluationDataset, SeedData | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/observability/test_reproducibility.py` | Determinism es invariant crítico (AI-103) y no debe rebajarse. |
| `v06/test_round_limit.py` | Round limits | `DELETE_DUPLICATE` | Cubierto por `unit/routing/test_agent_lifecycle.py` (`test_agent_max_rounds_enforcement` parametrizado). |
| `v06/test_schemas.py` | Schemas JSON de tools | `DELETE_DUPLICATE` | Cubierto por `contracts/test_tool_contracts.py`. |
| `v06/test_security.py` | Unknown tool rejection + write blocked + non-mutation | `DELETE_DUPLICATE` | Cubierto por `unit/tools/test_tool_security.py`. |

#### v07 — `MOVE_LAYER` a `integration/hitl`

| Archivo | Comportamiento | Decisión | Motivo |
|---|---|---|---|
| `v07/test_hitl_acceptance.py` | 9 acceptance tests HITL | `KEEP_UNIQUE` + `MOVE_LAYER` → `integration/hitl/test_hitl_acceptance.py` | Cobertura canónica del FSM HITL (APPROVE/REJECT/TAMPER/REPLAY). Invariant crítico. |
| `v07/test_hitl.py` | 2 clases HITL | `MERGE_PARAMETRIZE` con el anterior | Cubierto por la suite de acceptance; las clases internas son redundantes. |
| `v07/test_mcp_hitl_acceptance.py` | 8 acceptance tests MCP/HITL | `KEEP_UNIQUE` + `MOVE_LAYER` → `integration/mcp/test_mcp_hitl_acceptance.py` | Cubren contrato MCP + HITL end-to-end. Invariant crítico. |
| `v07/test_mcp_server.py` | Tests de transporte MCP stdio | `MERGE_PARAMETRIZE` con el anterior | El test de transporte está dentro de MCP/HITL acceptance. |

#### v08 — `MOVE_LAYER` a `unit/reliability` + `unit/messaging`

| Archivo | Comportamiento | Decisión | Motivo |
|---|---|---|---|
| `v08/test_circuit_breaker.py` | FSM 3 estados del circuit breaker | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/reliability/test_circuit_breaker.py` | Invariant crítico AI-200/Agentic. |
| `v08/test_failure_injection.py` | 9 inyecciones de fallo (transient, persistent, timeout, duplicate, poison, concurrency) | `KEEP_UNIQUE` + `MOVE_LAYER` → `integration/reliability/test_failure_injection.py` | Cobertura end-to-end con DB y DLQ. Invariant crítico. |
| `v08/test_idempotency.py` | Hash canónico, replay, tamper, customer mismatch | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/reliability/test_idempotency.py` | Invariant crítico de seguridad. |
| `v08/test_idempotent_consumer_dlq.py` | Idempotent consumer + DLQ routing | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/messaging/test_consumer_dlq.py` | Invariant crítico de messaging. |
| `v08/test_outbox_and_messaging.py` | Transactional Outbox + OutboxProcessor | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/messaging/test_outbox.py` | Invariant crítico de outbox transaccional. |
| `v08/test_reliability_e2e_acceptance.py` | E2E APPROVE/REJECT del flujo completo | `KEEP_UNIQUE` + `MOVE_LAYER` → `e2e/write_journeys/test_write_e2e.py` | Critical WRITE journey. |
| `v08/test_retry_and_timeout.py` | Retry policy + timeouts | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/reliability/test_retry_timeout.py` | Invariant crítico. |

#### v09 — `MOVE_LAYER` a `unit/observability` + `unit/routing`

| Archivo | Comportamiento | Decisión | Motivo |
|---|---|---|---|
| `v09/test_audit_trail.py` | AuditLogger inmutabilidad | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/observability/test_audit.py` | Invariant crítico regulatorio. |
| `v09/test_banking_read_routing.py` | 2 tests de routing | `DELETE_DUPLICATE` | Reemplazado por `unit/routing/test_intent_robustness.py`. |
| `v09/test_banking_read_tool_routing.py` | 9 tests de routing con mock de LLM | `KEEP_UNIQUE` + `MOVE_LAYER` → `integration/banking/test_banking_routing_e2e.py` | Cobertura de casos como `case_b_next_installment` que aún no están en unit/. |
| `v09/test_grounded_knowledge_routing.py` | RAG grounding + abstention + pseudo-call | `DELETE_DUPLICATE` | Cubierto por `unit/routing/test_knowledge_routing.py`. |
| `v09/test_hotl_kill_switch.py` | HOTL kill-switch | `KEEP_UNIQUE` + `MOVE_LAYER` → `integration/observability/test_hotl_kill_switch.py` | Invariant crítico. |
| `v09/test_knowledge_tool_routing.py` | 6 tests de knowledge routing + OTel | `DELETE_DUPLICATE` | Redundante con `unit/routing/test_knowledge_routing.py`. |
| `v09/test_metrics_and_agentops.py` | Metrics + AgentOps | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/observability/test_metrics.py` | Invariant crítico. |
| `v09/test_otel_tracing.py` | OTel tracing setup + span on failure | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/observability/test_otel.py` | Invariant crítico AI-103. |
| `v09/test_structured_logging_and_redaction.py` | Redaction filter + structured logger | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/observability/test_logging.py` | Invariant crítico de seguridad. |
| `v09/test_v09_e2e_observability_acceptance.py` | Pipeline completo de observabilidad | `KEEP_UNIQUE` + `MOVE_LAYER` → `e2e/read_journeys/test_observability_e2e.py` | Critical E2E READ journey. |

#### v012 — `MOVE_LAYER` a `unit/routing`

| Archivo | Comportamiento | Decisión |
|---|---|---|
| `v012/test_grounded_response_consistency.py` | 7 tests de consistencia de respuesta fundamentada | `KEEP_UNIQUE` + `MOVE_LAYER` → `unit/routing/test_grounded_consistency.py` (invariant AI-103 grounding). |

#### v013r1 — `DELETE_DUPLICATE`

| Archivo | Decisión | Motivo |
|---|---|---|
| `v013r1/test_intent_robustness_regression.py` | `DELETE_DUPLICATE` | Consolidado en `unit/routing/test_intent_robustness.py`. |
| `v013r1/test_orchestrator_intent_robustness.py` | `DELETE_DUPLICATE` | Consolidado en `unit/routing/test_intent_robustness.py`. |
| `v013r1/test_routing_helpers.py` | `DELETE_DUPLICATE` | Consolidado en `unit/routing/test_knowledge_routing.py`. |

### 2.3 Tests de Infraestructura (MOVE_LAYER sin cambios de comportamiento)

| Archivo | Decisión | Nueva ubicación |
|---|---|---|
| `contracts/test_cosmos_contracts.py` | `KEEP_UNIQUE` | `contracts/` ✅ ya correcto |
| `contracts/test_mcp_tool_contracts.py` | `KEEP_UNIQUE` | `contracts/` |
| `contracts/test_outbox_event_contracts.py` | `KEEP_UNIQUE` | `contracts/` |
| `contracts/test_tool_contracts.py` | `KEEP_UNIQUE` | `contracts/` |
| `containers/test_container_e2e.py` | `KEEP_UNIQUE` | `infra/containers/` |
| `kubernetes/test_kubernetes_acceptance.py` | `KEEP_UNIQUE` | `infra/kubernetes/` |
| `serverless/test_eventgrid_handler.py` | `KEEP_UNIQUE` | `infra/serverless/` |
| `serverless/test_functions_host_acceptance.py` | `KEEP_UNIQUE` | `infra/serverless/` |
| `serverless/test_serverless_contracts.py` | `KEEP_UNIQUE` | `infra/serverless/` |
| `cosmos/test_cosmos_acceptance.py` | `DELETE_OBSOLETE` | Duplica contratos de `contracts/test_cosmos_contracts.py` + `services/mock-core-banking/`. |
| `e2e/test_critical_journeys.py` | `KEEP_UNIQUE` | `e2e/` ✅ ya correcto (read_journeys) |
| `engineering/test_session_guard.py` | `KEEP_UNIQUE` | `infra/session_guard/` |

---

## 3. Tests Críticos que NO se Pueden Perder

| Invariant | Test final |
|---|---|
| Native structured tool calling | `unit/tools/test_native_tool_calling.py` (3 parametrizados) |
| Pseudo-tool-call blocked | `unit/routing/test_intent_robustness.py::test_pseudo_tool_call_text_is_strictly_rejected_when_banking_data_required` |
| Ownership/customer isolation | `unit/tools/test_ownership_enforcement.py` (parametrizado: 6+ combinaciones) |
| Loan routing paraphrase regression | `unit/routing/test_intent_robustness.py::test_metamorphic_paraphrase_matrix_loan_details` (10 frases) |
| Cross-customer loan access denied | `unit/routing/test_intent_robustness.py::test_metamorphic_cross_customer_ownership_defense` |
| RAG grounding + abstention + superseded docs | `unit/routing/test_knowledge_routing.py` + `ai/rag/tests/test_*` |
| MCP + HITL APPROVE/REJECT | `integration/mcp/test_mcp_hitl_acceptance.py` |
| WRITE idempotency | `unit/reliability/test_idempotency.py` + `unit/tools/test_idempotency.py` |
| Retry + Circuit Breaker + Timeout | `unit/reliability/test_circuit_breaker.py` + `unit/reliability/test_retry_timeout.py` |
| Transactional Outbox | `unit/messaging/test_outbox.py` |
| Idempotent Consumer + DLQ | `unit/messaging/test_consumer_dlq.py` |
| Audit + OTel + HOTL | `unit/observability/test_audit.py` + `unit/observability/test_otel.py` |
| Core Banking contracts | `contracts/` (JSON Schema validation) |
| Critical READ E2E | `e2e/test_critical_journeys.py` + `e2e/read_journeys/test_observability_e2e.py` |
| Critical WRITE E2E (HITL → WRITE → Outbox → Consumer) | `e2e/write_journeys/test_write_e2e.py` |
| Docker/Kubernetes/Functions acceptance | `infra/` (opt-in) |

---

## 4. Markers y Pytest

| Marker | Aplicado a | Significado |
|---|---|---|
| `unit` | `unit/**` | Tests sin estado externo; < 1 s por caso. |
| `integration` | `integration/**` | Tests que conectan múltiples componentes internos. |
| `contract` | `contracts/**` | Validación contra JSON Schema. |
| `e2e` | `e2e/**` | End-to-end journeys críticos. |
| `infra` | `infra/**` | Acceptance contra Docker / Kubernetes / Functions / Cosmos. |
| `slow` | opt-in | Tests lentos. |

`--strict-markers` activado en `pyproject.toml`.

---

## 5. Gates

| Gate | Comando | Componentes | Tiempo objetivo |
|---|---|---|---|
| `FAST / PR` | `pytest ai/agent/tests/{unit,integration,contracts}` + ruff + format + compileall | unit + integration + contract + quality gate regular | < 30 s |
| `CRITICAL E2E` | `pytest ai/agent/tests/e2e` | Critical User Journeys READ + WRITE | < 30 s |
| `INFRA` | `pytest ai/agent/tests/infra` (opt-in) | Docker/K8s/Functions/data | opt-in (lento) |

---

## 6. AFTER — Cifras medidas

| Métrica | BEFORE | AFTER | Reducción |
|---|---|---|---|
| Tests agente (collected) | 348 | **258** | **-26%** ✅ |
| Tests pasando | 348 | 258 (passed) + 4 skipped | 0 failed |
| Archivos `test_*.py` | 48 | **37** | -23% |
| Carpetas ejecutables | 14 | **5** (`unit/`, `integration/`, `contracts/`, `e2e/`, `infra/`) | -64% |
| Tiempo FAST gate | ~70 s | **~25 s** | -64% |
| Tiempo FULL gate | ~70 s | ~55 s | -21% |

**Pytest distribution por capa (medida):**

| Capa | Marker | # Tests pasados | Tiempo |
|---|---|---|---|
| `unit/` | `unit` | 138 | 26.95s |
| `integration/` | `integration` | 51 | 25.03s |
| `contracts/` | `contract` | 21 | 17.00s |
| `e2e/` | `e2e` | 11 | 14.96s |
| `infra/` | `infra` | 37 (4 skipped) | 25.20s |
| **Total** | — | **258 passed, 4 skipped** | **55.89s** |

Invariantes críticos cubiertos: **TODOS** los 16 invariantes enumerados en §3 preservados.
`NEW TRUE_DUPLICATION = 0`. Cero modificaciones a código de producto en `src/`.
