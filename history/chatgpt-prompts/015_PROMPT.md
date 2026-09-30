# 015 — AegisBank v0.10 Quality Engineering + CI/CD + DevSecOps

Continúa exclusivamente:
v0.10.0 — Quality Engineering + CI/CD + DevSecOps

Proyecto:
C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform

Baseline esperado:
branch: master
HEAD: 74301e9
working tree limpio

## TEACHING CONTRACT — obligatorio
Trabaja como Principal AI Engineer y como profesor de una Maestría en Inteligencia Artificial para un alumno que empieza desde cero.

Antes de implementar cada concepto nuevo y en el informe final explica SIEMPRE:
- nombre completo y sigla;
- traducción al español;
- qué significa;
- qué problema resuelve;
- cómo funciona internamente;
- por qué AegisBank lo necesita;
- ejemplo concreto del repositorio;
- alternativa principal y cuándo NO usarlo;
- errores/riesgos típicos;
- relación con el puesto Mibanco;
- relación con Microsoft AI-103 o AI-200;
- nivel de cobertura: LAB-COVERED, CI-CONFIGURED, CLOUD-PENDING o PROD-PARTIAL.

Crear/actualizar:
- docs/learning/TEACHING-CONTRACT.md
- docs/learning/GLOSSARY.md
- docs/learning/MASTERS-NOTES.md
- docs/requirements/COVERAGE-MATRIX.md

Cada futuro prompt y cada informe de OpenCode debe leer/respetar TEACHING-CONTRACT.md.

Guardar este prompt como:
docs/chatgpt-prompts/015_PROMPT.md

## Restricciones
- NO worktrees.
- NO Azure cloud.
- NO Docker/Kubernetes todavía.
- NO push.
- NO v0.11.
- NO cambiar phi-4-mini.
- NO modificar datasets/held-outs/métricas históricas.
- NO nuevas operaciones WRITE.
- Preservar v0.9.2 y todo comportamiento existente.
- Stage explícito solamente.
- PROHIBIDO git add . y git add -A.

## Objetivo
Convertir los tests y controles manuales acumulados en una estrategia de calidad reproducible y automatizable:
code change -> static checks -> unit -> integration -> contract -> E2E -> security -> quality gate

Preparar CI con GitHub Actions, pero NO hacer push. La ejecución real en GitHub queda CI-CONFIGURED / RUNNER-PENDING hasta que exista una ejecución remota verificable.

## 1. Test Strategy
Crear: docs/quality/TEST-STRATEGY.md
Explicar desde cero:
- QA = Quality Assurance;
- test pyramid;
- unit test;
- integration test;
- contract test;
- E2E = End-to-End;
- regression test;
- acceptance test;
- flaky test;
- test debt;
- code coverage;
- quality gate.

## 2. E2E formal
Crear una suite E2E separada para los journeys bancarios críticos:
A. READ account: User -> policy routing -> get_my_loans -> answer
B. Multi-step READ: User -> get_my_loans -> get_next_installment -> answer
C. RAG knowledge available: User -> search_knowledge -> evidence -> grounded answer
D. RAG knowledge gap: User -> search_knowledge -> no evidence -> abstention
E. WRITE REJECT: User -> Agent -> MCP -> HITL REJECT -> 0 side effects
F. WRITE APPROVE: User -> Agent -> MCP -> HITL APPROVE -> idempotent WRITE -> Outbox -> Consumer
G. HOTL kill-switch: WRITE proposed -> HOTL disabled -> blocked
H. Reliability: transient failure -> retry -> success; persistent failure -> circuit breaker; poison event -> DLQ.

## 3. Contract Testing
Definir contratos explícitos y versionados para:
- Core Banking OpenAPI;
- MCP tool registry/schemas;
- Agent -> Core Banking read/write adapter;
- Outbox event ServiceRequestCreated.

## 4. API Testing
Crear colección reproducible de API tests para Core Banking (docs/quality/core-banking-api-tests.json).

## 5. Code Coverage
Medir cobertura y definir baseline justificado.

## 6. SAST (Static Application Security Testing)
Ejecutar Bandit sobre código fuente propio y clasificar findings.

## 7. SCA (Software Composition Analysis) + Dependency Audit
Ejecutar pip-audit para revisar dependencias.

## 8. SBOM (Software Bill of Materials)
Generar SBOM CycloneDX JSON en docs/security/sbom.json.

## 9. Secret Scanning
Formalizar escaneo de secretos como quality gate.

## 10. GitHub Actions CI
Crear .github/workflows/ci.yml marcado como CI-CONFIGURED / RUNNER-PENDING.

## 11. CD (Continuous Delivery vs Deployment)
Documentar la distinción y preparar la base.

## 12. DevSecOps
Crear docs/security/DEVSECOPS-GATES.md explicando Shift-Left Security.

## 13. Quality Gate Script
Crear scripts/quality_gate.py como entrypoint local unificado con exit code 0/!=0 y reporte JSON.

## 14. Flaky Test Discipline
Documentar y verificar estabilidad de tests críticos.

## 15. Regression del bug v0.9.2
Consolidar tests permanentes de regresión para routing y abstención.

## 16. ADRs
ADR-022, ADR-023, ADR-024.

## 17. Validación Final
Ejecutar todos los gates, tests, linters y verificaciones.

## 18. Git
HEAD = 74301e9.
Commit: feat(v0.10): establish quality engineering and DevSecOps gates.
No push.
Finalizar con AEGISBANK_V0.10_QUALITY_DEVSECOPS_READY.
