# Prompt 017 — AegisBank v0.11.0 Containerization + Local Azure Messaging Foundation

```markdown
017 — AegisBank v0.11.0 Containerization + Local Azure Messaging Foundation

Continúa exclusivamente:
v0.11.0 — Containerization + Local Azure Messaging Foundation

Proyecto:
C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform

Baseline esperado:
branch: master
HEAD: d619263
working tree limpio

NO iniciar v0.11.1 ni v0.12.

0. TEACHING CONTRACT + CROSS-SESSION PROTOCOL
Lee primero:
docs/learning/TEACHING-CONTRACT.md
docs/architecture/CANONICAL-COMPONENTS.md
docs/engineering/OWNERSHIP-MAP.md
docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md

Explica desde cero y documenta cada concepto nuevo:
Container, Container Image, Dockerfile, Docker Compose, Registry, OCI, Port mapping,
Container network, Health check, Readiness, Liveness, Environment variable, Secret,
Volume, AMQP, Azure Service Bus, Queue, Topic, Subscription, KEDA, Azure Container Apps,
Kubernetes, AKS.

Para cada concepto:
nombre completo y sigla; traducción; qué es; problema que resuelve; cómo funciona internamente;
por qué AegisBank lo necesita; ejemplo concreto; alternativa y cuándo NO usarlo; errores/riesgos típicos;
relación con Mibanco; relación con AI-200; maturity status.

Guardar este prompt como:
docs/chatgpt-prompts/017_PROMPT.md

Single Writer:
Antes de cualquier WRITE:
.venv\Scripts\python.exe scripts\session_guard.py acquire --session-id "<unique-session-id>" --milestone "v0.11.0" --allowed-paths "containers/**,deploy/**,services/**,ai/agent/**,contracts/**,docs/**,scripts/**,.github/**,.gitignore,README.md"

Si ya existe writer:
AEGISBANK_CROSS_SESSION_WRITER_ACTIVE y STOP.

Antes de crear cualquier componente aplicar:
DISCOVER BEFORE CREATE
Clasificar cada decisión: REUSE, EXTEND, NEW_COMPONENT_JUSTIFIED. No duplicar componentes canónicos.

1. Preflight Git + Docker
Verificar:
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
docker version
docker compose version
docker info

NO instalar Docker automáticamente. NO modificar configuración global de Docker. NO activar Windows Containers. Usar Linux containers.
Si Docker Desktop/Engine no está disponible: AEGISBANK_V0.11_DOCKER_REQUIRED y STOP.

2. Objetivo del milestone
Aprender y demostrar localmente la transición:
Python processes on host -> container images -> container network -> containerized Core Banking/API -> Azure Service Bus Emulator -> AegisBank messaging adapter
Sin Azure cloud, sin costos y sin afirmar producción.
Mantener Foundry Local en el HOST (host.docker.internal).

3. Containerizar primero Core Banking
services/mock-core-banking
Dockerfile multi-stage, non-root, Python compatible, .dockerignore, bind 0.0.0.0, health endpoint.

4. Container Image Reproducibility
Tag: aegisbank/mock-core-banking:0.11.0. No push.

5. Docker Compose
deploy/local/docker-compose.yml
Servicios: mock-core-banking, Azure Service Bus Emulator, SQL Server Linux.

6. Azure Service Bus Emulator
Configuración declarativa JSON (Config.json), cola service-requests, DLQ, AMQP.

7. Service Bus Adapter
AzureServiceBusMessageBus implementando la interfaz canónica MessageBus (azure-servicebus SDK).

8. Outbox -> Service Bus Emulator
Transactional Outbox -> OutboxProcessor -> MessageBus -> Service Bus Emulator -> Consumer -> IdempotentConsumer.

9. E2E Container Acceptance
Pruebas A a I.

10. Security
docs/security/CONTAINER-SECURITY.md

11. Resource Discipline
docker compose up / tests / docker compose down.

12. AI-200 Mapping
docs/learning/MASTERS-NOTES.md

13. Container Apps vs AKS
docs/architecture/CONTAINER-PLATFORM-DECISION.md

14. Kubernetes Learning Artifact
deploy/kubernetes/

15. Quality Gate
scripts/quality_gate.py con --include-containers.

16. CI
.github/workflows/ci.yml (CI-CONFIGURED / RUNNER-PENDING).

17. ADRs
ADR-025, ADR-026, ADR-027.

18. Validation
Todos los checks y pruebas pasando.

19. Git
Commit: feat(v0.11): establish local container and Service Bus foundation.
Liberar session guard.
Finalizar con: AEGISBANK_V0.11_CONTAINER_MESSAGING_READY y STOP.
```
