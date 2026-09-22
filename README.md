# AegisBank AI Platform

Laboratorio educativo y de portafolio para construir IA bancaria segura con
Python y datos sintéticos. **Aegis** consulta documentación y datos bancarios
simulados, y propone solicitudes de servicio sujetas a aprobación humana.
El LLM interpreta y propone; las reglas de identidad, autorización y negocio
deciden qué se ejecuta.

## Estado del proyecto

**Cierre local 2026-09-21:** gate FAST 13/13, 466 pruebas aprobadas y 11 omitidas;
11 E2E aprobadas. Release bloqueada por 75 errores Pyright; R2 sigue parcial.
Consultar el [informe y plan de commits](docs/quality/LOCAL-BASELINE-CLOSURE-20260921.md).
Los resultados live anteriores son históricos; no se creó una nueva release.

Referencia revisada el **2026-09-15**: commit `477ac3b`, identificado como
**v1.0.6** en el historial Git. La organización documental v1.0.2 es un hito
anterior, no la versión técnica actual. Hay cambios locales de seguridad y
evaluación posteriores a esa base; no constituyen por sí solos una nueva release.

Consulta `git status --short` y `git log -1 --oneline` para conocer tu checkout.
Los resultados en [evidencia de release](docs/releases/V1.0-EVIDENCE.md) son
históricos. Esta actualización documental no vuelve a ejecutar ni certifica
las pruebas bancarias, los modelos, los contenedores o la nube.

## Entradas de lectura

Esta aplicación tiene su propio Git. El entorno de desarrollo `ai-env` es otro
repositorio: consulta [los límites](docs/engineering/REPOSITORY-BOUNDARIES.md).

| Necesidad | Punto de entrada |
| --- | --- |
| Contexto para LLMs y agentes de desarrollo | [README.LLM.md](README.LLM.md) y [AGENTS.md](AGENTS.md) |
| Navegación compacta | [llms.txt](llms.txt) |
| Inventario para herramientas | [project-index.json](project-index.json) |
| Documentación completa | [Portal documental](docs/README.md) |
| Arquitectura y responsabilidades | [Componentes canónicos](docs/architecture/CANONICAL-COMPONENTS.md) y [flujo E2E](docs/architecture/E2E-FINAL-ARCHITECTURE.md) |
| Demostración para entrevistas | [Evidencia de portafolio](docs/releases/PORTFOLIO-INTERVIEW-EVIDENCE.md) |
| Calidad y límites de evidencia | [Estrategia de pruebas](docs/quality/TEST-STRATEGY.md) y [evaluaciones](docs/evaluation/README.md) |

## Componentes

| Carpeta | Función |
| --- | --- |
| [services/mock-core-banking](services/mock-core-banking/README.md) | API FastAPI, datos sintéticos, préstamos, cuotas, solicitudes y persistencia. |
| [ml/intent-classifier](ml/intent-classifier/README.md) | Experimento independiente de clasificación de intenciones con ML clásico. |
| [ai/rag](ai/rag/README.md) | Recuperación documental y generación sustentada; adaptadores pgvector y Redis. |
| [ai/agent](ai/agent/README.md) | Un agente de aplicación, herramientas, sesiones, MCP, aprobación humana y controles de seguridad. |
| [functions/aegisbank-events](functions/aegisbank-events/) | Procesamiento de eventos mediante Azure Functions. |
| [contracts](contracts/) | Contratos JSON Schema de las fronteras de integración. |
| [deploy](deploy/) | Configuración local de contenedores y manifiestos Kubernetes; su existencia no prueba despliegue. |
| [scripts](scripts/) | Validación, evaluaciones, control de sesión y mantenimiento documental. |

RAG significa *Retrieval-Augmented Generation*: recuperar evidencia antes de
generar. MCP (*Model Context Protocol*) conecta herramientas con el agente.
HITL (*Human-in-the-Loop*) exige aprobación humana para cambios de estado.
Más conceptos en el [glosario](docs/learning/GLOSSARY.md).

## Flujo principal

```text
Consulta -> identidad y política deterministas -> conocimiento o herramientas
         -> respuesta sustentada o abstención -> trazas y auditoría

Propuesta de escritura -> aprobación humana -> controles de seguridad
                      -> operación idempotente + transacción + outbox
                      -> procesamiento del evento o cola de errores
```

La base confirmada incorpora defensas de acceso entre clientes, estado de
sesión persistente y reglas para impedir afirmaciones de cuenta sin herramientas.
Los documentos de diseño y los ensayos locales tienen alcances distintos:
consulta la [matriz de madurez](docs/requirements/V1.0-MATURITY-MATRIX.md).

## Trabajo local

Ejecuta los comandos desde **esta carpeta**, que contiene `ai/`, `services/`
y `scripts/`. Si abriste el workspace exterior, entra primero a
`aegisbank-ai-platform/`.

1. Revisa las [instrucciones](AGENTS.md) y el estado Git.
2. Sigue la instalación del componente correspondiente en la tabla anterior.
   Las dependencias están declaradas en sus `pyproject.toml`.
3. Para comprobar solo la navegación, con Python disponible:

```powershell
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
git diff --check
```

Para cambios de aplicación, consulta la estrategia de pruebas y
`python scripts/quality_gate.py --help`. Las ejecuciones requieren las
dependencias del entorno y pueden producir informes; no confundas estos
comandos documentados con evidencia de ejecución.

## Límites permanentes

- Solo datos sintéticos y reproducibles.
- Un agente de aplicación y monolito modular.
- Aprobación humana y autorización determinista para escrituras.
- Sin pagos, transferencias ni decisiones crediticias reales.
- Azure y recursos de pago requieren autorización explícita.
- Sin afirmaciones de certificación, cumplimiento o preparación productiva.

## Mantener la documentación

Consulta [DOCUMENTATION-MAINTENANCE.md](docs/engineering/DOCUMENTATION-MAINTENANCE.md)
para regenerar los índices y distinguir referencias vigentes de historia.
La [revisión documental](docs/quality/DOCUMENTATION-REORGANIZATION-20260915.md)
describe el alcance y la validación de esta reorganización.

## Navegación para empezar y mantener el orden

- [Empieza aquí](docs/START-HERE.md): explicación paso a paso y tareas frecuentes.
- [Mapa de carpetas](docs/DIRECTORY-MAP.md): responsabilidad y archivos por ubicación.
- [Contexto LLM ampliado](llms-full.txt): guías seleccionadas, con sus fuentes.

Los índices se regeneran; no es necesario copiar todos los archivos en un prompt.
Cambios de carpetas, interfaces o evidencia requieren actualizar la guía propietaria.
