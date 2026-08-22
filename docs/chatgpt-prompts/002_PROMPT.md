AUTORIZACIÓN EXPLÍCITA PARA CONTINUAR v0.2

Procede con el cierre y commit de v0.2.0 usando una excepción controlada únicamente para el gate global `ruff format --check .`.

La causa ya está identificada: el comando global falla exclusivamente por dos archivos concurrentes/preexistentes bajo `docs/research/` que están fuera del alcance y ownership de v0.2.

NO debes:
- modificar esos archivos;
- formatearlos;
- eliminarlos;
- incluirlos en staging;
- añadir `docs/research/` a `.gitignore`;
- modificar configuración Ruff raíz para ocultarlos;
- usar `--exclude` o `extend-exclude` como forma de hacer pasar artificialmente el gate;
- modificar otros artefactos concurrentes.

Para v0.2 queda autorizado reemplazar exclusivamente este gate:

`ruff format --check .`

por una comprobación scoped del código propiedad de v0.2 utilizando la capacidad oficial de Ruff para validar paths/directorios específicos, por ejemplo:

`.venv\Scripts\python.exe -m ruff format --check services/mock-core-banking`

o la forma equivalente correcta según el entorno actual.

Esta autorización NO elimina las demás validaciones.

Antes del staging debes repetir sobre el estado ACTUAL todas las comprobaciones relevantes posteriores a los últimos cambios:

1. pytest completo de v0.2
2. ruff check
3. ruff format --check sobre el scope v0.2
4. compileall sobre el source de v0.2
5. git diff --check
6. secret sanity check
7. validación OpenAPI
8. smoke tests
9. git status
10. revisión completa del diff

Confirma además que `httpx2` permanece instalado/configurado según el estado actualmente validado y NO reviertas esa decisión: Starlette actual utiliza `httpx2` como backend de TestClient.

Si cualquiera de las validaciones propias de v0.2 falla, corrige el problema y vuelve a ejecutar los gates.

Si todas pasan, procede al staging EXPLÍCITO.

Está prohibido:

`git add .`
`git add -A`

Agrega solamente los cambios legítimos de v0.2 correspondientes a:

`.gitignore`
`README.md`
`docs/architecture/adr/`
`services/mock-core-banking/`

Antes del commit ejecuta:

`git diff --cached --name-only`
`git diff --cached --stat`
`git diff --cached`

Verifica que NO aparezca ninguno de estos artefactos concurrentes:

`.ai-env/`
`.intelligence/`
`.opencode/`
`contracts/`
`docs/chatgpt-prompts/`
`docs/research/`
`opencode.json`
`opencode.json.tui-migration.bak`
`tui.json`

Si aparece cualquiera de ellos en staging:

STOP.

No elimines el archivo del filesystem; únicamente evita que forme parte del staged set.

Si el staged set contiene exclusivamente v0.2 y todos los gates propios del milestone pasan, crea el commit local:

`feat(v0.2): implement local core banking mock`

No hagas push.

Después ejecuta:

`git log -1 --oneline`
`git show --stat --oneline HEAD`
`git status --short`

En el informe final NO afirmes que `ruff format --check .` pasó.

Debes registrar transparentemente:

ROOT_RUFF_FORMAT_CHECK:
FAIL — exclusivamente archivos concurrentes fuera de v0.2

V0.2_RUFF_FORMAT_CHECK:
PASS

VALIDATION_EXCEPTION:
AUTHORIZED — root-wide formatting gate sustituido únicamente para v0.2 por scoped formatting validation debido a archivos concurrentes fuera del ownership del milestone.

Esto NO debe contarse como deuda funcional de Core Banking Mock, sino como estado concurrente del workspace que deberá resolverse separadamente por su propietario/origen.

El milestone podrá declararse COMPLETE únicamente si todas las validaciones propias de v0.2 pasan y el commit contiene exclusivamente artefactos de v0.2.

El informe final debe incluir:

Milestone:
v0.2.0 - Core Banking Mock

Estado:

PROJECT_PATH:
CURRENT_BRANCH:
START_COMMIT:
FINAL_COMMIT:
COMMIT_MESSAGE:

Tests:
TOTAL:
PASSED:
FAILED:

Validaciones:
- pytest
- ruff check
- scoped ruff format
- compileall
- git diff --check
- secret check
- OpenAPI
- smoke

Validation exception:
- root ruff format check
- causa exacta
- archivos externos afectados
- confirmación de que no fueron modificados

Staged files:
...

Concurrent artifacts preserved:
...

Git status final:
...

No iniciado:
- v0.3
- ML
- RAG
- Agent
- MCP
- HITL
- idempotency
- retry
- circuit breaker
- messaging
- Docker
- Azure

Si todo queda correctamente completado termina con:

AEGISBANK_V0.2_CORE_BANKING_MOCK_READY

Luego STOP.

NO inicies v0.3.