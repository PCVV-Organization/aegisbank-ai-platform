# Azure Staging Promotion Runbook

> **Status:** `READY-FOR-REVIEW`; not executed against Azure.
>
> This runbook describes a gated procedure. It does not authorize provisioning or deployment. The project requires explicit approval before creating paid Azure resources or deploying.

## Preconditions

1. Review the branch and immutable image; all local validations must pass in the repository virtual environment.
2. Use an isolated staging resource group and workload identity. Do not reuse production resources, stores, or vaults.
3. A platform owner prepares the GitHub OIDC federated credential and RBAC assignments from the architecture matrix. Do not create client secrets.
4. App Configuration contains non-secret settings under the `staging` label. Key Vault contains only secrets that cannot be eliminated through Entra ID.
5. Complete human review of endpoints, private networking, ingress, compute limits, retention, alerts, backups, and the Core Banking contract.
6. The manual workflow receives an existing isolated resource group and immutable
   agent and mock-core-banking image references. `latest` tags are rejected.
7. The protected `staging` environment contains `AZURE_CLIENT_ID`,
   `AZURE_TENANT_ID`, and `AZURE_SUBSCRIPTION_ID` variables for OIDC. No client
   secret is configured.

## Pre-deployment Validation

Run from the application Git root:

```powershell
Set-Location C:\aegisbank-ai-platform-ai-env\aegisbank-ai-platform
az bicep build --file deploy/azure/main.bicep --stdout > $null
& .\.venv\Scripts\python.exe -m pytest -c ai/agent/pyproject.toml ai/agent/tests/unit/configuration ai/agent/tests/unit/reliability/test_azure_identity_adapters.py -q
& .\.venv\Scripts\python.exe scripts\quality_gate.py --fast
```

The final command requires all editable packages to be installed in `.venv`. If it fails because a module is missing, repair the test environment before interpreting the failure as application evidence.

## Controlled Promotion

1. Manually review the infrastructure-as-code plan with the correct staging scope.
   The workflow runs `az deployment group what-if` before the deployment command.
2. Deploy the foundation only after approval. Verify redacted logs show `AEGISBANK_ENV=staging` selecting App Configuration, Key Vault, Service Bus, and Cosmos without connection strings or loopback endpoints.
3. Run synthetic read journeys and one write journey that requests and receives explicit human approval.
4. Verify ownership authorization, correlation, timeout behavior, cited RAG responses, and absence of secrets in logs, audit records, and telemetry.
5. Record image and Bicep versions, configuration label, and evidence in a dated report. Do not mark cloud validation complete without that evidence.

## Rollback

1. Stop promotion and block new business writes using the existing HITL control.
2. Revert the application revision or image to the previously tested digest. Do not alter secrets to conceal a failure.
3. Restore non-secret configuration from an approved App Configuration revision and retain an audit record of who authorized the rollback.
4. If exposure is suspected, revoke the identity's permissions and rotate the affected Key Vault secret. Document the incident without copying secrets.

## Explicit Limitations

This document does not prove a cloud deployment, cloud Foundry model, real Core Banking service authentication, data migration, load test, SLA, multi-region operation, or regulatory certification. AegisBank uses synthetic data and does not process real money.
