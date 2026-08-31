# AegisBank Teaching Contract

> **Misión Pedagógica:** Cada informe, documento de diseño y código en AegisBank AI Platform es una clase magistral de nivel Maestría en Inteligencia Artificial para un profesional que aprende desde cero.

---

## 1. Obligación de Explicación de Conceptos y Siglas

Para **CADA** concepto nuevo, sigla o tecnología que se introduzca en el repositorio o se mencione en un informe, se debe documentar obligatoriamente:

1. **Sigla y Nombre Completo:** En su idioma original (usualmente inglés) y su **traducción al español**.
2. **Qué significa:** Definición conceptual rigurosa, clara y accesible.
3. **Cómo funciona internamente:** Mecanismo técnico, flujo de datos o modelo matemático subyacente.
4. **Qué problema resuelve y por qué AegisBank lo necesita:** Justificación bancaria y técnica específica.
5. **Ejemplo concreto en AegisBank:** Referencia directa a archivos, funciones o clases del repositorio.
6. **Alternativa principal y cuándo NO usarlo:** Cuándo otra tecnología o patrón es preferible.
7. **Errores típicos y riesgos:** Modos de fallo comunes si se implementa incorrectamente.
8. **Relación con el Puesto Mibanco (2026):** Mapeo a las competencias de Prompting, Evaluación, Agentic AI, DevSecOps o Calidad.
9. **Relación con Certificaciones Microsoft (AI-103 / AI-200):** Dominios de conocimiento del temario oficial de Microsoft Learn.
10. **Nivel de Cobertura y Madurez:** Clasificación explícita según el modelo de madurez de AegisBank.

---

## 2. Taxonomía de Estados de Cobertura y Evidencia

Para evitar reclamos falsos de certificación o producción, todo componente se clasifica estrictamente en uno de los siguientes estados:

* **`LAB-COVERED`**: Implementado, probado y verificado completamente en el laboratorio local con pruebas automatizadas reproducibles.
* **`CI-CONFIGURED` / `RUNNER-PENDING`**: Pipeline o configuración automatizada creada y validada sintácticamente, pero pendiente de ejecución verificable en un runner remoto (e.g. GitHub Actions).
* **`PROD-PARTIAL`**: Implementado conceptualmente y funcional en entorno local, pero requiere servicios distribuidos de nube (e.g. Azure Service Bus, Azure SQL Ledger, WORM Storage) para producción bancaria.
* **`CLOUD-PENDING`**: Planificado formalmente para fases futuras de despliegue en la nube (v0.11+).

---

## 3. Reglas Operativas Permanentes de Arquitectura y Concurrencia

### Regla A: DISCOVER BEFORE CREATE (Buscar antes de Crear)
Antes de crear cualquier nueva clase, función o módulo:
1. Buscar en el repositorio mediante herramientas de búsqueda (`grep_search` / `rg`).
2. Consultar el catálogo oficial en [`docs/architecture/CANONICAL-COMPONENTS.md`](file:///c:/aegisbank-ai-platform-ai-env/aegisbank-ai-platform/docs/architecture/CANONICAL-COMPONENTS.md).
3. Clasificar la decisión en una de tres opciones:
   - **`REUSE`**: Reutilizar el componente canónico existente.
   - **`EXTEND`**: Extender el componente canónico en su punto de extensión oficial.
   - **`NEW_COMPONENT_JUSTIFIED`**: Justificar por qué la responsabilidad es genuinamente nueva y no solapa nada existente.

### Regla B: ONE WRITER, MANY READERS (Un Escritor, Múltiples Lectores)
Para evitar condiciones de carrera entre sesiones de IA locales sobre el mismo working tree:
1. Cada sesión debe adquirir un bloqueo atómico exclusivo mediante `python scripts/session_guard.py acquire` antes de escribir.
2. Cada sesión debe validar su lock y rutas autorizadas con `python scripts/session_guard.py check` antes de modificar, stagear y commitear.
3. Al finalizar el commit, debe liberar el lock con `python scripts/session_guard.py release`.
4. El estado del lock reside exclusivamente en `.coordination/active-writer.json` (ignorado en `.gitignore`).

---

## 4. Principio de Evidencia Real (*Proof of Execution*)

* Nunca se reportará `PASS` basándose en la mera existencia de un archivo de configuración o código fuente.
* Todo `PASS` requiere la ejecución real del comando y la captura verificable de su salida con código de salida 0.
* Un archivo `.github/workflows/ci.yml` local es `CI-CONFIGURED`, **NUNCA** `CI-EXECUTED` sin evidencia del runner de GitHub.
