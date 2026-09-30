# 009 — AegisBank v0.6.1 Native Tool Calling Acceptance

Corrige exclusivamente el defecto E2E detectado después de cerrar v0.6.
Proyecto: `C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

- NO iniciar v0.7.
- NO MCP/HITL/WRITE.
- NO worktrees.
- NO Azure/Docker.
- NO push.
- NO modificar ni reejecutar el held-out congelado de v0.6.

## Problema observado manualmente

Consulta: `¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?`
Resultado: `Tools Executed = 0`
El modelo imprimió `get_my_loans()` como texto. También ocurrió con `search_knowledge`.
Esto NO cumple la aceptación E2E de v0.6.

Primero investiga el flujo real:
Foundry Local response → FoundryLocalProvider / OpenAI Client → AgentOrchestrator → ToolRegistry

Verifica específicamente si se están preservando y procesando:
- `message.tool_calls`
- `finish_reason`
- `tool_call.id`
- `tool_call.function.name`
- `tool_call.function.arguments`

No hagas parsing de strings como `get_my_loans()` para simular tool calling.

## Diagnóstico obligatorio

Añade un probe local mínimo usando la misma configuración Foundry Local y `phi-4-mini`.
Envía una única función trivial/read-only con:
`tools=[...]`
`tool_choice="required"`
y confirma que Foundry Local devuelve un `message.tool_calls` estructurado.
No uses ese modo required en producción; es solo diagnóstico.

Si Foundry Local NO devuelve tool_calls estructurados:
STOP con: `AEGISBANK_V0.6_NATIVE_TOOL_CALLING_BLOCKED`

Si sí los devuelve, corrige el adapter/orchestrator/system prompt para mantener el contrato estructurado.

## Flujo correcto requerido

Primera petición: `messages + tools + tool_choice="auto"`
Si existe `tool_call`:
1. conservar assistant message + `tool_calls`;
2. validar nombre contra allowlist;
3. validar JSON/schema;
4. ejecutar tool;
5. añadir respuesta:
   - `role="tool"`
   - `tool_call_id=<id original>`
   - `content=<resultado sanitizado>`
6. volver a llamar al modelo;
7. repetir hasta respuesta final o `max_rounds`.

Nunca permitir WRITE. No convertir pseudo-tool-calls escritos como texto en llamadas reales.

## Acceptance tests NUEVOS

Sin modificar el held-out congelado, crea pruebas/smokes nuevos para:
1. CUST-0001: "¿Cuáles son mis préstamos activos?" → `get_my_loans` ejecutado >= 1
2. CUST-0001: consulta próxima cuota de un loan propio → `get_next_installment` ejecutado
3. consulta documental que requiera corpus → `search_knowledge` ejecutado
4. préstamo de otro cliente → ownership bloqueado
5. solicitud WRITE → 0 write tools y ninguna mutación

Para los tres primeros debe cumplirse: `Tools Executed > 0` y deben ser `tool_calls` estructurados reales, no texto.

Preserva las métricas históricas v0.6. Identifica además cuál es el `agent-metrics.json` canónico y explica la discrepancia entre los dos conjuntos de métricas reportados; no sobrescribas resultados históricos para reconciliarlos artificialmente.

Después ejecuta todas las regresiones existentes, Ruff, format, compileall, secret scan y git diff --check.
Stage explícito solamente. PROHIBIDO: `git add .` `git add -A`

Si todo pasa crea:
`fix(v0.6): execute native Foundry Local tool calls end to end`
No push.

Finaliza con:
`AEGISBANK_V0.6_NATIVE_TOOL_CALLING_READY`
y STOP. NO iniciar v0.7.
