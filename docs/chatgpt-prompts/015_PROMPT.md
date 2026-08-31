# 015 — AegisBank v0.10 Quality Engineering + CI/CD + DevSecOps

Continúa exclusivamente `v0.10.0 — Quality Engineering + CI/CD + DevSecOps` sobre
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`, baseline `74301e9`.

## Teaching contract

Lee y respeta `docs/learning/TEACHING-CONTRACT.md`. Explica desde cero cada concepto,
sigla, alternativa, riesgo, ejemplo AegisBank, relación Mibanco, relación AI-103/AI-200
y nivel de cobertura. Mantén actualizado `docs/learning/`, `docs/quality/`,
`docs/security/` y `docs/requirements/`.

## Scope

Construye una estrategia reproducible de unit, integration, contract, E2E, regression,
acceptance y security testing. Crea `scripts/quality_gate.py`,
`.github/workflows/ci.yml`, contratos deterministas, colección de API tests, cobertura,
Bandit, pip-audit, SBOM CycloneDX y secret scanning. El gate debe fallar de forma visible;
una auditoría de dependencias sin red es `DEPENDENCY_AUDIT_BLOCKED`, nunca PASS.

La suite E2E debe proteger READ routing, multi-step loan READ, RAG available/gap, HITL
reject/approve, HOTL, retry, circuit breaker y DLQ, usando exclusivamente datos sintéticos.
Convierte también el bug v0.9.2 de `get_my_loans()` textual en regresión permanente.

No uses Azure, Docker, Kubernetes, push, nuevos WRITE, nuevos modelos, datasets
held-out ni métricas históricas. Stage explícito, nunca `git add .` ni `git add -A`.
CI queda `CI-CONFIGURED / RUNNER-PENDING`; no afirmar ejecución remota sin evidencia.

Si todos los gates pasan, crea `feat(v0.10): establish quality engineering and DevSecOps gates`.
No iniciar v0.11.
