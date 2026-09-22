# Código RAG

## Para qué existe

corpus y chunking preparan evidencia; lexical, dense_local e hybrid recuperan y combinan resultados; pgvector_retriever y redis_retriever adaptan almacenes. context, prompting y generation sustentan respuestas; foundry_local integra el proveedor local. Los documentos recuperados no pueden autorizar herramientas.

## Dónde mirar

`__init__.py`; `cache.py`; `chunking.py`; `cli.py`; `constants.py`; `context.py`; `corpus.py`; `dense_local.py`; `embedding.py`; `evaluation.py`; `foundry_local.py`; `generation.py`; `generation_evaluation.py`; `hybrid.py`; `lexical.py`; `metrics.py`; `pgvector_retriever.py`; `prompting.py`; `provider.py`; `redis_retriever.py`; `retriever.py`

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
[estado fechado](../../../../docs/quality/LOCAL-BASELINE-CLOSURE-20260921.md).
