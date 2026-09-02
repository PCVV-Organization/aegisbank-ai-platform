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

---

### Gestión de Datos para IA y Búsqueda Vectorial (v0.12.0)

* **DBMS (Database Management System / Sistema Gestor de Bases de Datos):** Software del sistema responsable de almacenar, consultar, indexar y proteger datos estructurados o no estructurados (e.g. PostgreSQL, SQL Server, Redis, Cosmos DB).
* **RDBMS (Relational Database Management System / Sistema Gestor de Bases de Datos Relacional):** DBMS basado en el modelo relacional de tablas, filas y columnas vinculadas mediante claves y restricciones de integridad.
* **PostgreSQL:** Sistema gestor de bases de datos relacional de objetos de código abierto, altamente extensible y conforme con los estándares SQL y transaccionales ACID.
* **SQL (Structured Query Language / Lenguaje de Consulta Estructurado):** Lenguaje declarativo estándar para definir esquemas (*DDL*), manipular datos (*DML*) y consultar información relacional (*DQL*).
* **Schema (Esquema de base de datos):** Estructura organizativa formal y espacio de nombres que agrupa tablas, vistas, tipos de datos, índices y procedimientos dentro de una base de datos.
* **Table (Tabla):** Estructura bidimensional de almacenamiento compuesta por un conjunto fijo de columnas con tipo de datos y cero o más filas de datos.
* **Row (Fila / Registro / Tupla):** Instancia única y atómica de datos dentro de una tabla que representa una entidad concreta (e.g. un chunk de documento o una solicitud de servicio).
* **Primary Key (Clave primaria / PK):** Columna o combinación de columnas cuyos valores identifican de forma única e inequívoca cada fila de una tabla, prohibiendo valores nulos o duplicados.
* **Foreign Key (Clave foránea / FK):** Restricción de integridad referencial que vincula una columna de una tabla con la clave primaria de otra tabla.
* **Transaction (Transacción de base de datos):** Unidad lógica de trabajo compuesta por una o más operaciones SQL que deben ejecutarse bajo garantías atómicas de todo o nada (*all-or-nothing*).
* **ACID (Atomicidad, Consistencia, Aislamiento, Durabilidad):** Cuatro propiedades fundamentales que garantizan la fiabilidad y corrección de las transacciones de bases de datos ante fallos del sistema o concurrencia.
* **Index (Índice de base de datos):** Estructura de datos secundaria (e.g. B-Tree, Hash, HNSW) que acelera la búsqueda y recuperación de filas a costa de espacio en disco y sobrecarga de escritura.
* **Query Plan (Plan de ejecución de consulta):** Secuencia ordenada de pasos y algoritmos elegidos por el optimizador del motor de base de datos para ejecutar una consulta SQL con el menor costo estimado.
* **EXPLAIN:** Comando SQL que muestra el plan de ejecución previsto por el optimizador (estimaciones de costo, escaneos secuenciales vs escaneos por índice) sin ejecutar la consulta.
* **ANALYZE:** Modificador de `EXPLAIN` que ejecuta realmente la consulta SQL y reporta tiempos de ejecución reales, número de filas procesadas y bloques de memoria leídos (*Buffers*).
* **Connection (Conexión de base de datos):** Sesión TCP activa y autenticada establecida entre un proceso de aplicación cliente y el servidor de base de datos.
* **Connection Pool (Pool de conexiones):** Almacén administrado de conexiones reutilizables en memoria que elimina el costo recurrente de abrir y cerrar conexiones TCP para cada consulta.
* **Embedding (Incrustación / Vector de características):** Representación matemática densa y continua de un texto, imagen o concepto en un espacio vectorial multidimensional (e.g. 32 o 1536 dimensiones), donde la cercanía geométrica refleja similitud semántica.
* **Vector:** Arreglo unidimensional ordenado de números flotantes (e.g. `[0.14, -0.72, 0.33, ...]`) que codifica las propiedades semánticas de un dato.
* **Vector Database (Base de datos vectorial):** Motor de base de datos especializado u optimizado para indexar, almacenar y consultar vectores densos mediante algoritmos de búsqueda por similitud.
* **pgvector:** Extensión de código abierto para PostgreSQL que introduce el tipo de datos `vector`, operadores de distancia (Coseno, L2, Producto Interno) e índices vectoriales HNSW e IVFFlat.
* **Cosine Similarity (Similitud Coseno):** Métrica de similitud geométrica que mide el coseno del ángulo entre dos vectores no nulos, variando de -1 (opuestos) a 1 (idénticos), independiente de su magnitud.
* **L2 / Euclidean Distance (Distancia Euclidiana L2):** Distancia geométrica en línea recta entre dos puntos en un espacio multidimensional euclidiano; operador `<->` en pgvector.
* **Inner Product (Producto Interno / Dot Product):** Suma del producto elemento a elemento de dos vectores; para vectores unitarios normalizados equivale a la similitud coseno; operador `<#>` en pgvector.
* **Exact Nearest-Neighbor Search (Búsqueda exacta del vecino más cercano):** Búsqueda exhaustiva que compara el vector de consulta contra el 100% de los vectores de la tabla sin aproximaciones (recall del 100%, pero latencia lineal $O(N)$).
* **ANN (Approximate Nearest Neighbor / Vecino más próximo aproximado):** Familia de algoritmos de búsqueda que sacrifican una fracción mínima de exactitud/recall para lograr búsquedas sub-lineales ultrarrápidas ($O(\log N)$) en conjuntos de datos masivos.
* **HNSW (Hierarchical Navigable Small World):** Algoritmo de indexación vectorial basado en grafos jerárquicos multicapa que ofrece la mejor relación de velocidad y recall para búsqueda ANN a cambio de mayor consumo de memoria RAM y tiempo de construcción.
* **IVFFlat (Inverted File Flat):** Algoritmo de indexación vectorial que divide el espacio en conglomerados (*clusters*) mediante cuantización vectorial (Voronoi cells), buscando solo en los grupos más cercanos.
* **Metadata Filtering (Filtrado por metadatos):** Capacidad de combinar restricciones relacionales clásicas (`WHERE status = 'active' AND topic = 'creditos'`) con ordenamiento por similitud vectorial dentro de la misma consulta SQL.
* **Recall (Exhaustividad):** Proporción de documentos relevantes recuperados respecto al total de documentos relevantes existentes en la base de conocimiento para una consulta.
* **Latency (Latencia):** Tiempo total transcurrido desde que se emite una consulta hasta que se recibe el conjunto ordenado de resultados.
* **Throughput (Rendimiento / Capacidad de procesamiento):** Número de consultas o transacciones procesadas con éxito por unidad de tiempo (e.g. consultas por segundo - QPS).
* **Vector Store:** Abstracción de capa de acceso a datos que encapsula las operaciones de almacenamiento, actualización y búsqueda por similitud vectorial.
* **Migration (Migración de base de datos):** Script versionado y determinista de cambios de esquema (DDL/DML) que evoluciona la estructura de la base de datos de manera controlada y reversible.

---

### Azure Cosmos DB NoSQL y Change Feed (v0.12.1)

* **NoSQL (Not Only SQL / No Solo SQL):** Paradigma de bases de datos no relacionales optimizadas para esquemas flexibles, escalabilidad horizontal masiva, baja latencia y modelos de datos específicos (documentos, clave-valor, grafos, columnas).
* **Document Database (Base de datos documental):** Tipo de motor NoSQL que almacena, recupera y gestiona datos semi-estructurados en formato de documentos jerárquicos (comúnmente JSON).
* **Azure Cosmos DB:** Servicio de base de datos distribuida globalmente y multi-modelo administrado por Microsoft en Azure, diseñado para latencias de un solo dígito en milisegundos y alta disponibilidad.
* **API for NoSQL:** Modelo de datos y dialecto de consulta principal de Cosmos DB que almacena documentos JSON y permite consultarlos mediante sintaxis SQL declarativa.
* **Database (Base de datos en Cosmos DB):** Unidad lógica administrativa dentro de una cuenta de Cosmos DB que actúa como espacio de nombres para contenedores y gestiona el rendimiento compartido (*throughput*).
* **Container (Contenedor en Cosmos DB):** Unidad de escalabilidad y particionamiento en Cosmos DB (equivalente conceptual a una colección o tabla) donde se almacenan los items y se define la clave de partición.
* **Item / Document (Item / Documento en Cosmos DB):** Entidad atómica de datos representada como un objeto JSON arbitrario con un identificador único obligatorio (`id`) y el valor de la clave de partición.
* **JSON (JavaScript Object Notation):** Formato ligero de intercambio de datos basado en texto estructurado en pares clave-valor y arreglos, estándar en la API for NoSQL.
* **Partition Key (Clave de partición / PK):** Propiedad fija de cada item (e.g. `/customer_id`) que determina la partición lógica a la que pertenece y guía el enrutamiento físico y distribución de datos.
* **Logical Partition (Partición lógica):** Conjunto de items que comparten el mismo valor de la clave de partición; tiene un límite de tamaño de **20 GB** en Azure Cloud.
* **Physical Partition (Partición física):** Unidad interna de cómputo y almacenamiento SSD administrada y autoescalada por Azure que aloja un conjunto de particiones lógicas.
* **Cardinality (Cardinalidad de clave de partición):** Número de valores únicos distintos que puede tomar la clave de partición; una alta cardinalidad garantiza una distribución uniforme de datos y rendimiento.
* **Hot Partition (Partición saturada / Cuello de botella):** Partición lógica o física que recibe un volumen desproporcionadamente alto de lecturas/escrituras, agotando sus RUs y degradando el rendimiento general.
* **Point Read (Lectura puntual directa):** Operación de lectura más rápida y económica en Cosmos DB que recupera un item específico conociendo simultáneamente su `id` y su `partitionKey` (1 RU exacto en nube).
* **Cross-Partition Query (Consulta entre particiones):** Consulta SQL que no incluye la clave de partición en su cláusula `WHERE`, obligando al motor a consultar en abanico (*fan-out*) todas las particiones físicas.
* **TTL (Time-To-Live / Tiempo de vida):** Capacidad nativa de Cosmos DB para eliminar automáticamente items de un contenedor tras un periodo de tiempo determinado en segundos, sin consumir RUs de escritura adicionales.
* **Change Feed (Flujo de cambios):** Registro de auditoría persistente, ordenado y de solo lectura que emite en tiempo real todas las inserciones y modificaciones que ocurren en los documentos de un contenedor.
* **Change Feed Processor (Procesador del flujo de cambios):** Biblioteca / componente que distribuye la lectura del Change Feed entre múltiples instancias de consumidores garantizando tolerancia a fallos y avance coordinado mediante leases.
* **Checkpoint (Punto de control):** Mecanismo de persistencia del estado que almacena el último token de continuación procesado para permitir reanudar la lectura tras caídas o reinicios sin procesar eventos desde el inicio.
* **Lease (Arrendamiento en Change Feed):** Bloqueo distribuido temporal que asigna la lectura de una partición física a un consumidor específico para evitar que múltiples instancias procesen la misma partición simultáneamente.
* **At-Least-Once Delivery (Entrega al menos una vez):** Garantía de mensajería/eventos donde ningún mensaje se pierde, pero pueden ocurrir reentregas o duplicados ante fallos de red o reinicios, exigiendo consumidores idempotentes.
* **Idempotent Consumer (Consumidor idempotente):** Patrón arquitectónico donde el procesamiento repetido del mismo evento o cambio produce exactamente el mismo efecto lógico que procesarlo una sola vez.
* **Continuation Token (Token de continuación):** Cadena opaca emitida por Cosmos DB que codifica el cursor de posición exacto en el flujo de cambios para solicitudes de lectura posteriores.
* **Consistency Level (Nivel de consistencia):** Configuración que equilibra el compromiso entre coherencia de datos, latencia y disponibilidad en sistemas distribuidos (Strong, Bounded Staleness, Session, Consistent Prefix, Eventual).
* **Request Unit / RU (Unidad de solicitud):** Medida normalizada de rendimiento en Azure Cosmos DB que abstrae los recursos de CPU, memoria e IOPS necesarios para ejecutar una operación.
* **Indexing Policy (Política de indexación):** Configuración declarativa que define qué rutas del documento JSON se indexan automáticamente (por defecto `/*` indexa todos los campos) y qué tipo de índices usar (Range, Spatial, Vector).
* **Emulator (Emulador local de Cosmos DB):** Entorno local contenedorizado provisto por Microsoft que simula la API for NoSQL de Azure Cosmos DB para pruebas de desarrollo e integración sin costo cloud.
* **Cloud Parity (Paridad con la nube):** Grado de fidelidad y equivalencia funcional entre un entorno de emulación local y el servicio administrado real en producción de Azure.

---

### Consistencia de Respuestas, Fundamentación y Procedencia (v0.12.0-R1)

* **LLM Determinism (Determinismo del LLM):** Propiedad de un modelo de lenguaje por la cual, ante entradas idénticas (system prompt, user prompt, tool schemas, hiperparámetros y semilla), produce exactamente la misma secuencia de tokens o hechos factuales de salida.
* **Stochasticity (Estocasticidad / Aleatoriedad):** Naturaleza probabilística inherente a los modelos de lenguaje autorregresivos donde el siguiente token se selecciona mediante muestreo sobre una distribución de probabilidades.
* **Temperature (Temperatura):** Hiperparámetro que escala los logits antes de aplicar softmax (valores cercanos a 0 aplanan la distribución favoreciendo los tokens más probables y respuestas deterministas; valores altos aumentan la dispersión y creatividad).
* **Top-p / Nucleus Sampling (Muestreo de núcleo):** Técnica de decodificación que restringe la selección de tokens al subconjunto más probable cuya probabilidad acumulada alcanza el umbral $p$ (e.g. 0.9).
* **Seed (Semilla pseudoaleatoria):** Entero fijo que inicializa el generador de números pseudoaleatorios del motor de inferencia para maximizar la reproducibilidad de las respuestas entre llamadas idénticas.
* **Grounding (Fundamentación / Anclaje factual):** Principio de diseño de IA generativa que exige que cada afirmación factual de la respuesta esté directamente respaldada por una fuente de verdad verificable y autorizada (Core Banking, RAG o Esquemas de Dominio).
* **Provenance (Procedencia / Trazabilidad de origen):** Capacidad de rastrear y documentar la fuente exacta (documento, fila de base de datos, esquema de API o enum) de donde provino cada dato emitido por el modelo.
* **Source of Truth (Fuente de verdad):** Repositorio o definición canónica autorizada y única para una entidad o regla de negocio dentro del sistema (e.g. `ServiceRequestCategory` en el dominio de Core Banking).
* **Tool Schema (Esquema de herramienta):** Definición JSON Schema que describe los parámetros, tipos y enumeraciones que el modelo puede utilizar al invocar una función o tool.
* **Domain Schema (Esquema de dominio):** Estructura canónica de entidades y enumeraciones definida en el código de la lógica de negocio (`mock_core_banking.domain.enums`).
* **Response Consistency (Consistencia de respuesta):** Medida en que múltiples ejecuciones de una misma consulta factual devuelven el mismo conjunto de datos y hechos correctos sin contradicciones.
* **Semantic Consistency (Consistencia semántica):** Garantía de que el significado y los hechos centrales de la respuesta permanecen inalterados aunque varíe moderadamente la sintaxis o redacción léxica.
* **Lexical Variation (Variación léxica):** Fluctuación en la elección de palabras, sinónimos y estructura gramatical entre respuestas generadas por un LLM, la cual es secundaria frente a la exactitud factual en banca.
* **Relevance (Relevancia):** Grado en que la respuesta del agente responde directamente a la intención del usuario sin incluir instrucciones no solicitadas o información superflua.
* **Completeness (Exhaustividad de respuesta):** Grado en que la respuesta cubre todos los aspectos esenciales requeridos por la consulta del usuario.
* **Abstention (Abstención / Safe Fallback):** Comportamiento controlado donde el agente declara explícitamente no tener información suficiente en lugar de fabricar o adivinar datos no respaldados.

---

### Gestión de Datos en Memoria, Caché y Búsqueda Vectorial con Redis (v0.12.2)

* **Redis (Remote Dictionary Server):** Almacén de estructura de datos en memoria de código abierto utilizado como base de datos, caché y motor de búsqueda de baja latencia.
* **In-Memory Database (Base de datos en memoria):** Sistema de gestión de bases de datos que mantiene el conjunto activo de datos primariamente en la memoria RAM para lograr tiempos de respuesta de microsegundos.
* **Key-Value Store (Almacén clave-valor):** Paradigma NoSQL donde los datos se organizan y recuperan mediante identificadores únicos (*keys*) asociados a valores simples o estructurados.
* **Cache (Caché):** Capa de almacenamiento temporal de alta velocidad que almacena un subconjunto de datos para que futuras solicitudes se sirvan más rápidamente que consultando la fuente primaria.
* **Cache-Aside (Lectura perezosa / Lazy Loading):** Patrón arquitectónico donde la aplicación consulta primero la caché; si existe (*HIT*) lo devuelve; si no (*MISS*), consulta la base de datos canónica, actualiza la caché con TTL y devuelve el dato.
* **Cache Hit (Acierto de caché):** Suceso en el cual el dato solicitado se encuentra presente y vigente en la memoria de la caché.
* **Cache Miss (Fallo de caché):** Suceso en el cual el dato solicitado no está presente o ha expirado en la caché, forzando una consulta a la fuente de verdad.
* **Hit Ratio (Tasa de aciertos):** Métrica porcentual $\frac{\text{Hits}}{\text{Hits} + \text{Misses}}$ que cuantifica la efectividad operativa de la capa de caché.
* **TTL / Time To Live (Tiempo de vida):** Intervalo de tiempo máximo que un registro puede residir en caché antes de ser automáticamente eliminado por expiración.
* **Expiration (Expiración):** Proceso automático de depuración por el cual Redis marca y elimina claves cuyo TTL ha transcurrido.
* **Invalidation (Invalidación de caché):** Acción explícita de purgar o borrar entradas de caché cuando los datos subyacentes en la fuente de verdad han cambiado.
* **Stale Data (Datos obsoletos):** Condición indeseable donde la caché sirve una copia desactualizada de la información debido a una falta de invalidación o un TTL excesivamente largo.
* **Cache Key (Clave de caché):** Cadena identificadora única y determinista utilizada para direccionar un elemento almacenado en la memoria de Redis.
* **Namespace / Prefix (Espacio de nombres):** Prefijo jerárquico (`aegisbank:rag:v1:...`) utilizado para agrupar lógicamente claves de caché y permitir invalidaciones selectivas sin colisiones.
* **Serialization (Serialización):** Proceso de transformar estructuras de datos u objetos en memoria a una representación de bytes o JSON almacenable y recuperable desde Redis.
* **Cache Stampede / Thundering Herd (Inundación de caché):** Fenómeno donde múltiples peticiones concurrentes sufren un Cache Miss simultáneo sobre una misma clave y saturan la base de datos relacional subyacente.
* **Single-Flight (Vuelo único):** Patrón de concurrencia donde solo una petición adquiere el derecho de cargar la fuente de verdad mientras las demás esperan el resultado en caché.
* **Distributed Lock (Bloqueo distribuido):** Mecanismo de sincronización entre procesos distribuidos mediante claves con expiración y tokens únicos en Redis (`SET ... NX EX`).
* **Eviction Policy (Política de evicción):** Algoritmo que decide qué claves eliminar cuando la memoria asignada a Redis alcanza su límite máximo (`maxmemory`).
* **LRU / Least Recently Used (Menos usado recientemente):** Política de evicción que descarta las claves que no han sido leídas o escritas durante el período de tiempo más prolongado.
* **LFU / Least Frequently Used (Menos frecuentemente usado):** Política de evicción que descarta las claves con el menor contador acumulado de accesos.
* **No-Eviction (Sin evicción):** Política donde Redis retorna un error ante escrituras cuando la memoria está llena, preservando todas las claves existentes.
* **Persistence / RDB & AOF (Persistencia en Redis):** Mecanismos para salvar el estado en memoria a disco: RDB (*Redis Database Backup*, snapshots periódicos) y AOF (*Append Only File*, log de comandos continuos).
* **Redis Search / RediSearch:** Módulo oficial de Redis que agrega capacidades de indexación secundaria, búsqueda de texto completo y búsqueda vectorial sobre Hashes y JSON.
* **Vector Index (Índice vectorial):** Estructura de datos optimizada en memoria que organiza representaciones vectoriales densas para acelerar búsquedas de similitud geométrica.
* **KNN / K-Nearest Neighbors (K-Vecinos más cercanos):** Algoritmo que identifica los $K$ vectores de la base de datos con menor distancia matemática respecto al vector de consulta.
* **HNSW / Hierarchical Navigable Small World:** Grafo multicapa de alta eficiencia para búsqueda aproximada de vecinos más cercanos (*ANN*) soportado nativamente en RediSearch.
* **Semantic Cache (Caché semántica):** Técnica de caché basada en similitud vectorial de consultas en lugar de coincidencias de texto exacto; diferida en banca por riesgo de respuestas inexactas (*false positives*).
* **Similarity Threshold (Umbral de similitud):** Valor de distancia o similitud coseno mínima requerida para considerar que dos consultas o documentos son semánticamente equivalentes.
* **False Positive (Falso positivo en búsqueda/caché):** Error donde el sistema considera equivalente una consulta diferente debido a una similitud matemática engañosa.
* **Redis Connection Pool (Grupo de conexiones):** Conjunto reutilizable de conexiones TCP abiertas hacia Redis que reduce el costo de handshake y evita agotamiento de sockets.
* **Azure Managed Redis:** Servicio administrado de Redis de nivel empresarial en Microsoft Azure que integra Redis Enterprise y RediSearch con alta disponibilidad y escalabilidad automática.
* **Local Emulator vs Cloud Parity:** Azure Managed Redis no tiene emulador oficial. AegisBank usa Redis Open Source 8 en Docker para validar semánticas locales de caché y búsqueda, sin asumir paridad operativa con Azure Managed Redis.

---

### Reproducibilidad, Cadena de Suministro y Evidencia de Rendimiento (v0.12.2-R1)

* **Reproducible Build (Construcción reproducible):** Principio de ingeniería de software que garantiza que el mismo código fuente, bajo la misma configuración, genere exactamente el mismo artefacto binario o entorno de ejecución en cualquier momento y máquina.
* **Immutable Artifact (Artefacto inmutable):** Paquete de software, imagen de contenedor o modelo cuya composición y contenido no pueden ser alterados una vez construido y publicado.
* **Docker Tag (Etiqueta Docker):** Alias alfanumérico legible por humanos asignado a una imagen de contenedor en un registro (por ejemplo, el tag GA exacto `8.10.1-trixie`).
* **Floating Tag (Etiqueta flotante / Mutable):** Tag no determinista (como `:latest`, `:8` o `:v1`) cuyo puntero cambia periódicamente cuando el mantenedor publica una nueva versión, rompiendo la reproducibilidad.
* **Image Digest (Digest criptográfico de imagen):** Hash criptográfico inmutable `sha256:...` del manifiesto del contenedor que garantiza de forma matemática la identidad exacta de la imagen descargada.
* **Supply-Chain Risk (Riesgo de cadena de suministro):** Vulnerabilidad originada por cambios imprevistos, dependencias dinámicas o sustituciones maliciosas en imágenes o librerías de terceros.
* **Semantic Version / SemVer (Versionado semántico):** Estándar de nomenclatura formal `MAJOR.MINOR.PATCH` donde cada incremento comunica el tipo de cambio (ruptura de API, nueva funcionalidad compatible o corrección de bugs).
* **Maturity Level (Nivel de madurez de evidencia):** Taxonomía formal del proyecto para clasificar rigurosamente el estado de verificación de cada capacidad técnica:
  - **`LAB-COVERED`:** Capacidad validada localmente con pruebas unitarias, de integración o evaluación en memoria.
  - **`LOCAL-REDIS-COVERED`:** Capacidad validada contra un contenedor local de Redis 8 / RediSearch.
  - **`CI-CONFIGURED`:** Flujo o compuerta automatizada en GitHub Actions (`RUNNER-PENDING`).
  - **`PROD-PARTIAL`:** Patrón parcialmente implementado que requiere almacén o clúster productivo para paridad total.
  - **`CLOUD-PENDING`:** Capacidad arquitectónica diseñada pero pendiente de despliegue en infraestructura de Microsoft Azure.
  - **`SAFETY-DEFERRED`:** Decisión arquitectónica de posponer una técnica (e.g. caché semántica) para salvaguardar la seguridad bancaria.
* **Benchmark Evidence (Evidencia cuantitativa de rendimiento):** Mediciones reproducibles bajo condiciones controladas (muestras, calentamiento, distribución) que respaldan afirmaciones de latencia o throughput.
* **Latency Percentile (Percentil de latencia):** Métrica estadística que indica el tiempo máximo en el que se completó un porcentaje determinado de solicitudes:
  - **`p50` (Mediana):** El 50% de las solicitudes se completaron en este tiempo o menos.
  - **`p95`:** El 95% de las solicitudes se completaron en este tiempo o menos; captura la experiencia de la gran mayoría de usuarios.
  - **`p99`:** El 99% de las solicitudes se completaron en este tiempo o menos; mide el comportamiento ante colas o fluctuaciones extremas (*tail latency*).

---

### Serverless, Azure Functions y Event Grid (v0.13.0)

* **Serverless (Computación sin servidor):** Modelo de ejecución en la nube donde el desarrollador construye aplicaciones sin aprovisionar ni administrar directamente servidores, con escalado elástico automático (hasta cero instancias) y facturación por consumo real de recursos.
* **FaaS / Function as a Service (Función como servicio):** Categoría de computación serverless donde el código se empaqueta en funciones atómicas, efímeras y reactivas desencadenadas por eventos discretos.
* **Azure Functions:** Plataforma administrada FaaS de Microsoft Azure para ejecutar código reactivo en respuesta a eventos con múltiples lenguajes (Python, C#, Java, TypeScript).
* **Functions Host (Runtime de Azure Functions):** Motor de ejecución subyacente que escucha eventos, gestiona triggers y bindings, orquesta los procesos worker de lenguaje y expone endpoints locales de diagnóstico.
* **Azure Functions Core Tools (CLI `func`):** Toolchain oficial de Microsoft para compilar, ejecutar y depurar Function Apps localmente con paridad total respecto al runtime de nube.
* **Trigger (Desencadenador):** Mecanismo declarativo que inicia la ejecución de una Azure Function. **Una Function tiene exactamente un trigger.**
* **Binding (Enlace):** Conexión declarativa entre una Azure Function y recursos externos. Se divide en **Input Binding** (aporta datos al inicio) y **Output Binding** (persiste resultados al finalizar).
* **Python Programming Model v2:** Modelo moderno de Azure Functions basado en decoradores nativos de Python (`@app.event_grid_trigger`, `@app.route`) dentro de un único archivo `function_app.py`.
* **Stateless Function (Función sin estado):** Principio arquitectónico donde cada invocación es completamente independiente, sin memoria compartida ni persistencia en disco local permanente entre ejecuciones.
* **Cold Start (Arranque en frío):** Latencia inicial incurrida al levantar una nueva instancia serverless desde cero tras un período de inactividad.
* **Warm Instance (Instancia caliente):** Instancia de cómputo serverless ya inicializada y residente en memoria lista para atender solicitudes con latencia inmediata.
* **Event-Driven Architecture / EDA (Arquitectura orientada a eventos):** Patrón de diseño donde el flujo de información y la orquestación entre servicios se rigen por la producción, detección y consumo reactivo de eventos.
* **Azure Event Grid:** Servicio totalmente administrado de distribución y enrutamiento reactivo de eventos a gran escala con entrega push (*reactive pub/sub*).
* **CloudEvents 1.0:** Estándar abierto de la CNCF para describir metadatos de eventos de manera uniforme (`specversion`, `id`, `source`, `type`, `subject`, `time`, `datacontenttype`, `data`).
* **Event Grid Topic (Tópico de Event Grid):** Punto de conexión en la nube donde los productores envían eventos para su posterior enrutamiento.
* **Event Subscription (Suscripción de eventos):** Regla que asocia un tópico con un suscriptor específico, definiendo filtros, reintentos y destinos de dead-letter.
* **Dead-Letter Destination (Destino de mensajes muertos):** Contenedor de almacenamiento (Azure Blob Storage) donde Event Grid deposita eventos que no pudieron ser entregados tras agotar reintentos.
* **At-Least-Once Delivery (Entrega al menos una vez):** Garantía de mensajería donde cada evento se entrega con seguridad al menos una vez, pudiendo ocurrir entregas duplicadas ante fallos de red.
* **Idempotent Event Handler (Manejador de eventos idempotente):** Función receptora que procesa eventos garantizando que múltiples entregas del mismo identificador de evento generen un único efecto lógico.
