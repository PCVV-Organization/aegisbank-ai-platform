# 016 — AegisBank v0.10.1 Architecture Integrity + Cross-Session Coordination

Continúa exclusivamente v0.10.1 — Architecture Integrity + Cross-Session Coordination.

Proyecto:
C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform

NO iniciar v0.11.

## Teaching Contract
Lee primero docs/learning/TEACHING-CONTRACT.md.

Explica desde cero y documenta: DRY (Don't Repeat Yourself), code duplication, code smell, technical debt, refactoring, cohesion, coupling, canonical component, single-writer principle, concurrency, race condition, ownership, lease/lock, HEAD, working tree, staging/index, CI concurrency y CODEOWNERS.

Para cada concepto: significado, traducción, cómo funciona, problema que resuelve, riesgo, ejemplo AegisBank, relación con Mibanco y AI-103/AI-200.

Guarda este prompt como docs/chatgpt-prompts/016_PROMPT.md.

## 0. Reconciliar Git antes de escribir
Existe una inconsistencia que debe resolverse en READ-ONLY:
cierre A: d5c33a7 feat(v0.10): establish quality engineering and DevSecOps gates
cierre B: f97253e feat(v0.10): establish quality engineering and DevSecOps gates

Ejecuta:
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
git log -5 --oneline
git show --stat --oneline d5c33a7
git show --stat --oneline f97253e
git merge-base --is-ancestor d5c33a7 f97253e
git merge-base --is-ancestor f97253e d5c33a7
git diff --name-status d5c33a7 f97253e

No reset, rebase, amend ni reescritura de historia.
Define CANONICAL_V010_HEAD=<HEAD real validado>.

Si working tree no está limpio:
AEGISBANK_V0.10_1_DIRTY_BASELINE
y STOP.

## 1. Single Writer, Many Readers
No usamos worktrees. Por tanto, un solo chatbot/sesión puede escribir en el working tree a la vez.

Implementa scripts/session_guard.py.

Estado NO versionado:
.coordination/active-writer.json

Añade .coordination/ a .gitignore.

Adquisición mediante creación atómica, nunca overwrite. Guardar:
- session_id;
- PID;
- timestamp UTC;
- baseline HEAD;
- milestone;
- allowed_paths.

Si ya existe writer:
AEGISBANK_CROSS_SESSION_WRITER_ACTIVE
y STOP.

No auto-force-unlock. No borrar locks ajenos.

Comandos:
- session_guard acquire
- session_guard check
- session_guard release

check debe bloquear si:
- HEAD cambió;
- aparece un path modificado fuera de allowed_paths;
- existe staging inesperado.

Estados:
- AEGISBANK_CROSS_SESSION_HEAD_MOVED
- AEGISBANK_CROSS_SESSION_PATH_COLLISION

## 2. Ownership Map
Crear docs/engineering/OWNERSHIP-MAP.md.

Definir responsabilidades por componente:
Core Banking, RAG, Agent, MCP/HITL, Reliability, Observability, Quality/CI.

No crear .github/CODEOWNERS con usuarios inventados. Documentar que se añadirá cuando exista owner/team GitHub confirmado.

## 3. Canonical Components
Crear docs/architecture/CANONICAL-COMPONENTS.md.

Inventariar como mínimo:
- AgentOrchestrator
- ToolRegistry
- Banking routing policy
- RAG retriever
- LLM provider / Foundry Local adapter
- HITL manager
- MCP boundary/server
- IdempotencyGuard
- RetryPolicy
- CircuitBreaker
- timeout abstraction
- Transactional Outbox
- MessageBus / consumer / DLQ
- OpenTelemetry tracing
- structured logging
- metrics
- audit
- HOTL supervisor
- quality gate

Por responsabilidad indicar:
canonical path, public interface, consumers, extension point y DO NOT DUPLICATE.

## 4. Discover Before Create
Antes de crear cualquier módulo/clase/helper futuro:
1. buscar símbolos y términos equivalentes con rg;
2. consultar CANONICAL-COMPONENTS.md;
3. revisar imports/callers;
4. clasificar:
   - REUSE
   - EXTEND
   - NEW_COMPONENT_JUSTIFIED
si es nuevo, justificar por qué la responsabilidad es distinta y cómo se evita solapamiento.

No crear una segunda implementación para la misma responsabilidad por comodidad.

## 5. Duplicate-Code Audit
Ruff no sustituye un detector de copy/paste.

Usar Pylint 4.x si funciona correctamente con Python 3.14 y ejecutar únicamente duplicate-code / R0801 sobre:
- ai/agent/src
- ai/rag/src
- ml/intent-classifier/src
- services/mock-core-banking/src

Primero crear baseline. Clasificar findings:
- TRUE_DUPLICATION
- INTENTIONAL_SCHEMA_SIMILARITY
- TEST_FIXTURE_SIMILARITY
- FALSE_POSITIVE

Refactorizar solo TRUE_DUPLICATION si existe una abstracción clara y no aumenta coupling.
No crear god helpers ni abstracciones prematuras para satisfacer el detector.

## 6. Architecture Drift Audit
Buscar responsabilidades superpuestas, especialmente:
- múltiples registries;
- múltiples rutas de tool execution;
- más de una idempotency implementation;
- retries/circuit breakers duplicados;
- MCP boundary vs direct tool boundary;
- routing policy vs orchestrator;
- múltiples logging/audit pipelines equivalentes.

Crear:
docs/architecture/ARCHITECTURE-INTEGRITY-REPORT.md

Tabla:
responsibility | canonical implementation | suspected duplicate | decision | action | evidence.

## 7. Cross-Session Tests
Probar:
- primer writer adquiere lock;
- segundo writer queda bloqueado;
- path fuera de allowlist queda bloqueado;
- HEAD cambiado queda bloqueado;
- staging inesperado queda bloqueado;
- mismo session_id libera;
- otro session_id no libera;
- lock stale nunca se borra automáticamente.

## 8. CI Concurrency
Revisar .github/workflows/ci.yml.

Configurar concurrency para evitar workflows obsoletos/solapados del mismo workflow/ref si aún no existe.

Documentar:
GitHub Actions concurrency != local AI session coordination
CI concurrency protege runners; session_guard protege el working tree local.
No afirmar CI ejecutado mientras siga RUNNER-PENDING.

## 9. Quality Gate
Integrar en scripts/quality_gate.py:
- session guard tests;
- architecture inventory check;
- duplicate-code baseline/report;
- existing Ruff/tests/contracts/E2E/SAST/SCA/secrets.

No usar thresholds arbitrarios para duplicación.

## 10. Teaching Contract permanente
Actualizar:
- docs/learning/TEACHING-CONTRACT.md
- docs/learning/GLOSSARY.md
- docs/learning/MASTERS-NOTES.md
- docs/requirements/COVERAGE-MATRIX.md

Añadir reglas permanentes:
- DISCOVER BEFORE CREATE
- ONE WRITER, MANY READERS

Todo futuro prompt debe adquirir/checkear session guard antes de escribir/stagear/commitear y declarar allowed_paths.

## 11. Validación
Ejecutar:
- tests v0.10.1
- suite completa
- contracts
- E2E
- quality gate
- Ruff
- format
- compileall
- Bandit
- pip-audit
- secret scan
- duplicate-code audit
- git diff --check

## 12. Git
PROHIBIDO:
- worktrees
- git add .
- git add -A
- reset
- rebase
- amend
- push

Antes de staging:
session_guard check
git rev-parse HEAD
git status --porcelain=v2
git diff --name-status

Stagear solo paths legítimos v0.10.1.
Antes del commit repetir session_guard check.

Si todo pasa crear:
chore(v0.10): enforce architecture integrity and cross-session coordination

Liberar el session guard después del commit.
