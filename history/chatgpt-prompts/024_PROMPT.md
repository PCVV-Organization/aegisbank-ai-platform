# 024 — AegisBank v0.13.0-R2 Test Suite Rationalization

Actúa estrictamente como ORCHESTRATOR.

Objetivo único:
reducir y simplificar la suite de tests sin perder cobertura funcional, seguridad ni regresiones críticas.

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

## 0. Baseline primero

Verifica:

```
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -6 --oneline
```

Si `v0.13.0-R1` aún tiene cambios sin commit:
`STOP` con `AEGISBANK_TEST_RATIONALIZATION_NEEDS_CLEAN_BASELINE`.

No mezclar el commit funcional R1 con la limpieza de tests.

Luego adquiere SessionGuard.

NO Azure, NO v0.14, NO cambios funcionales de producción, NO push, NO worktrees, NO `git add .`/`-A`.

## 1. Principio rector

Aplica: **TEST VALUE > TEST COUNT**.

Clasifica cada test:

- `KEEP_CRITICAL`
- `KEEP_UNIQUE`
- `MERGE_PARAMETRIZE`
- `MOVE_LAYER`
- `DELETE_DUPLICATE`
- `DELETE_OBSOLETE`

## 2. Inventario real

`pytest --collect-only` → `docs/quality/TEST-SUITE-RATIONALIZATION.md` (comportamiento, capa, requisito, duplicados, decisión, motivo).

## 3. Tests que NO se pueden perder

native structured tool calling; pseudo-tool-call nunca ejecutado; ownership/customer isolation; loan routing/paraphrase regression; RAG grounding + abstention + superseded docs; MCP + HITL APPROVE/REJECT; WRITE idempotency; retries/circuit breaker/timeout; transactional outbox; idempotent consumer + DLQ; audit/OTel/HOTL; contracts de Core Banking/tools/events; critical E2E READ; critical E2E WRITE; security/secret gates; Docker/Kubernetes/serverless acceptance como INFRA.

## 4. Eliminar organización por milestone

Reorganiza SOLO los tests que sobrevivan hacia:

```
ai/agent/tests/
  unit/
  integration/
  contracts/
  e2e/
  infra/
    containers/
    kubernetes/
    serverless/
  conftest.py
```

Eliminar `__pycache__/` del árbol si aparece trackeado.

## 5. Consolidación

Prioriza `@pytest.mark.parametrize`, fixtures compartidas, un único test por propiedad, integration en lugar de múltiples E2E, pequeño conjunto de Critical User Journeys.

## 6. Pytest markers y gates

Markers: `unit`, `integration`, `contract`, `e2e`, `infra`, `slow`. `--strict-markers`.

Gates:

- `FAST / PR` → unit + contract + integración crítica.
- `CRITICAL E2E` → solo journeys bancarios críticos.
- `INFRA` → opt-in para Docker/K8s/Functions/data emulators.

## 7. Objetivo de reducción

Preferencia: ≥25% menos tests del paquete agent sin perder invariantes únicos.

## 8. Validación de no regresión

Después de cada lote: suite afectada, critical E2E, contracts, fast quality gate.

Al final: Agent, RAG, ML, Core Banking, contracts, critical E2E, ruff, format, compileall, bandit, pip-audit, secret scan, Pylint R0801, `git diff --check`. Mantener `NEW TRUE_DUPLICATION = 0`.

## 9. No tocar producción

NO modificar `src/` salvo bug real → `STOP` con `AEGISBANK_TEST_RATIONALIZATION_FOUND_PRODUCT_BUG`.

## 10. Documentación

`docs/quality/TEST-STRATEGY.md`, `docs/quality/TEST-SUITE-RATIONALIZATION.md`, `docs/learning/MASTERS-NOTES.md`.

Explicar desde cero: Test Pyramid, unit/integration/contract/E2E, regression test, parametrization, flaky test, Critical User Journey, diminishing returns, test maintenance debt.

## 11. Git

`session_guard check` antes de staging. Stage explícito. Commit `test(v0.13): rationalize suite around critical behavior`. No push. Liberar SessionGuard al final.

## Informe final

BASELINE / BEFORE / AFTER / REMOVED / MERGED / CRITICAL INVARIANTS / TEST PYRAMID / FAST GATE / FULL GATE / PRODUCT CODE CHANGED / NEW TRUE DUPLICATION / WORKING TREE / PUSH.

Finalizar únicamente con `AEGISBANK_V0.13_TEST_SUITE_RATIONALIZED` y STOP.

NO iniciar v0.14.
