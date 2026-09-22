# Mantenimiento de documentación y contexto para LLMs

## Distribución

- README: propósito, estado y enlaces para personas.
- README.LLM: resolución de raíz, autoridad, lectura por tarea y límites.
- AGENTS: instrucciones de trabajo; no duplicar el catálogo técnico.
- llms.txt: selección breve generada de puntos de entrada.
- project-index.json: inventario generado para herramientas.
- llms-full.txt: contenido de guías seleccionadas explícitamente, con fuente.
- docs/DIRECTORY-MAP.md: inventario por carpeta y responsabilidad.
- docs/navigation.json: fuentes permitidas del contexto ampliado y áreas.
- docs/README: portal temático completo.
- README de componente: uso local y alcance de ese módulo; fechar baselines antiguos.
- Evidencia en docs/quality o docs/releases; salidas nuevas en reports.
- ADRs y experimentos conservan su historia; no moverlos para ordenar visualmente.

## Actualización

Desde la raíz Git de la aplicación, con bloqueo de escritor adquirido:

```powershell
python -B scripts/documentation_index.py --write
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
git diff --check
git status --short
```

El generador usa solo la biblioteca estándar de Python y Git. Obtiene las rutas
Markdown versionadas y no ignoradas, excluye contexto local generado y privado,
ordena el inventario y verifica los puntos de entrada y componentes.
Los índices usan rutas; llms-full.txt incorpora únicamente las guías declaradas
en docs/navigation.json. No lee secretos ni concatena datasets o informes.

Las selecciones de entrada y categorías se mantienen en
[scripts/documentation_index.py](../../scripts/documentation_index.py).
Si añades, eliminas o cambias rutas o guías, regenera los cuatro derivados.
`--check` es de solo lectura: detecta diferencias y termina con código distinto
de cero ante índices obsoletos, rutas ausentes o enlaces locales rotos.

El control de enlaces cubre destinos locales de enlaces Markdown inline,
incluidos directorios. No valida anclas, URLs remotas, HTML ni enlaces por
referencia. Un PASS documental no demuestra comportamiento de la aplicación.

## Vigencia

El estado técnico se obtiene de Git y se resume en el README de la aplicación.
No duplicar tablas de versiones en el workspace exterior. Mantener citas
fechadas en los informes históricos y distinguir cambios sin commit de releases.
No cambiar versiones de paquetes ni publicar tags para una limpieza documental.

## Dos niveles del workspace

La carpeta exterior tiene un README y enlaces de acceso al repositorio interior.
Sus instrucciones se mantienen en su AGENTS y contrato de orquestación.
No copiar el entorno exterior dentro de la aplicación. El índice de aplicación
usa rutas relativas y funciona en un clon independiente.

Ai-env dispone de su propio generador independiente:
`python -B .ai-env/build_docs.py --write` y después `--check` desde su raíz.
El [sistema documental](DOCUMENTATION-SYSTEM.md) define la evolución por tipo de cambio.
