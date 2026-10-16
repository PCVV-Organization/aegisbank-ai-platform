# Synthetic customer authentication in Azure for Students

The staging laboratory uses the `synthetic-password` provider because the
current Azure for Students region policy rejects the Microsoft Entra External
ID `ciamDirectories` resource. This provider is for synthetic staging only; it
is not a production banking identity service.

The API stores password hashes, opaque session hashes, and throttling records in
the pre-provisioned Cosmos DB container `aegisbank-auth/identities`. The browser
keeps the short-lived bearer token in memory and does not use `localStorage`.

## Provision a synthetic user

Run from the agent package with staging configuration already available. The
password is prompted interactively and is never supplied as a command argument:

```powershell
python -m aegisbank_agent.auth_admin create-user `
  --dni 12345678 `
  --customer-id CUST-0001
```

Only synthetic `CUST-####` identifiers are accepted. There is no public
registration endpoint. Password rotation requires the explicit `--rotate` flag
and revokes existing sessions through the account epoch.

## Required hosted settings

```text
AEGISBANK_AUTH_MODE=synthetic-password
AEGISBANK_AUTH_COSMOS_ENDPOINT=https://aegisbankstagingcosmos.documents.azure.com:443/
AEGISBANK_AUTH_COSMOS_DATABASE=aegisbank-auth
AEGISBANK_AUTH_COSMOS_CONTAINER=identities
AEGISBANK_AUTH_SESSION_TTL_SECONDS=900
```

The Container App uses the user-assigned workload identity and a Cosmos data
plane role scoped to `/dbs/aegisbank-auth/colls/identities`. No Cosmos master
key is injected into the image or workflow.

## Acceptance checks

The staging acceptance journey is:

```text
login -> /api/v1/auth/me -> /api/v1/agent/run -> logout -> old token rejected
```

Acceptance remains incomplete until a synthetic user is provisioned and the
journey is executed against the deployed Static Web App and Agent API.
