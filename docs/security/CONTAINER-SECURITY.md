# AegisBank — Container Security & Hardening Standards

> **Propósito:** Definir los controles de seguridad, directrices de endurecimiento (*hardening*) y análisis de riesgos para las imágenes y contenedores de AegisBank AI Platform.
> **Hito:** v0.11.0 — Containerization + Local Azure Messaging Foundation.

---

## 1. Controles Obligatorios de Endurecimiento en Contenedores

| Control de Seguridad | Implementación en AegisBank | Justificación y Riesgo Mitigado |
|---|---|---|
| **Ejecución como Usuario No-Root** | `USER 10001:10001` declarado en `services/mock-core-banking/Dockerfile`. | **Escape de Contenedor:** Si un atacante compromete la aplicación vía RCE, no obtiene privilegios de `root` en el host subyacente. |
| **Imagen Base Mínima** | `python:3.14-slim` como base compatible con el proyecto. | **Reducción de Superficie de Ataque:** Evita utilidades innecesarias en el runtime; el digest debe fijarse antes de un target cloud. |
| **Dependencias de Runtime** | La receta instala únicamente el wheel de Core Banking; no copia toolchain, tests ni caches. | **Aislamiento de Toolchain:** Mantiene fuera del artefacto el contenido no necesario para ejecutar la API. |
| **Exclusión de Secretos y Metadatos** | `.dockerignore` exhaustivo excluyendo `.git`, `.venv`, `.env*`, `*.db`, caches y llaves privadas. | **Fuga de Credenciales:** Garantiza que ningún secreto, token o historial de control de versiones sea horneado en las capas inmutables de la imagen. |
| **Aislamiento de Red** | Red explícita `aegisbank-net` (bridge local) con mapeo de puertos estricto (`8000:8000`, `5672:5672`). | **Exposición Indebida:** Evita que servicios internos (como la base de datos SQL del emulador en puerto 1433) sean accesibles fuera del entorno de desarrollo. |
| **Verificación Automatizada de Salud** | Directiva `HEALTHCHECK` consultando `/health/live`; Compose además consulta `/health/ready`. | **Degradación Silenciosa:** Permite al orquestador detectar fallos de servicio y reiniciar contenedores que no respondan. |
| **Permisos Mínimos de Sistema de Archivos** | El proceso usa UID 10001 y solo `/app/data` es writable mediante volumen; Compose usa filesystem raíz read-only. | **Tampering / Modificación de Binarios:** Previene que un proceso comprometido altere el código Python o las dependencias instaladas. |

---

## 2. Análisis de Seguridad: ¿Por qué un Contenedor NO es un Límite de Seguridad Perfecto?

> [!WARNING]
> Un contenedor proporciona **aislamiento de procesos y recursos**, **NO** una frontera de seguridad estanca equivalente a una máquina virtual con hipervisor hardware dedicado.

### Razones Técnicas:
1. **Kernel Compartido:**
   A diferencia de las máquinas virtuales, todos los contenedores comparten el mismo kernel del sistema operativo host (Linux kernel en WSL2 / Azure Linux). Una vulnerabilidad en una llamada al sistema (*syscall*) del kernel (e.g. *Dirty COW*, *Dirty Pipe*) puede permitir a un atacante escapar del contenedor y comprometer el host.
2. **Capacidades de Linux (*Capabilities*):**
   Si un contenedor se ejecuta en modo privilegiado (`--privileged`) o con capacidades como `CAP_SYS_ADMIN` o `CAP_NET_ADMIN`, puede eludir el aislamiento de *cgroups* y *namespaces*. En AegisBank está estrictamente prohibido el modo privilegiado.
3. **Acceso al Docker Socket:**
   Montar `/var/run/docker.sock` dentro de un contenedor otorga acceso de administrador total sobre el daemon de Docker, permitiendo instanciar contenedores con acceso root al sistema de archivos del host. AegisBank prohíbe el montaje del Docker socket en cualquier servicio.

---

## 3. Principio de Defensa en Profundidad (*Defense-in-Depth*)

Para compensar los límites del aislamiento de contenedores, AegisBank implementa múltiples capas de seguridad convergentes:

```mermaid
graph TD
    A["Capa 1: Static Code Analysis (Bandit SAST)"] --> B["Capa 2: Dependency Supply Chain (pip-audit SCA)"]
    B --> C["Capa 3: Non-Root Minimal Container Image"]
    C --> D["Capa 4: Deterministic Input Validation & Pydantic Schemas"]
    D --> E["Capa 5: Human-in-the-Loop (HITL) for State Changes"]
    E --> F["Capa 6: Immutable WORM Audit Logging"]
```
