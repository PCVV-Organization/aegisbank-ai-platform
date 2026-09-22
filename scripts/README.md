# Comandos de mantenimiento y evaluación

Ejecutar desde la raíz Git de aplicación. Para pruebas y runtime usar su `.venv`;
el Python global no tiene necesariamente los paquetes instalados.

| Comando | Qué comprueba | Efectos / requisitos |
| --- | --- | --- |
| `python -B scripts/documentation_index.py --check` | Navegación, rutas y archivos generados | Solo lectura; Python estándar y Git |
| `python -B scripts/documentation_index.py --write` | Regenera índices y contexto LLM | Escribe cuatro archivos declarados; adquirir SessionGuard |
| `python -B scripts/test_documentation_index.py` | Pruebas del generador | Directorios temporales aislados |
| `python -B scripts/session_guard.py --help` | Contrato de coordinación | acquire/release modifican lock; check inspecciona |
| `.venv/Scripts/python.exe scripts/quality_gate.py --fast` | Ruff, compilación, suites, evaluación, inventario y secretos | Requiere SessionGuard y AEGISBANK_SESSION_ID; escribe reports/ y artefactos |
| `.venv/Scripts/python.exe scripts/evaluation_gate.py` | Comparación de trazas simuladas y promoción bajo política | Escribe informes/MLflow; no es una evaluación live |
| `run_local_red_team.py`, `run_phase22_live.py` | Evaluación opt-in con modelo local | Preservar informes antes; Foundry y para Phase2.2 pgvector |
| `container_acceptance.py`, `functions_runtime_acceptance.py`, `appconfig_emulator_acceptance.py` | Aceptación de infraestructura | Servicios locales; revisar configuración y efectos antes de ejecutar |
| `evaluate_retrievers_v012.py`, `capture_pgvector_query_plans.py` | Recuperación y planes SQL | Revisar pgvector y destinos de evidencia |
| `generate_sbom.py`, `performance_baseline.py` | Inventario de dependencias o mediciones | Generan artefactos; no pruebas universales de seguridad/rendimiento |

No ejecutar todos los scripts por defecto: algunos escriben informes, crean datos
o requieren servicios. Leer su ayuda/código y el alcance del hito. La
[estrategia](../docs/quality/TEST-STRATEGY.md) decide qué suites corresponden.
