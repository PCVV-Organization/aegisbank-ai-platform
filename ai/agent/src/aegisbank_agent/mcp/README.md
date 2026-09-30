# mcp

## Para qué existe

Adaptación del protocolo MCP de la aplicación. Modificar este componente exige revisar consumidores y su suite asociada; no crear una responsabilidad paralela.

## Dónde mirar

`__init__.py`; `server.py`

La [guía inicial](../../../../../docs/START-HERE.md) explica el flujo completo.
El [mapa de carpetas](../../../../../docs/DIRECTORY-MAP.md) identifica las subcarpetas.

## Antes de cambiar

Identificar entrada, salida y consumidores; consultar los
[componentes canónicos](../../../../../docs/architecture/CANONICAL-COMPONENTS.md).
Trabajar con datos sintéticos y adquirir SessionGuard según
[AGENTS](../../../../../AGENTS.md). Ejecutar la suite correspondiente de la
[estrategia de pruebas](../../../../../docs/quality/TEST-STRATEGY.md).
Un cambio de interfaz requiere actualizar pruebas y documentación en el mismo cambio.

## Límites

Esta guía describe responsabilidades del checkout, no una certificación ni una
ejecución live. Para evidencias y bloqueos consultar el
[estado fechado](../../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md).
