# Local Container Lab

Prerequisite: Docker Desktop Linux containers. Supply a synthetic local password
through the PowerShell process environment; do not put it in Git. The Compose
file requires `MSSQL_SA_PASSWORD`; the optional `data` profile also requires
`POSTGRES_PASSWORD`.

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
or an Azure deployment. Docker Compose does not automatically load the
application's `.env.local`; these commands use shell variables and Compose
defaults. See [local environment configuration](../../docs/operations/LOCAL-ENVIRONMENT-CONFIGURATION.md),
the [platform README](../../README.md), and
[historical runtime evidence](../../history/quality/V0131-RUNTIME-EVIDENCE.md).
