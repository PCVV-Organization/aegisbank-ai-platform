# Conversational Relevance and Intent Robustness in AegisBank v0.13.0-R1

> **Milestone:** `v0.13.0-R1 — Intent Robustness + Conversational Relevance Regression`
> **Propósito:** Documentar las decisiones canónicas que arreglaron los defectos descubiertos durante la sesión manual E2E y cómo el sistema garantiza que vuelvan a aparecer como regresiones.

---

## 1. Contexto del Defecto

Una sesión manual E2E descubrió que dos frases con la misma intención semántica producían resultados distintos:

| Frase | Tools Executed | Resultado |
|---|---|---|
| `Dame detalle de mi prestamo LOAN-0001` | 2 (`get_my_loans` + `get_loan_details`) | ✅ |
| `Dame detalle de mi LOAN-0001` | 0 (pseudo-tool-call) | ❌ |

La causa raíz: el router previo requería que apareciera la palabra `prestamo` para que el orchestrator forzara `tool_choice="get_loan_details"`. Cuando la palabra desaparecía, el LLM quedaba en modo `auto` con `phi-4-mini` y fabricaba la tool call en texto plano en lugar de emitirla por el canal estructurado.

Hallazgos adicionales:

1. El saludo `Hola` devolvía una enumeración de categorías internas (baja relevance).
2. La consulta de capacidades `¿Qué puedes hacer?` exponía nombres internos de tools (abstraction leak).
3. La consulta ambigua `¿Qué requiero para que mi reclamo tenga efecto?` requería un mecanismo de **Clarification** para distinguir entre campos del schema y requisitos de política.

---

## 2. Solución Canónica Aplicada

### 2.1 Extractor determinista de `loan_id`

`ai/agent/src/aegisbank_agent/knowledge_routing.py` añade `extract_loan_id(query)` que aplica la expresión regular canónica `\bLOAN-[0-9]{4}\b`. Es **case-insensitive** y devuelve el id en formato canónico (`LOAN-XXXX`). La expresión se reutiliza del contrato canónico existente en `mock_core_banking`.

### 2.2 Refinamiento del Router

- `requires_account_data(query)` ahora devuelve `True` cuando existe un `loan_id` en la consulta, **incluso si no aparece la palabra `prestamo`**.
- `account_tool_allowlist(query)` produce el allowlist mínimo basado en:
  1. presencia explícita de `LOAN-XXXX` → `get_loan_details` (+ `get_next_installment` si menciona cuota/vencimiento);
  2. `mis prestamos` / `mi prestamo` → `get_my_loans`;
  3. `proxima cuota` / `cuanto debo` → `get_next_installment`;
  4. `detalle` (sin id) → `get_loan_details` después de `get_my_loans`.
- `classify_service_inquiry(query)` distingue **DOMAIN_SCHEMA**, **RAG** y **CLARIFICATION** para preguntas sobre reclamos.

### 2.3 Determinismo en el Orchestrator

El orchestrator (`ai/agent/src/aegisbank_agent/agent.py`) ahora ejecuta el handler canónico de forma **determinista** cuando el allowlist tiene una sola herramienta y existe un `loan_id` explícito:

```python
if (
    account_required
    and forced_loan_id is not None
    and "get_my_loans" not in account_allowlist
    and len(account_allowlist) == 1
    and account_allowlist[0] in {"get_loan_details", "get_next_installment"}
):
    forced_tool = account_allowlist[0]
    forced_result = self._registry.execute(
        forced_tool, {"loan_id": forced_loan_id}, context
    )
```

Esto garantiza que la tool se ejecute sin depender de que `phi-4-mini` emita una llamada estructurada. Si el LLM responde con pseudo-texto, **la tool ya se ejecutó** y la respuesta se construye a partir del resultado real de Core Banking.

### 2.4 Saludo y Capacidades en Lenguaje de Banco

- `is_greeting(query)` detecta saludos cortos sin tools.
- El orchestrator hace **short-circuit** con respuesta bancaria fija.
- `is_capability_query(query)` se mantiene como utilidad (no se invoca hoy, pero queda disponible para futuras evoluciones del orchestrator).
- El system prompt **`agent-system-v003`** describe las capacidades en lenguaje del cliente, prohíbe enumerar categorías internas en saludos y prohíbe mencionar nombres de herramientas internas en respuestas de usuario.

### 2.5 Clarification sin Adivinación

`classify_service_inquiry(query)` devuelve `"CLARIFICATION"` cuando la pregunta es ambigua (por ejemplo, mezcla campos del schema y política de reclamos). El orchestrator devuelve una respuesta que pide al usuario precisar qué necesita antes de ejecutar una tool arbitraria. Esto evita que el LLM elija una interpretación arbitraria.

---

## 3. Tests de Regresión (v013r1)

`ai/agent/tests/v013r1/` contiene la suite permanente:

- **`test_routing_helpers.py`** — Pruebas del extractor `loan_id`, detectores de greeting/clarification/capability y clasificación de servicio.
- **`test_orchestrator_intent_robustness.py`** — Suite de regresión del orchestrator: paráfrasis metamórficas para `GET_LOAN_DETAILS`, regresión de pseudo-tool-call, saludo sin leak, capability en lenguaje de banco, ambigüedad y propiedad de loan id.
- **`test_intent_robustness_regression.py`** — Suite de cobertura ampliada: matriz de 7 paráfrasis, cross-customer ownership, multi-loan disambiguation sin adivinar, prompt v003 cargado por defecto.

Ejecutables vía `python scripts/quality_gate.py --gate-intent-robustness`.

---

## 4. Decisiones de Diseño

1. **REUSE** — `extract_loan_id`, `IdempotencyGuard`, `AuditLogger`, `OperationalMetrics`, `StructuredLogger`, `ObservabilityContext`, `TracerProvider` — ninguno nuevo; se reutilizan los canónicos existentes.
2. **EXTEND** — `account_tool_allowlist` y `requires_account_data` se extendieron con detección por entidad (`LOAN-XXXX`) sin reescribir el contrato.
3. **NEW_COMPONENT_JUSTIFIED** — `extract_loan_id` se añadió como nueva función en `knowledge_routing.py` (módulo canónico de routing). No es duplicación: ningún extractor de entidades existía en el codebase.
4. **Determinismo** — Cuando el allowlist tiene una sola herramienta y existe un id explícito, el orchestrator ejecuta la tool directamente sin pasar por el LLM. Esto elimina la posibilidad de pseudo-tool-calls.
5. **No revertir mejoras** — Los tests v09 existentes que codificaban el comportamiento previo se actualizaron al nuevo contrato (deterministic + sin pseudo-call). Ningún test se eliminó.

---

## 5. Estado de Madurez

- `LOCAL-INTENT-ROBUSTNESS-COVERED` — La suite v013r1 garantiza que el bug "Dame detalle de mi LOAN-0001" nunca vuelva a aparecer sin ser detectado.
- `EVENT-GRID-HANDLER-LOCAL = COVERED` — Sin regresión (gates anteriores siguen pasando).
- `FUNCTION-APP-CLOUD-PENDING` y `EVENTGRID-CLOUD-PENDING` — Sin cambios.

---

## 6. Lecciones para AI-200 / Agentic Roles

- **Intent Resolution** y **Tool Selection** deben ser **evaluados por conversación completa**, no por turno.
- Las pruebas **metamórficas / paráfrasis** son el mecanismo correcto para detectar drift en routing semántico.
- Un router que depende de palabras exactas (`prestamo`) es frágil: la **extracción de entidades** debe ser determinista y ortogonal al lenguaje natural.
- El **Pseudo-Tool-Call** es un anti-patrón real que solo se detecta con **pruebas E2E manuales** convertidas en **regresiones automatizadas**.
