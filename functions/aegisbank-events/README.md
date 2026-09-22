# Procesador de eventos

## Para qué existe

function_app.py declara el trigger; cloud_event.py interpreta el sobre; service_request_handler.py procesa la solicitud con controles de duplicación. samples contiene un evento sintético. requirements.txt declara el entorno; local.settings.example.json es la plantilla, local.settings.json permanece privado.

## Dónde mirar

`.gitignore`; `cloud_event.py`; `Dockerfile`; `function_app.py`; `host.json`; `local.settings.example.json`; `local.settings.json`; `requirements.txt`; `service_request_handler.py`

La [guía inicial](../../docs/START-HERE.md) explica el flujo completo.
El [mapa de carpetas](../../docs/DIRECTORY-MAP.md) identifica las subcarpetas.

## Antes de cambiar

Identificar entrada, salida y consumidores; consultar los
[componentes canónicos](../../docs/architecture/CANONICAL-COMPONENTS.md).
Trabajar con datos sintéticos y adquirir SessionGuard según
[AGENTS](../../AGENTS.md). Ejecutar la suite correspondiente de la
[estrategia de pruebas](../../docs/quality/TEST-STRATEGY.md).
Un cambio de interfaz requiere actualizar pruebas y documentación en el mismo cambio.

## Límites

Esta guía describe responsabilidades del checkout, no una certificación ni una
ejecución live. Para evidencias y bloqueos consultar el
[estado fechado](../../docs/quality/LOCAL-BASELINE-CLOSURE-20260921.md).
