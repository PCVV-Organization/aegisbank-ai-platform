# Local Container Lab

Prerequisite: Docker Desktop Linux containers. Supply a synthetic password only in the
shell, for example `$env:MSSQL_SA_PASSWORD='AegisBankLocal!2026'`; never commit it.

```powershell
docker compose -f deploy/local/docker-compose.yml config
docker compose -f deploy/local/docker-compose.yml up -d --build
docker compose -f deploy/local/docker-compose.yml ps
docker compose -f deploy/local/docker-compose.yml down
```

The stack contains Core Banking, SQL Server Linux and the official Microsoft Service Bus
emulator. Foundry Local stays on the host. The image is tagged
`aegisbank/mock-core-banking:0.11.0`; no image is pushed to a registry.
