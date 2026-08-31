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

---

## 7. v0.9.1: Routing Grounded y Abstención

**RAG** (*Retrieval-Augmented Generation*, generación aumentada mediante recuperación) no significa que el modelo diga que va a buscar; significa que el programa ejecuta retrieval y entrega evidencia al modelo. Un **tool call** es una estructura nativa, normalmente JSON, que el host valida y ejecuta. El texto `search_knowledge("...")` no es una llamada y nunca debe parsearse para fabricarla.

En modo **AUTO TOOL ROUTING**, `tool_choice="auto"` permite que el LLM elija responder o llamar una herramienta. Es útil para preguntas abiertas, pero deja un **routing gap** si un modelo pequeño responde con pseudo-código. En **POLICY-ENFORCED TOOL ROUTING**, una regla determinista identifica preguntas sobre políticas, productos, requisitos, tasas, comisiones o plazos y ejecuta primero `search_knowledge`. Esta alternativa reduce libertad del modelo, pero es apropiada cuando una respuesta bancaria debe estar **grounded** (fundamentada) en una fuente autorizada.

El experimento “plazo máximo para crédito vehicular” devolvió hits genéricos sobre crédito personal y tasas, pero ninguna evidencia vehicular específica. Por tanto, el resultado es `KNOWLEDGE_GAP`, no una política de “48” o “60 meses”. El comportamiento seguro es **abstention** (abstención): informar que no hay evidencia suficiente y conservar la procedencia de los hits. La implementación v0.9.1 registra `knowledge_required_count`, `knowledge_tool_invoked_count`, `knowledge_tool_missed_count` y `knowledge_abstention_count`.

Esto se relaciona con Mibanco porque evita afirmar condiciones no vigentes o no autorizadas. También practica AI-103: tool-access controls, grounding, guardrails y supervisión. La alternativa es `tool_choice="required"` o una función específica, pero en `phi-4-mini` sigue siendo best effort; por eso la policy del host es el control determinista y el LLM solo redacta con evidencia disponible.

## 8. v0.9.2: Banking Read Tool Routing

Un **account query** (consulta de cuenta) pide datos particulares del cliente autenticado, no conocimiento general. Por ejemplo, “¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?” requiere primero `get_my_loans` y después una READ (*operación de lectura*) como `get_next_installment`. La identidad no la decide el LLM: proviene de `AgentContext.session_customer_id` y cada tool aplica ownership.

La policy selecciona una **tool allowlist** (lista permitida mínima). Para listar préstamos se expone `get_my_loans`; para una próxima cuota se expone `get_next_installment`; para detalle se expone `get_loan_details`. En una consulta combinada, el host obtiene primero la lista autorizada y luego ofrece solo la tool de seguimiento. Esto reduce tool selection ambiguity y aplica **policy-enforced routing** sin cambiar `phi-4-mini` ni introducir una nueva escritura.

`tool_choice="auto"` sigue siendo adecuado para saludos y preguntas sin datos bancarios. Cuando la policy ya determinó que una READ es obligatoria, se usa un `tool_choice` específico. Si el modelo escribe `get_my_loans()` como texto, no se parsea: se registra `PSEUDO_TOOL_CALL`/`ROUTING_FAILURE` y no se ejecuta. Esta separación es importante para Mibanco: una respuesta factual sobre saldos o cuotas debe consultar la fuente de verdad, y AI-103 relaciona el patrón con function calling, tool-access controls y safeguards.

## 9. v0.10: Quality Engineering

**Quality Engineering** diseña calidad como propiedad del flujo completo, no como una inspección final. La **test pyramid** coloca muchos unit tests rápidos abajo, integration y contract tests en el centro y pocos E2E críticos arriba. AegisBank evita duplicar: los contratos comprueban interfaces, mientras que los E2E comprueban journeys.

**CI** (*Continuous Integration*, integración continua) significa que cada cambio pasa el pipeline. Un workflow local solo demuestra `CI-CONFIGURED`; un **runner** (máquina ejecutora) es necesario para `CI-EXECUTED`. **CD** puede ser *Continuous Delivery* (listo para promoción controlada) o *Continuous Deployment* (despliegue automático); ambos quedan fuera de este hito.

En **DevSecOps** (*Development, Security and Operations*) aplicamos *shift-left security*: Bandit hace **SAST** (*Static Application Security Testing*) sobre el AST, pip-audit hace **SCA** (*Software Composition Analysis*) de dependencias y una SBOM (*Software Bill of Materials*) CycloneDX inventaría componentes. La SBOM responde “¿qué tenemos?”; SCA responde “¿hay vulnerabilidades conocidas?”. Para Mibanco esto refleja testing, hardening y gestión de dependencias. Para AI-103/AI-200 representa lifecycle, seguridad y operación de soluciones de IA.

---

## 10. v0.10.1: Integridad Arquitectónica y Coordinación Cross-Session

En entornos donde múltiples agentes de inteligencia artificial y desarrolladores colaboran sobre un mismo repositorio, surgen dos riesgos críticos:
1. **Duplicación de Código y Deriva Arquitectónica (*Architecture Drift*):** Un agente genera una nueva clase o helper (e.g. `HumanApprovalService`) en lugar de descubrir y reutilizar la implementación canónica existente (`HITLApprovalManager`). Esto viola el principio **DRY** (*Don't Repeat Yourself*), multiplica la superficie de ataque y genera deuda técnica.
2. **Condiciones de Carrera Cross-Session (*Race Conditions*):** Si dos sesiones de IA escriben concurrentemente en el mismo *working tree* sin coordinación, una sesión puede sobrescribir silenciosamente los cambios de la otra.

AegisBank resuelve esto mediante dos pilares:
* **DISCOVER BEFORE CREATE:** Regla de oro que exige buscar símbolos existentes, revisar el catálogo oficial [`CANONICAL-COMPONENTS.md`](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/docs/architecture/CANONICAL-COMPONENTS.md) y clasificar la decisión en `REUSE`, `EXTEND` o `NEW_COMPONENT_JUSTIFIED` antes de escribir código.
* **ONE WRITER, MANY READERS:** Protocolo de coordinación pesimista implementado en [`scripts/session_guard.py`](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/scripts/session_guard.py) que gestiona bloqueos atómicos en `.coordination/active-writer.json` sin recurrir a *worktrees* de Git. El guardián valida la inmutabilidad del HEAD (`AEGISBANK_CROSS_SESSION_HEAD_MOVED`) y confina los cambios a las rutas declaradas en `allowed_paths` (`AEGISBANK_CROSS_SESSION_PATH_COLLISION`).

---

## 11. v0.11: Contenerización y Mensajería Azure Local (AI-200 Mapping)

El examen oficial **Microsoft AI-200** (*Designing and Implementing a Microsoft Azure AI Solution*) asigna un 20–25% del temario a arquitecturas contenerizadas, integración con Azure Container Registry (ACR), Azure Container Apps, orquestación en AKS, autoescalado guiado por eventos con KEDA y mensajería empresarial con Azure Service Bus.

AegisBank domina estos conceptos de forma local y reproducible mediante el siguiente mapeo bidireccional:

| Capacidad Arquitectónica | Laboratorio Local (AegisBank v0.11) | Producción Cloud Azure (AI-200 Target) | Estado de Madurez |
|---|---|---|---|
| **Empaquetado de Aplicación** | `Dockerfile` multi-stage Linux, usuario no-root (`aegisuser`), imagen local `aegisbank/mock-core-banking:0.11.0`. | Azure Container Registry (ACR) con escaneo de vulnerabilidades Trivy/Microsoft Defender. | `LAB-COVERED` / `CLOUD-PENDING` |
| **Composición de Servicios** | `deploy/local/docker-compose.yml` con red aislada `aegisbank-net`. | Azure Container Apps Environment o AKS Cluster con Virtual Networks (VNet). | `LAB-COVERED` / `CLOUD-PENDING` |
| **Mensajería Asíncrona** | Microsoft Azure Service Bus Emulator (`mcr.microsoft.com/azure-messaging/servicebus-emulator`) sobre AMQP (`5672`). | Azure Service Bus Namespace (Standard/Premium) con Managed Identity y TLS 1.3. | `LAB-COVERED` / `CLOUD-PENDING` |
| **Contrato de Mensajería** | Adapter `AzureServiceBusMessageBus` implementando la interfaz canónica `MessageBus` (`DISCOVER BEFORE CREATE`). | Mismo adapter sin cambios de lógica, variando únicamente el connection string o token OAuth Entra ID. | `LAB-COVERED` |
| **Autoescalado por Eventos** | Simulación de colas y consumo concurrente. | KEDA (*Kubernetes Event-driven Autoscaling*) escalando réplicas de contenedores desde 0 según longitud de cola. | `LAB-COVERED` / `CLOUD-PENDING` |
| **Inferencia de Modelos (LLM)** | Foundry Local (`phi-4-mini`) en el host de Windows, resolviendo vía `host.docker.internal` desde el contenedor. | Azure OpenAI Service / Foundry Cloud endpoints con Private Endpoints. | `LAB-COVERED` / `CLOUD-PENDING` |
| **Gestión de Secretos** | Variables de entorno inyectadas en Docker Compose (`Password123!`). | Azure Key Vault con Azure Key Vault Secrets CSI Driver o Container Apps Secrets. | `LAB-COVERED` / `CLOUD-PENDING` |

> [!NOTE]
> **Principio de Realismo de Laboratorio:** `Service Bus Emulator != Azure Service Bus producción`. El emulador local carece de SLA bancario, autenticación Microsoft Entra ID (Azure AD), VNet integration y geo-replicación, pero permite validar el protocolo AMQP, el ciclo de vida de mensajes (settlement), deduplicación y enrutamiento a Dead-Letter Queue (DLQ) con cero costo de infraestructura en la nube.
