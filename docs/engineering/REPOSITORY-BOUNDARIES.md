# Application and Development-Environment Repositories

This Git repository contains the AegisBank educational application: source
code, contracts, tests, synthetic data, and product documentation.

The separate `aegisbank-ai-platform-ai-env` repository contains developer
tooling and instructions. The development agent may use both repositories;
the Aegis banking assistant belongs only to this application repository.

In the local workspace, this application is checked out beneath ai-env. The
parent repository ignores the application checkout. Each repository has its
own history and remote configuration; the application is not a submodule or
gitlink.

The application can be cloned independently and retains its own `AGENTS.md`.
Instructions from ai-env are not assumed to load automatically. If work uses
that environment, consult its rules and workspace manifest as well.

Banking application changes belong here. Changes to developer tooling and
configuration belong in ai-env. Review cross-repository changes in both
repositories and record their dependencies.

This separation does not change banking milestones, create cloud resources, or
turn developer-agent permissions into banking authorization.
