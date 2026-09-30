# 025 — AegisBank v0.13.1 Azure Functions Live Runtime E2E Acceptance

Continúa exclusivamente `v0.13.1 — Azure Functions Live Runtime E2E Acceptance` en `C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`.

Baseline esperado: `c3f57310d20f49d81cb4fbf32fe5aa64b4c630d7`, master y working tree limpio. Verifica Git y adquiere SessionGuard antes de WRITE.

Objetivo único: cerrar la evidencia runtime pendiente de v0.13 sin agregar features.

## 1. Diagnóstico READ-ONLY

- `where func`, `func --version`
- `where python`, `.venv\Scripts\python.exe -V`
- Capturar `sys.executable` y `PATH`
- Ejecutar `func start --verbose` desde el virtual environment oficial
- Capturar la causa exacta de `cygrpc`
- **No** asumir que es long-path sin evidencia

## 2. Reglas

- No modificar Registry, PATH global, Windows policy.
- No instalar herramientas automáticamente.

## 3. Paths

### A. Windows Core Tools E2E

```
CloudEvent
    ↓
Azure Functions Host (Windows)
    ↓
Python Worker
    ↓
Event Grid Trigger
    ↓
service_request_handler
    ↓
IdempotencyGuard
    ↓
Audit + Metrics + Trace
```

Enviar el CloudEvent sample al endpoint `/runtime/webhooks/eventgrid?functionName=...`. Verificar: trigger descubierto, Python worker iniciado, handler ejecutado, duplicate event idempotent, malformed/version incorrecta sin side effect, audit/metrics/trace presentes.

Si PASS → `WINDOWS_CORE_TOOLS_E2E=PASS`.

### B. Fallback Linux container (sólo si A falla por entorno Windows)

Imagen oficial: `mcr.microsoft.com/azure-functions/python:4-python3.14`. Registrar tag y digest real, ejecutar la misma Function App localmente en Docker y repetir el E2E.

Clasificar como `LOCAL_FUNCTIONS_RUNTIME_E2E=PASS/FAIL`. No es un "workaround falso": es el runtime oficial de Functions sobre Linux.

## 4. Restricciones

- TEST VALUE > TEST COUNT
- suite racionalizada preservada
- NEW TRUE_DUPLICATION = 0
- No Azure cloud
- No Azure CLI
- No v0.14
- No push
- No worktrees

## 5. Finalización

Commit: `fix(v0.13): validate Azure Functions runtime end to end`

Cerrar únicamente con `AEGISBANK_V0.13_FUNCTIONS_RUNTIME_E2E_READY`.
