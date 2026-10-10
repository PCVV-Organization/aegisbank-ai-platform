# Operations

Procedures for diagnosing failures. Confirm the environment and permissions before commands that alter services or data.

## How to use this directory

Read the relevant procedure and verify its date, status, prerequisites, and target environment. A runbook documents a procedure; it does not authorize execution or prove that execution occurred.

## Documents

- [Local environment configuration](LOCAL-ENVIRONMENT-CONFIGURATION.md) — dotenv file locations, precedence, Git exclusions, Docker Compose boundaries, and cloud rules
- [Kubernetes troubleshooting](KUBERNETES-TROUBLESHOOTING.md)
- [Production configuration, secrets, and identity audit prompt (English, canonical for LLM use)](production-configuration-secrets-identity-audit-prompt.en.md) — read-only discovery prompt; planning only
- [Spanish source prompt](production-configuration-secrets-identity-audit-prompt.md) — retained for provenance; prefer the English version for LLM use
- [Production configuration, secrets, and identity audit — English summary](production-configuration-secrets-identity-audit.en.md) — dated read-only findings; superseded where later evidence exists
- [Detailed Spanish audit source](production-configuration-secrets-identity-audit.md) — full historical variable inventory and questionnaire; reconcile with current source
- [Azure staging runbook](AZURE-STAGING-RUNBOOK.md) — reviewed promotion and rollback sequence, not cloud execution evidence
- [RBAC least-privilege matrix](RBAC-LEAST-PRIVILEGE-MATRIX.md) — documented roles, not an assignment record
- [Staging acceptance runbook](STAGING-ACCEPTANCE-RUNBOOK.md) — criteria to execute only after authorized provisioning
- [Production deployment runbook](PRODUCTION-DEPLOYMENT-RUNBOOK.md) — procedure does not authorize deployment
- [Identity troubleshooting guide](IDENTITY-TROUBLESHOOTING.md)
- [Production foundation implementation report](PRODUCTION-FOUNDATION-IMPLEMENTATION-REPORT.md) — reported Azure staging configuration and foundation; verify against current evidence

## Maintenance

Add new documents to this index and link replacements when decisions change. Regenerate navigation indexes from the application root. See the [documentation system](../engineering/DOCUMENTATION-SYSTEM.md) and [project portal](../README.md).
