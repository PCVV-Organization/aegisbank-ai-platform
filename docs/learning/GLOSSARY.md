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
19. [ADR — Architecture Decision Record](#adr)
20. [Observabilidad, Traza (Trace) y Correlation ID](#observabilidad)

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
* **¿Qué es?** Patrón donde el sistema ejecuta automáticamente ciertas acciones dentro de umbrales seguros, pero un operador humano supervisa en tiempo real, recibe alertas y puede intervenir o pausar el sistema si detecta anomalías.

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

### ADR
* **Nombre completo:** Architecture Decision Record (Registro de Decisión de Arquitectura).
* **¿Qué es?** Documento inmutable y versionado que captura una decisión arquitectónica clave, su contexto, sus alternativas evaluadas y sus consecuencias.

---

### Observabilidad
* **¿Qué es?** Capacidad de entender el estado interno de un sistema a partir de sus salidas externas: Métricas (números), Logs (eventos textuales) y Trazas (recorrido de una petición a través de varios componentes correlacionados por un `trace_id`).
