# AegisBank Application — Instrucciones para Claude Code

Repositorio de la aplicación bancaria educativa de AegisBank (monolito modular en Python).
Este repositorio es independiente del entorno exterior `ai-env`.

## Contratos compartidos y lectura obligatoria

1. [AGENTS.md](AGENTS.md): Reglas permanentes del banco (datos sintéticos, HITL obligatorio, modular monolith, política de commits).
2. [README.LLM.md](README.LLM.md): Guía de contexto, resolución de rutas relativas y catálogo de fuentes.
3. [docs/architecture/CANONICAL-COMPONENTS.md](docs/architecture/CANONICAL-COMPONENTS.md): Catálogo canónico antes de crear implementaciones paralelas.
4. [docs/architecture/E2E-FINAL-ARCHITECTURE.md](docs/architecture/E2E-FINAL-ARCHITECTURE.md): Flujo E2E de lectura y escritura.

## Reglas de modificación y bloqueo

- Antes de modificar cualquier archivo, adquiere el bloqueo de sesión:
  `python -B scripts/session_guard.py acquire --session-id <ID> --milestone <M> --allowed-paths "<P>"`
- Verifica el bloqueo con:
  `python -B scripts/session_guard.py check --session-id <ID>`
- Libera al terminar:
  `python -B scripts/session_guard.py release --session-id <ID>`

## Comandos de verificación y pruebas

- Entorno virtual local: `.venv\Scripts\python.exe`
- Pruebas y validación documental:
  - `python -B scripts/documentation_index.py --check`
  - `python -B scripts/test_documentation_index.py`
  - `.\.venv\Scripts\python.exe -m pytest`
  - `git diff --check`

## Reglas permanentes (Non-negotiables)

- **Datos sintéticos exclusivamente**: Prohibido datos reales, personales o bancarios.
- **HITL estricto**: Toda escritura o solicitud de servicio requiere confirmación humana.
- **No duplicar contratos**: Las reglas viven únicamente en `AGENTS.md`.
- **Archivos generados**: No editar manualmente `project-index.json`, `llms.txt`, `llms-full.txt` ni `docs/DIRECTORY-MAP.md`; regenerar con `python -B scripts/documentation_index.py --write`.
- **Append-only ADRs**: Los ADRs aceptados no se modifican ni eliminan; las sustituciones se hacen con un nuevo ADR.
