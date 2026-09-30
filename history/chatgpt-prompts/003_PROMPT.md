# AegisBank — v0.5 Grounded Generation & Evaluation

Continúa exclusivamente:

`v0.5.0 — Grounded Generation & LLM Evaluation`

Proyecto:

`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline esperado:

`HEAD = 1e92a62`

Reglas:

* workspace único: carpeta del proyecto;
* NO worktrees;
* NO Agent;
* NO MCP;
* NO HITL;
* NO tools;
* NO Docker/Kubernetes;
* NO crear recursos Azure ni generar costos;
* NO modificar/tunear retrospectivamente el corpus o métricas de v0.4;
* NO iniciar v0.6.

Primero verifica:

```powershell
Set-Location 'C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform'
git branch --show-current
git rev-parse HEAD
git status --short
```

Debe ser `master`, HEAD `1e92a62...` y working tree limpio. Si no, STOP.

## Objetivo

Construir sobre `ai/rag/` una capa RAG de generación:

`query → retrieval v0.4 → context builder → LLM → grounded answer + citations`

Implementar:

1. interfaz `LLMProvider` desacoplada del proveedor;
2. context builder determinista que conserve `document_id`, `version`, `chunk_id` y `source`;
3. prompt versionado;
4. contrato estructurado de respuesta;
5. citations únicamente hacia chunks realmente recuperados;
6. abstención cuando no exista evidencia suficiente;
7. protección contra instrucciones encontradas dentro de los documentos recuperados;
8. dataset de evaluación separado del utilizado para desarrollar prompts.

Respuesta conceptual:

```json
{
  "answer": "...",
  "citations": ["chunk-id"],
  "abstained": false
}
```

No permitir citations inventadas.

## Provider

No crees infraestructura ni cuentas.

Si no existe un proveedor LLM ya autorizado/configurado mediante variables de entorno, implementa la interfaz, tests deterministas y harness de evaluación, pero STOP antes de declarar el milestone COMPLETE y reporta:

`AEGISBANK_V0.5_LIVE_LLM_REQUIRED`

No hardcodear API keys.

## Evaluación

Separar claramente:

`retrieval quality` — ya medida en v0.4

de:

`generation quality` — nueva en v0.5.

Evaluar como mínimo:

* groundedness;
* answer relevance;
* completeness cuando exista ground truth;
* citation validity;
* citation coverage;
* abstention correctness;
* unsupported-claim rate.

Incluir casos:

* respuesta directamente soportada;
* múltiples chunks;
* versión obsoleta vs vigente;
* evidencia insuficiente;
* pregunta fuera de dominio;
* contexto con instrucciones maliciosas/sospechosas.

No establecer thresholds productivos arbitrarios antes de obtener baseline.

## Prompting

Versionar prompts, por ejemplo:

`rag-answer-v001`

No almacenar prompts dispersos dentro del código.

Registrar:

* propósito;
* formato;
* reglas de evidencia;
* regla de abstención;
* restricciones;
* versión.

## ADR

Detecta el mayor ADR existente y usa los siguientes números libres para documentar, si realmente son decisiones nuevas:

* provider-agnostic LLM boundary;
* grounded generation with citation validation.

No duplicar IDs existentes.

## Tests

Añadir tests para:

* context construction;
* provenance;
* citations válidas;
* citation inventada rechazada;
* abstention;
* structured output;
* prompt version;
* provider boundary;
* evaluación reproducible donde corresponda.

Ejecutar además regresiones:

`v0.2 = 55/55`
`v0.3 = 17/17`
`v0.4 = 36/36`

y:

`ruff check`
`ruff format --check`
`compileall`
`git diff --check`
`secret check`

## Git

Antes del staging comprueba nuevamente que HEAD no cambió.

NO usar:

`git add .`
`git add -A`
`git push`

Stagea exclusivamente artefactos legítimos de v0.5.

Revisa:

```powershell
git diff --cached --name-only
git diff --cached
```

Si existe un LLM autorizado, las evaluaciones reales fueron ejecutadas y todos los gates pasan, crea:

`feat(v0.5): establish grounded generation and LLM evaluation`

No push.

Entrega:

* provider/model utilizado;
* prompt version;
* dataset/casos evaluados;
* métricas de generación;
* abstention results;
* citation results;
* tests v0.5;
* regresiones v0.2/v0.3/v0.4;
* ADRs;
* commit;
* git status.

Finaliza con:

`AEGISBANK_V0.5_GROUNDED_GENERATION_READY`

o, si falta acceso a un modelo real:

`AEGISBANK_V0.5_LIVE_LLM_REQUIRED`

y STOP.

NO iniciar v0.6.
