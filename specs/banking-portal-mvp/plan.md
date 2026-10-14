# Implementation plan

## Technical context

The frontend is a Vite React SPA in `frontend/`, using TypeScript strict, TanStack Router/Query/Form, Zod, MSW fixtures, OpenAPI-generated types, Tailwind, Radix, Oxfmt, Oxlint, Vitest, Testing Library, Playwright, and axe-core.

## Design

- Feature-first modules live under `frontend/src/features`.
- Router owns URL state and protected layouts; Query owns remote state; Form owns form lifecycle; Zod validates runtime input.
- A small `fetch` transport propagates abort signals and correlation metadata.
- Mock auth is the default local mode; real MSAL configuration is environment-driven for staging.
- UI primitives remain accessible and domain features do not depend on each other directly.

## Risks and mitigations

- Generated API drift: run generation in CI and review contract changes.
- Duplicate writes: disable automatic retries for mutations and require backend idempotency.
- Sensitive browser state: keep tokens and private responses out of localStorage.
- Router type growth: code-split domain routes as the portal expands.
