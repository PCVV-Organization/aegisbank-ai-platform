# AegisBank Test Strategy (v0.13.0-R2)

> **Milestone:** `v0.13.0-R2 — Test Suite Rationalization`
> **Guiding principle:** `TEST VALUE > TEST COUNT`.

## 1. Test pyramid

```text
            /\
           /  \          E2E (critical user journeys)
          / E2E \         A small set of complete banking journeys
         /──────\
        /Contract\       JSON Schema, MCP, and outbox-event contracts
       /──────────\
      /Integration\     Components connected in process
     /──────────────\
    /     Unit       \   One component, without I/O or with in-memory stubs
   /──────────────────\
```

Microsoft Well-Architected and Microsoft Foundry AI-200 guidance are cited for
the distribution above: many fast unit tests at the base and few E2E tests at
the top because E2E tests are more expensive and fragile. See
[Microsoft Learn 1][1] and [Microsoft Learn 2][2].

## 2. AegisBank test layers (after v0.13.0-R2)

```text
ai/agent/tests/
├── unit/           # One component; no external state
├── integration/    # Multiple in-process components
├── contracts/      # JSON Schema and interfaces
├── e2e/            # Critical user journeys
│   ├── read_journeys/
│   └── write_journeys/
└── infra/          # Opt-in: Docker, Kubernetes, Functions, Cosmos emulator
    ├── containers/
    ├── kubernetes/
    ├── serverless/
    ├── cosmos/
    └── session_guard/
```

Versioned test directories such as `v06/`, `v07/`, `v08/`, `v09/`, `v012/`,
and `v013r1/` were removed from the tree; their history remains in Git, ADRs,
and documentation.

## 3. Pytest markers (`--strict-markers`)

| Marker | Layer | Test location |
|---|---|---|
| `unit` | Single component | `unit/` |
| `integration` | In-process components | `integration/` |
| `contract` | JSON Schema and interfaces | `contracts/` |
| `e2e` | Critical user journeys | `e2e/` |
| `infra` | Docker, Kubernetes, Functions | `infra/` |
| `slow` | Tests with long waits or durations | Opt-in |

Each file under `unit/` applies `pytest.mark.unit` with `pytestmark`.
Do not mix test layers in one file.

## 4. Gates

### FAST / PR (default gate)

```bash
pytest ai/agent/tests/unit ai/agent/tests/integration ai/agent/tests/contracts
ruff check .
ruff format --check .
python -m compileall -q .
```

Target duration: **under 30 seconds**.

### Critical E2E (opt-in, pre-release)

```bash
pytest ai/agent/tests/e2e
```

Target duration: **under 30 seconds**.

### Infrastructure (opt-in, post-merge)

```bash
pytest ai/agent/tests/infra
pytest ai/agent/tests/contracts
scripts/container_acceptance.py   # requires Docker and MSSQL_SA_PASSWORD
```

This gate is opt-in because it requires Docker, a local Kubernetes cluster, or
other infrastructure.

## 5. Testing concepts

- **Unit test:** one component, without I/O.
- **Integration test:** connected components, such as DB, RAG, bus, or Cosmos,
  tested in process.
- **Contract test:** verifies that two components satisfy an interface, such
  as JSON Schema, MCP tool specification, or outbox-event payload.
- **E2E test:** completes a full user journey. Keep the suite to critical
  banking journeys.
- **Regression test:** captures a real defect so it does not recur. For
  example, `test_metamorphic_paraphrase_matrix_loan_details` captures the
  “Dame detalle de mi LOAN-0001” routing defect.
- **Parametrization:** exercises multiple inputs through one test using
  `@pytest.mark.parametrize`, avoiding near-duplicate functions.
- **Flaky test:** passes and fails without code changes. Investigate and isolate
  it; marking a test `slow` does not by itself fix flakiness.
- **Critical user journey:** the smallest set of full flows that protects
  important user value and safety properties.
- **Diminishing returns:** additional tests eventually add less confidence than
  maintenance cost and noise.
- **Test maintenance debt:** infrastructure that consumes time without
  protecting a meaningful risk.

## 6. Permanent rules

1. Do not retain a test solely because it was added in an earlier version; Git
   preserves history.
2. Do not delete tests just to reduce the count. Keep them when they protect a
   meaningful risk.
3. Before consolidating a test, classify the action:
   - `KEEP_CRITICAL`: protects HITL, outbox, ownership, idempotency, or another
     critical invariant.
   - `KEEP_UNIQUE`: uniquely covers a property.
   - `MERGE_PARAMETRIZE`: combines equivalent variants using parametrization.
   - `MOVE_LAYER`: moves a test to its correct test layer.
   - `DELETE_DUPLICATE`: removes coverage duplicated by another test.
   - `DELETE_OBSOLETE`: removes coverage for a responsibility that no longer
     exists.
4. Preserve coverage for structured tool calling, pseudo-tool-call blocking,
   customer ownership isolation, loan-routing paraphrases, RAG grounding and
   abstention, MCP and HITL approve/reject, write idempotency, retries, circuit
   breaker and timeout behavior, transactional outbox, idempotent consumers,
   DLQ, audit, OpenTelemetry, HOTL, Core Banking contracts, critical read and
   write journeys, secret controls, and infrastructure acceptance.

## 7. Adding a test

1. Choose the layer: `unit`, `integration`, `contract`, `e2e`, or `infra`.
2. Put the test file in the matching directory without a version prefix.
3. Set `pytestmark = pytest.mark.<layer>` at the top of the file.
4. Parametrize equivalent test variants.
5. Check whether another test already covers the same property.

[1]: https://learn.microsoft.com/en-us/azure/well-architected/operational-excellence/testing
[2]: https://learn.microsoft.com/en-us/azure/foundry/how-to/evaluate-generative-ai-app
