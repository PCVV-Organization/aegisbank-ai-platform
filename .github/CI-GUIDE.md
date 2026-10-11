# GitHub Automation Guide

This directory contains repository automation and host-specific instructions.
The [root README](../README.md) is the project's public introduction.

## Entry points

- [CI workflow](workflows/ci.yml): static analysis and test jobs.
- [Staging workflow](workflows/deploy-staging.yml): declared Azure promotion procedure.
- [Copilot instructions](copilot-instructions.md): navigation for that host.
- [Contribution guide](../CONTRIBUTING.md): validation and commit conventions.

## Evidence and changes

The application remote is
[PCVV-Organization/aegisbank-ai-platform](https://github.com/PCVV-Organization/aegisbank-ai-platform).
An uploaded commit establishes Git publication; a successful Actions run must
be verified separately in the repository's Actions tab. Azure staging also
requires approval and its own [acceptance evidence](../docs/operations/STAGING-ACCEPTANCE-RUNBOOK.md).

Before changing automation, identify its triggers, permissions, dependencies,
and generated outputs. Follow [AGENTS.md](../AGENTS.md), acquire SessionGuard,
and run checks appropriate to the affected [test layers](../docs/quality/TEST-STRATEGY.md).

Keep this guide named `CI-GUIDE.md`: GitHub prioritizes `.github/README.md`
over the root README for the repository landing page. See
[GitHub's README selection rules](https://docs.github.com/en/repositories/managing-your-repositorys-settings-and-features/customizing-your-repository/about-readmes).
