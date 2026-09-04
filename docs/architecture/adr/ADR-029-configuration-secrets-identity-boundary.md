# ADR-029: Configuration, Secrets, and Workload Identity Boundary

- Status: Accepted for v0.14.0 local laboratory scope
- Date: 2026-09-04

## Context

Application configuration and secrets have different confidentiality, access,
refresh, and audit requirements. The project must demonstrate the distinction
without creating Azure resources or placing credentials in source control.

## Decision

Use the canonical `aegisbank_agent.configuration` package. Non-secret values
are read through `ConfigurationProvider`; local development uses the official
Azure App Configuration Emulator `1.2.0` with a pinned image digest and an
environment-provider fallback. Labels identify the local configuration set.

Secrets are read through the separate `SecretProvider` contract. Local tests
use only in-memory synthetic values. `AzureKeyVaultSecretProvider` is a
dependency-injected adapter for the Azure SDK `SecretClient`; real Key Vault,
Managed Identity, Microsoft Entra ID, and RBAC are `CLOUD-PENDING`.

Required values fail fast. Optional values are explicit. Secret values are
never included in configuration snapshots, logs, or audit payloads. The
emulator is local infrastructure only and is not treated as a Key Vault
substitute.

## Consequences

- Providers can be contract-tested without Azure access.
- App Configuration refresh and labels are available locally.
- Production identity must use `DefaultAzureCredential` and least-privilege
  RBAC assignments after cloud approval.
- Secret rotation and Azure Monitor evidence remain cloud-pending.

## Evidence

- `deploy/local/docker-compose.yml` pins the emulator image and digest.
- `ai/agent/src/aegisbank_agent/configuration/` contains both contracts.
- `ai/agent/tests/unit/configuration/test_providers.py` covers fail-fast,
  labels, refresh, synthetic secrets, and the Key Vault adapter contract.
