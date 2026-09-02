# v0.11: Containers and Local Azure Messaging

This milestone is a local lab only. It does not deploy to Azure and the Service Bus
emulator is not a production boundary.

## Vocabulary

| Term | Full name / translation | Meaning and AegisBank example | Alternative, risks, Mibanco and AI-200 | Maturity |
|---|---|---|---|---|
| Container | Container / contenedor | Isolated process using an image filesystem; Core Banking runs as `mock-core-banking`. | A host process is simpler for local debugging; containers are not perfect security boundaries. | `LAB-COVERED` |
| Image | Container Image / imagen de contenedor | Immutable OCI template containing Python and the API. | A VM is heavier; unpinned bases reduce reproducibility. | `LAB-COVERED` |
| Dockerfile | Dockerfile / receta Docker | Declarative build recipe, multi-stage when justified. | Buildpacks reduce Docker knowledge; never copy `.env` or `.venv`. | `LAB-COVERED` |
| Compose | Docker Compose / composición Docker | Describes Core Banking, SQL Server and emulator as one local stack. | Kubernetes is excessive for this lab; overlapping Compose files drift. | `LAB-COVERED` |
| Registry / ACR | Azure Container Registry / registro de contenedores Azure | Future private OCI image registry; no push in v0.11. | Docker Hub is public and not the bank target; never publish synthetic lab images by accident. | `CLOUD-PENDING` |
| OCI | Open Container Initiative / iniciativa abierta de contenedores | Standard image/runtime format consumed by Docker and registries. | Vendor-specific formats reduce portability. | `LAB-COVERED` |
| Port mapping | Port mapping / mapeo de puertos | Host `8000` forwards to container `8000`; internal services use names, not host ports. | Expose only required ports. | `LAB-COVERED` |
| Network | Container network / red de contenedores | Explicit `aegisbank-net` bridge resolves service names. | Host networking reduces isolation; accidental public bindings are risky. | `LAB-COVERED` |
| Health check | Health check / comprobación de salud | Process probe calls `/health/ready`; Compose waits for SQL health. | A TCP probe cannot prove application readiness. | `LAB-COVERED` |
| Readiness / liveness | Readiness / disponibilidad; liveness / vivacidad | Ready means dependencies work; live means process responds. | One probe for both causes restart loops. | `LAB-COVERED` |
| Environment variable | Environment variable / variable de entorno | `AEGISBANK_DATABASE_URL` configures the container without code changes. | Do not place secrets in images or committed Compose. | `LAB-COVERED` |
| Secret | Secret / secreto | Password material supplied at runtime through shell/secret manager. | `.env` committed to Git is a leak; cloud target is Key Vault/managed identity. | `CLOUD-PENDING` |
| Volume | Volume / volumen | Named SQLite volume persists only local lab data. | Host bind mounts increase coupling and exposure. | `LAB-COVERED` |
| AMQP | Advanced Message Queuing Protocol / protocolo avanzado de colas | Protocol used by the emulator client on port 5672. | HTTP polling adds latency; protocol support is not cloud parity. | `LAB-COVERED` |
| Azure Service Bus | Azure Service Bus / bus de servicio Azure | Managed queues/topics; v0.11 uses only local emulator. | Cloud Service Bus adds SLA and identity; emulator is dev/test only. | `CLOUD-PENDING` |
| Queue | Queue / cola | FIFO-like event holding area; `service-requests` carries `ServiceRequestCreated`. | Topics add fan-out complexity not needed yet. | `LAB-COVERED` |
| Topic/subscription | Topic / tópico; Subscription / suscripción | Topic fan-out and per-consumer cursor; documented but not implemented. | Queue is the simpler first topology. | `CLOUD-PENDING` |
| KEDA | Kubernetes Event-driven Autoscaling / escalado por eventos | Future scaler based on queue depth in Container Apps/AKS. | Fixed replicas are adequate for this lab. | `CLOUD-PENDING` |
| Container Apps | Azure Container Apps / aplicaciones de contenedores Azure | Future managed/serverless container target with revisions and KEDA. | Prefer this before AKS for low operational overhead. | `CLOUD-PENDING` |
| Kubernetes / AKS | Kubernetes / Kubernetes; Azure Kubernetes Service / servicio Kubernetes Azure | Future orchestration model: Pods, Deployments, Services and ConfigMaps. | AKS gives control but adds cluster operations. | `CLOUD-PENDING` |
| Outbox and settlement | Transactional Outbox / buzón transaccional; complete/abandon/dead-letter | SQL commit precedes adapter send; receiver settlement controls completion, retry or DLQ. | Direct publish risks lost events; duplicate delivery requires idempotency. | `LAB-COVERED` |

## Flow

`HITL APPROVE -> idempotent WRITE -> SQL Outbox -> MessageBus -> Azure adapter ->
Service Bus emulator queue -> consumer`. `REJECT` stops before the write and therefore
creates no outbox event or queue message. `host.docker.internal` is reserved for a future
container-to-Foundry Local connection; Foundry Local remains on the Windows host.

## Evidence and Limits

Core Banking was built and run as `aegisbank/mock-core-banking:0.11.0`; `/health/live`
and `/health/ready` returned HTTP 200. The emulator remains `LAB-COVERED` only after its
full Compose acceptance run. Local emulator behavior is not Azure production parity:
identity, networking, scale, SLA, geo recovery and cloud observability remain pending.

Mibanco mapping: Docker/Compose demonstrates deployment discipline; Service Bus and
AMQP demonstrate asynchronous integration; KEDA, Container Apps, AKS and ACR map to
the AI-200 container/cloud domains without claiming certification.
