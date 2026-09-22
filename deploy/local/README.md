# Local Container Lab

Prerequisite: Docker Desktop Linux containers. Supply a synthetic password only in the
shell, for example `$env:MSSQL_SA_PASSWORD='AegisBankLocal!2026'`; never commit it.

```powershell
docker compose -f deploy/local/docker-compose.yml config
docker compose -f deploy/local/docker-compose.yml up -d --build
docker compose -f deploy/local/docker-compose.yml ps
docker compose -f deploy/local/docker-compose.yml down
```

The [Compose configuration](docker-compose.yml) defines Core Banking, SQL Server,
Service Bus emulator, PostgreSQL with pgvector, Cosmos emulator, Redis and
App Configuration emulator. Foundry Local stays on the host. The Core Banking image is tagged
`aegisbank/mock-core-banking:0.11.0`; no image is pushed to a registry.

Run these commands from the application Git root. The image tag is a component
tag, not the current platform version. Startup requires a working Docker engine
and downloads/builds images; configuration presence does not prove a running lab
or an Azure deployment. See the [platform README](../../README.md) and
[historical runtime evidence](../../docs/quality/V0131-RUNTIME-EVIDENCE.md).
