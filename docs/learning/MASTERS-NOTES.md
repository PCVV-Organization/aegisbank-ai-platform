# AegisBank — Notas de Cátedra de Nivel Maestría en Inteligencia Artificial

> **Módulo:** Observabilidad Agéntica, AgentOps, Auditoría Inmutable y Supervisión HOTL
> **Nivel:** Maestría / Posgrado en Inteligencia Artificial  
> **Profesor / Lead Architect:** Senior Principal AI Engineer  
> **Hito del Proyecto:** `v0.9.0 — Observability + AgentOps + Audit + HOTL Foundation`

---

## 1. Fundamentos de la Observabilidad en Sistemas de IA

En la ingeniería de software tradicional, la observabilidad responde a la pregunta: *¿El servidor está respondiendo con código HTTP 200?*
En la **Ingeniería de IA Agéntica (Agentic AI Engineering)**, la observabilidad debe responder preguntas mucho más complejas:
* ¿Por qué el modelo eligió llamar a una herramienta específica (`tool_choice`)?
* ¿Qué fragmentos de conocimiento recuperó el RAG y cuáles fueron citados?
* ¿La respuesta fue rechazada por el filtro de grounding o por el evaluador humano (HITL)?
* ¿Cuánto tiempo tomó la inferencia del LLM en comparación con la ejecución de la base de datos?
* ¿Ocurrió un fallo transitorio que requirió reintentos o la activación de un cortacircuitos (*Circuit Breaker*)?

---

## 2. Los Tres Pilares de OpenTelemetry (OTel) para Agentes

```
                       +-------------------------------+
                       |    OPENTELEMETRY STANDARD     |
                       +-------------------------------+
                         /            |              \
                        /             |               \
            [ LOGS ]              [ METRICS ]          [ TRACES ]
      Eventos en JSON       Valores agregados        Spans jerárquicos
      con Correlation ID    (p95, error rates)       (agent -> tool -> db)
```

---

### Pilar 1: Trazas Distribuidas y Spans (*Distributed Tracing & Spans*)

```
TRACE ID: 4bf92f3577b34da6a3ce929d0e0e4736 (Correlation ID: REQ-20260830-001)
│
├── SPAN: agent.run [Duration: 850ms]
│    │
│    ├── SPAN: llm.chat [Duration: 620ms] (Model: phi-4-mini, Tokens: 412)
│    │
│    ├── SPAN: mcp.tool_call [Duration: 180ms] (Tool: create_service_request)
│    │    │
│    │    ├── SPAN: hitl.approval [Duration: 120ms] (Status: APPROVED)
│    │    │
│    │    └── SPAN: core_banking.write [Duration: 45ms] (Status: OK)
│    │
│    └── SPAN: outbox.publish [Duration: 15ms] (Event: ServiceRequestCreated)
```

1. **Sigla y Nombre:** `OTel` — OpenTelemetry / Distributed Tracing.
2. **Definición Teórica:** Una **Traza (Trace)** representa el grafo acíclico dirigido (DAG) de operaciones ejecutadas para satisfacer una solicitud. Cada nodo del grafo es un **Span**.
3. **Atributos Clave de un Span:**
   * `span.name`: Nombre semántico (`agent.run`, `llm.chat`, `tool.execute`, `hitl.approval`).
   * `trace_id`: Identificador global de 128 bits.
   * `span_id`: Identificador único del paso de 64 bits.
   * `parent_span_id`: Identificador del span padre para formar el árbol jerárquico.
   * `attributes`: Metadatos contextuales (`gen_ai.system`, `gen_ai.model`, `tool.name`, `customer.id`).
4. **Por qué lo necesita AegisBank:** Permite identificar inmediatamente en qué milisegundo exacto ocurrió un cuello de botella o en qué componente falló una transacción.
5. **Relación con Microsoft Certifications:**
   * **AI-103 & AI-200:** Distributed Tracing con OpenTelemetry en Azure Monitor y Application Insights.

---

### Pilar 2: Registros Estructurados y Redacción (*Structured Logging & Redaction*)

```json
{
  "timestamp": "2026-08-30T21:25:00.123456Z",
  "level": "INFO",
  "event_name": "tool_executed",
  "correlation_id": "REQ-20260830-001",
  "trace_id": "4bf92f3577b34da6a3ce929d0e0e4736",
  "span_id": "00f067aa0ba902b7",
  "session_customer_id": "CUST-0001",
  "tool_name": "create_service_request",
  "approval_status": "APPROVED",
  "execution_status": "SUCCESS",
  "latency_ms": 45.2
}
```

1. **Regla de Redacción Obligatoria (Seguridad Bancaria):**
   * **PROHIBIDO:** Registrar API Keys, contraseñas, bearer tokens, prompts conversacionales completos con datos sensibles o PII real en los logs de telemetría.
   * **PERMITIDO:** Metadatos de la operación, nombres de herramientas, IDs sintéticos, estados de aprobación, latencias y códigos de error.

---

### Pilar 3: Métricas Operativas y Percentiles de Latencia (*Metrics & Percentiles*)

1. **Contadores Operativos:**
   * `request_count`: Total de interacciones con el agente.
   * `request_error_count`: Interacciones que resultaron en error.
   * `tool_call_count` / `tool_call_failure_count`: Tasa de éxito y fallo por herramienta.
   * `hitl_approved_count` / `hitl_rejected_count`: Proporción de aprobaciones humanas.
   * `retry_count`: Reintentos ejecutados ante fallas transitorias.
   * `circuit_breaker_open_count`: Incidentes de disparo de cortacircuitos.
   * `dlq_count`: Mensajes envenenados derivados a la cola de mensajes muertos.
2. **Cálculo de Percentiles de Latencia:**
   * **p50 (Mediana):** El 50% de las peticiones se atendieron por debajo de este tiempo.
   * **p95:** El 95% de las peticiones se atendieron por debajo de este tiempo (métrica clave para SLAs).
   * **p99:** Identifica casos atípicos o anomalías extremas (*tail latency*).

---

## 3. Registro de Auditoría Inmutable vs. Logs Operacionales

| Característica | Log Operacional / Telemetría | Registro de Auditoría Bancaria (Audit Trail) |
|---|---|---|
| **Audiencia** | Desarrolladores / SRE / DevOps | Oficiales de Cumplimiento / Auditores / Reguladores |
| **Persistencia** | Rotativa (retención 30 a 90 días) | Inmutable / Append-Only (retención de años) |
| **Contenido** | Trazas técnicas, spans, latencias | Decisiones de negocio, hashes criptográficos, aprobaciones HITL |
| **Garantía** | Mejor esfuerzo (*Best effort*) | No repudio (*Non-repudiation*) y secuencia garantizada |

---

## 4. Supervisión HOTL (Human-on-the-Loop) y Kill-Switch

```
                 [ FLUJO NORMAL AGÉNTICO ]

  Cliente ---> Agente ---> [ HOTL Kill-Switch: ACTIVO? ]
                                   |
                         +---------+---------+
                         |                   |
                     NO (Permitido)     SÍ (Bloqueado)
                         |                   |
                  [ Ejecutar Tool ]    [ FAST-FAIL HOTL ]
                  (Requiere HITL)     "Escrituras suspendidas
                                       por supervisión"
```

1. **Diferencia Fundamental:**
   * **HITL (Human-in-the-Loop):** Decisión microscópica sobre una transacción individual.
   * **HOTL (Human-on-the-Loop):** Control macroscópico sobre la capacidad del sistema.
2. **Kill-Switch Supervisorio:** Permite a un operador humano o a un sistema de alerta automática deshabilitar de forma inmediata la herramienta de escritura (`create_service_request`) en toda la plataforma sin necesidad de redesplegar el código.

---

## 5. Masterclass KQL (Kusto Query Language) para Azure Monitor

En producción (Microsoft AI-200), las trazas y logs de OpenTelemetry se consultan en Azure Log Analytics mediante KQL.

### Consulta 1: Tasa de Fallo por Herramienta
```kql
AegisAgentSpans
| where Name == "tool.execute"
| summarize
    TotalCalls = count(),
    FailedCalls = countif(Status == "ERROR")
    by ToolName = tostring(Attributes["tool.name"])
| extend FailureRatePct = round((FailedCalls * 100.0) / TotalCalls, 2)
| order by FailureRatePct desc
```

### Consulta 2: Distribución de Latencia del Agente (p50, p95, p99)
```kql
AegisAgentSpans
| where Name == "agent.run"
| summarize
    P50_Ms = percentile(DurationMs, 50),
    P95_Ms = percentile(DurationMs, 95),
    P99_Ms = percentile(DurationMs, 99)
    by Model = tostring(Attributes["gen_ai.model"])
```

### Consulta 3: Proporción de Aprobación vs. Rechazo en HITL
```kql
AegisAuditEvents
| where EventType in ("HITL_APPROVED", "HITL_REJECTED")
| summarize
    Approvals = countif(EventType == "HITL_APPROVED"),
    Rejections = countif(EventType == "HITL_REJECTED")
    by bin(Timestamp, 1h)
| extend ApprovalRatio = round((Approvals * 100.0) / (Approvals + Rejections), 2)
```

### Consulta 4: Incidentes de Disparo de Cortacircuitos (Circuit Breaker)
```kql
AegisAuditEvents
| where EventType == "CIRCUIT_STATE_CHANGED" and Payload has "OPEN"
| project Timestamp, CorrelationId, DependencyName = tostring(Payload.dependency), Reason = tostring(Payload.reason)
| order by Timestamp desc
```

### Consulta 5: Auditoría de Mensajes en Cola de Mensajes Muertos (DLQ)
```kql
AegisAuditEvents
| where EventType == "MESSAGE_DEAD_LETTERED"
| project Timestamp, CorrelationId, EventId = tostring(Payload.event_id), FailureReason = tostring(Payload.failure_reason), Attempts = toint(Payload.attempts)
| order by Timestamp desc
```

---

## 6. Matriz de Madurez: Laboratorio Local vs. Producción Cloud

| Capacidad | Estado en AegisBank (v0.9 Local) | Estado en Producción Cloud (Azure / AI-200) |
|---|---|---|
| **Tracing** | `InMemorySpanExporter` local | Azure Monitor Exporter $\to$ Application Insights |
| **Logs** | JSON estructurado en stream/archivo | Azure Log Analytics Workspace |
| **Métricas** | Contadores en memoria + percentiles | Azure Monitor Metrics / Prometheus |
| **Auditoría** | SQLite `audit_logs` append-only | Azure SQL Immutable Ledger / Azure Cosmos DB WORM |
| **HOTL Kill-Switch** | Variable atómica thread-safe en memoria | Azure App Configuration / Feature Flags dinámicos |
| **Consultas** | Filtros Python en memoria | Consultas KQL en Azure Log Analytics |
