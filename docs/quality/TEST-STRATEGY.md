# AegisBank — Test Strategy (v0.13.0-R2)

> **Milestone:** `v0.13.0-R2 — Test Suite Rationalization`
> **Principio rector:** `TEST VALUE > TEST COUNT`.

## 1. Test Pyramid

```
            /\
           /  \          E2E (Critical User Journeys)
          / E2E \         pocos journeys bancarios completos
         /──────\
        / Contract\      Contratos JSON Schema, MCP, Outbox events
       /──────────\
      /Integration\     Componentes conectados (DB + RAG + Bus + Cosmos)
     /──────────────\
    /     Unit       \   Pieza única, sin I/O o con stubs en memoria
   /──────────────────\
```

Microsoft Well-Architected y Microsoft Foundry AI-200 recomiendan esta distribución: muchos unit tests rápidos en la base y muy pocos E2E en la cima porque los E2E son los más costosos y frágiles. ([Microsoft Learn][1]; [Microsoft Learn][2]).

## 2. Capas AegisBank (post v0.13.0-R2)

```
ai/agent/tests/
├── unit/           # pieza única, < 1 s por caso, sin estado externo
├── integration/    # múltiples componentes internos en proceso
├── contracts/      # JSON Schema, interfaces
├── e2e/             # Critical User Journeys
│   ├── read_journeys/
│   └── write_journeys/
└── infra/           # opt-in: Docker, K8s, Functions, Cosmos emulator
    ├── containers/
    ├── kubernetes/
    ├── serverless/
    ├── cosmos/
    └── session_guard/
```

Los números de versión (v06/, v07/, v08/, v09/, v012/, v013r1/) **ya no existen en el árbol**; viven en Git history, ADRs y documentación.

## 3. Pytest Markers (estrictos, `--strict-markers`)

| Marker | Capa | `pytest ai/agent/tests/...` |
|---|---|---|
| `unit` | Pieza única | `unit/` |
| `integration` | Componentes en proceso | `integration/` |
| `contract` | JSON Schema | `contracts/` |
| `e2e` | Critical User Journeys | `e2e/` |
| `infra` | Docker / K8s / Functions | `infra/` |
| `slow` | Tests con sleeps o tiempos largos | opt-in |

`pytest.mark.unit` se aplica vía `pytestmark = pytest.mark.unit` en cada archivo de `unit/`. No se permite mezclar capas en un mismo archivo.

## 4. Gates

### FAST / PR (gate por defecto)
```bash
pytest ai/agent/tests/unit ai/agent/tests/integration ai/agent/tests/contracts
ruff check .
ruff format --check .
python -m compileall -q .
```
Tiempo objetivo: **< 30 s**.

### CRITICAL E2E (opt-in, pre-release)
```bash
pytest ai/agent/tests/e2e
```
Tiempo objetivo: **< 30 s**.

### INFRA (opt-in, post-merge)
```bash
pytest ai/agent/tests/infra
pytest ai/agent/tests/contracts
scripts/container_acceptance.py   # requiere Docker + MSSQL_SA_PASSWORD
```
Opt-in porque requiere Docker, Kubernetes cluster local, etc.

## 5. Conceptos Pedagógicos (Maestría)

- **Unit Test** = pieza única, sin I/O.
- **Integration Test** = piezas conectadas (DB + RAG + Bus + Cosmos in-process).
- **Contract Test** = dos componentes cumplen su contrato (JSON Schema, MCP tool spec, Outbox event payload).
- **E2E Test** = journey completo del usuario. Solo journeys bancarios críticos.
- **Regression Test** = test que codifica un bug real para que no vuelva a aparecer (p. ej. `test_metamorphic_paraphrase_matrix_loan_details` codifica el bug "Dame detalle de mi LOAN-0001" descubierto manualmente).
- **Parametrization** (`@pytest.mark.parametrize`) = un test con varios inputs para evitar duplicar funciones casi idénticas.
- **Flaky Test** = test que pasa y falla sin cambios de código. Marcar como `slow` y aislar.
- **Critical User Journey** = el subconjunto mínimo de journeys que cubren el valor de negocio.
- **Diminishing Returns** = a partir de cierta densidad, agregar tests ya no aumenta la confianza sino el costo y el ruido.
- **Test Maintenance Debt** = infraestructura de tests que consume tiempo sin proteger ningún riesgo. Es exactamente lo que `v0.13.0-R2` ataca.

## 6. Reglas Permanentes

1. **No se conservan tests solo porque existen desde versiones antiguas.** Git preserva el historial.
2. **No se borran tests solo para bajar el contador.** Un test permanece porque protege un riesgo, no porque aumenta el contador.
3. **Antes de consolidar un test, clasificarlo:**
   - `KEEP_CRITICAL` (HITL, Outbox, ownership, idempotency, etc.)
   - `KEEP_UNIQUE` (un test único para una propiedad)
   - `MERGE_PARAMETRIZE` (variantes equivalentes → `@pytest.mark.parametrize`)
   - `MOVE_LAYER` (el test está bien pero pertenece a otra capa)
   - `DELETE_DUPLICATE` (otro test ya lo cubre)
   - `DELETE_OBSOLETE` (la responsabilidad ya no existe en el código)
4. **Críticos que NO se pueden perder:**
   - Native structured tool calling
   - Pseudo-tool-call blocked
   - Ownership/customer isolation
   - Loan routing paraphrase regression
   - RAG grounding + abstention + superseded docs
   - MCP + HITL APPROVE/REJECT
   - WRITE idempotency
   - Retry + Circuit Breaker + Timeout
   - Transactional Outbox
   - Idempotent Consumer + DLQ
   - Audit + OTel + HOTL
   - Core Banking contracts
   - Critical READ E2E
   - Critical WRITE E2E (HITL → WRITE → Outbox → Consumer)
   - Security/secret gates
   - Docker/Kubernetes/Functions acceptance como INFRA

## 7. How to Add a Test

1. Decidir capa (`unit` / `integration` / `contract` / `e2e` / `infra`).
2. Colocar el archivo en la carpeta correcta **sin prefijo de versión**.
3. Definir `pytestmark = pytest.mark.<capa>` al inicio del archivo.
4. Si hay variantes equivalentes, **parametrizar**.
5. Antes de agregar, verificar si la propiedad ya está cubierta por otro test.

[1]: https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/testing
[2]: https://learn.microsoft.com/en-us/azure/foundry/how-to/evaluate-generative-ai-app
