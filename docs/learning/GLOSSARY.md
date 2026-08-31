# AegisBank — Glosario Pedagógico Fundamental (De Cero a Experto)

Este glosario define cada término, sigla y concepto utilizado en la arquitectura de **AegisBank AI Platform**, con definiciones claras, sin asumir conocimientos previos y con ejemplos prácticos.

---

## Índice Alfabético

1. [AI / IA — Inteligencia Artificial](#ai--ia)
2. [LLM — Large Language Model](#llm)
3. [Prompt y Prompting](#prompt-y-prompting)
4. [RAG — Retrieval-Augmented Generation](#rag)
5. [Retrieval (Recuperación) y Chunking (Fragmentación)](#retrieval-y-chunking)
6. [Grounding (Fundamentación) y Citations](#grounding-y-citations)
7. [MCP — Model Context Protocol](#mcp)
8. [Tool Calling / Function Calling](#tool-calling)
9. [HITL — Human-in-the-Loop](#hitl)
10. [HOTL — Human-on-the-Loop](#hotl)
11. [Idempotencia e Idempotency-Key](#idempotencia)
12. [Retry (Reintento), Backoff y Jitter](#retry-backoff-jitter)
13. [Circuit Breaker (Cortacircuitos)](#circuit-breaker)
14. [Timeout (Tiempo Límite)](#timeout)
15. [Transactional Outbox Pattern (Bandeja de Salida Transaccional)](#transactional-outbox)
16. [Message Bus (Bus de Mensajes) y Queues](#message-bus)
17. [Idempotent Consumer (Consumidor Idempotente)](#idempotent-consumer)
18. [DLQ — Dead-Letter Queue (Cola de Mensajes Muertos)](#dlq)
19. [OTel — OpenTelemetry](#otel)
20. [Trace (Traza) y Span](#trace-y-span)
21. [Correlation ID vs. Trace ID](#correlation-id-vs-trace-id)
22. [Structured Logging (Logs Estructurados) y Redaction](#structured-logging-y-redaction)
23. [Operational Metrics (Métricas Operativas) y Percentiles](#operational-metrics)
24. [AgentOps — Operaciones de Agentes](#agentops)
25. [Audit Log (Registro de Auditoría)](#audit-log)
26. [KQL — Kusto Query Language](#kql)
27. [ADR — Architecture Decision Record](#adr)

---

### AI / IA
* **Nombre completo:** Artificial Intelligence / Inteligencia Artificial.
* **¿Qué es?** Campo de las ciencias de la computación enfocado en crear sistemas capaces de realizar tareas complejas que típicamente requerirían cognición humana (procesar texto, razonar sobre políticas, clasificar intenciones, estructurar respuestas).
* **En AegisBank:** Asistente educativo ("Aegis") que interpreta consultas de clientes y propone acciones bancarias seguras.

---

### LLM
* **Nombre completo:** Large Language Model (Modelo de Lenguaje Grande).
* **¿Qué es?** Red neuronal profunda (usualmente con arquitectura Transformer) entrenada con cientos de miles de millones de palabras para predecir y generar texto de forma coherente.
* **En AegisBank:** Usamos modelos locales como `phi-4-mini` (Foundry Local) para razonar e interpretar lenguaje natural sin enviar datos fuera de la máquina local.

---

### Prompt y Prompting
* **Prompt:** La instrucción estructurada que se le da al LLM.
* **Prompting:** La disciplina de diseñar, estructurar, versionar y evaluar las instrucciones para garantizar que el modelo no alucine, respete las reglas bancarias y produzca salidas estrictas.
* **En AegisBank:** Los prompts son versionados como código inmutable (`rag-answer-v001.json`, `agent-system-v002.json`).

---

### RAG
* **Nombre completo:** Retrieval-Augmented Generation (Generación Aumentada por Recuperación).
* **¿Qué es?** Patrón de arquitectura donde, antes de que el LLM responda, el sistema busca fragmentos de información autorizada en una base documental y se los pasa al LLM como contexto.
* **¿Qué problema resuelve?** Evita las "alucinaciones" (inventar datos) y permite al LLM responder con información privada y actualizada sin necesidad de reentrenar el modelo.

---

### Retrieval y Chunking
* **Chunking (Fragmentación):** Dividir documentos largos (ej. contratos, normativas) en piezas más pequeñas de tamaño controlado (`chk__...`), preservando su contexto.
* **Retrieval (Recuperación):** Algoritmo (léxico TF-IDF, semántico denso o híbrido RRF) que selecciona los fragmentos más relevantes para la consulta del usuario.

---

### Grounding y Citations
* **Grounding (Fundamentación):** Obligar al LLM a que cada afirmación de su respuesta esté 100% justificada en los fragmentos de contexto recuperados.
* **Citations:** Referencias explícitas (`[doc_id, v1, chunk_0]`) que validan la procedencia de cada dato.

---

### MCP
* **Nombre completo:** Model Context Protocol (Protocolo de Contexto de Modelos).
* **¿Qué es?** Estándar abierto creado por Anthropic y adoptado en la industria para que los agentes descubran y ejecuten herramientas (*tools*) y recursos de manera estandarizada y segura.
* **En AegisBank:** Servidor MCP en Python (`mcp==2.1.1`, protocolo `2026-07-28`) comunicado por `stdio`.

---

### Tool Calling
* **¿Qué es?** Mecanismo donde el LLM no ejecuta código por sí mismo, sino que emite una estructura JSON solicitando invocar una función específica (ej. `get_my_loans()`, `create_service_request()`). El código host valida y ejecuta la función.

---

### HITL
* **Nombre completo:** Human-in-the-Loop (Humano en el Ciclo).
* **¿Qué es?** Patrón de gobernanza y seguridad donde el agente IA puede proponer una acción que cambia el estado (WRITE), pero **requiere la aprobación explícita de un ser humano** antes de que el sistema la ejecute.
* **En AegisBank:** Ninguna creación de reclamo (`create_service_request`) se ejecuta sin confirmación interactiva humana previa (`Approve? [y/N]`).

---

### HOTL
* **Nombre completo:** Human-on-the-Loop (Humano sobre el Ciclo).
* **¿Qué es?** Patrón donde el sistema opera con supervisión continua de un operador humano que monitorea métricas operativas, alertas en tiempo real y cuenta con un **Kill-Switch supervisorio** para desactivar capacidades (ej. escrituras) si detecta anomalías.

---

### Idempotencia
* **Definición:** Propiedad de una operación de generar exactamente el mismo resultado final independientemente de si se ejecuta 1 vez o 100 veces.
* **Idempotency-Key:** Identificador único enviado con una petición para que el servidor recuerde el resultado de la primera ejecución y no procese duplicados.

---

### Retry, Backoff y Jitter
* **Retry (Reintento):** Volver a intentar una llamada fallida si el error es temporal (transitorio).
* **Exponential Backoff:** Multiplicar el tiempo de espera entre intentos sucesivos ($2^n$).
* **Jitter:** Introducir ruido aleatorio al tiempo de espera para que miles de clientes desconectados no reintenten en el mismo instante.

---

### Circuit Breaker
* **Nombre completo:** Cortacircuitos de software.
* **¿Qué es?** Patrón que detecta cuando un servicio dependiente está caído de forma continua y "abre el circuito", fallando de inmediato para evitar desperdiciar recursos y saturar el servicio en problemas.

---

### Timeout
* **¿Qué es?** Límite estricto de tiempo que una llamada puede esperar antes de ser cancelada, evitando bloqueos indefinidos o hilos colgados.

---

### Transactional Outbox
* **¿Qué es?** Patrón de diseño donde los cambios en la base de datos y los eventos de negocio a publicar se guardan en la **misma transacción SQL atómica**, garantizando que nunca se pierda un evento.

---

### Message Bus
* **¿Qué es?** Infraestructura que permite la comunicación asíncrona y desacoplada entre componentes mediante el envío y recepción de mensajes y eventos.

---

### Idempotent Consumer
* **¿Qué es?** Consumidor de mensajes que verifica si ya procesó previamente el `event_id` recibido antes de ejecutar su lógica, evitando duplicaciones derivadas de la entrega *at-least-once*.

---

### DLQ
* **Nombre completo:** Dead-Letter Queue (Cola de Mensajes Muertos).
* **¿Qué es?** Cola secundaria a donde se envían automáticamente los mensajes que fallaron repetidamente y no pudieron procesarse tras alcanzar el número máximo de reintentos (*poison messages*).

---

### OTel
* **Nombre completo:** OpenTelemetry.
* **¿Qué es?** Estándar abierto y vendor-neutral de la CNCF para instrumentar, generar, recolectar y exportar telemetría (trazas, métricas y logs) en aplicaciones modernas e IA.

---

### Trace y Span
* **Trace (Traza):** El recorrido completo de una petición distribuida de punta a punta a través de todos los componentes.
* **Span:** Unidad individual de trabajo dentro de una traza con nombre, hora de inicio, hora de fin, atributos, eventos y estado.

---

### Correlation ID vs. Trace ID
* **Correlation ID:** Identificador generado a nivel de negocio/aplicación para correlacionar una interacción de usuario (`CORR-20260830-001`).
* **Trace ID:** Identificador hexadecimal de 128 bits generado por OpenTelemetry para la traza técnica distribuida.

---

### Structured Logging y Redaction
* **Structured Logging:** Emisión de logs en formato JSON con campos uniformes (`timestamp`, `level`, `correlation_id`, `trace_id`, `event_name`, `latency_ms`).
* **Redaction (Enmascaramiento):** Filtrado automático para eliminar API keys, contraseñas, tokens y prompts confidenciales de los registros.

---

### Operational Metrics
* **¿Qué son?** Mediciones numéricas agregadas en el tiempo (contadores de llamadas, tasas de error, percentiles de latencia p50, p95, p99) para evaluar la salud del agente.

---

### AgentOps
* **Nombre completo:** Agent Operations (Operaciones de Agentes IA).
* **¿Qué es?** Disciplina que gestiona el ciclo de vida, observabilidad, calidad, costos, latencia y estabilidad operativa de agentes IA en producción.

---

### Audit Log
* **¿Qué es?** Registro inmutable, secuencial y persistente (*append-only*) de eventos críticos de seguridad y negocio que permite reconstruir fehacientemente quién hizo qué, cuándo, con qué autorización y cuál fue el resultado.

---

### KQL
* **Nombre completo:** Kusto Query Language.
* **¿Qué es?** Lenguaje de consultas potente y optimizado para analizar grandes volúmenes de telemetría estructurada en Azure Monitor, Azure Log Analytics y Microsoft Sentinel.

---

### ADR
* **Nombre completo:** Architecture Decision Record (Registro de Decisión de Arquitectura).
* **¿Qué es?** Documento inmutable y versionado que captura una decisión arquitectónica clave, su contexto, sus alternativas evaluadas y sus consecuencias.

---

### Tool Routing y Knowledge Gap
* **Tool routing (enrutamiento de herramientas):** Decisión del sistema sobre cuándo y cómo ejecutar una herramienta. `tool_choice=auto` deja esa decisión al LLM; el routing impuesto por policy la exige para clases de preguntas concretas.
* **Knowledge base (base de conocimiento):** Colección autorizada de documentos y chunks que el sistema puede recuperar.
* **Knowledge gap:** No existe evidencia suficiente en la base autorizada para responder. AegisBank debe abstenerse, no completar el dato con memoria del LLM.
* **Routing gap:** La evidencia podría existir, pero el agente no emitió un `tool_call` estructurado. Es distinto de un knowledge gap.
* **En AegisBank:** Políticas, requisitos, tasas, comisiones y plazos se recuperan antes de la generación; las citas conservan `document_id`, versión y `chunk_id`.

### Account Query y Tool Allowlist
* **Account query:** Pregunta que necesita datos específicos de la cuenta autenticada, por ejemplo “mis préstamos” o “mi próxima cuota”.
* **Tool allowlist:** Subconjunto explícito de herramientas que el modelo puede ver para una intención. Limitarlo reduce ambigüedad y superficie de riesgo.
* **Policy-enforced routing:** Para datos personales, la aplicación fuerza primero la consulta READ autorizada; el LLM no decide si puede responder desde memoria.
* **En AegisBank:** `AgentContext.session_customer_id` determina la identidad y `get_loan_details`/`get_next_installment` validan ownership. Nunca se acepta `customer_id` suministrado por el LLM.

### QA, CI, SAST, SCA y SBOM
* **QA:** Quality Assurance (aseguramiento de calidad), proceso que demuestra que una promesa del sistema se cumple.
* **CI:** Continuous Integration (integración continua), ejecución automática de validaciones por cambio.
* **SAST:** Static Application Security Testing (análisis estático), inspección del código sin ejecutarlo; AegisBank usa Bandit.
* **SCA:** Software Composition Analysis (análisis de composición), auditoría de dependencias; AegisBank usa pip-audit.
* **SBOM:** Software Bill of Materials (lista de materiales de software), inventario CycloneDX de componentes. No es un escaneo de vulnerabilidades.
* **En AegisBank:** `scripts/quality_gate.py` encadena estos controles. La workflow es `CI-CONFIGURED / RUNNER-PENDING` hasta que un runner de GitHub produzca evidencia.

---

### Arquitectura, Integridad y Coordinación Cross-Session (v0.10.1)

* **DRY (Don't Repeat Yourself / No te repitas):** Principio de diseño de software formulado por Andy Hunt y Dave Thomas que postula que "cada pieza de conocimiento o responsabilidad debe tener una representación única, inequívoca y autorizada dentro de un sistema". No prohíbe líneas de código sintácticamente similares que tienen propósitos de negocio distintos; prohíbe duplicar la misma regla de negocio en varios lugares.
* **Code Duplication (Duplicación de código):** Existencia de múltiples bloques de código idénticos o estructuralmente equivalentes que resuelven exactamente la misma responsabilidad, aumentando el costo de mantenimiento y el riesgo de inconsistencia ante cambios.
* **Code Smell (Olor a código):** Síntoma superficial en el código fuente que suele indicar un problema de diseño o arquitectura subyacente (e.g. clases monstruo, métodos excesivamente largos, lógica copiada y pegada).
* **Technical Debt (Deuda técnica):** Metáfora de Ward Cunningham que describe el costo implícito del retrabajo futuro causado por elegir una solución rápida y subóptima en el presente en lugar de un diseño arquitectónicamente robusto.
* **Refactoring (Refactorización):** Proceso disciplinado de reestructurar el código existente sin alterar su comportamiento observable externo, con el fin de mejorar su legibilidad, reducir su complejidad o facilitar su extensibilidad.
* **Cohesion (Cohesión):** Grado en que los elementos internos de un módulo o clase pertenecen juntos y colaboran estrechamente para cumplir una única responsabilidad bien definida (*Single Responsibility Principle*).
* **Coupling (Acoplamiento):** Nivel de interdependencia entre diferentes módulos o clases de software. Un bajo acoplamiento (*loose coupling*) permite modificar un componente sin afectar a otros.
* **Canonical Component (Componente canónico):** Implementación oficial, autorizada y única designada para asumir una responsabilidad arquitectónica concreta dentro de la plataforma (e.g. `RetryPolicy` para reintentos, `HITLApprovalManager` para aprobaciones).
* **Single-Writer Principle (Principio de escritor único):** Regla de concurrencia pesimista (*pessimistic coordination*) que establece que un único proceso, agente o sesión puede poseer permisos de escritura sobre un recurso compartido (en este caso, el working tree local de Git) a la vez, mientras múltiples lectores concurrentes están permitidos.
* **Concurrency (Concurrencia):** Capacidad de un sistema para gestionar la ejecución de múltiples tareas o procesos que se solapan en el tiempo.
* **Race Condition (Condición de carrera):** Modos de fallo donde el resultado final de una operación depende del orden temporal o entrelazado no controlado en que se ejecutan múltiples hilos o procesos concurrentes.
* **Ownership (Propiedad / Dominio de código):** Delimitación explícita de qué componente o módulo es responsable de cada conjunto de rutas, datos o reglas de negocio dentro del repositorio.
* **Lease / Lock (Arrendamiento / Bloqueo):** Mecanismo de sincronización que concede acceso exclusivo temporal a un recurso a un titular específico mediante la creación atómica de un identificador no reescribible.
* **HEAD:** Puntero en Git que referencia el commit actual sobre el que está posicionado el repositorio.
* **Working Tree (Árbol de trabajo):** Directorio local del sistema de archivos donde residen los archivos descomprimidos y editables del proyecto.
* **Staging / Index (Área de preparación):** Espacio intermedio de Git donde se seleccionan y preparan explícitamente los cambios que formarán parte del siguiente commit.
* **CI Concurrency (Concurrencia en CI):** Configuración en pipelines de integración continua (e.g. GitHub Actions) que previene la ejecución simultánea de múltiples ejecuciones de workflow sobre la misma rama o pull request, cancelando ejecuciones obsoletas intermedias.
* **CODEOWNERS:** Mecanismo nativo de plataformas como GitHub y GitLab que asigna automáticamente revisores o aprobadores obligatorios a pull requests en función de las rutas de archivos modificadas.
