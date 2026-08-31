# 013 — AegisBank v0.9.1 Knowledge Tool Routing + RAG Acceptance

Continúa exclusivamente:
v0.9.1 — Knowledge Tool Routing & RAG Acceptance
Proyecto: C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform
Baseline esperado: master HEAD = 0275290 working tree limpio
NO iniciar v0.10. NO Azure. NO Docker. NO cambiar modelo. NO push.
NO modificar el corpus para hacer pasar la prueba.
NO modificar métricas históricas.
NO parsear pseudo-tool-calls escritos como texto.

Guarda este prompt como:
docs/chatgpt-prompts/013_PROMPT.md

## Regla pedagógica
Explica desde cero:
- RAG = Retrieval-Augmented Generation;
- retrieval;
- knowledge base;
- tool call;
- tool routing;
- tool_choice;
- abstention;
- grounding;
- knowledge gap;
- routing gap.
Para cada concepto: qué es, cómo funciona, por qué importa, relación con Mibanco y relación con AI-103.

## Problema real observado
Comando:
.venv\Scripts\python.exe -m aegisbank_agent.cli run "¿Cuáles son los plazos máximos para un crédito vehicular?" --customer-id CUST-0001
Resultado repetido:
Tools Executed: 0
y el modelo escribió textualmente:
search_knowledge("plazos máximos para un crédito vehicular")
Esto NO demuestra que el corpus carezca de información; demuestra únicamente que search_knowledge no fue ejecutado.

## 1. Diagnóstico RAG directo
Ejecuta directamente:
python -m aegisbank_rag.cli search "plazos máximos para un crédito vehicular"
Registra:
- top-k hits;
- document_id;
- chunk_id;
- score/rank;
- contenido relevante sanitizado;
- si existe evidencia suficiente para contestar exactamente la pregunta.
Clasifica:
KNOWLEDGE_AVAILABLE
o:
KNOWLEDGE_GAP
No alteres el corpus.

## 2. Diagnóstico con OpenTelemetry
Reproduce una sola vez la consulta mediante aegisbank_agent.
Usa la instrumentación v0.9 para determinar:
- tools enviadas al LLM;
- tool_choice efectivo;
- finish_reason;
- existencia de message.tool_calls;
- tool seleccionado;
- ToolRegistry execution;
- search_knowledge execution;
- retrieval execution.
No guardar prompts completos ni secretos en telemetría.

## 3. Native tool probe
Prueba search_knowledge usando la misma integración Foundry Local + phi-4-mini con una función específica/required solo como diagnóstico.
Confirma si el modelo puede emitir:
message.tool_calls
para search_knowledge.
No usar parsing de texto para fabricar llamadas.

## 4. Clasificación de causa raíz
Determina exactamente uno o más:
A. KNOWLEDGE_GAP
B. TOOL_ROUTING_GAP
C. TOOL_SCHEMA_GAP
D. ORCHESTRATOR_GAP
E. MODEL_SELECTION_LIMITATION
Documenta evidencia.

## 5. Política de conocimiento autorizado
Si existe TOOL_ROUTING_GAP, no dependas exclusivamente de tool_choice="auto" para consultas que necesitan conocimiento bancario autorizado.
Implementa una política explícita y testeable:
Las consultas sobre:
- políticas;
- productos;
- requisitos;
- comisiones;
- tasas;
- plazos;
- condiciones bancarias;
deben recuperar primero conocimiento autorizado antes de que el LLM pueda dar una respuesta factual.
Preferir el mecanismo mínimo que preserve native tool calling.
Si phi-4-mini ignora consistentemente la selección específica, el orquestador puede ejecutar determinísticamente search_knowledge antes de generar la respuesta.
Documentar claramente esa decisión.
NO interpretar texto como: `search_knowledge(...)` para ejecutar herramientas.

## 6. Knowledge gap behavior
Si el corpus no contiene evidencia suficiente:
el resultado correcto debe ser abstención explícita.
Ejemplo conceptual:
"No encuentro información suficiente en la base de conocimiento autorizada para confirmar el plazo máximo de ese producto."
NO inventar datos.
NO añadir el dato al corpus en este hito.

## 7. Acceptance tests
Añadir casos nuevos independientes:
1. conocimiento existente -> search_knowledge realmente ejecutado.
2. política/requisito bancario existente -> Tools Executed > 0.
3. conocimiento inexistente -> tool ejecutado + abstention.
4. pseudo-tool-call textual -> NO se ejecuta como herramienta.
5. pregunta que no necesita información bancaria -> no fuerza RAG innecesariamente.
6. provenance/citations preservadas.
7. OpenTelemetry demuestra tool/retrieval execution.
Ejecutar también todas las regresiones existentes.

## 8. Métricas
Añadir métricas de aceptación, como mínimo:
knowledge_required_count
knowledge_tool_invoked_count
knowledge_tool_missed_count
knowledge_abstention_count
No establecer thresholds productivos.

## 9. Documentación
Actualizar:
docs/learning/GLOSSARY.md
docs/learning/MASTERS-NOTES.md
docs/requirements/COVERAGE-MATRIX.md
Explicar especialmente:
AUTO TOOL ROUTING vs POLICY-ENFORCED TOOL ROUTING
y por qué en banca las respuestas sobre políticas deben estar grounded en fuentes autorizadas.

## 10. Git
Verificar HEAD antes del staging.
PROHIBIDO:
git add .
git add -A
push
Stagear únicamente archivos legítimos v0.9.1.
Si todos los tests/regresiones/gates pasan, crear:
fix(v0.9): enforce grounded knowledge tool routing
No push.

## Informe final
Entregar:
DIRECT_RAG_RESULT: KNOWLEDGE_AVAILABLE / KNOWLEDGE_GAP
ROOT_CAUSE: ...
AUTO_TOOL_CHOICE_BEHAVIOR: ...
FIX: ...
MANUAL_ACCEPTANCE:
Tools Executed:
search_knowledge executed:
abstention:
citations:
Tests: ...
Finalizar con:
AEGISBANK_V0.9_GROUNDED_TOOL_ROUTING_READY
y STOP.
NO iniciar v0.10.
