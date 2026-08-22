# AegisBank AI Platform — Prompt v0.2.0 Core Banking Mock

Continúa el proyecto **AegisBank AI Platform** desde el milestone aprobado `v0.1.0 — Project Charter`.

Actúa como:

* Principal Backend Engineer
* Senior Python Engineer
* Software Architect
* Test Engineer
* Banking Systems Engineer
* Security-minded Technical Lead

Tu objetivo es implementar **exclusivamente**:

```text
v0.2.0 — Core Banking Mock
```

No debes comenzar `v0.3`.

---

# 0. Estado de partida autorizado

El milestone anterior terminó con esta evidencia:

```text
PROJECT_PATH: C:\aegisbank-ai-platform
CURRENT_BRANCH: master
COMMIT: 4cee550
COMMIT_MESSAGE: docs(v0.1): establish AegisBank project charter
RESULTADO: PASS
```

Archivos versionados creados en `v0.1`:

```text
.gitignore
AGENTS.md
README.md
docs/charter/01-vision.md
docs/charter/02-scope.md
docs/charter/03-use-cases.md
docs/charter/04-non-goals.md
docs/charter/05-success-criteria.md
```

Existen además artefactos preexistentes/concurrentes deliberadamente NO incluidos en el commit:

```text
.intelligence/
.opencode/
contracts/
docs/chatgpt-prompts/
opencode.json
```

No los modifiques, elimines, muevas, renombres ni agregues al commit.

---

# 1. Workspace canónico

Trabaja únicamente en:

```text
C:\aegisbank-ai-platform
```

Preflight obligatorio:

```powershell
Set-Location 'C:\aegisbank-ai-platform'

Get-Location
git branch --show-current
git rev-parse HEAD
git status --short
git log -1 --oneline
```

Debes comprobar:

```text
branch = master
HEAD   = 4cee550
```

También debes comprobar que no existan modificaciones TRACKED inesperadas.

Son aceptables únicamente estos untracked preexistentes:

```text
?? .intelligence/
?? .opencode/
?? contracts/
?? docs/chatgpt-prompts/
?? opencode.json
```

Si:

* HEAD no es `4cee550`;
* hay modificaciones tracked no explicadas;
* existen archivos conflictivos inesperados;

debes:

```text
STOP
```

y reportar la diferencia.

No intentes arreglarla automáticamente.

---

# 2. Restricciones Git

Durante todo `v0.2`:

NO ejecutar:

```text
git add .
git add -A
git clean
git reset --hard
git checkout .
git restore .
git rebase
git push
```

Los archivos de `v0.2` deberán añadirse explícitamente mediante paths concretos.

Los artefactos preexistentes no versionados deben continuar fuera del commit.

---

# 3. Objetivo exacto de v0.2

Construir un **Mock Core Banking local**, pequeño, determinista y completamente ficticio que proporcione la capa backend sobre la cual posteriormente se conectarán:

```text
v0.3 ML/NLP
v0.4 RAG
v0.5 Agent
v0.6 MCP/HITL
v0.7 Reliability/Messaging
```

Este milestone debe demostrar:

```text
Python backend
REST API
typed contracts
validation
relational persistence
transactions
synthetic banking data
error handling
API versioning
correlation IDs
automated testing
clear architecture boundaries
```

No debe incluir IA.

---

# 4. Principio arquitectónico

Continuar con:

```text
MODULAR MONOLITH FIRST
```

No crear microservicios distribuidos.

El Mock Core Banking será un módulo/servicio claramente delimitado dentro del monorepo, pero continuará ejecutándose como una sola aplicación.

No introducir:

```text
Kafka
Redis
Kubernetes
Docker
Azure
Service Bus
Event Grid
MCP
LLM
Foundry
RAG
agents
ML models
OpenTelemetry exporter
Application Insights
```

en este milestone.

---

# 5. Tecnología de v0.2

Utilizar:

```text
Python
FastAPI
Pydantic v2
SQLAlchemy 2.x
SQLite local
pytest
HTTPX / FastAPI TestClient
Ruff
```

SQLite es deliberadamente válido **solo como datastore local del milestone v0.2**.

La arquitectura debe permitir reemplazar posteriormente:

```text
SQLite
   ↓
PostgreSQL
```

sin reescribir el dominio ni las APIs.

No agregar PostgreSQL, Docker ni infraestructura ahora.

Documentar esta decisión mediante ADR.

---

# 6. Antes de instalar dependencias

Ejecutar:

```powershell
python --version
python -m pip --version
```

Si Python no existe o la versión instalada es incompatible con las versiones estables actuales de las dependencias:

```text
STOP
```

No instales Python globalmente.

No modifiques PATH.

No utilices permisos administrativos.

---

# 7. Entorno Python

Si el repositorio todavía no tiene un entorno Python local apropiado, crear:

```text
C:\aegisbank-ai-platform\.venv
```

mediante:

```powershell
python -m venv .venv
```

Usar exclusivamente:

```text
.venv\Scripts\python.exe
```

y:

```text
.venv\Scripts\python.exe -m pip
```

para las operaciones Python de este proyecto.

`.venv/` debe permanecer ignorado por Git.

No modificar Python global.

---

# 8. Dependencias

Antes de escoger versiones:

1. consulta documentación oficial vigente;
2. usa únicamente versiones estables compatibles;
3. evita versiones preview;
4. evita librerías abandonadas;
5. documenta las dependencias;
6. conserva reproducibilidad razonable.

Prioriza documentación oficial de:

```text
FastAPI
Pydantic
SQLAlchemy
pytest
Python
```

No agregues frameworks innecesarios.

No utilizar todavía:

```text
LangChain
LangGraph
Semantic Kernel
Agent Framework
MCP SDK
MLflow
scikit-learn
Transformers
PyTorch
Azure SDK
```

---

# 9. Ubicación del servicio

Crear:

```text
services/mock-core-banking/
```

Estructura objetivo aproximada:

```text
services/
└── mock-core-banking/
    ├── README.md
    ├── pyproject.toml
    ├── src/
    │   └── aegisbank_mock_core/
    │       ├── __init__.py
    │       ├── main.py
    │       ├── config.py
    │       │
    │       ├── api/
    │       │   ├── __init__.py
    │       │   ├── dependencies.py
    │       │   ├── errors.py
    │       │   ├── middleware.py
    │       │   └── routes/
    │       │       ├── __init__.py
    │       │       ├── health.py
    │       │       ├── customers.py
    │       │       ├── loans.py
    │       │       └── service_requests.py
    │       │
    │       ├── domain/
    │       │   ├── __init__.py
    │       │   └── errors.py
    │       │
    │       ├── schemas/
    │       │   ├── __init__.py
    │       │   ├── common.py
    │       │   ├── customers.py
    │       │   ├── loans.py
    │       │   └── service_requests.py
    │       │
    │       └── persistence/
    │           ├── __init__.py
    │           ├── base.py
    │           ├── models.py
    │           ├── session.py
    │           ├── repositories.py
    │           └── seed.py
    │
    └── tests/
        ├── unit/
        └── integration/
```

Puedes realizar pequeñas simplificaciones si eliminan boilerplate sin destruir las separaciones:

```text
API
domain/schema
persistence
testing
```

No crear arquitectura ceremonial innecesaria.

---

# 10. API versionada

Todos los endpoints de negocio deben comenzar con:

```text
/api/v1
```

No crear `/v2`.

La versión de la aplicación es:

```text
0.2.0
```

FastAPI debe exponer OpenAPI automáticamente.

---

# 11. Health endpoints

Implementar:

```http
GET /health/live
```

Debe indicar que el proceso está vivo.

Ejemplo conceptual:

```json
{
  "status": "ok",
  "service": "aegisbank-mock-core",
  "version": "0.2.0"
}
```

Implementar también:

```http
GET /health/ready
```

Este segundo endpoint debe verificar que la aplicación pueda conversar con su datastore local.

No debe realizar modificaciones.

---

# 12. Dominio mínimo

Crear únicamente estas entidades:

```text
Customer
Loan
Installment
ServiceRequest
```

No agregar:

```text
Account
Card
Transaction
Transfer
Payment
Mortgage
Insurance
Investment
Employee
Branch
```

---

# 13. Customer

Campos mínimos:

```text
customer_id
display_name
segment
status
created_at
```

Los valores son sintéticos.

No agregar:

```text
DNI
document_number
phone
email
address
biometric data
real birth date
```

---

# 14. Loan

Campos mínimos:

```text
loan_id
customer_id
product_code
currency
principal_amount
outstanding_balance
status
opened_at
```

Utilizar cantidades monetarias con representación adecuada para dinero.

No usar `float` para la lógica monetaria.

Utilizar:

```text
Decimal
```

o representación equivalente segura.

---

# 15. Installment

Campos:

```text
installment_id
loan_id
installment_number
due_date
principal_due
interest_due
fees_due
total_due
status
```

Estados mínimos:

```text
PENDING
PAID
OVERDUE
```

`total_due` debe ser consistente con sus componentes.

---

# 16. ServiceRequest

Representará solicitudes/reclamos completamente ficticios.

Campos mínimos:

```text
service_request_id
customer_id
category
description
status
created_at
```

Categorías iniciales pequeñas y tipadas.

Por ejemplo:

```text
LOAN
INSTALLMENT
FEE
GENERAL
```

Estados:

```text
OPEN
IN_REVIEW
RESOLVED
REJECTED
```

No construir workflow complejo.

---

# 17. Datos sintéticos deterministas

Crear un mecanismo explícito de seed.

No utilizar generación aleatoria irreproducible.

Debe existir como mínimo:

```text
3 synthetic customers
4 synthetic loans
8+ installments
2 synthetic service requests
```

Usar IDs evidentemente ficticios:

```text
CUST-0001
CUST-0002
CUST-0003

LOAN-0001
LOAN-0002
...

SR-000001
SR-000002
```

Ningún dato debe pertenecer a personas reales.

---

# 18. Endpoints de lectura

Implementar:

```http
GET /api/v1/customers/{customer_id}
```

Retorna el cliente sintético o `404`.

---

Implementar:

```http
GET /api/v1/customers/{customer_id}/loans
```

Retorna exclusivamente los préstamos del cliente solicitado.

---

Implementar:

```http
GET /api/v1/loans/{loan_id}
```

Retorna el préstamo solicitado o `404`.

---

Implementar:

```http
GET /api/v1/loans/{loan_id}/installments/next
```

Debe devolver la siguiente cuota pendiente según reglas determinísticas.

No debe retornar una cuota ya pagada como siguiente cuota.

Definir y probar la regla.

---

# 19. Operación WRITE mínima

Implementar:

```http
POST /api/v1/service-requests
```

Objetivo:

```text
registrar un reclamo/solicitud ficticia
```

Esta API es una CAPACIDAD INTERNA del Core Banking Mock.

IMPORTANTE:

v0.2 todavía NO implementa:

```text
Agent
MCP
HITL
idempotency
retry
circuit breaker
```

Por tanto, documentar claramente:

> La existencia de este endpoint no autoriza a futuros agentes a llamarlo directamente. El control HITL se introducirá en v0.6 antes de exponer esta capacidad como tool, y la idempotencia/reliability se endurecerá en v0.7.

No simules HITL falso dentro del endpoint.

---

# 20. Consulta de ServiceRequest

Implementar:

```http
GET /api/v1/service-requests/{service_request_id}
```

Retornar:

```text
200
```

si existe, y:

```text
404
```

si no existe.

No agregar búsquedas complejas, filtros ni paginación todavía.

---

# 21. Correlation ID

Implementar desde ahora una base simple de correlación HTTP.

Header:

```text
X-Correlation-ID
```

Regla:

Si el cliente proporciona un identificador válido:

```text
request
X-Correlation-ID: <value>
```

la respuesta debe devolverlo.

Si no existe, la aplicación debe generar uno.

Toda respuesta debe incluir:

```text
X-Correlation-ID
```

No implementar todavía distributed tracing ni OpenTelemetry.

Esto es únicamente la primitive de correlación.

---

# 22. Error contract

No devolver stack traces al consumidor.

Utilizar un contrato de error consistente.

Forma conceptual:

```json
{
  "error": {
    "code": "CUSTOMER_NOT_FOUND",
    "message": "Synthetic customer was not found.",
    "correlation_id": "..."
  }
}
```

Definir códigos estables como:

```text
CUSTOMER_NOT_FOUND
LOAN_NOT_FOUND
INSTALLMENT_NOT_FOUND
SERVICE_REQUEST_NOT_FOUND
VALIDATION_ERROR
INTERNAL_ERROR
```

No exponer:

```text
filesystem paths
SQL queries
secrets
stack traces
internal implementation details
```

en respuestas HTTP.

---

# 23. HTTP semantics

Usar correctamente:

```text
200 OK
201 Created
404 Not Found
422 Unprocessable Content / validation equivalent produced by FastAPI
500 Internal Server Error
```

No usar siempre `200`.

`POST /service-requests` debe retornar:

```text
201 Created
```

cuando cree correctamente la solicitud.

---

# 24. Response models

Todos los endpoints de negocio deben utilizar modelos explícitos de respuesta.

Evitar retornar directamente objetos ORM sin una frontera de serialización bien definida.

La API debe tener contratos Pydantic claros.

No exponer columnas internas accidentalmente.

---

# 25. Persistencia

Utilizar SQLAlchemy 2.x siguiendo su API moderna.

Separar:

```text
ORM models
```

de:

```text
API schemas
```

No compartir una instancia global mutable de `Session`.

La duración de cada sesión/transacción debe estar claramente delimitada.

Para escrituras:

```text
begin
↓
operation
↓
commit
```

y ante fallo:

```text
rollback
```

con lifecycle controlado.

---

# 26. SQLite local

El archivo local de desarrollo puede vivir bajo algo similar a:

```text
data/local/aegisbank-dev.db
```

pero debe quedar fuera de Git.

Actualizar `.gitignore` únicamente con las entradas necesarias.

Los tests NO deben utilizar la base de desarrollo compartida.

Cada test suite debe usar una base aislada/temporal.

---

# 27. Configuración

Configuración mediante variables de entorno o defaults seguros.

Ejemplo conceptual:

```text
AEGISBANK_ENV=development
AEGISBANK_DATABASE_URL=...
```

No introducir secretos.

Crear `.env.example` solamente si resulta necesario.

No crear `.env` con información sensible.

---

# 28. Seguridad en v0.2

El Core Mock debe ejecutarse localmente.

Documentar ejecución preferida:

```text
127.0.0.1
```

No:

```text
0.0.0.0
```

por defecto.

No configurar:

```text
CORS *
```

No implementar autenticación falsa.

Autenticación/autorización empresarial se introducirá posteriormente.

Documentar la limitación claramente.

---

# 29. Testing unitario

Crear unit tests únicamente cuando prueben lógica pura relevante.

Como mínimo probar:

```text
money calculations / validation if present
next-installment selection
domain validation
error mapping where appropriate
```

No crear mocks absurdos solo para incrementar cobertura.

---

# 30. Integration/API tests

Usar `pytest` + FastAPI `TestClient`/HTTPX según las recomendaciones oficiales actuales.

Probar como mínimo:

### Health

```text
GET /health/live -> 200
GET /health/ready -> 200 cuando DB disponible
```

### Customer

```text
existing customer -> 200
unknown customer -> 404
```

### Loans

```text
customer loans -> only that customer's loans
existing loan -> 200
unknown loan -> 404
```

### Installments

```text
next pending installment -> correct installment
loan without applicable installment -> defined behavior
```

### ServiceRequest

```text
valid POST -> 201
result can be retrieved
invalid payload -> validation failure
unknown request -> 404
```

### Correlation

```text
provided X-Correlation-ID -> preserved
missing X-Correlation-ID -> generated
```

### OpenAPI

Comprobar que:

```text
/openapi.json
```

incluya los endpoints públicos esperados.

Esto NO es todavía el milestone de contract testing completo.

No introducir Pact todavía.

---

# 31. Seed testing

Los tests deben confirmar que el seed:

```text
es determinista
no contiene datos reales
mantiene relaciones válidas
```

Ejemplo:

```text
Loan.customer_id
```

debe apuntar a un Customer existente.

```text
Installment.loan_id
```

debe apuntar a un Loan existente.

---

# 32. No PII

Realizar una comprobación automatizada o documental sencilla para evitar campos prohibidos.

No deben existir dentro de los modelos sintéticos:

```text
dni
document_number
card_number
cvv
password
real_account_number
biometric
```

No inventar tarjetas falsas porque tampoco son necesarias.

---

# 33. Quality checks

Configurar Ruff de forma simple.

Validaciones mínimas finales:

```powershell
.venv\Scripts\python.exe -m pytest
.venv\Scripts\python.exe -m ruff check .
.venv\Scripts\python.exe -m ruff format --check .
.venv\Scripts\python.exe -m compileall <src-path>
```

Si la sintaxis exacta cambia por la herramienta/versiones estables instaladas, utiliza la forma oficial equivalente.

No declares PASS si alguna validación obligatoria falla.

---

# 34. Ejecución manual

Después de pasar tests, ejecutar temporalmente la aplicación local.

Utilizar algo equivalente a:

```text
127.0.0.1:8001
```

Realizar smoke tests reales contra:

```text
/health/live
/health/ready
/api/v1/customers/CUST-0001
/api/v1/customers/CUST-0001/loans
/api/v1/loans/LOAN-0001
```

y un POST válido de ServiceRequest.

Después detener correctamente el proceso.

No dejar servicios innecesarios ejecutándose.

---

# 35. No Azure

No ejecutar:

```text
az login
az group create
az deployment
az containerapp
az aks
terraform apply
bicep deployment
```

No crear recursos cloud.

No generar costos.

---

# 36. No Docker

No introducir todavía:

```text
Dockerfile
docker-compose.yml
container image
```

Docker aparecerá en un milestone posterior.

El objetivo actual es:

```text
Python local backend
```

---

# 37. No IA

Está prohibido implementar en `v0.2`:

```text
LLM
prompting
embeddings
vector search
RAG
ML classifier
agent
MCP
guardrails LLM
Foundry
Azure OpenAI
```

Esos componentes pertenecen a milestones posteriores.

---

# 38. No reliability avanzada todavía

No implementar en este milestone:

```text
Idempotency-Key
retry policies
exponential backoff
circuit breaker
message broker
dead-letter queues
distributed locks
```

Esos componentes son intencionalmente parte de:

```text
v0.7 — Reliability + Messaging
```

Sí puedes dejar interfaces suficientemente limpias para poder añadirlos después.

No los implementes anticipadamente.

---

# 39. No HITL todavía

`POST /service-requests` representa solamente la capacidad del Mock Core.

No introducir:

```text
human approval database
approval dashboard
approval workflow
agent approval
```

ahora.

El gating HITL será responsabilidad de:

```text
v0.6 — MCP + HITL
```

---

# 40. ADR obligatorios

Crear:

```text
docs/architecture/adr/
```

y documentar al menos:

```text
ADR-001-modular-monolith-first.md
ADR-002-local-sqlite-before-postgresql.md
```

Cada ADR debe contener:

```text
Status
Context
Decision
Alternatives considered
Consequences
```

`ADR-002` debe aclarar:

```text
SQLite = local v0.2 convenience
PostgreSQL = target relational datastore later
SQLAlchemy boundary minimizes migration impact
```

No afirmar que SQLite sería apropiado para un core bancario real.

---

# 41. README del servicio

Crear:

```text
services/mock-core-banking/README.md
```

Debe explicar:

```text
purpose
architecture
synthetic-data warning
setup
run
test
API endpoints
known limitations
future milestones
```

Debe indicar explícitamente:

> This is a local educational mock. It is not a real core banking system.

---

# 42. README raíz

Actualizar:

```text
README.md
```

sin destruir el contenido de `v0.1`.

El roadmap debe mostrar el estado real.

Al terminar satisfactoriamente:

```text
v0.1 Project Charter        COMPLETE
v0.2 Core Banking Mock      COMPLETE
v0.3 ML/NLP Baseline        NOT STARTED
v0.4 RAG                    NOT STARTED
v0.5 Agent                  NOT STARTED
v0.6 MCP + HITL             NOT STARTED
v0.7 Reliability/Messaging  NOT STARTED
v0.8 Quality/Evaluations    NOT STARTED
v0.9 Azure Deployment       NOT STARTED
v1.0 Enterprise Hardening   NOT STARTED
```

No marques como implementado nada futuro.

---

# 43. AGENTS.md

Lee:

```text
AGENTS.md
```

antes de trabajar.

No lo modifiques salvo que exista una razón realmente necesaria derivada de `v0.2`.

Si las reglas actuales ya son suficientes:

```text
no modificar
```

---

# 44. Charter

No modificar los cinco documentos de:

```text
docs/charter/
```

salvo que encuentres una contradicción crítica que haga imposible implementar el milestone.

Si encuentras una:

```text
STOP
```

y repórtala antes de cambiar el charter.

---

# 45. Artefactos concurrentes prohibidos

No tocar:

```text
.intelligence/
.opencode/
contracts/
docs/chatgpt-prompts/
opencode.json
```

Aunque parezcan relacionados.

No investigues su contenido salvo que sea absolutamente necesario para evitar una colisión directa.

No agregarlos a `.gitignore` únicamente para ocultar el estado.

Deben continuar visibles como untracked si ese era su estado.

---

# 46. Revisión de seguridad

Antes del commit, buscar accidentalmente:

```text
password
secret
token
api_key
private_key
connection strings sensibles
```

Distingue entre:

```text
nombre de variable
```

y:

```text
secreto real
```

Un placeholder como:

```text
DATABASE_URL=
```

no es un secreto.

No imprimir secretos existentes en el informe final.

---

# 47. Revisión de arquitectura

Antes del commit responde internamente:

```text
¿Agregamos algo que pertenece a v0.3+?
¿Existe dependencia innecesaria?
¿Estamos usando datos reales?
¿La API tiene contratos claros?
¿La persistencia está separada de los schemas HTTP?
¿Los tests dependen de la DB de desarrollo?
¿Estamos usando float para dinero?
¿Existe lógica escondida en routers que debería estar separada?
```

Corrige cualquier violación antes de continuar.

---

# 48. Validaciones finales obligatorias

Ejecutar todas las validaciones relevantes.

Como mínimo:

```text
pytest
ruff check
ruff format --check
compileall
git diff --check
secret sanity check
manual API smoke test
OpenAPI inspection
```

Registrar exactamente:

```text
command
exit code
result
```

No inventar resultados.

---

# 49. Git review antes de staging

Ejecutar:

```powershell
git status --short
git diff
git diff --check
```

Confirmar nuevamente que:

```text
.intelligence/
.opencode/
contracts/
docs/chatgpt-prompts/
opencode.json
```

continúan fuera del cambio.

---

# 50. Staging seguro

PROHIBIDO:

```text
git add .
git add -A
```

Agregar solamente los paths creados/modificados para `v0.2`.

Después:

```powershell
git diff --cached --name-only
git diff --cached --stat
git diff --cached
```

Inspeccionar el staged set completo.

Si aparece cualquier artefacto preexistente/concurrente:

```text
STOP
```

y retirarlo del staging sin eliminarlo del filesystem.

---

# 51. Commit

Solo si TODO pasa:

```text
pytest PASS
ruff PASS
compile PASS
smoke PASS
OpenAPI PASS
secret check PASS
git diff --check PASS
staged review PASS
```

crear commit local:

```text
feat(v0.2): implement local core banking mock
```

No push.

---

# 52. Validación post-commit

Después del commit ejecutar:

```powershell
git log -1 --oneline
git status --short
git show --stat --oneline HEAD
```

Verificar que el commit contiene solamente archivos de `v0.2`.

Los artefactos concurrentes conocidos pueden permanecer:

```text
?? .intelligence/
?? .opencode/
?? contracts/
?? docs/chatgpt-prompts/
?? opencode.json
```

Eso NO invalida el milestone.

---

# 53. Definition of Done v0.2

`v0.2` está COMPLETE únicamente si:

* [ ] Preflight confirma `4cee550`.
* [ ] Se respetan todos los archivos preexistentes.
* [ ] Existe Mock Core Banking local.
* [ ] FastAPI inicia correctamente.
* [ ] `/health/live` funciona.
* [ ] `/health/ready` verifica datastore.
* [ ] API está versionada bajo `/api/v1`.
* [ ] Existen Customer, Loan, Installment y ServiceRequest.
* [ ] Todos los datos son sintéticos.
* [ ] No existe PII innecesaria.
* [ ] Dinero no usa float para lógica.
* [ ] Seed es determinista.
* [ ] Customers pueden consultarse.
* [ ] Loans pueden consultarse.
* [ ] Siguiente cuota puede consultarse.
* [ ] ServiceRequest puede crearse.
* [ ] ServiceRequest puede recuperarse.
* [ ] Errores tienen contrato consistente.
* [ ] Correlation ID funciona.
* [ ] Response schemas son explícitos.
* [ ] SQLAlchemy Session tiene lifecycle controlado.
* [ ] Tests usan DB aislada.
* [ ] Tests pasan.
* [ ] Ruff pasa.
* [ ] Compile check pasa.
* [ ] Smoke test real pasa.
* [ ] OpenAPI contiene los endpoints previstos.
* [ ] No existen secretos reales.
* [ ] ADR-001 existe.
* [ ] ADR-002 existe.
* [ ] README del servicio existe.
* [ ] README raíz refleja estado real.
* [ ] No existe IA.
* [ ] No existe MCP.
* [ ] No existe Docker.
* [ ] No existe Azure.
* [ ] No existe HITL todavía.
* [ ] No existe idempotencia/retry/circuit breaker todavía.
* [ ] `v0.3` no fue iniciado.
* [ ] Commit local fue creado correctamente.

---

# 54. Informe final obligatorio

Al terminar entrega exactamente un informe estructurado con:

```text
Milestone:
v0.2.0 - Core Banking Mock

Estado:
COMPLETE / BLOCKED / FAILED

PROJECT_PATH:
CURRENT_BRANCH:
START_COMMIT:
FINAL_COMMIT:
COMMIT_MESSAGE:

Arquitectura:
- ...

Stack:
- Python:
- FastAPI:
- Pydantic:
- SQLAlchemy:
- SQLite:
- pytest:
- Ruff:

Endpoints:
- METHOD PATH -> purpose

Datos sintéticos:
- customers:
- loans:
- installments:
- service requests:

Archivos creados:
...

Archivos modificados:
...

Artefactos preexistentes preservados:
...

Validaciones ejecutadas:
COMMAND -> EXIT CODE -> PASS/FAIL

Tests:
TOTAL:
PASSED:
FAILED:

Smoke tests:
...

OpenAPI:
PASS/FAIL

Security review:
PASS/FAIL

Git staged review:
PASS/FAIL

Git Status final:
...

Decisiones:
...

Deuda técnica deliberada:
...

Fuera de alcance preservado:
- ML
- RAG
- Agent
- MCP
- HITL
- reliability
- messaging
- Docker
- Azure

Siguiente milestone recomendado:
v0.3 - ML/NLP Baseline
```

---

# 55. Estado final

Solo si TODOS los criterios de `v0.2` fueron realmente satisfechos y validados, finalizar con:

```text
AEGISBANK_V0.2_CORE_BANKING_MOCK_READY
```

Si existe cualquier blocker:

```text
AEGISBANK_V0.2_BLOCKED
```

y explica la causa exacta.

Después:

```text
STOP.
```

NO comiences:

```text
v0.3
```

hasta recibir mi aprobación explícita.
