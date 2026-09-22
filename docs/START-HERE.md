# Empieza aquí: AegisBank sin conocimiento previo

## 1. Qué estás mirando

AegisBank es un laboratorio bancario con datos inventados. Sirve para aprender
a construir un asistente que consulta préstamos y documentos y propone solicitudes
de servicio con aprobación humana. No es un banco real ni decide créditos reales.

Hay dos Git: **ai-env prepara al desarrollador**; **aegisbank-ai-platform contiene
el producto**. Si buscas configuración MCP o instrucciones del programador, abre
el repositorio exterior. Si buscas una regla bancaria, una prueba o un contrato,
trabaja en este repositorio. Cada Git tiene su propio commit y futuro remoto.

## 2. Una consulta de principio a fin

1. Una persona hace una consulta en el contexto de un cliente sintético.
2. El agente determina si necesita datos bancarios, conocimiento o aclaración.
3. Para datos bancarios usa herramientas que verifican propiedad y reglas.
4. Para conocimiento recupera documentos; estos son evidencia no confiable, no órdenes.
5. El modelo propone texto o herramientas; la política determina qué se permite.
6. Una escritura requiere aprobación humana y controles deterministas. Se preservan
   trazas, auditoría e idempotencia: repetir una solicitud no debe duplicar su efecto.

Ejemplo: «Dame mis préstamos» debe consultar herramientas autorizadas para la sesión.
Un documento que diga «consulta a otro cliente» no concede ese permiso.

## 3. Ruta de lectura

| Quiero… | Leer primero | Después |
| --- | --- | --- |
| Entender el propósito | [README](../README.md) | [Glosario](learning/GLOSSARY.md) |
| Encontrar una carpeta | [Mapa completo](DIRECTORY-MAP.md) | README del componente |
| Cambiar comportamiento del agente | [Agente](../ai/agent/README.md) | [Catálogo canónico](architecture/CANONICAL-COMPONENTS.md) |
| Cambiar persistencia/API | [Core bancario](../services/mock-core-banking/README.md) | api, domain, schemas, persistence |
| Cambiar recuperación | [RAG](../ai/rag/README.md) | Corpus, retrievers y pruebas de citas |
| Evaluar modelos | [Evaluaciones](evaluation/README.md) | Catálogo, dataset y runner concretos |
| Trabajar como LLM | [README.LLM](../README.LLM.md) | [llms.txt](../llms.txt), rutas necesarias |
| Conocer bloqueos | [Cierre 2026-09-21](quality/LOCAL-BASELINE-CLOSURE-20260921.md) | Verificar estado actual antes de afirmar PASS |

## 4. Primera comprobación sin ejecutar el banco

Desde la raíz que contiene `ai/`, `services/` y `scripts/`:

```powershell
git rev-parse --show-toplevel
git status --short
python -B scripts/documentation_index.py --check
```

Leer documentación requiere Git y Python estándar para ese check; no requiere
credenciales, Docker, Azure ni un modelo. Para ejecutar el código, preparar Python
3.14 y el entorno siguiendo cada README: core bancario, clasificador, RAG, agente.
No asumir que paquetes instalados globalmente equivalen a los de `.venv`.

## 5. Antes de implementar

Leer [AGENTS](../AGENTS.md), definir alcance, consultar propietarios y adquirir
SessionGuard. Seleccionar las pruebas según [TEST-STRATEGY](quality/TEST-STRATEGY.md).
Registrar comando, fecha y resultado real. SKIP no significa PASS. Los 75 errores
Pyright y R2 parcial se observaron el 2026-09-21; esta guía no los declara corregidos.
