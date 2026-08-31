# ADR-022: Layered Test Strategy and Quality Gates

- Status: Accepted
- Date: 2026-08-31

## Context

AegisBank had many milestone tests, but no single reproducible release decision.

## Decision

Use a test pyramid with unit, integration, contract, focused E2E, regression and security
gates. `scripts/quality_gate.py` is the local entrypoint and GitHub Actions invokes it.

## Consequences

Critical journeys are protected without making every test an expensive E2E test. Local
evidence is `LAB-COVERED`; the workflow is `CI-CONFIGURED / RUNNER-PENDING` until GitHub
actually executes it. No cloud deployment is part of this decision.
