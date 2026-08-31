# AegisBank Test Strategy

## Purpose

**QA (Quality Assurance, aseguramiento de calidad)** is the complete process of proving
that the system behaves as promised, not merely the existence of tests. The repository
uses a test pyramid: many fast unit tests, fewer integration and contract tests, and a
small set of critical E2E journeys.

| Layer | Meaning | AegisBank responsibility | Evidence |
|---|---|---|---|
| Unit | One function/class in isolation | Money rules, routing policy, retry decisions | `tests/unit` or focused package tests |
| Integration | Multiple local components together | Agent + tools + synthetic database, API + persistence | package integration tests |
| Contract | Agreement between components | OpenAPI, tool schemas, event payloads | `tests/contracts` |
| E2E (End-to-End, extremo a extremo) | Complete user journey | READ, RAG, HITL WRITE, outbox and reliability paths | `ai/agent/tests/e2e` |
| Regression | A previously discovered defect remains fixed | v0.9.2 pseudo-tool routing gap | named acceptance tests |
| Acceptance | Behavior judged against a requirement | tool really executes and ownership is preserved | acceptance tests |

**Flaky test** means a test that changes result without a relevant code/input change.
One failure does not prove flakiness; this project requires repeated independent runs and
identical failure evidence before labeling one. **Test debt** is unverified behavior
that should be covered later. **Code coverage** measures executed code, not correctness;
it is reported but no arbitrary production percentage is imposed.

## Quality Gate

The local gate runs static checks, unit/integration/contract/E2E tests, coverage, SAST,
SCA, SBOM and secret scanning in that order. A gate is PASS only when the command
actually ran and returned zero. Dependency audit is `DEPENDENCY_AUDIT_BLOCKED` when its
advisory service is unavailable, never an invented PASS.

## Critical Journeys

The separate E2E suite covers authenticated READ routing, the multi-step loan journey,
RAG evidence and abstention, HITL rejection/approval, HOTL blocking, retry, circuit
breaker and DLQ. Existing v0.6-v0.9 tests remain regression evidence and are not silently
reclassified as production guarantees.

## Observed Coverage Baseline

The v0.10 local run observed **78.72% line coverage** across the four packages. The
quality gate does not impose an arbitrary production threshold. Modules below 50% in
this baseline are `aegisbank_agent/cli.py`, `hitl_cli.py`, `mcp_server.py`,
`aegisbank_rag/cli.py` and `aegisbank_intent_classifier/cli.py` at 0%, plus
`aegisbank_intent_classifier/pipeline.py` at 48.28%. They are recorded as test debt,
not hidden by exclusions.

## Concepts and Career Mapping

**CI (Continuous Integration, integración continua)** runs these checks for each change.
**CD (Continuous Delivery/Deployment)** prepares or automatically promotes a release;
this milestone does not deploy. **DevSecOps (Development, Security and Operations)**
moves security into the SDLC (Software Development Life Cycle, ciclo de vida del
software). These practices map to Mibanco's unit/integration/E2E, contract testing,
hardening and pipeline responsibilities, and to AI-103/AI-200 lifecycle and security
objectives.
