# 008 — AegisBank v0.6 Single Agent + Read-Only Tools

Continúa exclusivamente:
`v0.6.0 — Single Agent + Read-Only Function Tools`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline esperado:
`master` HEAD = `ebeb378`

Reglas:
- NO worktrees.
- NO Azure.
- NO Docker.
- NO MCP.
- NO HITL/HOTL todavía.
- NO messaging/retry/circuit breaker/idempotencia todavía.
- NO herramientas WRITE.
- NO modificar los resultados congelados de v0.5.
- NO iniciar v0.7.
- NO push.

Guarda este prompt como:
`docs/chatgpt-prompts/008_PROMPT.md`

Primero verifica Git y working tree limpio.

## Objetivo
Construir UN único agente local capaz de decidir entre responder sin herramienta, consultar conocimiento RAG o consultar información bancaria sintética mediante function tools READ-ONLY.
Usar Foundry Local + `phi-4-mini` mediante la integración Chat Completions ya existente. No cambiar de modelo.

## Herramientas permitidas
Implementar únicamente una allowlist READ-ONLY:
1. `search_knowledge(query)`
2. `get_my_loans()`
3. `get_loan_details(loan_id)`
4. `get_next_installment(loan_id)`

NO exponer:
`POST /api/v1/service-requests` ni ninguna futura operación WRITE.
El `customer_id` de sesión debe provenir de contexto determinístico de runtime y NO ser elegido libremente por el LLM.
Los tools de préstamo deben validar que el préstamo pertenece al cliente sintético de la sesión.

## Agent loop
Implementar:
`user request → model with tool schemas → optional tool call → validate arguments → execute allowed read-only tool → return tool result to model → final answer`

Usar `tool_choice="auto"`.
Limitar el número de rondas/tool calls para evitar loops.
Rechazar:
- nombre de tool desconocido;
- argumentos inválidos;
- acceso a préstamo de otro cliente sintético;
- cualquier intento de WRITE.

Versionar las instrucciones del agente, por ejemplo:
`agent-system-v001`

## RAG
`search_knowledge` debe reutilizar v0.4/v0.5.
No modificar:
- corpus;
- qrels;
- retrieval metrics;
- `rag-answer-v001`;
- held-out v0.5.

## Evaluación v0.6
Crear un dataset sintético NUEVO y separado para evaluar:
- consultas informativas → `search_knowledge`;
- consultas de préstamos/cuotas → read tools correctos;
- consultas que no requieren tool → ninguna llamada;
- solicitud de reclamo/write → ninguna herramienta WRITE;
- acción sensible → ninguna herramienta WRITE;
- acceso a recurso de otro cliente → rechazado;
- input inválido → rechazado.

Medir determinísticamente como mínimo:
- `tool_selection_accuracy`;
- `tool_input_accuracy`;
- `tool_call_success`;
- `no_write_compliance`;
- `ownership_enforcement`;
- `task_completion_proxy`.

No usar LLM-as-judge ni thresholds productivos.
Ejecutar una evaluación live local congelada UNA sola vez después de fijar dataset, schemas e instrucciones.
No modificar `agent-system-v001` después de observar ese held-out.

## Tests
Probar como mínimo:
- registry/allowlist;
- schemas;
- read-only enforcement;
- customer ownership;
- unknown tool rejection;
- invalid argument rejection;
- maximum tool-call rounds;
- RAG tool;
- Core Banking read tools;
- no WRITE tools exposed;
- evaluation harness;
- reproducibility donde corresponda.

Ejecutar también todas las regresiones existentes:
`v0.5/RAG` `v0.4` `v0.3` `v0.2`
y:
`ruff check`
`scoped ruff format --check`
`compileall`
`secret scan`
`git diff --check`

Detecta el siguiente ADR libre y documenta solamente decisiones nuevas, incluyendo:
- single-agent/read-only-first;
- deterministic tool authorization boundary.
No renumerar ADR históricos.

Antes del staging verifica que HEAD siga en `ebeb378`.

PROHIBIDO:
`git add .`
`git add -A`

Stagea únicamente archivos legítimos de v0.6 y revisa:
`git diff --cached --name-only`
`git diff --cached --stat`
`git diff --cached`

Si todos los gates pasan crea:
`feat(v0.6): establish single-agent read-only tool orchestration`

No push.

Entrega:
- tools expuestos;
- modelo;
- agent prompt version;
- casos de evaluación;
- métricas;
- tests/regresiones;
- ADRs;
- commit;
- git status final.

Finaliza únicamente con:
`AEGISBANK_V0.6_SINGLE_AGENT_READ_ONLY_READY`

y STOP.

NO iniciar v0.7.
