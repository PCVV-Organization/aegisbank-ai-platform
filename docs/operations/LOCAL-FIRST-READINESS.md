# Local-First Readiness

This document records the gate for Azure preparation. Azure remains **ready but
not deployed** until a separate, explicit staging authorization is granted.

## Required local evidence

Run these commands from the repository root with the project virtual
environment active:

```powershell
.venv\Scripts\python.exe -B scripts\quality_gate.py
python -B scripts\documentation_index.py --check
az bicep build --file deploy\azure\main.bicep --stdout
git diff --check
```

The quality gate includes linting, formatting, bytecode compilation, core
banking tests, ML tests, RAG tests, agent unit/integration/contract tests,
evaluation, SAST, SCA, architecture inventory, secret scanning, and whitespace
validation. A local pass is evidence for this checkout only; it is not Azure
staging acceptance.

## Local boundary

- Tests use synthetic fixtures, local persistence, emulators, or in-memory
  adapters.
- Local execution must not require Azure credentials, network access to Azure,
  or cloud-hosted data.
- `.env` and `.env.local` remain ignored. Commit only non-secret placeholders in
  `.env.example`.
- Production and staging identity paths must fail closed when managed identity
  configuration is missing.

## Staging promotion gate

After the local gate is green, create a dedicated preparation PR. Do not deploy
from that PR. A separately authorized staging change must:

1. Review the exact Bicep parameters and target resource group.
2. Confirm workload identity, least-privilege roles, secret references, and
   redacted observability settings.
3. Deploy only to an isolated staging resource group.
4. Run the staging smoke and acceptance suites.
5. Record the immutable image digest, test evidence, operator, and rollback
   target in the staging acceptance runbook.
6. Make an explicit Go/No-Go decision before any production discussion.

See [Azure staging runbook](AZURE-STAGING-RUNBOOK.md), [staging acceptance
runbook](STAGING-ACCEPTANCE-RUNBOOK.md), and [rollback procedure](runbooks/rollback.md).

## Current limits

Static Bicep compilation does not prove that Azure resources exist or that
runtime identity and network access work. No Azure resource provisioning or
deployment is authorized by this document.
