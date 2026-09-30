# Revisión de navegación documental — 2026-09-15

## Alcance observado

Se revisaron la estructura del workspace exterior, el inventario Git de la
aplicación, el grafo de código y las fuentes de arquitectura, componentes,
evaluación, operación y gobierno. No es una auditoría línea por línea de toda
la aplicación ni una nueva validación funcional o de seguridad bancaria.

Base observada: `477ac3b` (mensaje v1.0.6). El inventario inicial contenía
419 archivos versionados y 130 Markdown. Había 15 archivos modificados o
no versionados, relacionados con seguridad, evaluación y briefings; se
registraron sus hashes antes de editar para comprobar su preservación.

## Hallazgos y acciones

| Hallazgo | Acción |
| --- | --- |
| README exterior v0.3 e interior v1.0.2 frente a base Git v1.0.6 | Entrada exterior orientada al workspace y estado centralizado en el README interior. |
| Confusión entre raíz del entorno y raíz Git | Guías con rutas relativas y directorio de ejecución explícito. |
| README del agente con alcance y árbol v0.6 obsoletos | Mapa actualizado y enlace al experimento histórico. |
| README RAG describía exclusiones v0.4/v0.5 como alcance general | Baseline histórico identificado y enlazado a integraciones posteriores. |
| Guía Compose omitía servicios declarados | Lista alineada con los siete servicios del archivo de configuración. |
| Título del catálogo decía 20 responsabilidades y contenía 24 | Título sin contador duplicado y búsqueda alineada con el grafo. |
| Ausencia de entrada LLM portable e inventario de navegación | README.LLM, AGENTS interior, llms.txt e índice JSON reproducible. |

Los documentos históricos y ADRs conservan su ubicación. Los cambios de
seguridad preexistentes no se incorporan como resultados de esta revisión.
El briefing existente figura como snapshot en el índice, no como fuente de
instrucciones ni prueba de ejecución. No se modificaron configuraciones de
OpenCode, modelos, dependencias bancarias ni hitos de aplicación.

## Validación

Resultados ejecutados el 2026-09-15:

| Comprobación | Resultado observado |
| --- | --- |
| `python -B scripts/documentation_index.py --write` | PASS; 2 índices generados y 131 rutas Markdown seleccionadas. |
| `python -B scripts/documentation_index.py --check` | PASS; índices sincronizados y destinos locales válidos. |
| `python -B -m unittest discover -s scripts -p test_documentation_index.py -v` | PASS; 7 pruebas de exclusión, Git ignore, clasificación, rutas, primera generación y detección de desfase. |
| Ruff check y format --check sobre los 2 scripts nuevos | PASS. |
| `git diff --check` | PASS tras corregir whitespace de los README. |
| Hash SHA-256 de los 15 archivos preexistentes | Todos iguales al registro previo; ningún cambio ajeno sobrescrito. |
| Enlaces de README, README.LLM y llms.txt exteriores | PASS; destinos locales existentes. |
| Índice JSON | Parseo correcto, rutas documentales únicas y todos los destinos existentes. |
| SessionGuard | Bloqueo anterior archivado tras confirmación del usuario; bloqueo propio adquirido y verificado. |

La primera generación detectó que los enlaces a índices aún inexistentes
necesitaban resolverse contra las salidas previstas. Se corrigió y se añadió
una prueba de regresión. El índice excluye Markdown dentro de datos, entornos,
informes generados y otras carpetas locales: 131 es el conjunto seleccionado,
no el total bruto de Markdown del checkout.

El workspace exterior no es Git: sus cambios se verificaron directamente.
No se creó commit ni se hizo push. La evidencia temporal de hashes y el
bloqueo archivado permanecen en la carpeta local ignorada `.coordination/`.

## Límites

La revisión de enlaces cubre destinos locales Markdown inline, no anclas ni
URLs remotas. La clasificación del inventario es por carpeta: no certifica
la actualidad de cada frase. Los números de versión de paquetes e imágenes
se conservaron porque tienen ciclos propios. CI remota, modelos, contenedores,
pruebas bancarias y despliegues no se ejecutaron en esta tarea documental.
