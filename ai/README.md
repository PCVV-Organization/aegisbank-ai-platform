# IA de la aplicación

## Para qué existe

agent coordina la consulta y sus permisos; rag recupera documentos y valida citas. El clasificador ML vive en ml/. Las herramientas del desarrollador viven en el repositorio ai-env, no aquí.

## Dónde mirar

- [agent/README.md](agent/README.md)
- [rag/README.md](rag/README.md)

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
