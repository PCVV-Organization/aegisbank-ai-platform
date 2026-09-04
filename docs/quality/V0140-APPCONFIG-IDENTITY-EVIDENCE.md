# AegisBank — v0.14.0 Configuration, Secrets & Workload Identity Evidence

> **Milestone:** `v0.14.0 — Configuration, Secrets & Workload Identity Foundation`
> **Status:** `PASS` (Local Laboratory Verified)
> **Date:** 2026-09-04
> **Canonical Package:** `aegisbank_agent.configuration`
> **Architecture Decision Record:** [ADR-029](../architecture/adr/ADR-029-configuration-secrets-identity-boundary.md)
> **Evidence Report:** [`reports/appconfig_emulator_evidence.json`](../../reports/appconfig_emulator_evidence.json)

---

## 1. Executive Summary & Core Principle

In production banking systems, **Configuration** and **Secrets** have completely different access controls, lifecycle cadences, auditing requirements, and blast radiuses:

$$\text{CONFIGURATION} \neq \text{SECRET}$$

| Dimension | Configuration (`ConfigurationProvider`) | Secrets (`SecretProvider`) |
|---|---|---|
| **Purpose** | Operational behavior tuning (e.g. `rag.top_k=5`, `agent_write_enabled=false`) | Sensitive authentication materials (passwords, tokens, API keys, private keys) |
| **Local Laboratory** | Microsoft Azure App Configuration Emulator `1.2.0` | In-memory synthetic secrets (`LocalSyntheticSecretProvider`) |
| **Cloud Runtime** | Azure App Configuration | Azure Key Vault |
| **Cloud Identity** | Managed Identity (`App Configuration Data Reader`) | Managed Identity (`Key Vault Secrets User`) |
| **Audit & Redaction** | Safe to log in configuration summaries and telemetry | **NEVER** logged, redacted across all loggers, traces, and metrics |
| **Maturity Tag** | `LOCAL-APPCONFIG-COVERED` / `CLOUD-APPCONFIG-PENDING` | `LOCAL-SECRETS-COVERED` / `CLOUD-KEYVAULT-PENDING` |

Zero real credentials or cloud resources were created during this milestone. Real Azure Key Vault, Managed Identity, and Microsoft Entra ID are classified strictly as `CLOUD-PENDING`.

---

## 2. Pinned OCI Infrastructure & Port Mapping

The Microsoft Azure App Configuration Emulator is pinned to an exact release and sha256 digest in [`deploy/local/docker-compose.yml`](../../deploy/local/docker-compose.yml):

```yaml
app-configuration-emulator:
  profiles: ["config", "all"]
  image: mcr.microsoft.com/azure-app-configuration/app-configuration-emulator:1.2.0@sha256:f84ca52fcf51aab3bad8a0363198c161e8a79eb41712d27779f6e0eb777c7000
  container_name: aegisbank-app-configuration-emulator
  restart: unless-stopped
  ports:
    - "127.0.0.1:8483:8483"
  environment:
    Tenant:AnonymousAuthEnabled: "true"
    Authentication:Anonymous:AnonymousUserRole: "Owner"
  networks:
    - aegisbank-net
  healthcheck:
    test: ["CMD-SHELL", "curl -f http://127.0.0.1:8483/health || exit 1"]
    interval: 5s
    timeout: 3s
    retries: 10
    start_period: 10s
```

* **Healthcheck Endpoint:** `GET http://127.0.0.1:8483/health` -> HTTP 200 `Healthy`.
* **REST API:** Standard Azure App Configuration REST API `/kv`, `/labels`, `/locks`, `/revisions`.

---

## 3. Canonical Architecture & Component Inventory

The canonical implementation lives in `ai/agent/src/aegisbank_agent/configuration/`:

```
ai/agent/src/aegisbank_agent/configuration/
├── __init__.py           # Re-exports contracts, providers, errors, resolvers
├── config.py             # ConfigurationProvider protocol, AppConfigurationEmulatorProvider, EnvironmentConfigurationProvider
└── secrets.py            # SecretProvider protocol, LocalSyntheticSecretProvider, AzureKeyVaultSecretProvider, KeyVaultReferenceResolver
```

### Component Mapping

1. **`ConfigurationProvider` (Protocol):**
   - Methods: `get(key)`, `get_optional(key)`, `require(key)`, `current_label()`, `refresh()`, `describe(key)`.
   - Coercion utilities: `coerce_int`, `coerce_float`, `coerce_bool`, `coerce_json`. Fail-fast on invalid types via `InvalidConfigurationValue`.
2. **`AppConfigurationEmulatorProvider`:**
   - Communicates with the local container over HTTP on port 8483.
   - Isolates configuration sets using Azure labels (e.g. `local`, `production`, `canary`).
   - Supports feature flags via official schema (`.appconfig.featureflag/{id}`).
   - Supports dynamic refresh: reads are cached in memory; `refresh()` polls changes from the store.
3. **`SecretProvider` (Protocol):**
   - Methods: `get(name)`, `get_optional(name)`, `require(name)`, `describe(name)`.
   - `LocalSyntheticSecretProvider`: In-memory synthetic secret dictionary for test isolation.
   - `AzureKeyVaultSecretProvider`: Cloud adapter wrapping Azure SDK `SecretClient` with structured error mapping (`MissingSecret`, `SecretAccessDenied`). Tagged `CLOUD-KEYVAULT-PENDING`.
4. **`KeyVaultReferenceResolver`:**
   - Implements official Microsoft Key Vault Reference format:
     `{"uri": "https://<vault-name>.vault.azure.net/secrets/<secret-name>[/<version>]"}`
   - Content-Type: `application/vnd.microsoft.appconfig.keyvaultref+json;charset=utf-8`.
   - Parses the vault URI and resolves the underlying secret through the authorized `SecretProvider`.
   - Plaintext secrets are never stored in App Configuration.

---

## 4. Workload Identity & Cloud Architecture Design (AI-200)

### 4.1 Microsoft Entra ID & Managed Identity

In traditional cloud deployments, applications stored service principal credentials (`client_id` and `client_secret`) in environment variables or configuration files. This created secret-sprawl vulnerabilities.

In Azure:
- **Managed Identity (Identidad Administrada):** Azure automatically injects an identity into the host runtime (Azure App Service, Azure Functions, Azure Container Apps, or VM) backed by Microsoft Entra ID.
  - **System-Assigned:** Tied directly to the lifecycle of the Azure resource. Deleted when the resource is deleted.
  - **User-Assigned:** Independent Azure resource with its own lifecycle, shared across multiple instances of a service.
- **`DefaultAzureCredential`:** The Azure SDK credential pipeline attempts authentication in an ordered, deterministic sequence:
  1. Environment (`AZURE_CLIENT_ID`, `AZURE_TENANT_ID`, `AZURE_CLIENT_SECRET`)
  2. Workload Identity (Kubernetes OIDC federated tokens)
  3. Managed Identity (Azure IMDS endpoint `http://169.254.169.254/metadata/identity/oauth2/token`)
  4. Developer tooling (Azure CLI, Azure PowerShell, Visual Studio Code)

### 4.2 RBAC Least-Privilege Mapping

Azure implements a strict division between the **Control Plane** (ARM management) and the **Data Plane** (accessing keys and secrets):

```
                                  [ MICROSOFT ENTRA ID ]
                                             │
                                   (Managed Identity)
                                             │
                       ┌─────────────────────┴─────────────────────┐
                       ▼                                           ▼
          [ Azure App Configuration ]                    [ Azure Key Vault ]
        Role: App Configuration Data Reader          Role: Key Vault Secrets User
        Actions:                                     Actions:
        - Microsoft.AppConfiguration/                - Microsoft.KeyVault/vaults/
          configurationStores/keyValues/read           secrets/getSecret/action
```

* **Violation:** Assigning `Contributor` or `Owner` at the resource group level violates least privilege by granting control-plane delete/write access.
* **Banking Standard:** Workload identities are granted solely Data Plane read roles:
  - `App Configuration Data Reader` on the App Configuration store.
  - `Key Vault Secrets User` on the Key Vault instance (or scoped to specific secret paths).

### 4.3 Secret Rotation & Resiliency

1. **Versioning in Key Vault:** Each secret modification generates a new 32-character hex version identifier.
2. **Key Vault References in App Configuration:**
   - Unversioned reference: `https://<vault>.vault.azure.net/secrets/<name>` resolves to the latest secret version.
   - Versioned reference: `https://<vault>.vault.azure.net/secrets/<name>/<version>` pins an immutable version for canary testing.
3. **Cache Invalidation & Rotation Cadence:**
   - Applications configure a Sentinel Key (e.g. `App:Configuration:Sentinel`) in App Configuration.
   - When secrets rotate in Key Vault, the operator bumps the sentinel key revision.
   - App Configuration triggers dynamic refresh without application restart or downtime.

---

## 5. Verification Evidence & Test Results

### 5.1 Automated Test Execution

```powershell
.venv\Scripts\python.exe -m pytest ai/agent/tests/unit/configuration/ ai/agent/tests/infra/appconfig/ -v
```

```
============================= test session starts =============================
platform win32 -- Python 3.14.4, pytest-9.1.1, pluggy-1.6.0
collected 17 items

ai\agent\tests\unit\configuration\test_keyvault_references.py::test_keyvault_reference_resolver_json_payload PASSED [  5%]
ai\agent\tests\unit\configuration\test_keyvault_references.py::test_keyvault_reference_resolver_raw_versioned_uri PASSED [ 11%]
ai\agent\tests\unit\configuration\test_keyvault_references.py::test_keyvault_reference_resolver_malformed_formats PASSED [ 17%]
ai\agent\tests\unit\configuration\test_keyvault_references.py::test_keyvault_reference_resolver_missing_secret PASSED [ 23%]
ai\agent\tests\unit\configuration\test_azure_keyvault_provider_access_denied_mapping PASSED [ 29%]
ai\agent\tests\unit\configuration\test_azure_keyvault_provider_not_found_mapping PASSED [ 35%]
ai\agent\tests\unit\configuration\test_default_secret_provider_lifecycle PASSED [ 41%]
ai\agent\tests\unit\configuration\test_providers.py::test_environment_provider_is_fail_fast PASSED [ 47%]
ai\agent\tests\unit\configuration\test_providers.py::test_emulator_provider_reads_label_and_refreshes PASSED [ 52%]
ai\agent\tests\unit\configuration\test_providers.py::test_local_secret_provider_is_separate_and_synthetic PASSED [ 58%]
ai\agent\tests\unit\configuration\test_providers.py::test_key_vault_adapter_matches_secret_client_contract PASSED [ 64%]
ai\agent\tests\unit\configuration\test_providers.py::test_invalid_boolean_fails_fast PASSED [ 70%]
ai\agent\tests\infra\appconfig\test_appconfig_emulator_e2e.py::test_appconfig_emulator_kv_lifecycle_and_labels PASSED [ 76%]
ai\agent\tests\infra\appconfig\test_appconfig_emulator_e2e.py::test_appconfig_emulator_feature_flags PASSED [ 82%]
ai\agent\tests\infra\appconfig\test_appconfig_emulator_e2e.py::test_appconfig_emulator_keyvault_reference_resolution PASSED [ 88%]
ai\agent\tests\infra\appconfig\test_appconfig_emulator_e2e.py::test_appconfig_emulator_dynamic_refresh PASSED [ 94%]
ai\agent\tests\infra\appconfig\test_appconfig_emulator_e2e.py::test_appconfig_emulator_missing_key_fails_fast PASSED [100%]

============================= 17 passed in 0.26s ==============================
```

### 5.2 Live Acceptance Script Output

```powershell
.venv\Scripts\python.exe scripts/appconfig_emulator_acceptance.py
```

```
======================================================================
AegisBank v0.14.0 — Azure App Configuration Emulator Acceptance
======================================================================
[*] App Configuration Emulator is healthy.
  [✓] Step 1: Health check passed (HTTP 200 Healthy)
  [✓] Step 2: Multi-environment label isolation verified (local=10, prod=5)
  [✓] Step 3: Feature Flag stored and verified (.appconfig.featureflag/agent_write_enabled)
  [✓] Step 4: Key Vault reference stored and resolved safely without plaintext in config
  [✓] Step 5: Dynamic config refresh & cache isolation verified
  [✓] Step 6: Fail-fast on missing key verified
  [✓] Step 7: Secret hygiene assertion verified across 7 keys

======================================================================
[+] ACCEPTANCE COMPLETED: PASS
[+] Evidence report written to: C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform\reports\appconfig_emulator_evidence.json
======================================================================
```

---

## 6. Official Maturity Tags

| Capability | Maturity Status | Notes |
|---|---|---|
| Azure App Configuration REST API & Keys | `LOCAL-APPCONFIG-COVERED` | Verified against official Microsoft container emulator `1.2.0` |
| Azure App Configuration Labels & Refresh | `LOCAL-APPCONFIG-COVERED` | Verified with label isolation (`local` vs `production`) |
| Azure Feature Flags Schema | `LOCAL-APPCONFIG-COVERED` | Verified with `.appconfig.featureflag/*` content-type |
| Key Vault References Pattern | `LOCAL-APPCONFIG-COVERED` | Stored as reference JSON; resolved via `KeyVaultReferenceResolver` |
| Synthetic Secret Store | `LOCAL-SECRETS-COVERED` | Synthetic in-memory store for unit and acceptance tests |
| Azure Key Vault Adapter Contract | `LOCAL-SECRETS-COVERED` | Contract-tested against Azure SDK `SecretClient` |
| Real Azure App Configuration Cloud | `CLOUD-APPCONFIG-PENDING` | Requires Azure subscription and deployment approval |
| Real Azure Key Vault Cloud | `CLOUD-KEYVAULT-PENDING` | No cloud resources created in local lab |
| Microsoft Entra ID & Managed Identity | `MANAGED-IDENTITY-CLOUD-PENDING` | Architecture documented; cloud deployment pending |
| `DefaultAzureCredential` Local Chain | `DEFAULT-AZURE-CREDENTIAL-LOCAL-COVERED`| Standard credential interface compatible with local and cloud |
