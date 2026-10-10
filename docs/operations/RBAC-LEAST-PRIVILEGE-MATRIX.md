# Azure RBAC Least-Privilege Matrix (Microsoft Entra ID)

> **Status:** `DOCUMENTED_LEAST_PRIVILEGE`; `CLOUD_UNVALIDATED`.
> **Scope:** Azure staging and production runtime design for AegisBank AI Platform. Local development and automated tests use local trust or emulators, not Azure RBAC.
>
> This is a proposed/documented role model, not evidence that roles or identities have been assigned in Azure.

## 1. Separation Principles

1. **Separate identities:** The GitHub Actions deployment identity and runtime workload managed identities are independent.
2. **No generic runtime roles:** Application runtimes must not receive broad roles such as `Owner`, `Contributor`, or `User Access Administrator`.
3. **Prefer passwordless data-plane access:** Prefer narrowly scoped data-plane roles (`Data Reader`, `Data Receiver/Sender`, `Secrets User`) over static credentials or connection strings.

## 2. Workload Identity Inventory

| Identity | Type | Purpose | Responsibility |
|---|---|---|---|
| `id-aegisbank-<env>-workload` | User-assigned managed identity | Container Apps agent/API | Configuration, unavoidable secrets, and messaging access. |
| `id-aegisbank-<env>-functions` | User-assigned managed identity | Azure Functions event consumer | Service Bus consumption and idempotency/outbox persistence. |
| `id-aegisbank-<env>-corebanking` | User-assigned managed identity | Mock Core Banking service, if hosted in cloud | Mock banking database isolation and secure endpoints. |
| `id-aegisbank-<env>-deployer` | Microsoft Entra app with federated OIDC | GitHub Actions pipeline | Declarative infrastructure deployment and Container Apps revision updates. |

## 3. Proposed Role Assignments

| Runtime identity | Azure resource | RBAC role | Access | Least-privilege rationale |
|---|---|---|---|---|
| Agent workload | Azure App Configuration | `App Configuration Data Reader` (`516239f1-63e1-4d78-a4de-a74fb236a071`) | Read-only | Reads runtime parameters filtered by label; no write permission. |
| Agent workload | Azure Key Vault | `Key Vault Secrets User` (`4633458b-17de-408a-b874-0445c86b69ea`) | Read-only | Resolves unavoidable secret references; no cryptographic key or certificate permissions. |
| Agent workload | Azure Service Bus | `Azure Service Bus Data Sender` (`69a216fc-b8fb-44d8-bc22-1f3c2cd27a39`) | Send-only | Sends authorized audit events and HITL-approved service requests to permitted queues/topics. |
| Agent workload | Azure Cosmos DB | `Cosmos DB Built-in Data Reader` (NoSQL data plane) | Read-only | Reads partitioned agent session state and events. |
| Agent workload | Azure AI Foundry / Azure OpenAI | `Cognitive Services OpenAI User` (`5e6ce059-de30-45e8-b8e7-e898950d9990`) | Inference | Uses Entra tokens for grounded chat completion (`phi-4-mini`) rather than static API keys. |
| Functions consumer | Azure Service Bus | `Azure Service Bus Data Receiver` (`4f6d3a01-b2a5-4e24-9d14-70f80761a4c6`) | Receive and settle | Receives, completes/abandons, or dead-letters service events. |
| Functions consumer | Azure Key Vault | `Key Vault Secrets User` | Read-only | Reads secrets required by external event integrations. |
| GitHub Actions deployer | Resource group `rg-aegisbank-<env>` | Scoped deployment role (`Deployment Operator` / ARM deployment) | Control plane | Creates or updates ARM/Bicep resources and Container Apps revisions; no banking-data or secret access. |

Validate role names, scopes, and permissions against current Azure documentation and the target environment before assignment. This matrix does not grant deployment approval.

## 4. Identity Audit and Revocation

1. **No secrets in Git:** Assigned identities must not have persisted passwords or client secrets.
2. **OIDC federation:** GitHub Actions should use temporary federated authentication with a subject restricted to the authorized branch/environment, for example:
   `repo:VegaValverde/aegisbank-ai-platform:environment:staging`
3. **Emergency revocation:** If compromise is suspected, remove the role assignment in Azure Portal or CLI. This changes cloud state and requires the appropriate operator authorization; it does not require rebuilding application code.

Example only; verify the exact principal, role, and scope before execution:

```bash
az role assignment delete --assignee <principal-id> --role "Key Vault Secrets User" --scope <vault-id>
```
