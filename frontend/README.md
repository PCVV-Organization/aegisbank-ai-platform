# AegisBank Web

The AegisBank web portal is a Vite + React TypeScript application. It is a
synthetic banking laboratory UI; it is not a production banking client.

## Local development

```powershell
corepack enable
pnpm install --frozen-lockfile
Copy-Item .env.example .env.local
pnpm dev
```

The default local mode uses a synthetic customer and does not require Azure.

The checked-in backend contract is a JSON Schema that validates an OpenAPI
document. To regenerate types from a running API, set `VITE_OPENAPI_URL` to
its `/openapi.json` endpoint before running `pnpm generate:api`.

## Commands

```text
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
```

Authentication, API contracts, privacy, testing, and deployment boundaries are
defined in the parent repository documentation and `specs/banking-portal-mvp/`.
