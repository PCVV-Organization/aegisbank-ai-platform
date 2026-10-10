# Production Deployment, Operations, and Promotion Runbook (Design Only)

> **Recorded classification:** `AZURE_DEPLOYMENT_PREPARED`; `CLOUD_UNVALIDATED`.
> **Scope:** Proposed procedures for promotion, operations, credential rotation, incidents, and rollback.
> **Product boundary:** AegisBank is an educational banking-AI laboratory, not a commercial bank; it does not process real money.
>
> **Critical:** This document is not deployment authorization or evidence of a production environment. No Azure resources may be provisioned and no deployment may be run without explicit approval. Validate every command, resource name, role, endpoint, configuration value, and rollback target against the authorized environment before use. Examples are not verified production settings.

## 1. Prerequisites for Any Future Promotion

1. The exact immutable image digest has documented `STAGING_ACCEPTED` evidence under the [staging acceptance runbook](STAGING-ACCEPTANCE-RUNBOOK.md).
2. An isolated, explicitly authorized production resource group and region exist; never reuse staging resources, stores, or vaults.
3. The base infrastructure template and production parameters have been reviewed for the approved target.
4. `id-aegisbank-production-workload` and least-privilege role assignments have been verified against the [RBAC matrix](RBAC-LEAST-PRIVILEGE-MATRIX.md).

These are proposed gates, not statements that they have been met.

## 2. Proposed Non-Secret Runtime Bootstrap Settings

The following names and values are documentation examples only; they have not been validated as live endpoints:

```bash
AEGISBANK_ENV=production
AEGISBANK_CONFIG_LABEL=production
AZURE_APPCONFIG_ENDPOINT=https://aegisbank-production-config.azconfig.io
AZURE_KEY_VAULT_URL=https://aegisbank-production-kv.vault.azure.net/
AEGISBANK_SERVICEBUS_NAMESPACE=aegisbank-production.servicebus.windows.net
AZURE_OPENAI_ENDPOINT=https://aegisbank-production-ai.cognitiveservices.azure.com/
AZURE_OPENAI_DEPLOYMENT_NAME=phi-4-mini
AZURE_OPENAI_API_VERSION=2024-10-21
```

Do not inject secrets, passwords, tokens, or access keys through environment variables. The proposed cloud design uses Microsoft Entra ID for Azure resource access; validate actual credential behavior before use.

## 3. Documented App Configuration Key Catalog

These values are illustrative defaults, not approved production configuration:

| Key | Type | Example | Description |
|---|---|---:|---|
| `AegisBank:Agent:MaxRounds` | int | `3` | Maximum tool rounds per invocation. |
| `AegisBank:Agent:TimeoutSeconds` | float | `45.0` | Agent invocation timeout. |
| `AegisBank:RAG:Retriever` | string | `hybrid_rrf` | Retrieval strategy. |
| `AegisBank:RAG:TopK` | int | `3` | Maximum corpus documents returned. |
| `AegisBank:RAG:CacheTtlSeconds` | int | `3600` | Document/embedding cache TTL. |
| `AegisBank:CoreBanking:TimeoutSeconds` | float | `5.0` | Core Banking service call timeout. |
| `AegisBank:Reliability:RetryCount` | int | `3` | Bounded retries for transient failures. |
| `AegisBank:Reliability:CircuitBreakerThreshold` | int | `5` | Consecutive failures before opening the circuit breaker. |
| `AegisBank:Observability:LogLevel` | string | `INFO` | Minimum structured log level. |
| `AegisBank:Observability:SamplingRatio` | float | `0.1` | OpenTelemetry distributed trace sampling ratio. |

## 4. Key Vault Secret Names (No Values)

The design limits Key Vault to unavoidable third-party secrets that cannot use Entra ID. The following names are illustrative and do not imply that secrets exist:

| Secret name | Intended purpose | Format |
|---|---|---|
| `external-sms-gateway-api-key` | Third-party SMS/OTP notification gateway | Alphanumeric token |
| `legacy-vendor-webhook-signing-key` | HMAC verification for external vendor webhooks | 256-bit hexadecimal value |

App Configuration may store `@Microsoft.KeyVault(SecretUri=...)` references to approved secret names. Never place secret values in this document.

## 5. Immutable Staging-to-Production Promotion (Proposed)

1. Do not rebuild the production image. Promote only the exact staging-accepted digest, for example `aegisbank-agent@sha256:<ACCEPTED_DIGEST>`.
2. An authorized operator must verify the account, subscription, resource group, app name, and digest before any update command. The original design's `az containerapp update` example is intentionally not repeated here because target details are unverified.
3. Validate `/health/live` and `/health/ready` only after an approved deployment, and record the exact revision and evidence.

## 6. Emergency Write Kill Switch (Proposed)

If a future authorized deployment exhibits anomalous model behavior, the design calls for a human-on-the-loop (HOTL) supervisor to disable mutations using the approved App Configuration feature flag or supervision endpoint.

The intended invariant is deterministic: state-changing requests such as `create_service_request` remain blocked regardless of LLM output, while approved read-only operations may continue if safe. Verify actual implementation before relying on this behavior. Any state change requires an authorized operator.

## 7. Rollback (Proposed)

1. An authorized operator may reactivate a previously verified healthy revision after confirming the exact target and impact.
2. Verify the selected revision returns `200 OK` from `/health/ready`.
3. Record the incident and post-mortem without exposing sensitive audit data.

No rollback command should be run from this design document without target-specific review and authorization.

## 8. Credential and Identity Rotation (Proposed)

1. Rotate unavoidable Key Vault secrets by creating an approved new version; verify whether consumers use a floating or pinned version and refresh behavior.
2. Rotate GitHub Actions OIDC federated credentials by updating the Entra service principal configuration.
3. Validate identity continuity, least privilege, and service health. Do not assume zero downtime without testing.

## 9. Explicit Limitations

- AegisBank is not a real bank; all data and customer identifiers (including `CUST-0001` through `CUST-0004`) are synthetic.
- No BCRP, Electronic Clearing House, or SWIFT settlement exists.
- No SBS or PCI-DSS certification/compliance is claimed.
- Cloud status remains unvalidated until authorized provisioning, execution, and evidence are completed.
