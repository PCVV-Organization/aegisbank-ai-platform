# 020A — AegisBank v0.12.0-R1 Grounded Response Consistency + Provenance

Actúa estrictamente como ORCHESTRATOR.
Tu objetivo NO es cambiar respuestas para que sean diferentes.
Tu objetivo es demostrar por qué se produce la respuesta, cuál es su fuente factual y si el comportamiento es correcto.

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline esperado:
- branch = master
- working tree limpio

NO iniciar Cosmos DB.
NO Redis.
NO Azure.
NO cambiar modelo.
NO cambiar temperatura para fabricar variedad.
NO nuevas WRITE tools.
NO push.

Guardar:
`docs/chatgpt-prompts/020A_PROMPT.md`

==================================================
0. TEACHING CONTRACT
==================================================
Leer primero:
- `docs/learning/TEACHING-CONTRACT.md`
- `docs/architecture/CANONICAL-COMPONENTS.md`
- `docs/engineering/OWNERSHIP-MAP.md`

Aplicar:
`ONE WRITER, MANY READERS`
`DISCOVER BEFORE CREATE`
`REUSE / EXTEND / NEW_COMPONENT_JUSTIFIED`

Explicar desde cero:
- LLM determinism
- stochasticity
- temperature
- top_p
- seed
- grounding
- provenance
- source of truth
- RAG
- tool schema
- domain schema
- enum
- response consistency
- semantic consistency
- lexical variation
- relevance
- completeness
- abstention

Para cada concepto: qué significa, cómo funciona, por qué existe, ejemplo AegisBank, riesgo, AI-103 y Mibanco.

==================================================
1. GIT + SESSION GUARD
==================================================
Verificar READ-ONLY:
```powershell
git branch --show-current
git rev-parse HEAD
git status --porcelain=v2 --branch
```
Adquirir SessionGuard antes de WRITE.

==================================================
2. REPRODUCIR PROBLEMA EXACTO
==================================================
Ejecutar únicamente el número mínimo de veces necesario:
```powershell
.venv\Scripts\python.exe -m aegisbank_agent.cli run "¿que tipos de reclamos hay?" --customer-id CUST-0001
```
Registrar:
- model id;
- system prompt version;
- temperature efectiva;
- top_p efectivo;
- seed si existe;
- tool_choice;
- tools enviadas;
- finish_reason;
- message.tool_calls;
- Tools Executed;
- response.
No registrar secrets.
No modificar configuración todavía.

==================================================
3. IDENTIFICAR SOURCE OF TRUTH
==================================================
Buscar con rg:
LOAN
INSTALLMENT
FEE
GENERAL
create_service_request

Determinar EXACTAMENTE dónde están definidas las categorías.
Clasificar source of truth:
A. CORE_BANKING_DOMAIN_ENUM
B. TOOL_SCHEMA
C. SYSTEM_PROMPT
D. RAG_CORPUS
E. DUPLICATED_DEFINITION
F. MODEL_PRIOR_KNOWLEDGE
G. UNKNOWN

Si existen múltiples definiciones independientes: analizar si hay DRY violation.
NO refactorizar todavía hasta demostrar cuál debe ser canónica.

==================================================
4. TRACE PROVENANCE
==================================================
Usar observabilidad v0.9 para responder:
¿por qué el agente dijo exactamente LOAN / INSTALLMENT / FEE / GENERAL?

Registrar:
grounding_source =
- core_banking
- rag
- tool_schema
- domain_schema
- none

Si grounding_source = none: esto es un defecto factual.

==================================================
5. DEFINIR POLICY CORRECTA
==================================================
Clasificar la pregunta: "¿qué tipos de reclamos hay?"
Determinar si realmente significa:
A. categorías soportadas por AegisBank
o
B. políticas generales sobre reclamos bancarios.

No asumir que todas las preguntas que contienen "reclamo" requieren RAG.

Regla deseada:
DOMAIN CAPABILITY QUESTION → canonical domain/tool schema
POLICY / PROCEDURE QUESTION → search_knowledge / RAG
CUSTOMER-SPECIFIC QUESTION → Core Banking READ tool
WRITE REQUEST → MCP + HITL

Documentar la decisión.

==================================================
6. NO FORZAR VARIACIÓN ARTIFICIAL
==================================================
NO aumentar temperature simplemente para obtener respuestas diferentes.
Para información bancaria factual: facts deben ser consistentes.
Separar: FACTUAL CONSISTENCY vs LEXICAL VARIATION.
No utilizar lexical variation como quality metric principal.

==================================================
7. RESPONSE CONTRACT
==================================================
Si las categorías son canónicas: la respuesta debe indicar explícitamente algo equivalente a:
"En AegisBank, las categorías soportadas actualmente son..."
NO: "generalmente se clasifican..." porque esa frase sugiere conocimiento universal/no grounded.
No añadir información irrelevante sobre create_service_request salvo que ayude directamente a la pregunta.

==================================================
8. CONSISTENCY ACCEPTANCE
==================================================
Crear dataset pequeño y NUEVO, separado de held-outs históricos.
Ejecutar varias repeticiones controladas de preguntas factuales.
Medir:
- factual_consistency
- unsupported_category_rate
- grounding_source_accuracy
- relevance
- completeness

No exigir igualdad textual byte-for-byte.
Ejemplo:
Respuesta A: "En AegisBank existen LOAN, INSTALLMENT, FEE y GENERAL."
Respuesta B: "Las categorías soportadas son LOAN, INSTALLMENT, FEE y GENERAL."
Ambas pueden ser correctas. Pero los FACTS deben coincidir.

==================================================
9. NEGATIVE ACCEPTANCE
==================================================
Probar que nunca aparecen categorías inventadas:
PAYMENT
TRANSFER
CARD
FRAUD
salvo que realmente sean agregadas al dominio canónico en el futuro.
unsupported_category_rate debe ser 0 en acceptance determinista.

==================================================
10. RAG DISTINCTION
==================================================
Probar:
"¿Qué tipos de reclamos admite el sistema?" → domain schema
"¿Cuál es el procedimiento para presentar un reclamo?" → RAG
"¿Cuál es el plazo regulatorio para responder un reclamo?" → RAG o abstention si corpus no tiene evidencia

No confundir taxonomy con policy.

==================================================
11. TOOL EXECUTION
==================================================
Tools Executed = 0 NO es automáticamente fallo.
Es válido SI:
- la pregunta no requiere ejecutar una operación;
- la respuesta está grounded en schema canónico visible al agente;
- provenance lo demuestra.
Pero si la pregunta requiere fuente dinámica:
Tools Executed = 0 puede ser routing failure.
Documentarlo como regla pedagógica.

==================================================
12. EVALUATION
==================================================
Añadir acceptance alineado con Microsoft Foundry:
- Intent Resolution
- Tool Selection
- Groundedness
- Relevance
- Response Completeness
- Abstention cuando aplique

No inventar equivalencia exacta con evaluadores cloud si se implementan localmente.

==================================================
13. ARCHITECTURE
==================================================
Si categorías están duplicadas en:
enum + tool schema + prompt
elegir UNA source of truth canónica.
Preferir generar/derivar schemas desde el dominio cuando sea compatible.
No mantener listas manuales duplicadas.
NEW TRUE DUPLICATION = 0.

==================================================
14. DOCUMENTACIÓN
==================================================
Actualizar:
docs/learning/GLOSSARY.md
docs/learning/MASTERS-NOTES.md
docs/requirements/COVERAGE-MATRIX.md

Documentar:
DETERMINISTIC FACTS ≠ REPETITION BUG
y:
GROUNDING ≠ RAG ONLY

==================================================
15. REGRESSION TESTS
==================================================
Agregar tests:
1. taxonomy query -> categorías canónicas exactas.
2. same query repeated -> same factual set.
3. paraphrased query -> same factual set.
4. no unsupported categories.
5. provenance source is canonical.
6. procedural complaint question -> RAG.
7. missing policy -> abstention.
8. no unnecessary WRITE execution.
9. no unnecessary HITL invocation.
10. no regression banking routing.
11. no historical metric changes.
12. no true duplication.

==================================================
16. VALIDACIÓN
==================================================
Ejecutar:
- nueva acceptance suite;
- agent suite;
- RAG suite;
- Core Banking;
- ML;
- pgvector regressions;
- contracts;
- E2E;
- quality gate;
- Ruff;
- format;
- compileall;
- Bandit;
- pip-audit;
- secret scan;
- Pylint R0801;
- git diff --check.

==================================================
17. GIT
==================================================
PROHIBIDO:
worktrees
git add .
git add -A
reset
rebase
amend
push

Stage explícito.
Si todo pasa:
fix(v0.12): enforce grounded factual response provenance
Liberar SessionGuard.

==================================================
18. INFORME FINAL
==================================================
Reportar:
ROOT_CAUSE: ...
MODEL_PARAMETERS:
  temperature:
  top_p:
  seed:
SOURCE_OF_TRUTH: ...
GROUNDING_SOURCE: ...
WHY_TOOLS_EXECUTED_ZERO: ...
RAG_REQUIRED: YES/NO + reason
SAME_RESPONSE: EXPECTED / DEFECT
  reason:
FACTUAL_CONSISTENCY: ...
LEXICAL_VARIATION: ...
UNSUPPORTED_CATEGORY_RATE: ...
ARCHITECTURE:
  canonical source:
  duplicates removed:
TESTS: ...

Finalizar solo con:
AEGISBANK_V0.12_GROUNDED_RESPONSE_CONSISTENCY_READY
y STOP.
NO iniciar Cosmos DB.
