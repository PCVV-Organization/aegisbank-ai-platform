# ADR-024: CI Security Gates Before Deployment

- Status: Accepted
- Date: 2026-08-31

## Context

Deploying before repeatable tests, SAST, dependency auditing, secret scanning and SBOM
generation would move defects into a harder-to-control environment.

## Decision

Run static checks, tests, Bandit, pip-audit, CycloneDX SBOM and secret scanning in CI
before any future delivery stage. This milestone configures CI only and stores no Azure
credentials.

## Consequences

The pipeline may fail or report dependency audit blocked when external advisory data is
unavailable. That is evidence, not a reason to claim PASS. Continuous Deployment remains
out of scope.
