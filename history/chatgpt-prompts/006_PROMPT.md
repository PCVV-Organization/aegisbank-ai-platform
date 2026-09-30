# 005 — Continuar v0.5 con Foundry Local

Continúa exclusivamente `v0.5.0 — Grounded Generation & LLM Evaluation`.

Proyecto:

`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Cambio autorizado: usar **Microsoft Foundry Local** en vez de Azure/Foundry cloud.

NO usar Azure CLI, Azure, Docker, Agent, MCP, HITL ni iniciar v0.6.

Primero verifica Git y preserva todo el trabajo v0.5 existente.

Detecta Foundry Local mediante:

* `foundry --version`
* `foundry server status`
* endpoint local
* modelos disponibles/cached

Modelo preferido:

`phi-4-mini`

Usa el modelo realmente disponible/cargado y registra alias + model ID no secreto.

Implementa únicamente el adapter local necesario detrás de `LLMProvider`.

Prioridad:

1. OpenAI SDK contra el endpoint local `/v1`;
2. usar Responses API si Foundry Local 0.10.3 realmente la soporta;
3. si no está soportada, usar `/v1/chat/completions` y adaptar internamente el resultado al contrato existente de `LLMProvider`.

No hardcodear el puerto si puede obtenerse de `foundry server status`/configuración.

No usar API keys reales. Foundry Local no requiere autenticación cloud.

Antes del held-out:

1. prueba una sola llamada smoke local;
2. valida structured/parsing/citations;
3. confirma que no existe tráfico externo.

Si el smoke pasa, ejecuta exactamente UNA VEZ los 6 casos held-out.

NO modificar `rag-answer-v001`, corpus, retrieval, dataset ni parámetros después de observar held-out.

Registrar:

* provider = `foundry-local`;
* Foundry Local version;
* model alias;
* model ID;
* prompt version;
* groundedness;
* answer relevance;
* completeness;
* citation validity;
* citation coverage;
* abstention correctness;
* unsupported-claim rate.

Ejecuta después:

* v0.5 tests;
* v0.4 = 36/36;
* v0.3 = 17/17;
* v0.2 = 55/55;
* Ruff;
* format;
* compileall;
* secret check;
* `git diff --check`.

Stagea solo archivos legítimos v0.5.

NO usar:

`git add .`
`git add -A`

Si todo pasa crea:

`feat(v0.5): establish grounded generation and LLM evaluation`

No push.

Finaliza con:

`AEGISBANK_V0.5_GROUNDED_GENERATION_READY`

y STOP.

NO iniciar v0.6.
