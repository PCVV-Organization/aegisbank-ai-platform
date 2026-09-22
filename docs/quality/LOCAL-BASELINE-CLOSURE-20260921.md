# Local Baseline Closure & Release Readiness — 2026-09-21

## 1. STATUS

Auditoría y estabilización local completadas; **NOT_RELEASE_READY**.
R2: **R2_PARTIAL**. Recomendación única: **BLOCKED_BY_BASELINE_DEFECT**.
Se corrigieron defectos reproducidos y se prepararon commits; no hay staging,
commits, etiquetas, remotos, despliegues ni nueva funcionalidad bancaria.
Evidencia estructurada: [JSON](LOCAL-BASELINE-EVIDENCE-20260921.json).

## 2. APPLICATION PREFLIGHT

Raíz: `C:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform`; alias de escritura
permitido: `C:/aegisbank-ai-platform/aegisbank-ai-platform`.
Rama `master`; HEAD `477ac3b4ddf07931b6c4f50650bf1a6d98944e62`.
Título: `feat(v1.0.6): invariant no account facts without tools, comparative read plan and placeholder defense`.
Tags existentes `v1.0.0`, `v1.0.1`; ninguno apunta a HEAD. Remotos: ninguno.
Preflight: 13 archivos tracked modificados, 19 untracked; 359 inserciones/245
eliminaciones en diff tracked. Staging vacío. SessionGuard inicialmente ausente;
se adquirió `baseline-closure-20260921` antes de modificar o ejecutar el gate.
El guard se verifica y libera al cierre. No se liberaron sesiones ajenas.
Los cinco títulos recientes usan versiones/alcances, pero sus cuerpos están vacíos.
No se reescribe el historial; AGENTS exige títulos revisados y cuerpos detallados.

## 3. AI-ENV PREFLIGHT

Raíz `C:/aegisbank-ai-platform-ai-env`, rama `main`, sin HEAD, tags ni remotos.
Preflight: 51 archivos untracked, staging vacío, `git diff --check` PASS.
La aplicación está ignorada y `git ls-files aegisbank-ai-platform` no devuelve
archivos. No hay submódulo ni gitlink. No se propone combinar repositorios.

## 4. APPLICATION DIFF INVENTORY

Inventario final de 37 rutas de entrega, respecto de HEAD y archivos
no ignorados. No hay cambios funcionales nuevos en contratos, persistencia, ML o
infraestructura; sus cambios listados son documentación. Los artefactos runtime
ignorados no forman parte de esta selección.

| Archivo | Clasificación | Propósito / propietario |
| --- | --- | --- |
| `AGENTS.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `README.LLM.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `README.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `ai/agent/README.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `ai/agent/src/aegisbank_agent/agent.py` | AGENT/RUNTIME; SECURITY | Orquestador: aislar contexto y denegar herramientas fuera de política |
| `ai/agent/src/aegisbank_agent/evaluation/__init__.py` | EVALUATION | Extensión del evaluador canónico, métricas y exportaciones |
| `ai/agent/src/aegisbank_agent/evaluation/red_team.py` | EVALUATION | Extensión del evaluador canónico, métricas y exportaciones |
| `ai/agent/src/aegisbank_agent/knowledge_routing.py` | SECURITY | Routing: selección mínima, intención de escritura y detección de clientes |
| `ai/agent/tests/unit/evaluation/test_invariant_registry_consistency.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `ai/agent/tests/unit/evaluation/test_least_agency.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `ai/agent/tests/unit/evaluation/test_output_guard.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `ai/agent/tests/unit/evaluation/test_phase2_red_team.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `ai/agent/tests/unit/routing/test_adversarial_red_team.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `ai/agent/tests/unit/routing/test_agent_lifecycle.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `ai/rag/README.md` | RAG; CANONICAL DOCUMENTATION | Entrypoint del RAG existente |
| `deploy/local/README.md` | INFRASTRUCTURE; CANONICAL DOCUMENTATION | Requisitos operativos existentes |
| `docs/README.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `docs/architecture/CANONICAL-COMPONENTS.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `docs/briefings/AEGISBANK-AI-PLATFORM-CHATGPT-BRIEFING.md` | HISTORICAL/WALKTHROUGH | Contexto histórico preservado con advertencia de vigencia |
| `docs/engineering/DOCUMENTATION-MAINTENANCE.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `docs/engineering/REPOSITORY-BOUNDARIES.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `docs/evaluation/EVALUATION-CATALOG.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `docs/quality/BASELINE-COMMIT-PLAN-20260921.json` | REPORT/EVIDENCE | Cierre, procedencia y selección explícita; documentación de calidad |
| `docs/quality/DOCUMENTATION-REORGANIZATION-20260915.md` | HISTORICAL/WALKTHROUGH | Contexto histórico preservado con advertencia de vigencia |
| `docs/quality/LOCAL-BASELINE-CLOSURE-20260921.md` | REPORT/EVIDENCE | Cierre, procedencia y selección explícita; documentación de calidad |
| `docs/quality/LOCAL-BASELINE-EVIDENCE-20260921.json` | REPORT/EVIDENCE | Cierre, procedencia y selección explícita; documentación de calidad |
| `docs/requirements/V1.0-MATURITY-MATRIX.md` | REPORT/EVIDENCE | Cierre, procedencia y selección explícita; documentación de calidad |
| `docs/security/PHASE2-LOCAL-RED-TEAM-EVIDENCE.md` | REPORT/EVIDENCE | Evidencia histórica y corrección de alcance R1/R2 |
| `docs/security/V1.0-THREAT-MODEL.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `llms.txt` | CANONICAL DOCUMENTATION | Índices generados para navegación máquina |
| `ml/intent-classifier/README.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |
| `project-index.json` | CANONICAL DOCUMENTATION | Índices generados para navegación máquina |
| `scripts/documentation_index.py` | OTHER | Generación documental determinista, no runtime bancario |
| `scripts/run_local_red_team.py` | EVALUATION | Harness opt-in de modelos locales; fixtures sintéticos y evidencia |
| `scripts/run_phase22_live.py` | EVALUATION | Harness opt-in de modelos locales; fixtures sintéticos y evidencia |
| `scripts/test_documentation_index.py` | TEST | Regresión de la responsabilidad correspondiente; sin nuevo componente |
| `services/mock-core-banking/README.md` | CANONICAL DOCUMENTATION | Propósito, reglas, límites y navegación del componente existente |

## 5. CANONICAL RESPONSIBILITY CLASSIFICATION

**NEW TRUE CANONICAL RESPONSIBILITIES: 0**.

| Responsabilidad canónica | Decisión | Cambio / invariantes / evidencia |
| --- | --- | --- |
| AgentOrchestrator / routing | EXTEND | Etiquetas no confiables, I_4 postgeneración, selección y rechazo de tools; I_1/I_2/I_3/I_4/I_7; lifecycle, least-agency, adversarial y E2E |
| ToolRegistry, HITL, HOTL, ownership | REUSE | Sin nuevo ejecutor ni autorización LLM; política se aplica antes de invocar los componentes |
| Local AI Evaluation & MLOps | EXTEND | red_team y exportaciones, oráculos/UTPR, runner local y pgvector; tests Phase2 y registro de invariantes; live histórico |
| RAG / banking tools | REUSE | Los harness usan retriever y capacidades reales existentes; fixtures sintéticos no crean un segundo RAG |
| Quality/documentation ownership | EXTEND | Índices de rutas, pruebas e informes de cierre; soporte a separación de repositorios |

El cambio previo cubría Phase2, Phase2.2-R1 y R2. Este cierre añade únicamente
correcciones demostradas: rechazo de herramientas fuera de política, imperativo
«crea un reclamo», oráculo de cualquier cliente ajeno y formato Ruff.

## 6. CURRENT PHASE-2 CAPABILITY INVENTORY

- Routing adversarial fijo y consistencia de 15 invariantes: pruebas presentes y ejecutadas.
- Evaluador Phase2: ASR, utilidad, rechazos, escrituras y UTPR; no es un evaluador universal.
- Live XPIA/outputs: harness opt-in con pgvector, herramientas reales y cuatro ataques/dos controles.
- I_4: filtro de IDs ajenos antes de devolver la respuesta generada; redacción auxiliar no está integrada.
- Least agency: subsets según intención; OTHER aún entrega todo el registro. Ahora se deniegan propuestas fuera del subset antes de ejecución/HITL.
- Output guard: tests de detector y redacción; ejemplos benignos con IDs ajenos se etiquetan positivos, por lo que no acreditan precisión semántica.
- UTPR: calcula anomalías desde ToolCallRecord y herramientas declaradas en fixtures; mezcla propuestas con prelecturas deterministas.

## 7. R2 STATUS CLASSIFICATION

**R2_PARTIAL**, no R2_NOT_STARTED. Existen implementación, tests y un JSON histórico
R2 con UTPR 0/2. Falta demostrar: propuestas reales por ronda frente a ejecución,
conjunto efectivamente ofrecido al modelo, benignos semánticos y falsos positivos
del guard, y evidencia live posterior a las correcciones. El nombre de la suite
no sustituye estos criterios. El fallback OTHER conserva una superficie amplia.

## 8. EVIDENCE RECONCILIATION

| Afirmación | Clasificación | Conclusión |
| --- | --- | --- |
| Phase2.1, 2026-09-11, phi-4-mini-instruct-openvino-gpu | HISTORICAL_EXECUTED | ASR 0/8, utilidad 3/3; no reejecutada |
| Phase2.2, 2026-09-12, phase2.2-r2-live-v1 | HISTORICAL_EXECUTED | ASR 0/4, utilidad 2/2, rechazo 0/2, UTPR 0/2; límites del oráculo |
| Prosa R1 / anteriores 0/2 ataques | STALE | El artefacto actual es R2 con cuatro ataques; no inventar una ejecución R1 separada |
| «trayectorias completas / herramientas expuestas autoritativas» | DOCUMENTATION_ONLY | Fixtures y ToolCallRecord no son captura independiente del protocolo por ronda |
| Routing, least-agency, I_4, regresiones nuevas | REEXECUTED_THIS_MILESTONE | 81 casos enfocados, incluidos 40 adversariales; no llamarlos 81 ataques |
| Guard sin falsos positivos | NOT_REPRODUCED | Tests del detector no equivalen a utilidad semántica |
| FAST histórico | HISTORICAL_EXECUTED | Payload original preservado, no atribuido a este checkout |
| FAST actual / E2E / esquemas / tipos | REEXECUTED_THIS_MILESTONE | Resultados en secciones 9–11 |
| MLOps promotion actual | DERIVED_FROM_CURRENT_TESTS | Trazas simuladas; superioridad estadística no establecida |
| Docker motor indisponible en matriz antigua | STALE | Docker responde ahora; reproducción aislada NOT_REPRODUCED |
| CI remoto / Azure / producción | DOCUMENTATION_ONLY | Configurado o pendiente; sin ejecución acreditada |

Antes del gate se copió `reports/` a `.coordination/baseline-closure-20260921/historical-reports/`.
El JSON versionable conserva tres payloads históricos completos con sus SHA-256,
fechas originales y clasificación. Gate inicial falló lint y formato; el final
pasó tras correcciones. Los live JSON originales no se sobrescribieron.

## 9. TEST EXECUTION

Comandos desde la raíz de aplicación, usando `.venv/Scripts/python.exe` (P).
El intento inicial con Python global falló importando `mock_core_banking`;
se corrigió el intérprete sin instalar paquetes.

| Comando | PASS / FAIL / SKIP | Tiempo pytest |
| --- | --- | --- |
| P -m pytest -q ai/agent/tests/unit/evaluation/test_invariant_registry_consistency.py ai/agent/tests/unit/evaluation/test_least_agency.py ai/agent/tests/unit/evaluation/test_output_guard.py ai/agent/tests/unit/evaluation/test_phase2_red_team.py ai/agent/tests/unit/routing/test_adversarial_red_team.py | 59 / 0 / 0 | 3.57s |
| P -m pytest -q ai/agent/tests/unit/evaluation ai/agent/tests/unit/routing/test_agent_lifecycle.py ai/agent/tests/unit/routing/test_adversarial_red_team.py | 81 / 0 / 0 | 2.67s |
| P -m pytest services/mock-core-banking/tests | 58 / 0 / 0 | 5.88s |
| P -m pytest ml/intent-classifier/tests | 22 / 0 / 0 | 2.09s |
| P -m pytest ai/rag/tests | 77 / 0 / 11 | 9.17s |
| P -m pytest -c ai/agent/pyproject.toml ai/agent/tests/unit ai/agent/tests/integration ai/agent/tests/contracts | 309 / 0 / 0 | 19.53s |
| P -m pytest -q ai/agent/tests/e2e | 11 / 0 / 0 | 1.99s |
| P -B scripts/test_documentation_index.py | 7 / 0 / 0 | 0.205s unittest (última ejecución) |

FAST: **466 PASS, 11 SKIP**. E2E aparte: **11 PASS**. No sumar suites enfocadas
de nuevo: se solapan. Los 11 skips requieren Redis en 127.0.0.1:6379, ausente;
confirmado con `P -m pytest -q -rs ai/rag/tests` (77/0/11, 9.03s, dos warnings
SVD). No se afirma suite infra completa. Regresión del dispatcher falló 1/1 antes
del fix; disclosure falló 2/3 antes del fix; se conservó HITL en E2E de escritura.

## 10. STATIC / CONTRACT VALIDATION

Ruff lint, format y compileall: PASS por gate. Nueve JSON Schema 2020-12
validados con `Draft202012Validator.check_schema`; cinco imports canónicos PASS.
Arquitectura: verificación existente de catálogo y ownership PASS; no es prueba
semántica exhaustiva. Secret scan tracked PASS; extensión de los mismos patrones
sobre tracked+untracked: 441 app / 52 ai-env, sin hallazgos en la captura final.
El escáner omite ejemplos/placeholders y es heurístico; staging permanece vacío.

Pyright se ejecutó sin suprimir reglas, usando las cuatro raíces fuente y el
intérprete local. No se encontró configuración Pyright por proyecto. Comando:

```powershell
node ../.opencode/node_modules/pyright/index.js --pythonpath .venv/Scripts/python.exe ai/agent/src ai/rag/src ml/intent-classifier/src services/mock-core-banking/src --outputjson
```

Resultado final: **75 errores / 0 warnings / 97 archivos / 11.925s**.
Los 15 archivos distintos de agent.py no tienen diff en esta baseline; los tres
diagnósticos de agent.py están en `_call_completions`, cuyo código se contrastó
con HEAD y no cambió. Esto localiza deuda preexistente en archivos/líneas, pero
no sustituye una ejecución histórica de Pyright sobre HEAD. No se silenció ni
se acometió una migración de tipos transversal para fingir readiness.

| Archivo | Errores |
| --- | ---: |
| `ai/agent/src/aegisbank_agent/agent.py` | 3 |
| `ai/agent/src/aegisbank_agent/cli.py` | 1 |
| `ai/agent/src/aegisbank_agent/mcp_boundary.py` | 6 |
| `ai/agent/src/aegisbank_agent/observability/telemetry.py` | 1 |
| `ai/agent/src/aegisbank_agent/tools/banking_tools.py` | 1 |
| `ai/rag/src/aegisbank_rag/cache.py` | 1 |
| `ai/rag/src/aegisbank_rag/dense_local.py` | 2 |
| `ai/rag/src/aegisbank_rag/embedding.py` | 22 |
| `ai/rag/src/aegisbank_rag/evaluation.py` | 1 |
| `ai/rag/src/aegisbank_rag/lexical.py` | 14 |
| `ai/rag/src/aegisbank_rag/pgvector_retriever.py` | 4 |
| `ai/rag/src/aegisbank_rag/redis_retriever.py` | 4 |
| `ml/intent-classifier/src/aegisbank_intent_classifier/evaluation.py` | 10 |
| `services/mock-core-banking/src/mock_core_banking/api/loans.py` | 1 |
| `services/mock-core-banking/src/mock_core_banking/main.py` | 3 |
| `services/mock-core-banking/src/mock_core_banking/persistence/types.py` | 1 |

## 11. FAST QUALITY GATE

Comando: `$env:AEGISBANK_SESSION_ID='baseline-closure-20260921'; P -B scripts/quality_gate.py --fast`.
Reporte `reports/quality_gate_summary.json`, timestamp `2026-09-21T13:45:22Z`;
copia durable en JSON de evidencia. Resultado: **13 PASS + 0 SKIP; overall PASS**.
Los skips internos de pytest se informan aparte. Bandit/pip-audit y gates infra
opt-in no forman parte de FAST: NOT RUN, no PASS.

| Gate | Estado | Segundos |
| --- | --- | ---: |
| Cross-Session Writer Guard | PASS | 0.143 |
| Redis Image Reproducibility Gate | PASS | 0.000 |
| Static Analysis: Ruff Lint | PASS | 0.206 |
| Static Analysis: Ruff Format | PASS | 0.183 |
| Python Bytecode Compilation | PASS | 13.616 |
| Core Banking Tests & Contracts | PASS | 7.754 |
| ML Intent Classifier Tests | PASS | 3.101 |
| AI RAG Tests | PASS | 12.417 |
| AI Agent FAST Gate (unit + integration + contracts) | PASS | 24.585 |
| AI Evaluation and MLOps Promotion Gate | PASS | 7.305 |
| Architecture Inventory Gate | PASS | 0.000 |
| Secret Scanning Gate | PASS | 0.294 |
| Git Whitespace & Diff Check | PASS | 0.077 |

## 12. LIVE EVIDENCE STATUS

No se reejecutó ninguna suite live. `foundry status -o json`: CLI 0.10.3,
servicio `not_running`, ready false, sin modelos servidos. Docker responde;
pgvector healthy y App Configuration activo, además de contenedores ajenos al
alcance. Redis, Cosmos, Service Bus y Core Banking no aparecen activos.
Phase2.1 necesita Foundry y datos locales; Phase2.2 requiere además PostgreSQL +
pgvector, corpus sintético y modelo/embeddings. Son evaluaciones estocásticas.
Reejecutarlas será útil tras corregir tipos y completar instrumentación R2;
ahora no cerrarían esos defectos. Antes del futuro run versionar destino y
capturar modelo, runtime, suite y fecha. No arrancar/parar servicios existentes.

## 13. RELEASE READINESS

**NOT_RELEASE_READY** por Pyright fallido y aceptación R2 incompleta. No proponer
semver ni tag. El nombre v1.0.6 del último commit no acredita tag v1.0.6.
Maturity: TESTED-LOCAL con skips declarados; CI-CONFIGURED/RUNNER-PENDING,
CLOUD-PENDING, PROD-UNPROVEN. Los commits propuestos son estabilización/documentación,
no una release. Excluir reports locales, entornos, bases, secretos, cachés, mlruns,
artefactos y locks. Las rutas de entrega exactas están abajo y en JSON.

## 14. PROPOSED APPLICATION COMMIT PLAN

Plan [machine-readable](BASELINE-COMMIT-PLAN-20260921.json). **No ejecutado**.
Tres commits ordenados: seguridad/pruebas/evidencia relacionada juntos para evitar
tests huérfanos; navegación después; cierre al final. El briefing se incluye en el
primero porque el test de invariantes lo requiere. Revisar diff completo y título
antes del staging explícito; usar archivo UTF-8 para el cuerpo. Revalidar checks
tras materializar cada selección: las pruebas actuales cubren el árbol combinado,
no snapshots de commits aún inexistentes. No `git add .`, `git add -A` ni amend.

### Aplicación 1: fix(agent): enforce query tool policy and correct disclosure evaluation

Dependencia: ninguna. Rutas exactas:

- `ai/agent/src/aegisbank_agent/agent.py`
- `ai/agent/src/aegisbank_agent/evaluation/__init__.py`
- `ai/agent/src/aegisbank_agent/evaluation/red_team.py`
- `ai/agent/src/aegisbank_agent/knowledge_routing.py`
- `ai/agent/tests/unit/evaluation/test_invariant_registry_consistency.py`
- `ai/agent/tests/unit/evaluation/test_least_agency.py`
- `ai/agent/tests/unit/evaluation/test_output_guard.py`
- `ai/agent/tests/unit/evaluation/test_phase2_red_team.py`
- `ai/agent/tests/unit/routing/test_adversarial_red_team.py`
- `ai/agent/tests/unit/routing/test_agent_lifecycle.py`
- `docs/briefings/AEGISBANK-AI-PLATFORM-CHATGPT-BRIEFING.md`
- `docs/evaluation/EVALUATION-CATALOG.md`
- `docs/security/PHASE2-LOCAL-RED-TEAM-EVIDENCE.md`
- `docs/security/V1.0-THREAT-MODEL.md`
- `scripts/run_local_red_team.py`
- `scripts/run_phase22_live.py`

Mensaje completo propuesto:

```text
fix(agent): enforce query tool policy and correct disclosure evaluation

Purpose
Close an evidenced gap where a model proposal could invoke a registered tool
outside the active query allowlist. Consolidate the existing uncommitted Phase-2
security work without adding a banking capability or architectural component.

Changes
Enforce query policy before registry dispatch, cached reads and HITL requests.
Recognize explicit Spanish claim imperatives while retaining human approval.
Reuse the canonical customer detector in the disclosure oracle; include regression
cases beyond the numerically next customer. Preserve the existing untrusted-context
labels, least-agency routing, Phase-2 harness and invariant consistency tests.
Reconcile R1 narrative labels with the historical R2 JSON and document telemetry limits.

Validation
Focused evaluation/routing suite: 81 passed in 2.67s. E2E: 11 passed in 1.99s.
Canonical scripts/quality_gate.py --fast: 13 PASS, 0 gate SKIP; underlying suites
466 passed and 11 Redis-dependent tests skipped. New dispatch and disclosure
regressions failed before the fixes and passed afterwards.

Limitations
No live Foundry rerun. R2 remains partial: model-only proposal capture and semantic
output-guard false positives are not established. Pyright still reports 75 errors
across 97 source files analyzed. This commit does not declare a release.
```

### Aplicación 2: docs(application): define repository boundaries and machine navigation

Dependencia: [1]. Rutas exactas:

- `AGENTS.md`
- `README.LLM.md`
- `README.md`
- `ai/agent/README.md`
- `ai/rag/README.md`
- `deploy/local/README.md`
- `docs/README.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/DOCUMENTATION-MAINTENANCE.md`
- `docs/engineering/REPOSITORY-BOUNDARIES.md`
- `docs/quality/DOCUMENTATION-REORGANIZATION-20260915.md`
- `llms.txt`
- `ml/intent-classifier/README.md`
- `project-index.json`
- `scripts/documentation_index.py`
- `scripts/test_documentation_index.py`
- `services/mock-core-banking/README.md`

Mensaje completo propuesto:

```text
docs(application): define repository boundaries and machine navigation

Purpose
Make the independent application understandable to developers and LLMs without
confusing it with the outer development environment or historical milestone claims.

Changes
Update component entrypoints, repository boundaries, application instructions and
documentation ownership. Add deterministic JSON/llms navigation generation and its
tests. Require reviewed commit titles and detailed purpose/change/validation/limits
bodies. Preserve the historical Git messages and uncommitted-work distinction.

Validation
scripts/test_documentation_index.py: 7 passed. Regenerate project-index.json and
llms.txt, then run scripts/documentation_index.py --check and git diff --check.
The final closure report records observed checks and exact file selection.

Limitations
Navigation indexes do not certify runtime behavior. Absolute workspace paths are
local setup information; application and ai-env remain independent Git repositories.
This commit depends on the security/evaluation files referenced by the documentation.
```

### Aplicación 3: docs(quality): record baseline evidence and blocked release readiness

Dependencia: [1, 2]. Rutas exactas:

- `docs/quality/BASELINE-COMMIT-PLAN-20260921.json`
- `docs/quality/LOCAL-BASELINE-CLOSURE-20260921.md`
- `docs/quality/LOCAL-BASELINE-EVIDENCE-20260921.json`
- `docs/requirements/V1.0-MATURITY-MATRIX.md`

Mensaje completo propuesto:

```text
docs(quality): record baseline evidence and blocked release readiness

Purpose
Record the current local state after 477ac3b with reproducible evidence provenance
and an explicit commit plan before another application milestone is selected.

Changes
Add the 20-section closure report, machine-readable evidence and exact per-commit
file lists. Preserve historical report payloads, dates and SHA-256 digests. Record
the failed first lint/format gate and successful final gate separately. Update the
maturity matrix for current Docker availability without claiming reproducibility.

Validation
Final FAST: 13/13 gates passed; 466 tests passed and 11 skipped inside these suites.
Critical E2E: 11 passed. Nine contract schemas and five canonical imports passed.
Tracked-plus-untracked secret-pattern scan passed; no staged files or remotes.
Pyright: 75 errors, 0 warnings, 97 files analyzed; release remains blocked.

Limitations
No semantic version, tag, remote CI run, cloud deployment or new live evaluation.
R2 remains partial. Isolated Docker reproduction and type remediation remain open.
This evidence commit depends on both preceding commits and is not release approval.
```

## 15. AI-ENV INITIAL COMMIT READINESS

**INITIAL_COMMIT_READY para la selección acotada** documentada en
`docs/BASELINE-COMMIT-PLAN-20260921.md` del repositorio exterior
(abrir desde ai-env). No significa que todo untracked
deba incluirse. Se excluyen `.intelligence/*` heredados (manifest desactualizado
sin git-ai-env/codebase) y `_probe.mjs` (solo comentario «deleted»).
No se promueve ni elimina ese material. La selección inicial incluye configuración
actual, tooling, lockfile, instrucciones y documentación del entorno.
Tests: Codex 8+6, workspace 4, Node scopes 1 PASS. pnpm frozen/offline lockfile-only
PASS para dos proyectos; no acredita instalación limpia. Context7 deshabilitado
con placeholder documentado, no credencial real. Paths absolutos de MCP son
dependencias locales documentadas. Aplicación excluida, staging vacío.

## 16. DOCKER REPRODUCIBILITY GAPS

No se ejecutó reproducción aislada. Compose tiene container_name fijos, puertos
host y volúmenes con `name` global: un simple `-p` no aísla todo. MSSQL, Service
Bus y Cosmos usan tags mutables; Redis/App Configuration están fijados por digest.
Dependencias: contraseñas locales, disco/RAM, Python 3.14, datos bootstrap,
config Service Bus, Foundry host y modelo ya descargado; verificar arquitectura.

Ejercicio futuro concreto:
1. Preparar configuración temporal que quite/reemplace TODOS los container_name,
   nombres globales de volúmenes y puertos host; asignar proyecto único y red privada.
2. Resolver imágenes por digest, guardar manifiesto y validar config sin imprimir secretos.
3. Build/pull, startup y espera acotada de health checks; capturar exit codes/logs redactados.
4. Crear schema/seed sintético e índices vectoriales en volúmenes nuevos; comprobar recuentos.
5. Ejecutar integración y journeys con URLs/credenciales del proyecto aislado.
6. Guardar evidencia y borrar solo recursos etiquetados del proyecto temporal;
   verificar nombres/labels antes de teardown. Nunca prune global ni volúmenes actuales.

## 17. REMOTE CI READINESS

Existe `.github/workflows/ci.yml` para GitHub Actions; sin remotos no hay proveedor
autoritativo ni ejecución acreditada. El workflow invoca `ai/agent/tests` completo,
incluyendo infra, sin preparar todos sus servicios; lint/tools usan installs no
totalmente fijados y pip-audit del job no representa necesariamente dependencias
de todos los paquetes. El job de secretos solo inspecciona tracked.
Antes de habilitar: elegir proveedor/URL por repo, fijar herramientas, separar
FAST/E2E de infra, instalar dependencias coherentes, añadir artefactos y tests del
ai-env. Gates estáticos, esquemas, doc-index y suites in-memory no requieren nube.
Redis/pgvector/emuladores necesitan Docker configurado; Foundry necesita runner
local adecuado y debe ser opt-in separado. Credenciales se inyectan desde el
almacén del runner; ningún secreto Azure es necesario para FAST local.

## 18. NEXT APPLICATION MILESTONE

**BLOCKED_BY_BASELINE_DEFECT**. Siguiente trabajo concreto: remediar los 75
diagnósticos con cambios revisables por componente y pruebas de comportamiento,
sin `Any`/supresiones masivas. Después verificar de nuevo readiness y cerrar
las lagunas R2 identificadas; no iniciar Phase2.3 automáticamente.

## 19. REMAINING RISKS

- 75 errores Pyright; FAST no incluye ese análisis y no basta para release.
- R2: UTPR no mide solo propuestas; `get_*` es heurística del oráculo de tools;
  número de aprobaciones no empareja escrituras individualmente; OTHER amplia tools.
- Detector de IDs no equivale a detector de toda fuga financiera; ejemplos benignos
  pueden rechazarse. No relajar el control sin aceptación específica.
- Live anterior al fix; muestras pequeñas; no superioridad estadística demostrada.
- 11 skips Redis, infra completa no ejecutada, warnings SVD, CI no probado.
- Runtime/dependencias locales, tags Docker mutables y nombres globales impiden
  afirmar reproducción en otra máquina. Outer aún sin primer commit/remotos.

## 20. EXACT USER DECISIONS REQUIRED

1. Revisar títulos, cuerpos y selección de los tres commits de aplicación y el
   commit inicial ai-env; autorización posterior requerida para ejecutarlos.
2. Confirmar si desea commits de estabilización aun con release bloqueada, o
   esperar la remediación de tipos. Ninguna opción autoriza una release/tag.
3. Elegir remotos/proveedor solo cuando corresponda habilitar CI; no es necesario
   para conservar el trabajo local. Phase2.3/Azure siguen fuera de alcance.

La pausa antes de commits procede del documento aportado por el usuario:
“Do NOT actually commit unless the user explicitly authorizes it after reviewing
this report.” No es una aprobación añadida por una skill.
