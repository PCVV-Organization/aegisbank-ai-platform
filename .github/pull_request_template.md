## Purpose

<!-- State the problem and intended outcome in 1–3 sentences. -->

## Related work

<!-- Link an issue, milestone, ADR, or write `Not applicable` with a reason. -->

## Scope

<!-- Identify the areas changed and explicitly state what is out of scope. -->

### Changes

-

### Behavior and contracts

<!-- Describe observable behavior, API/schema changes, migrations, or say `No behavior or contract change`. -->

## Validation evidence

<!-- List exact commands and observed results. Do not claim checks you did not run. -->

| Check | Command | Result |
|---|---|---|
| Tests | `...` | `PASS`, `FAIL`, or `NOT RUN` |
| Lint/type/security | `...` | `PASS`, `FAIL`, or `NOT RUN` |
| Build/contract/evaluation | `...` | `PASS`, `FAIL`, or `NOT RUN` |

## Risk and operations

- **Security, privacy, or data impact:** <!-- State impact or `None`. -->
- **Configuration or migration impact:** <!-- State impact or `None`. -->
- **Rollback:** <!-- Give the reversal or say why rollback is unnecessary. -->
- **Deployment boundary:** <!-- Local, CI-only, staging, production, or `No deployment`. -->

## Documentation

<!-- List updated docs, generated indexes, or explain why documentation is unchanged. -->

## Author checklist

- [ ] The title follows `type(scope): imperative description`.
- [ ] The diff is limited to the stated scope; unrelated changes are excluded.
- [ ] Tests and checks are listed with exact commands and observed results.
- [ ] Secrets, personal data, and production credentials are absent.
- [ ] Required documentation and generated navigation are updated.
- [ ] Remaining failures, skipped checks, and limitations are explicit.
- [ ] This PR is ready for review; deployment or merge is not implied by opening it.
