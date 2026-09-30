# Navegación y entendimiento — 2026-09-22

## Alcance y resultado

Se revisaron las rutas no ignoradas de ambos Git, con inventario por directorio.
Se completaron guías de entrada donde faltaba una responsabilidad propia. Los
subdirectorios restantes se explican en DIRECTORY-MAP.md y heredan la guía de su
componente. Esto es cobertura de navegación, no una nueva auditoría exhaustiva
de cada línea de negocio ni una garantía de comprensión de todos los modelos.

## Qué leer

- README.md: propósito, estado y primeros pasos.
- README.LLM.md: fuentes, límites de autoridad y selección de contexto.
- llms.txt: mapa breve; llms-full.txt: guías seleccionadas con procedencia.
- project-index.json: rutas máquina; docs/DIRECTORY-MAP.md: ubicación por ubicación.
- docs/navigation.json: fuentes del paquete ampliado y áreas de responsabilidad.
- docs/START-HERE.md: explicación inicial y rutas por tarea.
- docs/engineering/DOCUMENTATION-SYSTEM.md: reglas de evolución e investigación aplicada.

No se concatenaron código, datasets, secretos ni todos los informes históricos.
Los archivos llms son una convención local; no obligan a un cliente a cargarlos.
El generador no sigue fuentes que escapen del repositorio y excluye datos privados.
Los enlaces del texto ampliado se interpretan desde la fuente rotulada.

## Iteraciones del loop

1. Inventario: dos Git, carpetas, README existentes y fuentes de evidencia;
   consulta del grafo y de convenciones públicas (llms.txt, Diátaxis, Write the Docs, Git).
2. Implementación: guías por responsabilidad, contexto explícito, índices propios
   por Git, pruebas de curation/aislamiento, corrección de la contradicción RAG.
3. Convergencia: corregir formato y CRLF, preservar el índice ADR original,
   regenerar dos veces sin diferencias, comprobar enlaces y exclusiones.

La skill loop se adaptó a esta sesión: no se lanzó un segundo escritor OpenCode
ni se cambió el modelo. No se amplió a nuevas funcionalidades bancarias.

## Validaciones ejecutadas

Desde aplicación:

```powershell
python -B scripts/documentation_index.py --write
python -B scripts/documentation_index.py --check
python -B scripts/test_documentation_index.py
.venv/Scripts/python.exe -B scripts/quality_gate.py --fast
.venv/Scripts/python.exe -m pytest -q ai/agent/tests/e2e
git diff --check
```

Generador: 9 pruebas PASS. FAST del 2026-09-22: 13 gates PASS, 0 gates SKIP;
sus suites suman 466 PASS y 11 SKIP por Redis ausente. E2E: 11 PASS en 2.18s.
El gate se ejecutó con SessionGuard y AEGISBANK_SESSION_ID. El primer intento
detectó formato/finales de línea; se corrigieron y se repitió el gate completo.
El reporte previo se preservó en coordinación local antes de sobrescribir reports/.
No se reejecutó Pyright: los 75 errores del 2026-09-21 siguen siendo deuda pendiente.

Desde ai-env: `python -B -m unittest discover -s .ai-env -p 'test_*.py'`
(6 PASS), tests de .codex (14 PASS), Node scopes (1 PASS),
`python -B .ai-env/build_docs.py --check` y `python -B .ai-env/check_workspace.py`
PASS. Ruff de los scripts modificados PASS. pnpm frozen/offline lockfile-only
PASS; no es una instalación en máquina limpia. Los dos git diff --check PASS.

## Exclusiones y conservación

Aplicación: entornos .venv*, .smoke, .codebase-memory y mlruns quedan ignorados;
se mantienen fixtures, contratos, ejemplos redactados y lockfiles. Los informes
históricos ya tracked se preservan: gitignore no los retira ni es control de acceso.
Ai-env: aplicación anidada excluida; metadatos .intelligence heredados y no
verificados permanecen locales, junto al probe vacío. Su README explica el límite.

## Commits y continuidad

La petición del 2026-09-22 solicita generar commits y cuerpos completos después
del informe anterior. El plan actual es NAVIGATION-COMMIT-PLAN-20260922.json;
reemplaza las selecciones preparadas el 2026-09-21, que se conservan como snapshots.
Separa defensas previamente pendientes, documentación de aplicación y Git ai-env.
Los SHA ejecutados se obtienen de git log; el plan no afirma por sí solo ejecución.
No hay nueva release/tag, push, remoto ni despliegue. R2 permanece parcial y el
bloqueo de tipos continúa. Toda futura modificación de estructura debe actualizar
guía propietaria, manifiesto e índices en el mismo cambio.
