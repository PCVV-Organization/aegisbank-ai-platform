# 010 — AegisBank v0.7 MCP + HITL

Continúa exclusivamente `v0.7.0 — MCP + Human-in-the-Loop` en
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`, con baseline `master`
en `73b7dac`.

Usa un único MCP local por `stdio`, el SDK oficial Python MCP estable compatible
con Python 3.14 y Foundry Local + `phi-4-mini`. No usar worktrees, Azure,
Docker, push, v0.8, retries, circuit breakers, messaging, Idempotency-Key ni
operaciones financieras reales. Preserva íntegramente v0.5/v0.6/v0.6.1 y sus
métricas.

Expón solamente READ `search_knowledge`, `get_my_loans`, `get_loan_details`,
`get_next_installment` y WRITE `create_service_request`. No crear otros WRITE.
El `customer_id` proviene del runtime determinístico, nunca del LLM. Las
annotations MCP son metadata, no autorización.

Antes de ejecutar `create_service_request`: propuesta -> validación
determinística -> mostrar al humano argumentos exactos -> aprobación `y`
explícita -> MCP `tools/call` -> Core Banking POST. Default DENY; REJECT no
ejecuta ni muta. Implementa `ApprovalRequest` con approval_id, tool_name,
synthetic_customer_id, normalized_arguments, status y created_at; estados
PENDING, APPROVED, REJECTED, EXECUTED. Argumentos alterados, approval ajeno,
inexistente o ya ejecutado deben bloquearse.

Usa schemas estrictos, outputs sanitizados y errores estructurados sin stack
traces/secrets. Añade acceptance E2E para READ, reject/approve, alteración,
ownership, inexistente, ejecutado, unknown tool, identidad no controlable y
ausencia de otros WRITE. Añade smoke local APPROVE y REJECT. No modificar
datasets/held-outs congelados.

Detecta ADRs libres y documenta solo boundary MCP stdio y HITL obligatorio.
Ejecuta tests v0.7 y regresiones v0.6/v0.5/v0.4/v0.3/v0.2, Ruff, format scoped,
compileall, secret scan y `git diff --check`. Stage explícito, nunca `git add .`
ni `git add -A`. Si todo pasa crea:

`feat(v0.7): establish MCP human-approved write boundary`

No push. No iniciar v0.8.
