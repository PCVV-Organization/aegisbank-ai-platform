# Código del agente

## Para qué existe

agent.py contiene AgentOrchestrator; knowledge_routing.py decide rutas y herramientas; session_store.py conserva contexto; hitl.py gestiona aprobación. mcp_boundary.py y mcp_server.py conectan el protocolo. Leer el catálogo canónico antes de extender estos componentes.

## Dónde mirar

`__init__.py`; `agent.py`; `cli.py`; `constants.py`; `cosmos.py`; `hitl.py`; `hitl_cli.py`; `knowledge_routing.py`; `mcp_boundary.py`; `mcp_server.py`; `session_store.py`

La [guía inicial](../../../../docs/START-HERE.md) explica el flujo completo.
El [mapa de carpetas](../../../../docs/DIRECTORY-MAP.md) identifica las subcarpetas.

## Antes de cambiar

Identificar entrada, salida y consumidores; consultar los
[componentes canónicos](../../../../docs/architecture/CANONICAL-COMPONENTS.md).
Trabajar con datos sintéticos y adquirir SessionGuard según
[AGENTS](../../../../AGENTS.md). Ejecutar la suite correspondiente de la
[estrategia de pruebas](../../../../docs/quality/TEST-STRATEGY.md).
Un cambio de interfaz requiere actualizar pruebas y documentación en el mismo cambio.

## Límites

Esta guía describe responsabilidades del checkout, no una certificación ni una
ejecución live. Para evidencias y bloqueos consultar el
[estado fechado](../../../../history/quality/LOCAL-BASELINE-CLOSURE-20260921.md).
