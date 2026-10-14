# Frontend security boundaries

- No client secret belongs in Vite environment variables or browser storage.
- Tokens and private banking responses must not be persisted to localStorage.
- UI route guards improve navigation only; backend authorization remains the
  source of truth.
- Mutating requests must use backend idempotency keys before retries are added.
- Assistant output is untrusted content and must not authorize a banking write.
