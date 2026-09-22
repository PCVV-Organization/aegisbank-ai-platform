# Contratos de integración

## Para qué existe

JSON Schema fija las formas admitidas de eventos y fronteras MCP/datos. cloudevents separa el sobre de integración. Cambiar un esquema obliga a revisar su productor, consumidor y pruebas; no basta con que el JSON se pueda parsear.

## Dónde mirar

`bootstrap-manifest.schema.json`; `core-banking-openapi.schema.json`; `cosmos-event-item.schema.json`; `graph.schema.json`; `index.schema.json`; `manifest.schema.json`; `mcp-tools.schema.json`; `service-request-created.schema.json`; `session.schema.json`

La [guía inicial](../docs/START-HERE.md) explica el flujo completo.
El [mapa de carpetas](../docs/DIRECTORY-MAP.md) identifica las subcarpetas.

## Antes de cambiar

Identificar entrada, salida y consumidores; consultar los
[componentes canónicos](../docs/architecture/CANONICAL-COMPONENTS.md).
Trabajar con datos sintéticos y adquirir SessionGuard según
[AGENTS](../AGENTS.md). Ejecutar la suite correspondiente de la
[estrategia de pruebas](../docs/quality/TEST-STRATEGY.md).
Un cambio de interfaz requiere actualizar pruebas y documentación en el mismo cambio.

## Límites

Esta guía describe responsabilidades del checkout, no una certificación ni una
ejecución live. Para evidencias y bloqueos consultar el
[estado fechado](../docs/quality/LOCAL-BASELINE-CLOSURE-20260921.md).
