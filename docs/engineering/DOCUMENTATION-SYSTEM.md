# Sistema documental y evolución

## Contrato de lectura

README.md explica qué es, cómo empezar y dónde seguir. README.LLM.md explica
autoridad, límites y recuperación por tarea. llms.txt es el mapa breve.
llms-full.txt es un paquete generado de guías explícitas: no contiene todo el
código ni todos los históricos. project-index.json es un inventario de rutas.
DIRECTORY-MAP.md cubre carpetas y archivos por responsabilidad sin leer datasets.
Ningún archivo obliga a todos los clientes LLM a cargarlo automáticamente.

## Una fuente por responsabilidad

README de componente: propósito, entradas/salidas, código, ejecución, pruebas y
límites. docs: tutorial inicial, instrucciones prácticas, referencia y explicación
separadas. Los informes fechados conservan resultados; el README enlaza su vigencia.
No copiar métricas históricas en veinte README. No renombrar carpetas para igualar
un hito ni borrar experimentos para ocultar contradicciones.

## Cuándo crear o actualizar documentos

| Cambio | Documentos necesarios | Validación |
| --- | --- | --- |
| Nueva responsabilidad | README del componente, catálogo y ownership; ADR si corresponde | Revisar consumidores y pruebas |
| Nuevo directorio interno | Incluirlo en mapa; README si añade una interfaz/procedimiento propio | Índice sin rutas huérfanas |
| API/contrato | Esquema, productor, consumidor y guía de uso | Contratos y casos de error |
| Nueva variable | Nombre, propósito, obligatoriedad y plantilla sin valor real | Configuración y exclusión de secretos |
| Nuevo script | Directorio de ejecución, efectos, requisitos y outputs | Ejecutar el check pertinente |
| Cambio de arquitectura | Nuevo ADR; enlazar el sustituido | Catálogo y mapa de ownership |
| Nuevo informe | Fecha, Git base, entorno, comando, muestras, skips y límites | Preservar anterior; no sobrescribir evidencia |
| Release | Changelog/notas y evidencias de tag/commit reales | No deducir release del título |
| Archivo movido | Actualizar enlaces, README e índices en el mismo cambio | Regeneración determinista |

## Gitignore y lectura máquina

Gitignore evita incorporar archivos no versionados; no retira lo que ya está
tracked ni controla acceso o lectura de un LLM. Mantener reglas raíz por repositorio;
usar reglas locales solo donde cambie la responsabilidad. Versionar ejemplos
redactados, lockfiles, pruebas, guías e índices reproducibles. Excluir .env reales,
claves, bases locales, entornos, caches, reports/ de ejecución y MLflow local.
Preservar informes históricos ya tracked; no eliminarlos con una limpieza masiva.
Una lista explícita de fuentes limita el contexto ampliado. No concatenar el árbol.

## Ciclo de mantenimiento

1. Cambiar la guía propietaria junto al código/configuración.
2. Si cambia el alcance, actualizar el manifiesto de navegación y sus fuentes.
3. Regenerar índices y texto ampliado; revisar el diff, no editar derivados a mano.
4. Ejecutar pruebas del generador, enlaces, exclusiones y comprobaciones del componente.
5. Revisar títulos y cuerpos recientes de Git. Escribir un título descriptivo y
   cuerpo con problema, cambios, validación observada y límites. Staging explícito.
6. En revisión de hito verificar enlaces y vigencia; en release revisar madurez.

## Investigación aplicada — 2026-09-22

- [llms.txt](https://llmstxt.org/): mapa Markdown de información y enlaces; adaptación
  local con rutas relativas. Es una propuesta orientada a sitios, no permiso de acceso.
- [Write the Docs](https://www.writethedocs.org/guide/writing/beginners-guide-to-docs/):
  partir de necesidades del lector, ejemplos y mantenimiento junto al producto.
- [Diátaxis](https://diataxis.fr/): distinguir aprender, resolver una tarea,
  consultar referencia y comprender una explicación.
- [Git ignore](https://git-scm.com/docs/gitignore): reglas de exclusión de archivos
  no versionados; no son frontera de seguridad para contenido ya tracked.
- [Make a README](https://www.makeareadme.com/): propósito, instalación, uso y apoyo
  ajustados al proyecto. Aquí las instrucciones operativas permanecen en su componente.

Se aplican estas ideas sin instalar una plataforma documental ni nuevas dependencias.
