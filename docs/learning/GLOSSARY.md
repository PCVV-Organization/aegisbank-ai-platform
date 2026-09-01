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

---

### Contenedores y Mensajería Azure (v0.11.0)

* **Container (Contenedor):** Instancia estándar, aislada y ejecutable de un software que empaqueta código, bibliotecas y dependencias del sistema operativo, compartiendo el kernel del host sin la sobrecarga de una máquina virtual.
* **Container Image (Imagen de contenedor):** Paquete binario estático, inmutable y compuesto por capas superpuestas de solo lectura que contiene la plantilla para instanciar contenedores.
* **Dockerfile:** Archivo declarativo de texto plano con instrucciones secuenciales (`FROM`, `COPY`, `RUN`, `USER`, `EXPOSE`, `CMD`) que define la receta para construir una imagen de contenedor reproducible.
* **Docker Compose:** Herramienta y formato declarativo YAML para definir, configurar y coordinar la ejecución multi-contenedor de aplicaciones complejas y sus redes/volúmenes locales.
* **Registry (Registro de contenedores):** Servicio de almacenamiento y distribución indexada de imágenes de contenedores (e.g. Docker Hub, Azure Container Registry - ACR, GitHub Container Registry).
* **OCI (Open Container Initiative / Iniciativa de Contenedores Abiertos):** Estándar de la industria gobernado por la Linux Foundation que especifica los formatos de imagen (*Image Spec*) y entornos de ejecución (*Runtime Spec*) para garantizar portabilidad universal entre Docker, containerd, Podman y Kubernetes.
* **Port Mapping (Mapeo de puertos):** Configuración de traducción de direcciones de red (NAT) que vincula un puerto del host local (e.g. `8000`) a un puerto interno del contenedor (e.g. `8000`), permitiendo el tráfico entrante.
* **Container Network (Red de contenedores):** Capa de red virtual aislada (comúnmente tipo *bridge*) gestionada por el runtime que permite a los contenedores comunicarse entre sí mediante resolución DNS interna por nombre de servicio (e.g. `mssql`, `mock-core-banking`).
* **Health Check (Comprobación de salud):** Mecanismo periódico definido en el Dockerfile o orquestador que ejecuta un comando dentro del contenedor para verificar si el servicio está respondiendo adecuadamente y puede procesar tráfico.
* **Readiness Probe (Sonda de preparación):** Sonda de orquestación (Kubernetes / Container Apps) que determina si el contenedor ha completado su inicialización y está listo para recibir peticiones del balanceador de carga.
* **Liveness Probe (Sonda de vida):** Sonda de orquestación que determina si el proceso principal del contenedor sigue vivo y en estado saludable; si falla, el orquestador destruye y reinicia el contenedor automáticamente.
* **Environment Variable (Variable de entorno):** Parámetro dinámico inyectado en tiempo de ejecución en el proceso del contenedor para configurar comportamiento (`AEGISBANK_ENV`, URLs) sin modificar el código fuente inmutable.
* **Secret (Secreto):** Objeto de configuración sensible protegido (contraseñas, llaves criptográficas, connection strings) que debe inyectarse en memoria en tiempo de ejecución (e.g. Azure Key Vault, Docker Secrets) y nunca hornearse dentro de una imagen de contenedor.
* **Volume (Volumen de almacenamiento):** Directorio o mecanismo de persistencia gestionado por el host que desacopla los datos del ciclo de vida efímero del contenedor, permitiendo persistencia duradera.
* **AMQP (Advanced Message Queuing Protocol / Protocolo Avanzado de Encolamiento de Mensajes):** Protocolo binario de red estándar abierto a nivel de aplicación (puerto `5672`) optimizado para enrutamiento, encolamiento y entrega fiable de mensajes entre sistemas heterogéneos.
* **Azure Service Bus:** Servicio empresarial administrado de mensajería como plataforma (MaaS) de Microsoft Azure que ofrece colas punto a punto fiables y tópicos pub/sub con garantías transaccionales y DLQ.
* **Queue (Cola de mensajes):** Estructura de datos primero en entrar, primero en salir (FIFO) donde los productores depositan mensajes y un único consumidor los procesa mediante el patrón de entrega punto a punto.
* **Topic (Tópico de mensajería):** Entidad de mensajería de tipo publicación/suscripción (Pub/Sub) que permite a un emisor publicar un evento y distribuirlo concurrentemente a múltiples suscriptores independientes.
* **Subscription (Suscripción a tópico):** Receptor lógico adjunto a un tópico que filtra y retiene copias de los mensajes publicados para que un consumidor específico los procese independientemente.
* **KEDA (Kubernetes Event-driven Autoscaling / Autoescalamiento de Kubernetes Guiado por Eventos):** Componente de orquestación que monitoriza fuentes de eventos externas (e.g. longitud de cola en Azure Service Bus) para autoescalar contenedores desde 0 hasta N instancias en función de la demanda en Azure Container Apps o AKS.
* **Azure Container Apps:** Plataforma serverless totalmente administrada de Azure construida sobre Kubernetes que permite ejecutar microservicios y trabajos en contenedores con autoescalado KEDA, revisiones automáticas y baja sobrecarga operativa.
* **Kubernetes (K8s):** Sistema de código abierto de nivel empresarial para automatizar el despliegue, escalado, balanceo de carga y gestión de aplicaciones contenerizadas en clústeres de servidores.
* **AKS (Azure Kubernetes Service):** Servicio de Kubernetes administrado por Microsoft en Azure donde el plano de control (*control plane*) es operado por Microsoft, permitiendo control exhaustivo de infraestructura, pods, deployments e ingress.

---

### Orquestación y Runtime Kubernetes Local (v0.11.1)

* **Cluster (Clúster Kubernetes):** Conjunto completo de nodos de cómputo (físicos o virtuales) coordinados por un plano de control común que ejecutan aplicaciones contenerizadas.
* **Control Plane (Plano de control):** Cerebro central de Kubernetes (`kube-apiserver`, `etcd`, `kube-scheduler`, `kube-controller-manager`) que mantiene y reconcilia el estado deseado del clúster frente al estado real.
* **Node (Nodo de cómputo):** Máquina de trabajo individual (física o virtual) dentro del clúster donde el agente `kubelet` y el runtime de contenedores (`containerd`) instancian y ejecutan los Pods.
* **Pod:** Unidad atómica mínima de ejecución y despliegue en Kubernetes; encapsula uno o más contenedores estrechamente acoplados que comparten almacenamiento, red (IP única) y especificaciones de ciclo de vida.
* **Deployment:** Objeto declarativo de alto nivel que gestiona el ciclo de vida, actualizaciones progresivas (*rolling updates*), historial de revisiones y auto-recuperación de un conjunto de Pods idénticos.
* **ReplicaSet:** Controlador de nivel inferior gestionado por el Deployment cuyo único propósito es asegurar que un número exacto de réplicas de Pods saludables estén ejecutándose en todo momento.
* **Namespace (Espacio de nombres):** Mecanismo de particionamiento lógico y aislamiento de nombres/recursos dentro de un mismo clúster físico (e.g. `aegisbank-local`, `kube-system`); no constituye un límite de seguridad estanco.
* **ConfigMap:** Objeto de configuración desacoplado para almacenar datos no confidenciales en formato clave-valor, inyectables como variables de entorno o archivos montados en los Pods.
* **kubeconfig:** Archivo estructurado YAML (comúnmente en `~/.kube/config`) que define clústeres, usuarios, credenciales y contextos para autenticar comandos `kubectl`.
* **Context (Contexto de Kubernetes):** Tupla lógica dentro de `kubeconfig` que combina un Clúster específico, un Usuario/Credencial y un Namespace predeterminado (e.g. `docker-desktop`).
* **Rollout (Despliegue progresivo):** Proceso automatizado mediante el cual Kubernetes reemplaza gradualmente Pods de una versión antigua por una nueva versión sin interrumpir la disponibilidad del servicio.
* **Rollback (Reversión de despliegue):** Operación de emergencia (`kubectl rollout undo`) que restaura de forma inmediata el Deployment a una revisión previa conocida y saludable ante fallos en producción.
* **Replica (Réplica de Pod):** Instancia idéntica e intercambiable de un Pod ejecutando la misma imagen y configuración para balanceo de carga o tolerancia a fallos.
* **Resource Request (Solicitud de recursos):** Cantidad garantizada mínima de CPU (e.g. `100m`) y Memoria (e.g. `128Mi`) que el planificador (*scheduler*) reserva en un nodo para ubicar un Pod.
* **Resource Limit (Límite de recursos):** Techo máximo estricto de CPU y Memoria (e.g. `256Mi`) que un contenedor puede consumir antes de ser estrangulado (CPU throttling) o terminado por el kernel (`OOMKilled`).
* **SecurityContext (Contexto de seguridad):** Directivas de endurecimiento a nivel de Pod y Contenedor (`runAsNonRoot`, `allowPrivilegeEscalation: false`, `drop: [ALL]`, `seccompProfile: RuntimeDefault`) para restringir privilegios y mitigar escapes de contenedor.
* **imagePullPolicy (Política de descarga de imágenes):** Regla de obtención de imágenes (`IfNotPresent`, `Never`, `Always`); en laboratorio local `IfNotPresent`/`Never` permite usar imágenes de Docker Desktop sin descargarlas de internet.
* **port-forward (Reenvío de puertos):** Túnel TCP seguro temporal creado por `kubectl` que redirige el tráfico desde un puerto del host local hacia un puerto interno de un Pod o Service en el clúster.
