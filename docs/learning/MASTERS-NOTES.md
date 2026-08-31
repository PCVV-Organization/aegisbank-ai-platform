# AegisBank — Notas de Cátedra de Nivel Maestría en Inteligencia Artificial

> **Módulo:** Arquitectura Agéntica, Resiliencia y Sistemas de Mensajería para Banca  
> **Nivel:** Maestría / Posgrado en Inteligencia Artificial  
> **Profesor / Lead Architect:** Senior Principal AI Engineer  
> **Hito del Proyecto:** `v0.8.0 — Reliability + Messaging Foundation`

---

## 1. Introducción al Problema de la Escritura en Sistemas de IA

En las fases anteriores (`v0.1` a `v0.7`), construimos un agente capaz de:
1. Responder consultas fundamentadas en conocimiento autorizado mediante **RAG** (Retrieval-Augmented Generation).
2. Consultar saldos y cronogramas de préstamos mediante herramientas de lectura seguras (**READ tools**).
3. Formular una propuesta de reclamo bancario a través de **MCP** (Model Context Protocol).
4. Exigir la aprobación interactiva de un ser humano (**HITL**) antes de cualquier ejecución en el sistema transaccional.

Sin embargo, en el mundo real de la banca y la nube:
* Las redes fallan momentáneamente (*transient network glitches*).
* Los clientes pierden conectividad y reintentan la misma operación.
* Los servidores transaccionales pueden estar caídos o saturados.
* Las bases de datos pueden bloquearse (*database locking*).

Si un sistema de IA ejecuta escrituras sin una **base de confiabilidad (Reliability)**, ocurren desastres financieros:
* **Duplicación de reclamos o transacciones**.
* **Pérdida de eventos de negocio**.
* **Saturación en cascada (*cascading failures*)**.

El hito **`v0.8.0`** resuelve este problema mediante una arquitectura bancaria de grado empresarial.

---

## 2. Los Ocho Pilares de Confiabilidad de AegisBank

---

### Pilar 1: Idempotencia (*Idempotency*)

```
               Petición 1 (Key: IDEMP-001)
  Agente/Cliente --------------------------> [ Idempotency Guard ]
                                                      |
                                             ¿Existe en BD?
                                            /              \
                                          NO               SÍ
                                          /                  \
                            [ Ejecutar WRITE ]        [ Retornar Respuesta ]
                            [ Guardar Hash/Respuesta] [ Cachada Inmediata  ]
```

1. **Sigla y Nombre:** `Idempotency` (Idempotencia).
2. **Definición Teórica:** Para una función $f(x)$, la propiedad de idempotencia establece que $f(f(x)) = f(x)$. En sistemas distribuidos, enviar la misma solicitud $N$ veces produce exactamente el mismo cambio de estado que enviarla 1 sola vez.
3. **¿Qué problema resuelve?** La duplicación accidental de recursos bancarios cuando ocurren reintentos de red, timeouts o doble clic del usuario.
4. **Cómo funciona internamente:**
   - La petición incluye una llave única llamada `Idempotency-Key` (ej. UUIDv4 o digest determinista).
   - Se calcula el hash canónico SHA-256 de los parámetros de la solicitud:
     $$\text{hash} = \text{SHA256}(\text{canonical\_json}(\text{arguments}))$$
   - En la base de datos se consulta la tabla `idempotency_records`:
     - **Caso A (Nueva):** Se ejecuta la operación, se guarda el resultado y el hash atómicamente.
     - **Caso B (Duplicada idéntica):** Se retorna la respuesta guardada previamente con estado HTTP 200/201 sin volver a ejecutar la lógica de negocio.
     - **Caso C (Misma llave, datos alterados):** Se detecta que $\text{hash}_{\text{nuevo}} \neq \text{hash}_{\text{guardado}}$ y se lanza un error de conflicto (`IdempotencyConflictError`).
5. **Por qué lo necesita AegisBank:** Porque si el agente o la red reintenta la creación de un reclamo `create_service_request`, el cliente solo debe tener un único reclamo registrado.
6. **Alternativa y cuándo NO usarlo:** No se necesita en operaciones puramente de lectura (los métodos `GET` en REST son naturalmente idempotentes).
7. **Riesgos típicos:** Generar llaves no únicas o no comparar los argumentos, lo que permitiría que una segunda operación distinta use la llave de la primera y quede enmascarada.
8. **Relación con Mibanco (Perfil COE IA):** "Manejo de transacciones, consistencia y prevención de reprocesos en automatizaciones agénticas".
9. **Relación con Microsoft Certifications:**
   - **AI-103 / AI-200:** Mensajería y APIs resilientes en Azure API Management y Azure Service Bus.
10. **Ejemplo en el código:** Módulo `aegisbank_agent.reliability.idempotency` y tabla `idempotency_records`.

---

### Pilar 2: Tiempos Límite (*Timeouts*)

1. **Nombre:** Timeouts (Tiempos máximos de espera).
2. **Definición:** Límite temporal estricto tras el cual una llamada a una dependencia externa se cancela forzosamente.
3. **¿Qué problema resuelve?** Bloqueo indefinido de hilos/recursos por servicios remotos lentos (*thread pool starvation*).
4. **Cómo funciona internamente:** Se programa un temporizador no bloqueante. Si la corutina o función no concluye antes de $\Delta t$, se interrumpe y se genera una excepción `ExecutionTimeoutError`.
5. **Por qué lo necesita AegisBank:** Evita que el agente se quede colgado si Core Banking tarda en responder.
6. **Alternativa:** Dejar que el sistema operativo cierre la conexión TCP tras minutos (muy lento e inaceptable para SLAs bancarios).
7. **Riesgos:** Configurar timeouts demasiado cortos que aborten transacciones normales en horas punta.
8. **Relación con Mibanco:** Cumplimiento de **SLA operativos** y tiempos de respuesta.
9. **Relación con AI-200:** Políticas de timeout en Azure Functions y Azure Container Apps.

---

### Pilar 3: Reintentos Acotados con Retroceso Exponencial y Jitter

```
Intento 0: Falla (t=0)
           |-- Espera t1 = Base * 2^0 + Jitter (ej. 100ms + 23ms)
Intento 1: Falla
           |-- Espera t2 = Base * 2^1 + Jitter (ej. 200ms + 45ms)
Intento 2: Falla
           |-- Espera t3 = Base * 2^2 + Jitter (ej. 400ms + 89ms)
Intento 3: Éxito o Aborto definitivo
```

1. **Nombre:** Bounded Exponential Backoff with Jitter.
2. **Algoritmo Matemático:**
   Para el intento $n \in \{0, 1, \dots, N-1\}$:
   $$\text{Backoff}(n) = \min(\text{MaxDelay}, \text{BaseDelay} \times 2^n)$$
   $$\text{ActualDelay}(n) = \text{random.uniform}(0, \text{Backoff}(n)) \quad \text{(Full Jitter)}$$
3. **¿Qué problema resuelve?** Recuperarse automáticamente de micro-cortes de red sin saturar al servidor destino con una tormenta simultánea de reintentos (*thundering herd problem*).
4. **Regla de Clasificación de Errores:**
   * **Reintentables (Transitorios):** Conexión reseteada, timeout de socket, base de datos bloqueada temporalmente (`SQLITE_BUSY`).
   * **NO Reintentables (Permanentes):** Error de validación de datos (HTTP 400), credencial incorrecta (HTTP 401/403), rechazo humano en HITL, conflicto de idempotencia (HTTP 409).
5. **Precondición Innegociable:** **Idempotencia previa**. Nunca reintentar una escritura si no se cuenta con `Idempotency-Key`.
6. **Relación con AI-200:** Transient Fault Handling con librerías Polly en .NET o Tenacity en Python sobre servicios Azure.

---

### Pilar 4: Cortacircuitos (*Circuit Breaker Pattern*)

```
             Fallas < Umbral
           +-----------------+
           |                 |
           v                 |
      +--------+         +------+
      | CLOSED | ------> | OPEN |
      +--------+  Fallas +------+
          ^       >= Umbral  |
          |                  | Cooldown expirado
          |  1 Éxito         v
          +------------ +-----------+
                        | HALF_OPEN |
                        +-----------+
                             |
                             | 1 Falla
                             +-------> (Regresa a OPEN)
```

1. **Nombre:** Circuit Breaker (Cortacircuitos de Software).
2. **Estados del Autómata Finito:**
   * **`CLOSED` (Cerrado):** Estado normal. Las peticiones fluyen hacia la dependencia. Si falla, se incrementa el contador de fallas consecutivas.
   * **`OPEN` (Abierto):** Al alcanzar el umbral de fallas consecutivas (ej. 3 fallas), el circuito se abre. Todas las peticiones entrantes son rechazadas **instantáneamente** con `CircuitBreakerOpenError`, sin tocar la red.
   * **`HALF_OPEN` (Semi-abierto):** Tras expirar un tiempo de enfriamiento (*cooldown*, ej. 2.0s), se deja pasar una única petición de sondeo (*probe*). Si tiene éxito, el circuito vuelve a `CLOSED`; si falla, regresa a `OPEN`.
3. **¿Qué problema resuelve?** Evita el efecto dominó o fallo en cascada en arquitecturas de microservicios y protege los recursos cuando una dependencia está caída.
4. **Diferencia clave con Retry:**
   * *Retry* reintenta una llamada asumiendo que el fallo pasará en milisegundos.
   * *Circuit Breaker* detiene los reintentos cuando detecta que la falla es sistémica y durará segundos o minutos.

---

### Pilar 5: Bandeja de Salida Transaccional (*Transactional Outbox Pattern*)

```
[ BASE DE DATOS TRANSACCIONAL ]
+-------------------------------------------------------------+
|                                                             |
|   BEGIN TRANSACTION;                                        |
|                                                             |
|   1. INSERT INTO service_requests (...) VALUES (...);       |
|   2. INSERT INTO outbox_events (event_id, payload, PENDING) |
|                                                             |
|   COMMIT;                                                   |
|                                                             |
+-------------------------------------------------------------+
                            |
                     (Proceso Asíncrono)
                            |
                            v
             [ Local Message Bus / Event Bus ]
                            |
                            v
             [ Consumidores / Notificaciones ]
```

1. **Nombre:** Transactional Outbox Pattern.
2. **¿Qué problema resuelve?** El problema de la "Doble Escritura" (*Dual-Write Problem*). Si una aplicación intenta escribir en la base de datos SQL y enviar un mensaje a un bus (como Azure Service Bus) en dos pasos separados, inevitablemente ocurrirá que uno de los dos falle, dejando el sistema en estado inconsistente.
3. **Cómo funciona:**
   - La creación del reclamo bancario y la inserción del evento `ServiceRequestCreated` se ejecutan dentro del mismo bloque transaccional atómico (`session.commit()`).
   - Una tarea en segundo plano (*Outbox Processor*) lee los eventos en estado `PENDING`, los despacha al bus de mensajes y los marca como `PUBLISHED`.
4. **Relación con Mibanco:** "Garantía de auditoría, trazabilidad y consistencia transaccional".

---

### Pilar 6: Abstracción de Mensajería Local (*Local Message Bus*)

1. **Nombre:** Message Bus Abstraction (Bus de Mensajes Desacoplado).
2. **Diseño:** Creamos una interfaz agnóstica (`MessageBus`) que permite publicar eventos a tópicos y suscribir colas consumidoras.
3. **Local vs Cloud:**
   - En `v0.8` (local): Bus en memoria / SQLite determinista, sin necesidad de infraestructura pesada.
   - En `v0.9+` / Cloud (AI-200): Se reemplaza la implementación concreta por **Azure Service Bus Topics/Subscriptions** sin alterar una sola línea de lógica de negocio.

---

### Pilar 7: Consumidor Idempotente (*Idempotent Consumer*)

1. **Nombre:** Idempotent Consumer Pattern.
2. **¿Qué problema resuelve?** Los sistemas de colas profesionales (Azure Service Bus, RabbitMQ, Kafka) garantizan entrega "al menos una vez" (*at-least-once delivery*), lo que significa que en casos raros de reconexión de red, un mismo mensaje puede ser entregado dos veces al consumidor.
3. **Cómo funciona:** El consumidor mantiene una tabla o conjunto de `processed_event_ids`. Cuando recibe un mensaje, verifica si el `event_id` ya fue procesado: si ya existe, lo descarta silenciosamente con éxito sin volver a ejecutar la acción.

---

### Pilar 8: Cola de Mensajes Muertos (*Dead-Letter Queue - DLQ*)

```
[ Mensaje Entrante ] ---> Intento 1 (Falla) ---> Intento 2 (Falla) ---> Intento 3 (Falla)
                                                                             |
                                                                             v
                                                                   [ Mover a DLQ ]
                                                                   (Error: Formato inválido)
```

1. **Sigla y Nombre:** DLQ — Dead-Letter Queue (Cola de Mensajes Muertos).
2. **¿Qué es?** Cola secundaria reservada para almacenar mensajes que no pueden ser procesados exitosamente tras agotar los reintentos permitidos (*poison messages*).
3. **¿Qué problema resuelve?** Evita que un mensaje defectuoso bloquee la cola principal en un ciclo infinito de fallas (*poison pill block*), permitiendo a los ingenieros de soporte inspeccionar el mensaje y su causa raíz.
4. **Relación con Azure (AI-200):** Azure Service Bus habilita DLQ nativo configurando `MaxDeliveryCount`.

---

## 3. Matriz Comparativa: Implementación Local v0.8 vs Equivalente Azure (AI-200)

| Concepto de Confiabilidad | Implementación Local en AegisBank (v0.8) | Equivalente Cloud en Azure (AI-200 / Producción) |
|---|---|---|
| **Idempotency** | `IdempotencyGuard` + SQLite `idempotency_records` | Azure Service Bus Duplicate Detection / Azure Cosmos DB ETag |
| **Retries & Backoff** | `RetryPolicy` (Python con Exponential Backoff & Jitter) | Azure SDK built-in Retry Policies / Polly en Azure Functions |
| **Circuit Breaker** | `CircuitBreaker` (FSM `CLOSED`, `OPEN`, `HALF_OPEN`) | Azure App Gateway / Dapr Resiliency Policies / Envoy Proxy |
| **Timeouts** | `with_timeout` (Python `asyncio.timeout` / threading) | HTTP Request Timeouts en Azure API Management / Function Timeouts |
| **Transactional Outbox** | SQLite `outbox_events` en transacción atómica | SQL Database Outbox + Change Data Capture (CDC) / Debezium |
| **Message Bus** | `LocalMessageBus` (En memoria / SQLite) | **Azure Service Bus Topics & Queues** / Azure Event Grid |
| **Idempotent Consumer** | `IdempotentConsumer` con registro de `event_id` | Azure Service Bus Session Processing + Deduplication Store |
| **Dead-Letter Queue (DLQ)** | `DeadLetterQueue` local con tracking de fallas | **Azure Service Bus Dead-Letter Sub-queue (`$deadletterqueue`)** |

---

## 4. Síntesis para Examen de Maestría / Entrevista Técnica en Mibanco

1. **¿Por qué la idempotencia debe preceder a los reintentos?**  
   *Respuesta:* Reintentar una operación no idempotente ante un error transitorio duplica la transacción si la petición original sí llegó a la base de datos pero la respuesta de red se perdió.
2. **¿Qué diferencia a un Circuit Breaker de un Retry Policy?**  
   *Respuesta:* El Retry mitiga fallos transitorios en milisegundos aislando la petición individual; el Circuit Breaker protege al sistema contra fallos persistentes deteniendo proactivamente el tráfico hacia la dependencia dañada.
3. **¿Cómo garantiza el Transactional Outbox que no haya inconsistencias?**  
   *Respuesta:* Al acoplar la mutación del agregado y el registro del evento en la misma transacción ACID de la base de datos, eliminando la posibilidad de que una ocurra sin la otra.
