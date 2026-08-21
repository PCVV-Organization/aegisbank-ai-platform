# Repository Instructions

## Mission

Build AegisBank AI Platform incrementally as a secure, educational banking AI
laboratory. It is not a real bank or production financial system.

## Permanent Rules

- Modify project files only inside `C:\aegisbank-ai-platform`.
- Use only synthetic, reproducible data. Never add real personal, banking, or confidential data.
- Work local first, then Docker, CI, and Azure in the approved roadmap order.
- Do not create paid Azure resources or run deployments without explicit approval.
- Start with one agent and a modular monolith. Do not introduce early microservices, AKS, or multi-agent flows.
- The LLM may interpret and propose; deterministic identity, policy, authorization, validation, and business rules decide.
- Require explicit HITL approval for every state-changing operation.
- Never commit secrets. Keep `.env` ignored and publish placeholders only in `.env.example` when needed.
- Minimize and redact sensitive content in logs, prompts, audit records, and telemetry.
- Add a dependency or technology only when it resolves a requirement, reduces a risk, or demonstrates a defined competency.
- Keep changes within the authorized milestone. Scope expansion requires an explicit decision.
- Preserve pre-existing OpenCode bootstrap artifacts unless a task explicitly targets them.
- Promote only verified, durable project knowledge to `.intelligence/`.

## Quality Rules

- Add tests appropriate to every implementation change.
- Separate unit, integration, contract, end-to-end, and AI evaluation concerns.
- Validate actual behavior before reporting `PASS`; never substitute expected behavior for executed evidence.
- Writes must be idempotent before any retry policy is enabled.
- Use bounded retries only for known transient failures and circuit breakers for persistent dependency failures.
- Propagate correlation and trace identifiers across every future execution boundary.
- Do not claim legal, regulatory, NIST, Microsoft, or banking certification/compliance.

## Milestone Workflow

1. Inspect the current repository and milestone state.
2. Explain the bounded change briefly.
3. Implement only the authorized phase.
4. Run relevant validation and correct failures.
5. Update status and documentation with real evidence.
6. Stop before the next milestone and request approval.

## Definition Of Done

A milestone is done only when its scoped artifacts are complete, required tests
and checks have actually passed, documentation reflects the observed result, and
remaining risks are reported. Never advance to the next milestone automatically.

## Baseline Validation

For documentation-only changes, run:

```powershell
git diff --check
git status --short
```

Use milestone-specific format, lint, type, test, security, evaluation, and build
commands once those toolchains exist.
