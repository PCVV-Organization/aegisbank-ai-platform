# Frontend architecture

The web portal is a modular React SPA. TanStack Router owns URL state and
protected layouts; TanStack Query owns server state; TanStack Form owns form
state; Zod validates runtime input; the OpenAPI client and `fetch` transport
own HTTP boundaries.

Features are grouped by banking domain under `src/features/`. Shared Radix
primitives and Tailwind tokens live under `src/components` and
`src/design-system`; domain code must not import another domain directly.

Local development defaults to synthetic auth and MSW-compatible fixtures. Real
Entra configuration is staging-only and must never include a client secret.

Azure Static Web Apps uses `staticwebapp.config.json` for SPA fallback and
baseline browser security headers. API authorization remains a backend concern.
