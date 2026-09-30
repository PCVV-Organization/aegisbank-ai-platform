# 014 — AegisBank v0.9.2 Banking Read Tool Routing Acceptance

Continúa exclusivamente:
v0.9.2 — Banking Read Tool Routing Acceptance
Proyecto: C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform
Baseline esperado: master HEAD = 0275290 working tree limpio
NO iniciar v0.10. NO Azure. NO Docker. NO cambiar phi-4-mini.
NO modificar held-outs/métricas históricas. NO nuevas operaciones WRITE.
NO push. NO parsear pseudo-tool-calls escritos como texto.

Guarda este prompt como:
docs/chatgpt-prompts/014_PROMPT.md

## Regla pedagógica
Explica desde cero:
LLM = Large Language Model
tool calling
tool routing
tool_choice
policy-enforced routing
account query
tool allowlist
grounding
RAG
knowledge gap
routing gap
Para cada concepto: qué significa, cómo funciona, por qué se usa, riesgos, ejemplo AegisBank, relación con Mibanco y AI-103.

## Problema observado
Consulta:
"¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?"
Resultado actual:
Rounds: 1
Tools Executed: 0
El modelo escribió:
get_my_loans()
como texto normal.
Esto es incorrecto porque una consulta factual sobre datos bancarios propios debe consultar Core Banking antes de responder.
La consulta RAG:
"¿Cuáles son los plazos máximos para un crédito vehicular?"
ya ejecuta correctamente:
search_knowledge -> Success=True
y se abstiene cuando no existe evidencia.
NO romper ese comportamiento.

## 1. Diagnóstico con v0.9
Usa OpenTelemetry/traces para la consulta de préstamos y registra:
- tools entregadas al modelo;
- tool_choice efectivo;
- finish_reason;
- message.tool_calls;
- tool execution;
- rounds.
Confirma la causa raíz.

## 2. Verificar Core Banking directamente
Sin usar el LLM, verifica mediante las funciones READ existentes que:
get_my_loans
puede ejecutarse para:
CUST-0001
y registra únicamente datos sintéticos necesarios para comprobar que el backend responde.
Si el backend falla: STOP y clasifica CORE_BANKING_GAP.
Si funciona: continúa como TOOL_ROUTING_GAP.

## 3. Banking Data Routing Policy
Implementa una política determinista antes del LLM.
Consultas que requieren datos específicos de la sesión, como:
- mis préstamos;
- saldo de mi préstamo;
- detalles de mi préstamo;
- próxima cuota;
- fecha/monto de próxima cuota;
NO pueden responderse desde conocimiento interno del LLM.
Deben consultar las banking READ tools autorizadas.
Reutiliza, si es adecuado, la clasificación/intención ya existente en AegisBank; no dupliques lógica innecesariamente.
La identidad continúa viniendo de:
AgentContext.session_customer_id
El LLM nunca puede proporcionar customer_id.

## 4. Tool exposure mínimo
Para cada intención expón al modelo únicamente el subconjunto mínimo de tools relevantes cuando sea posible.
Ejemplo conceptual:
account loans list -> get_my_loans
specific loan information -> get_loan_details
next installment -> get_next_installment
bank policy/product knowledge -> search_knowledge
Esto reduce ambigüedad de tool selection.

## 5. Native tool calling obligatorio
Mantener tool calls estructurados reales:
message.tool_calls
NO ejecutar texto como: `get_my_loans()`
Si el modelo imprime un pseudo-tool-call textual: no ejecutarlo y registrarlo como routing failure.
Usar tool_choice controlado cuando una policy haya determinado que una tool es obligatoria.
No usar required globalmente para todas las consultas.

## 6. Multi-step account query
La consulta:
"¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?"
puede requerir más de una herramienta.
Debe soportar el flujo:
get_my_loans ↓ identificar loans propios ↓ get_next_installment(...) ↓ respuesta final
sin permitir acceso a loans de otro customer.
Respetar max_rounds y ownership existentes.

## 7. Acceptance tests
Añadir casos nuevos:
A. "¿Cuáles son mis préstamos activos?" -> get_my_loans ejecutado.
B. "¿Cuándo vence la próxima cuota de LOAN propio?" -> get_next_installment ejecutado.
C. pregunta combinada préstamos + próxima cuota -> tool chain real, Tools Executed > 0.
D. loan de otro customer -> ownership denied.
E. política bancaria -> search_knowledge ejecutado.
F. knowledge gap -> search_knowledge + abstention.
G. pregunta casual que no requiere datos/KB -> ninguna tool forzada.
H. pseudo-tool-call textual -> nunca ejecutado.

## 8. Métricas
Añadir:
banking_data_required_count
banking_tool_invoked_count
banking_tool_missed_count
pseudo_tool_call_count
forced_routing_count
No definir thresholds productivos.

## 9. Observabilidad
Los traces deben permitir distinguir:
AUTO_ROUTING
POLICY_ENFORCED_ROUTING
TOOL_CALL_STRUCTURED
PSEUDO_TOOL_CALL
ROUTING_FAILURE
No registrar secretos ni contenido sensible innecesario.

## 10. Regresiones
Ejecutar:
v0.9
v0.8
v0.7/v0.6
RAG
ML
Core Banking
Ruff format
compileall
secret scan
git diff --check

## 11. Documentación
Actualizar:
docs/learning/GLOSSARY.md
docs/learning/MASTERS-NOTES.md
docs/requirements/COVERAGE-MATRIX.md
Explicar:
AUTO TOOL ROUTING vs POLICY-ENFORCED TOOL ROUTING
y por qué las respuestas factuales bancarias deben consultar la fuente de verdad autorizada.
No marcar producción/cloud como COVERED.

## 12. Git
Verificar HEAD antes de staging.
PROHIBIDO:
git add .
git add -A
push
Stagear únicamente archivos legítimos v0.9.2.
Si todo pasa crear:
fix(v0.9): enforce banking read tool routing
No push.

## Informe final
Entregar:
DIRECT_CORE_BANKING_RESULT: PASS / FAIL
ROOT_CAUSE: ...
BANKING_ROUTING_POLICY: ...
Manual acceptance:
"¿Cuáles son mis préstamos activos?"
Tools Executed:
Tools:
"¿Cuáles son mis préstamos activos y cuánto debo en la próxima cuota?"
Rounds:
Tools Executed:
Tools:
RAG regression: PASS / FAIL
Tests: ...
Finalizar con:
AEGISBANK_V0.9_BANKING_TOOL_ROUTING_READY
y STOP.
NO iniciar v0.10.
