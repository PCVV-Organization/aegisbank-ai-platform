# Research decisions

| Decision | Rationale | Alternative rejected |
|---|---|---|
| TanStack Router | Typed routes and URL search state integrate with Query | React Router is valid but less aligned with the selected TanStack stack |
| Native fetch transport | No duplicate HTTP abstraction and direct AbortSignal support | Axios adds interceptors that are not required for the initial API surface |
| MSW-first local mode | Reproducible tests without Azure | Direct staging integration would make local validation fragile |
| Oxfmt + Oxlint | Fast formatter/linter with TypeScript and React support | Running Biome and Oxlint together duplicates responsibility |
