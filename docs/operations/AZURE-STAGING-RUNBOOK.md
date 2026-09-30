# Runbook de promoción a Azure staging

> **Estado:** `READY-FOR-REVIEW` · no ejecutado contra Azure.

## Precondiciones

1. La rama y la imagen inmutable fueron revisadas y las validaciones locales están
   verdes con la `.venv` del repositorio.
2. Existe un grupo de recursos aislado de staging y una identidad asignada al
   workload. No reutilizar recursos, stores ni vaults de producción.
3. Un responsable de plataforma prepara la federated credential GitHub OIDC y las
   asignaciones RBAC de la matriz de arquitectura. No crear credenciales cliente.
4. App Configuration contiene solo configuración no secreta por label `staging`.
   Key Vault contiene únicamente secretos que no puedan eliminarse mediante Entra.
5. Se completó una revisión humana de endpoints, redes privadas, ingress, límites
   de cómputo, retención, alertas, backups y el contrato de Core Banking.

## Validación antes de desplegar

```powershell
Set-Location C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform
az bicep build --file deploy/azure/main.bicep --stdout > $null
& .\.venv\Scripts\python.exe -m pytest -c ai/agent/pyproject.toml ai/agent/tests/unit/configuration ai/agent/tests/unit/reliability/test_azure_identity_adapters.py -q
& .\.venv\Scripts\python.exe scripts\quality_gate.py --fast
```

El último comando depende de que la `.venv` tenga todos los paquetes editables
instalados. Si falla por un módulo ausente, corregir el entorno de pruebas antes
de interpretar el fallo como evidencia de aplicación.

## Promoción controlada

1. Revisar manualmente el plan de IaC con el scope de staging correcto.
2. Desplegar primero la fundación y verificar desde logs redacted que
   `AEGISBANK_ENV=staging` selecciona App Configuration, Key Vault, Service Bus
   y Cosmos sin connection strings ni endpoints loopback.
3. Ejecutar solo journeys sintéticos de lectura y un journey de escritura que
   solicite y reciba aprobación humana explícita.
4. Verificar autorización de propietario, correlación, timeout, RAG con citas y
   ausencia de secretos en logs, auditoría y telemetría.
5. Registrar versiones de imagen, Bicep, configuración label y evidencia en un
   informe fechado. No actualizar el estado a cloud-validado sin esa evidencia.

## Rollback

1. Detener la promoción y bloquear nuevas escrituras de negocio con el control
   HITL existente.
2. Revertir la revisión de aplicación o imagen al digest anterior probado; no
   modificar secretos para ocultar un fallo.
3. Restaurar la configuración no secreta con una revisión aprobada de App
   Configuration y mantener auditoría de quién autorizó el rollback.
4. Si hay riesgo de exposición, revocar permisos de la identidad y rotar el
   secreto afectado en Key Vault. Documentar el incidente sin copiar secretos.

## Límites explícitos

No existe despliegue cloud ejecutado, modelo Foundry cloud, autenticación de
servicio Core Banking real, migración de datos, prueba de carga, SLA, multi-región
ni certificación regulatoria. AegisBank conserva datos sintéticos y no procesa
dinero real.
