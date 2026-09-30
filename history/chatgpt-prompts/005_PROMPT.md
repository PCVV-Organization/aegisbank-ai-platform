# 005 — AegisBank v0.5 Live LLM Evaluation

Continúa exclusivamente:

`v0.5.0 — Grounded Generation & LLM Evaluation`

Proyecto único:

`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Usa el **orchestrator** y las skills disponibles que sean relevantes. No instales nuevas skills ni amplíes el alcance.

## 1. Preflight Git

Primero:

```powershell
Set-Location 'C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform'
git branch --show-current
git rev-parse HEAD
git status --short
git diff
```

Baseline esperado:

`master`
`HEAD = 1e92a6223bc5a96890f8b0d7ca5be43cb7e35bc2`

Preserva íntegramente el trabajo v0.5 existente sin reconstruirlo ni descartarlo.

Si HEAD cambió o existen cambios ajenos inesperados, STOP y reporta el estado.

Guarda este prompt como:

`docs/chatgpt-prompts/005_PROMPT.md`

## 2. Restricciones absolutas

NO:

* crear recursos Azure;
* desplegar modelos;
* modificar billing/quota;
* realizar login interactivo;
* solicitar, imprimir, registrar o copiar secretos;
* usar Azure AI Inference beta SDK;
* iniciar Agent, MCP, HITL o tools;
* iniciar v0.6;
* usar worktrees;
* hacer push.

La única inferencia externa permitida es:

`1 smoke + 6 held-out`

y únicamente si usa una configuración previamente autorizada. Si pudiera generar un costo no autorizado o no puedes determinar que el deployment está autorizado para esta evaluación, STOP.

## 3. Detectar configuración Foundry

Inspecciona exclusivamente configuración local ya existente y autorizada para determinar:

* endpoint;
* deployment/model;
* autenticación.

No muestres valores secretos. Reporta solo:

`PRESENT / MISSING`
y, para información no secreta, provider/model/deployment.

No inventes nombres, endpoints, deployments ni credenciales.

Usa la integración estable:

`OpenAI/v1 + Responses API`

con el SDK estable `openai`.

NO usar:

`azure-ai-inference`

Prefiere `gpt-5-mini` únicamente si el deployment configurado realmente corresponde a ese modelo y es compatible. En caso contrario usa el deployment autorizado existente.

Si falta endpoint, deployment/model o autenticación:

`AEGISBANK_V0.5_FOUNDRY_CONFIGURATION_REQUIRED`

y STOP sin staging ni commit.

## 4. Conectar provider

Si la configuración es válida, conecta exclusivamente el `LLMProvider` provider-agnostic ya implementado.

No rediseñes la arquitectura.

Mantén:

`rag-answer-v001`

como versión congelada del prompt.

No modifiques corpus, qrels, retrieval v0.4 ni los seis casos held-out.

## 5. Smoke

Ejecuta exactamente **UNA** llamada smoke mínima usando el provider configurado.

Verifica:

* conexión;
* Responses API;
* structured response;
* parsing;
* provider/model correctos.

No registres secretos ni headers de autenticación.

Si falla, STOP sin ejecutar held-out y reporta el error sanitizado.

## 6. Held-out

Si el smoke pasa, ejecuta exactamente **UNA VEZ** los **6 casos held-out**.

Antes de hacerlo confirma que no existe evidencia de una ejecución live previa de ese held-out.

Después de observar resultados:

**NO modificar `rag-answer-v001`, retrieval, dataset, contexto, parámetros ni criterios de evaluación.**

Registrar:

* provider;
* deployment/model;
* prompt version;
* número de casos;
* groundedness;
* answer relevance;
* completeness;
* citation validity;
* citation coverage;
* abstention correctness;
* unsupported-claim rate.

No inventar thresholds productivos.

Guardar resultados y reporte reproducibles/sanitizados dentro de los artefactos legítimos de v0.5.

## 7. Validación

Ejecuta:

* v0.5 tests;
* v0.4 regression: `36/36`;
* v0.3 regression: `17/17`;
* v0.2 regression: `55/55`;
* `ruff check`;
* scoped `ruff format --check`;
* `compileall`;
* `git diff --check`;
* secret scan.

El fallo global ya conocido de formato causado exclusivamente por archivos preexistentes de `docs/research/` no autoriza modificarlos.

No ocultes failures reales propios de v0.5.

## 8. Documentación

Completa únicamente documentación v0.5 necesaria con:

* provider/model;
* `rag-answer-v001`;
* metodología;
* resultados reales;
* limitaciones;
* ausencia de thresholds productivos;
* confirmación de que corpus/retrieval v0.4 no se modificaron.

Mantén ADR-010 y ADR-011 si siguen correctos.

No renumeres ni reescribas ADR históricos.

## 9. Git

Antes del staging:

```powershell
git rev-parse HEAD
git diff
```

HEAD debe seguir en:

`1e92a6223bc5a96890f8b0d7ca5be43cb7e35bc2`

Está prohibido:

`git add .`
`git add -A`

Stagea explícitamente solo archivos legítimos de v0.5, incluido:

`docs/chatgpt-prompts/005_PROMPT.md`

Después revisa:

```powershell
git diff --cached --name-only
```

Si aparece cualquier archivo ajeno a v0.5, retíralo del staging y STOP si existe ambigüedad.

## 10. Commit

Solo si:

* configuración autorizada válida;
* smoke PASS;
* seis held-out ejecutados exactamente una vez;
* métricas registradas;
* prompt no modificado post-held-out;
* todos los tests/regresiones PASS;
* quality gates PASS;
* secret scan limpio;
* staged review limpio;

crea exactamente:

`feat(v0.5): establish grounded generation and LLM evaluation`

No push.

Verifica después:

```powershell
```

Entrega resumen con provider/model, prompt version, métricas, tests, regresiones, archivos, commit y estado Git, sin secretos.

Si todo quedó completado:

`AEGISBANK_V0.5_GROUNDED_GENERATION_READY`

y STOP.

NO iniciar v0.6.
