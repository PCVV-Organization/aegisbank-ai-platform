# Repository and Environment Workflow

This project uses one protected integration branch and separate deployment
environments. Development, staging, and production are not permanent Git
branches.

## Branch policy

- `master` is the only permanent integration branch and is protected.
- Every change starts from a short-lived `feature/*`, `fix/*`, `docs/*`, or
  `chore/*` branch.
- Changes reach `master` only through a pull request that passes required CI
  checks and review.
- Do not create permanent `dev`, `qa`, `staging`, `production`, or `main`
  branches unless an approved architecture decision changes this policy.
- Releases use immutable tags such as `v1.0.0` when a release process is
  approved.

## Environment policy

GitHub Environments represent deployment targets and hold their own variables,
secrets, approvals, and protection rules:

| Environment | Purpose | Promotion rule |
|---|---|---|
| `development` | Local and automated development validation | No cloud deployment is implied |
| `staging` | Pre-production acceptance | Explicitly authorized deployment and acceptance evidence |
| `production` | Future production target | Separate approval and immutable staging-accepted artifact |

CI can run entirely on GitHub without Azure. Azure is only involved when an
authorized deployment workflow targets an Azure environment. A successful CI
run or a valid Bicep compilation is not evidence that staging or production has
been deployed.

## Promotion flow

```text
short-lived branch -> pull request -> CI -> master
master -> approved staging deployment -> acceptance evidence
staging artifact -> separate production approval -> production
```

The active GitHub workflow targets `master`; `main` is not an active branch in
this repository.
