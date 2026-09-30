# 011 — AegisBank v0.8 Reliability + Messaging Foundation

Continúa exclusivamente:

`v0.8.0 — Reliability + Messaging Foundation`

Proyecto:
`C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`

Baseline esperado:
- branch: `master`
- HEAD: `56aaa83`
- working tree limpio

## Regla pedagógica obligatoria

Trabaja como Senior/Principal AI Engineer **y como profesor de una Maestría en Inteligencia Artificial para un alumno que empieza desde cero**.

Antes de implementar cada concepto nuevo y en el informe final explica:

1. nombre completo y sigla;
2. qué significa;
3. qué problema resuelve;
4. cómo funciona internamente;
5. por qué AegisBank lo necesita;
6. alternativa principal y cuándo NO usarlo;
7. errores/riesgos típicos;
8. relación con el puesto IA Engineer LLM/Prompting o IA Engineer Agentic;
9. relación con Microsoft AI-103 o AI-200;
10. ejemplo concreto dentro del milestone.

Actualiza de forma incremental:
- `docs/learning/GLOSSARY.md`
- `docs/learning/MASTERS-NOTES.md`
- `docs/requirements/MIBANCO-JOB-PROFILE-2026.md`
- `docs/requirements/COVERAGE-MATRIX.md`

No inventes cobertura: usa `COVERED`, `PARTIAL` o `PENDING` con evidencia verificable.

Guarda este prompt como:
`docs/chatgpt-prompts/011_PROMPT.md`

## Restricciones

- NO worktrees.
- NO Azure cloud ni costos.
- NO push.
- NO v0.9.
- NO multi-agent.
- NO nuevas operaciones bancarias WRITE.
- Mantener como único WRITE `create_service_request`.
- Mantener MCP + HITL de v0.7.
- No modificar resultados históricos congelados v0.3-v0.7.
- No implementar observabilidad completa todavía; solo eventos/logs mínimos requeridos por reliability.

## Objetivo

Hacer confiable la escritura aprobada por HITL:

`APPROVED -> create_service_request`

ante duplicados, timeouts y fallos transitorios/persistentes.

Implementa por capas y con tests antes de integrar:

### 1. Idempotency

Añadir una `Idempotency-Key` estable a la operación WRITE.

Definición:
la misma intención de negocio con la misma key debe producir exactamente un `ServiceRequest`, aunque la petición se repita.

Persistir el resultado de idempotencia.

Probar:
- mismo key + mismos argumentos -> mismo resultado;
- mismo key + argumentos diferentes -> conflicto/bloqueo;
- dos ejecuciones concurrentes con mismo key -> un único efecto.

### 2. Timeout

Toda dependencia externa/simulada debe tener tiempo máximo de espera explícito.

No permitir espera indefinida.

### 3. Retry

Implementar bounded retry únicamente para fallos transitorios reconocidos.

Usar:
- número máximo pequeño de intentos;
- exponential backoff;
- jitter.

NO reintentar:
- validation errors;
- authorization failures;
- HITL reject;
- conflictos de idempotencia;
- errores de negocio permanentes.

Nunca reintentar WRITE si no está protegida por idempotencia.

### 4. Circuit Breaker

Implementar estados:

`CLOSED -> OPEN -> HALF_OPEN -> CLOSED`

para una dependencia simulada que falle persistentemente.

Retry y Circuit Breaker deben ser componentes separados y documentados.

### 5. Transactional Outbox

Cuando `create_service_request` se confirme, persistir en la misma transacción lógica un evento:

`ServiceRequestCreated`

en una tabla/registro Outbox.

Objetivo:
evitar el fallo dual:
- DB commit sí / evento no;
- evento sí / DB commit no.

### 6. Messaging abstraction

Crear una interfaz de mensajería local y un publisher/consumer determinista para procesar eventos Outbox.

No acoplar dominio directamente a Azure.

Diseñar el contrato para que después pueda mapearse a:
- Azure Service Bus;
- Service Bus Emulator local.

No introducir Docker en este milestone salvo que sea estrictamente necesario y se solicite autorización separada.

### 7. Idempotent Consumer + DLQ concept

El consumidor debe procesar un `event_id` una sola vez aunque se entregue repetido.

Tras fallos persistentes, mover el evento a una representación local de DLQ.

DLQ = Dead-Letter Queue.

### 8. Failure injection tests

Crear fallos deterministas simulados para demostrar:

- transient failure -> retry -> success;
- persistent failure -> circuit OPEN;
- timeout -> failure controlado;
- duplicate request -> no duplicate ServiceRequest;
- duplicate event -> consumer idempotente;
- poison event -> DLQ;
- HITL REJECT -> cero WRITE, cero evento;
- APPROVE repetido/replay -> no doble efecto;
- concurrencia con misma idempotency key -> un solo efecto.

## Documentación AI-200

En `MASTERS-NOTES.md` mapear explícitamente:

- retries / transient faults;
- Circuit Breaker;
- idempotency;
- queues/events;
- dead-letter queue;
- Service Bus target;
- consistency;
- concurrency;
- timeout;
- transactional outbox.

Explicar qué parte es local y qué servicio Azure sería el equivalente futuro.

## ADRs

Detecta números libres y crea ADRs solo si la decisión es nueva, como mínimo:

- idempotent banking writes before retries;
- transactional outbox + message abstraction;
- circuit breaker policy.

No renumerar ADRs históricos.

## Validación

Ejecutar:
- tests v0.8;
- regresiones v0.7/v0.6;
- ai/rag;
- v0.3;
- v0.2;
- Ruff;
- scoped format;
- compileall;
- secret scan;
- `git diff --check`.

Añadir acceptance E2E del flujo:

`User -> Agent -> MCP -> HITL APPROVE -> idempotent WRITE -> Outbox -> Consumer`

y el equivalente REJECT sin efectos.

## Git

Antes del staging:
- verificar que HEAD siga en `56aaa83`;
- revisar `git status --short`, `git diff`, `git diff --check`.

PROHIBIDO:
- `git add .`
- `git add -A`
- push

Stagear solo paths legítimos de v0.8 y documentación pedagógica actualizada.

Revisar:
- `git diff --cached --name-only`
- `git diff --cached --stat`
- `git diff --cached`

Si todo pasa crear:

`feat(v0.8): establish reliable idempotent messaging foundation`

No push.

## Informe final obligatorio

Además del resumen técnico, incluir:

### LEARNING NOTES
Para cada concepto introducido:
`SIGLA -> nombre completo -> qué es -> cómo funciona -> por qué -> ejemplo AegisBank -> AI-103/AI-200 -> requisito del puesto`

### COVERAGE UPDATE
Mostrar qué requisitos del perfil pasaron de `PENDING` a `PARTIAL/COVERED` y qué evidencia lo demuestra.

Finalizar solo con:

`AEGISBANK_V0.8_RELIABILITY_MESSAGING_READY`

y STOP.

NO iniciar v0.9.
