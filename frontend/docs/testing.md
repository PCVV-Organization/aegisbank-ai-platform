# Frontend testing

Run these checks from `frontend/`:

```powershell
pnpm format:check
pnpm lint
pnpm typecheck
pnpm test
pnpm build
pnpm test:e2e
pnpm test:a11y
```

Unit tests use Vitest. Component and API behavior uses Testing Library and
MSW. Playwright validates browser journeys and axe-core blocks critical or
serious accessibility regressions. Tests use synthetic data only.
