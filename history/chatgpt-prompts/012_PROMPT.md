# 012 — AegisBank v0.9 Observability + AgentOps + Audit

Continúa exclusivamente:

`v0.9.0 — Observability + AgentOps + Audit`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline esperado:
- branch: `master`
- HEAD: `ce79759`
- working tree limpio

## Regla pedagógica obligatoria

Trabaja como Principal AI Engineer y como profesor de Maestría para un alumno que empieza desde cero.

Antes de implementar cada concepto nuevo y en el informe final explica:

1. nombre completo y sigla;
2. qué significa;
3. qué problema resuelve;
4. cómo funciona internamente;
5. por qué AegisBank lo necesita;
6. alternativa y cuándo NO usarlo;
7. riesgos/errores típicos;
8. relación con el puesto Mibanco;
9. relación con Microsoft AI-103 o AI-200;
10. ejemplo concreto del milestone.

Actualiza de forma incremental:
- `docs/learning/GLOSSARY.md`
- `docs/learning/MASTERS-NOTES.md`
- `docs/requirements/MIBANCO-JOB-PROFILE-2026.md`
- `docs/requirements/COVERAGE-MATRIX.md`

Guarda este prompt como:
`docs/chatgpt-prompts/012_PROMPT.md`

## Restricciones

- NO worktrees.
- NO Azure cloud ni costos.
- NO Docker/Kubernetes todavía.
- NO push.
- NO v0.10.
- NO multi-agent.
- NO nuevas operaciones WRITE.
- Preservar v0.8 y sus métricas/resultados.
- Mantener Foundry Local.
- No registrar prompts completos, secrets ni PII innecesaria.

## Objetivo

Instrumentar AegisBank con observabilidad local estándar y auditoría estructurada para poder responder:

- ¿qué petición ocurrió?
- ¿qué agente/modelo intervino?
- ¿qué tool/MCP se llamó?
- ¿hubo HITL APPROVE/REJECT?
- ¿cuánto tardó cada paso?
- ¿hubo retry, timeout, circuit breaker o DLQ?
- ¿qué falló y dónde?
- ¿qué correlation_id y trace_id permiten reconstruir el flujo?

## Conceptos a implementar

### 1. OpenTelemetry (OTel)

Usar OpenTelemetry como estándar vendor-neutral.

Instrumentar traces/spans al menos en:
- request/CLI run;
- agent orchestration;
- LLM call;
- retrieval;
- tool call;
- MCP call;
- HITL decision;
- Core Banking write;
- retry;
- circuit breaker;
- outbox publish;
- consumer processing.

No enviar telemetría a Azure todavía.
Usar un exporter/local sink apropiado para tests/desarrollo.

### 2. Correlation ID + Trace ID

Propagar identificadores consistentes E2E.

Diferenciar:
- `correlation_id`: identificador de negocio/request que AegisBank controla;
- `trace_id`: identificador técnico distribuido de OpenTelemetry.

### 3. Logs estructurados

Emitir logs JSON/estructurados con campos mínimos:
- timestamp;
- level;
- event_name;
- correlation_id;
- trace_id;
- session_id;
- synthetic_customer_id cuando sea necesario y permitido;
- tool_name;
- approval_status;
- execution_status;
- latency_ms;
- error_code.

Redactar secretos y contenido sensible.

### 4. Metrics

Crear métricas operativas locales, al menos:
- request_count;
- request_error_count;
- latency;
- llm_call_count;
- tool_call_count;
- tool_call_failure_count;
- hitl_approved_count;
- hitl_rejected_count;
- retry_count;
- circuit_breaker_open_count;
- outbox_pending_count;
- dlq_count.

No inventar SLOs productivos todavía.

### 5. AgentOps

Crear una vista/resumen local de operación del agente basada en métricas y traces:
- éxito/fallo de tool calls;
- latencia;
- HITL;
- retries;
- circuit state;
- DLQ;
- calidad histórica ya existente donde aplique.

No crear dashboard Azure todavía.

### 6. Audit Log

Implementar un audit trail persistente y append-oriented para eventos críticos:
- agent_run_started/completed;
- tool_proposed;
- tool_executed/denied;
- hitl_requested/approved/rejected/executed;
- service_request_created;
- idempotency_replay/conflict;
- retry_performed;
- circuit_opened/half_open/closed;
- message_dead_lettered.

Debe permitir reconstruir la secuencia E2E sin guardar secretos ni prompts completos.

### 7. HOTL foundation

HOTL = Human-on-the-Loop.

No automatizar acciones nuevas.

Implementar solo la base de supervisión:
- estado operativo visible;
- alert condition local para eventos críticos;
- capacidad determinista de deshabilitar temporalmente el único WRITE tool;
- default seguro.

Documentar claramente diferencia HITL vs HOTL.

### 8. KQL learning mapping

No requiere Azure.

En `MASTERS-NOTES.md`, enseñar KQL = Kusto Query Language y escribir ejemplos conceptuales equivalentes para consultas futuras en Azure Monitor:
- errores por tool;
- p95 latency;
- approvals/rejections;
- circuit breaker opens;
- DLQ events.

No ejecutar KQL contra Azure.

## Seguridad y privacidad

La telemetría NO debe almacenar:
- API keys/tokens;
- passwords;
- prompts completos por defecto;
- raw tool arguments sensibles;
- PII real.

Usar datos sintéticos y redacción.
Añadir tests para demostrar redaction.

## Acceptance E2E

Probar al menos:
- READ exitoso produce trace + logs + metrics.
- WRITE APPROVE produce spans desde agent hasta outbox/consumer + audit trail.
- WRITE REJECT produce audit sin side effect.
- retry aparece en trace/metrics.
- circuit breaker OPEN aparece en trace/metrics/audit.
- DLQ genera evento auditable.
- correlation_id se preserva E2E.
- secrets/redacted fields no aparecen.
- HOTL disable-write bloquea WRITE aunque LLM lo proponga.

## ADRs

Detecta los siguientes números libres y documenta solo decisiones nuevas, como mínimo:
- OpenTelemetry as vendor-neutral observability standard;
- structured audit event model;
- HOTL supervisory kill-switch for writes.

No modificar ADR históricos.

## Validación

Ejecutar:
- tests v0.9;
- regresión v0.8/v0.7/v0.6;
- ai/rag;
- v0.3;
- v0.2;
- Ruff;
- scoped format;
- compileall;
- secret scan;
- `git diff --check`.

## Git

Antes del staging verificar HEAD `ce79759`.

PROHIBIDO:
- `git add .`
- `git add -A`
- push

Stagear solo archivos legítimos v0.9 y documentación pedagógica.

Si todo pasa crear:
`feat(v0.9): establish OpenTelemetry AgentOps and audit foundation`

No push.

## Informe final

Incluir:

### LEARNING NOTES
`SIGLA -> nombre completo -> qué es -> cómo funciona -> por qué -> ejemplo AegisBank -> AI-103/AI-200 -> requisito Mibanco`

### COVERAGE UPDATE
Indicar qué requisitos pasaron de PENDING a PARTIAL/COVERED, con evidencia.

Finalizar solo con:
`AEGISBANK_V0.9_OBSERVABILITY_AGENTOPS_AUDIT_READY`
y STOP.

NO iniciar v0.10.
