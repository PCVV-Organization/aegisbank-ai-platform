# Local Environment Configuration

This guide defines the application's local dotenv convention. A dotenv file is
a developer convenience, not a deployment secret store or a substitute for
process-level configuration.

## File layout

| File | Git status | Scope |
|---|---|---|
| `.env.example` | Tracked | Root template for local application configuration; contains safe local emulator values and commented cloud bootstrap names only. |
| `.env.local` | Ignored | Developer-specific root configuration. Copy the root template here and keep private values local. |
| `ai/agent/.env.example` | Tracked | Smaller agent-only template for running with `ai/agent/` as the working directory. |
| `ai/agent/.env.local` | Ignored | Optional agent-working-directory override; preserve local values and never commit it. |

The agent loader searches for `.env.local` in the current working directory and
then parent directories up to the application Git root. Existing files are
loaded nearest-to-root: the closest file wins for duplicate variables, and
parent files supply only variables not already set. Existing process variables
take precedence over every dotenv file (`override=False`). Outside a Git
checkout, the loader checks only the current working directory. The application
does not load a plain `.env` file.
The repository `.gitignore` excludes `.env` and `.env.*` while explicitly
allowing `.env.example` templates.

For the agent, choose the template matching the intended scope:

```powershell
# Shared application configuration, copied from the application root:
Copy-Item .env.example .env.local

# Optional isolated agent configuration, when running from ai/agent/:
Copy-Item ai/agent/.env.example ai/agent/.env.local
```

Do not overwrite an existing `.env.local` blindly. Preserve local values and
merge only missing keys from the matching template. Leave the Foundry URL empty
to use documented local endpoint discovery. `.env.example` values for Cosmos,
Service Bus, Redis, or PostgreSQL are synthetic local-emulator settings; they
are not production credentials.

## Docker Compose

The local Compose lab is a separate process boundary. Its current commands use
Compose defaults for ports and names and require `MSSQL_SA_PASSWORD` in the
PowerShell environment. The optional `data` profile also requires
`POSTGRES_PASSWORD`. Set these only in the shell session used to run Compose;
the application `.env.local` is not automatically read by these commands. If a
Compose dotenv file is introduced later, pass it explicitly with `--env-file`
and keep it separate from application-only settings unless the values belong
to both scopes. Do not expose resolved configuration containing credentials in
logs or support reports.

## Runtime boundaries

- Local `.env.local` loading is disabled when `AEGISBANK_ENV` is supplied as
  `staging` or `production` by the runtime environment.
- Cloud non-secret configuration belongs in Azure App Configuration; cloud
  secrets belong in Key Vault and should be accessed through managed identity.
- Never copy a developer dotenv file into a container image, CI artifact, or
  cloud deployment. Never commit populated `.env*` files.
- Supply only synthetic, reproducible values to local emulators and tests.
- Missing dotenv support must be a visible setup error when a local file exists;
  it must not silently start the application with unintended defaults.

See [cloud configuration and identity](../architecture/CLOUD-CONFIGURATION-IDENTITY.md),
the [local Compose lab](../../deploy/local/README.md), and the
[application environment template](../../.env.example).
