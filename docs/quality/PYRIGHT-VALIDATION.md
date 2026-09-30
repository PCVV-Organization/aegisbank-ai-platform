# Validación de tipos con Pyright

## Propósito

`pyrightconfig.json` define el alcance canónico del análisis estático de la
aplicación. Incluye las cuatro raíces que componen el monolito modular:
orquestación del agente, RAG, clasificador de intenciones y Core Banking.
No incluye artefactos, entornos virtuales, cachés, pruebas ni Functions, que
tienen ciclos de ejecución y dependencias propios.

La configuración usa el intérprete local `.venv/Scripts/python.exe` mediante
`venvPath` y `venv`. No baja la severidad de diagnósticos ni usa supresiones.
Las anotaciones y adaptadores de cada componente siguen siendo la fuente de
verdad para el contrato de tipos.

## Ejecución

Desde la raíz Git de la aplicación:

```powershell
node ..\tools\node\node_modules\pyright\index.js `
  --pythonpath .venv\Scripts\python.exe --outputjson
```

El comando no recibe rutas posicionales: estas se resuelven exclusivamente desde
`pyrightconfig.json`, por lo que una ejecución local y una futura automatización
analizan el mismo conjunto de fuentes. Revisa `errorCount`, `warningCount` y
`filesAnalyzed` del JSON antes de afirmar una base limpia.

## Límites

Pyright comprueba contratos estáticos; no sustituye las suites unitarias,
integración, contratos, E2E ni la compuerta FAST. Las rutas de Functions se
validan en su propio entorno cuando ese alcance esté autorizado.
