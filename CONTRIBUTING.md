# Contributing to AegisBank

Read [AGENTS.md](AGENTS.md) for development authority and coordination,
[README.LLM.md](README.LLM.md) for targeted navigation, and the
[documentation standard](docs/engineering/DOCUMENTATION-STANDARD.md) for names,
placement, language, and evidence rules.

## Change workflow

1. Inspect Git state, find the owning component, and preserve unrelated edits.
2. Define a bounded change. Acquire SessionGuard before writing; check it before
   every write, stage, and commit. Release only your session's lock.
3. Update the owning source/tests and guide together. Use synthetic fixtures.
4. Run checks appropriate to the change and record actual results and skips.
5. For documentation changes, regenerate navigation and run:

```powershell
python -B scripts/documentation_index.py --write
python -B scripts/documentation_index.py --check
python -B -m unittest discover -s scripts -p test_documentation_index.py
git diff --check
```

Use the application `.venv` for application checks. The
[test strategy](docs/quality/TEST-STRATEGY.md) distinguishes unit, integration,
contract, E2E, infrastructure, and AI evaluation evidence.

## Pull requests

Every pull request uses the repository
[template](.github/pull_request_template.md). Keep the description complete but
bounded: explain purpose, scope, observable changes, exact validation evidence,
risks, rollback, deployment boundary, and remaining limits. Use `Not applicable`
with a reason rather than leaving a section ambiguous. A reviewer should be
able to understand what changed, why, how it was validated, and what remains
without reading the entire repository.

## Commit convention

Use [Conventional Commits 1.0.0](https://www.conventionalcommits.org/en/v1.0.0/):

```text
type(scope): concise imperative description

Purpose
Why this change is needed.

Changes
What changes for a reader or caller.

Validation
Exact commands and observed results, including skips or failures.

Limitations
Remaining boundaries and checks not executed.
```

Use lowercase types: `feat`, `fix`, `docs`, `test`, `refactor`, `perf`, `build`,
`ci`, or `chore`. Choose a meaningful scope such as `config`, `routing`,
`navigation`, or `documentation`. Mark a breaking interface with `!` and
describe it in a `BREAKING CHANGE:` footer. The mandatory body sections are
this repository's addition to the upstream specification.

Review `git log -5 --format=fuller` and compare the title with the actual diff.
Stage explicit paths. Write the multiline message to a UTF-8 file and use
`git commit -F PATH`. Group one coherent responsibility per commit; do not
rewrite published history or announce a release without verified release evidence.
Push to the verified remote/branch when authorized, then verify its commit ID.

## Boundaries

Never commit populated `.env` files, real customer data, local databases,
credentials, or runtime artifacts. Banking writes retain deterministic policy,
ownership checks, explicit human approval, and idempotency. Azure deployments
and paid resources require separate authorization. Git publication is distinct
from successful CI execution and cloud acceptance.
