# Banking Portal MVP

## User scenarios

### US1 — Synthetic customer access (P1)
As a synthetic customer, I can enter the portal locally and see a protected overview without Azure dependencies.

### US2 — Banking navigation (P1)
As a customer, I can navigate accounts, cards, loans, payments, requests, and assistant modules with keyboard and responsive layouts.

### US3 — Assistant conversation (P1)
As a customer, I can submit a question to the assistant, see loading and error states, and cancel or recover from a failed request.

### US4 — Secure form foundation (P2)
As a product team, we can add forms with typed TanStack Form state, Zod runtime validation, and OpenAPI-compatible payloads.

## Functional requirements

- **FR-001** The portal MUST run locally with synthetic data and no Azure service dependency.
- **FR-002** Protected application routes MUST redirect unauthenticated users to `/login`.
- **FR-003** Navigation MUST expose overview, accounts, cards, loans, payments, service requests, and assistant modules.
- **FR-004** The assistant MUST expose loading, success, error, and cancellation-safe states.
- **FR-005** API requests MUST propagate `AbortSignal` and classify non-2xx responses as typed client errors.
- **FR-006** Forms MUST validate untrusted input at runtime before submission.
- **FR-007** Interactive controls MUST support keyboard navigation, visible focus, labels, and screen-reader feedback.
- **FR-008** The build MUST use pinned Node/pnpm versions and pass formatting, lint, type, unit, build, and E2E checks.
- **FR-009** The frontend MUST contain no client secrets or real banking data.

## Success criteria

- A clean checkout installs with `pnpm install --frozen-lockfile`.
- A synthetic user can reach `/app/overview` and `/app/assistant` in a browser test.
- An assistant request can be aborted without an unhandled error.
- Critical or serious automated accessibility findings are zero.
- CI commands are documented and reproducible.

## Out of scope

Real Entra acceptance, Azure deployment, real payments, production banking data, and complete domain implementations are deferred to staging milestones.
