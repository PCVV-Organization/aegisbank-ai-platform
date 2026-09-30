# 026 — AegisBank v0.14.0 App Configuration + Identity/Secrets Boundary

Continúa exclusivamente `v0.14.0 — App Configuration + Identity/Secrets Boundary` en `C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform`.

Primero verifica `master`, `git rev-parse HEAD`, árbol limpio y SessionGuard; existen reportes contradictorios de hash v0.13.1, así que el HEAD real es el único baseline válido.

Aplica ONE WRITER MANY READERS, DISCOVER BEFORE CREATE y REUSE/EXTEND antes de crear componentes.

## Objetivo

Integrar el **Azure App Configuration Emulator** oficial local mediante Docker usando una versión exacta y reproducible.

## Reglas estrictas

1. **CONFIGURATION ≠ SECRET.**
   - App Configuration → comportamiento, feature flags, configuración.
   - Key Vault → secretos, passwords, tokens.
   - **Ningún password / token / API key puede almacenarse como App Configuration ordinaria.**

2. **REUSE / EXTEND primero.** Verificar si ya existe `ConfigurationProvider`, `SecretProvider`, `Settings`, `EnvSettings` o similar en el codebase. Si existe, extender. Si no, justificar el nuevo componente.

3. **Key Vault emulator local NO existe.** No fabricar Key Vault falso. Si hace falta `SecretProvider` local, usar implementación con secretos sintéticos/efímeros y **adapter contract-tested** para Azure Key Vault.

4. **Managed Identity / Key Vault reales = `CLOUD-PENDING`.** Documentar y probar `DefaultAzureCredential`, `TokenCredential`, Microsoft Entra ID, RBAC, secret rotation, least privilege — pero nunca afirmar cobertura cloud que no existe localmente.

5. **Demo real con App Configuration Emulator oficial:**
   - Imagen: `mcr.microsoft.com/azure-app-configuration/app-configuration-emulator:1.2.0`
   - Soporte para: keys, values, labels, locks, revisions, snapshots
   - Key/value, labels, refresh, versionado, fail-fast

6. Reutilizar:
   - OpenTelemetry tracing
   - Audit logger
   - Security gates
   - Secret Scan
   - Ruff + format + compileall

## Restricciones

- NO Azure cloud
- NO Azure CLI
- NO v0.15
- NO push
- NO worktrees
- NO `git add .` / `git add -A`
- Mantener TEST VALUE > TEST COUNT
- NEW TRUE_DUPLICATION = 0

## Finalización

Commit con mensaje describiendo el alcance del milestone.

Cerrar únicamente con `AEGISBANK_V0.14_CONFIG_IDENTITY_BOUNDARY_READY`.

## Tags de madurez a usar

- `LOCAL-APPCONFIG-COVERED` — emulator verificado
- `CLOUD-APPCONFIG-PENDING` — Azure real pendiente
- `LOCAL-SECRETS-COVERED` — secret provider local sintético verificado
- `CLOUD-KEYVAULT-PENDING` — Azure Key Vault real pendiente
- `MANAGED-IDENTITY-CLOUD-PENDING` — Managed Identity no reproducible localmente
- `DEFAULT-AZURE-CREDENTIAL-LOCAL-COVERED` — `DefaultAzureCredential` documentado con fallback a `AzureCliCredential` / `EnvironmentCredential`
