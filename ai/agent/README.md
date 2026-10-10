# AegisBank Agent

Single application agent with controlled banking tools, retrieval, durable session
state, MCP and human-approved service-request operations. See the
[platform README](../../README.md) for the checkout baseline; the package version
in pyproject.toml is component metadata, not the platform release number.

## Responsibilities

- Route banking reads through deterministic identity and ownership policies.
- Use registered tools and validate their inputs and outputs.
- Retrieve knowledge and abstain when supporting evidence is missing.
- Bind writes to explicit human approval and enforce supervision and idempotency.
- Preserve trace context, structured logs, audit events and synthetic session state.
- Evaluate safety and behavior separately from infrastructure acceptance.

The original v0.6 read-only scope has been extended. Historical measurements
remain in the [experiment record](../../history/experiments/v0.6.1-native-tool-calling.md).
Current components are mapped in the
[canonical catalog](../../docs/architecture/CANONICAL-COMPONENTS.md).

## Navigation

| Path | Responsibility |
| --- | --- |
| [agent.py](src/aegisbank_agent/agent.py) | Main orchestration and execution controls. |
| [knowledge_routing.py](src/aegisbank_agent/knowledge_routing.py) | Deterministic routing policies. |
| [tools](src/aegisbank_agent/tools/) | Tool contracts, registry and implementations. |
| [hitl.py](src/aegisbank_agent/hitl.py) | Approval lifecycle. |
| [mcp_boundary.py](src/aegisbank_agent/mcp_boundary.py) | MCP tool boundary. |
| [reliability](src/aegisbank_agent/reliability/) | Idempotency, retry, timeout, outbox and messaging. |
| [observability](src/aegisbank_agent/observability/) | Traces, logs, metrics, audit and supervision. |
| [configuration](src/aegisbank_agent/configuration/) | Configuration and secret boundaries. |
| [evaluation](src/aegisbank_agent/evaluation/) and [mlops](src/aegisbank_agent/mlops/) | Evaluation and experiment tooling. |
| [tests](tests/) | Unit, integration, contracts, E2E and infrastructure suites. |

## Local usage

Run from the application Git root. Use its Python 3.14 environment and the local
packages declared in [pyproject.toml](pyproject.toml); see the
[Core Banking setup](../../services/mock-core-banking/README.md) and
[RAG setup](../rag/README.md) for those dependencies.

### Durable conversational state

The CLI persists only structured, synthetic session state in SQLite. The
default session is isolated by customer (`session-CUST-0001`); provide an
explicit session ID when a caller owns multiple conversations:

```powershell
python -m aegisbank_agent.cli run "Dame detalle de LOAN-0001" --customer-id CUST-0001 --session-id SESSION-A
python -m aegisbank_agent.cli run "¿Cuál fue el último préstamo que consulté?" --customer-id CUST-0001 --session-id SESSION-A
```

Set `AEGISBANK_SESSION_DB_PATH` to relocate the SQLite file. A session cannot
be opened by a different customer. Explicit loan reads and structured session
references do not require the LLM.

### Foundry Local configuration

The runtime searches for `.env.local` in the process working directory and
parents up to the application Git root. It loads found files nearest-to-root:
the closest file overrides duplicate values, while parent files fill variables
that are not set closer to the working directory. Exported process variables
always win. Copy the root `.env.example` to `.env.local` for shared settings;
optionally use `ai/agent/.env.example` as a small agent-specific override at
`ai/agent/.env.local`. Both local files are ignored by Git. The application
does not load a plain `.env` file. Alternatively, export the same variables in
the process environment. `AEGISBANK_FOUNDRY_LOCAL_BASE_URL` takes precedence;
when empty, the adapter discovers the current endpoint with `foundry server
status -o json`. LLM calls use a bounded timeout and retry count from the
environment and never retry indefinitely.

## Validation and evidence

Use the [test strategy](../../docs/quality/TEST-STRATEGY.md) and
[evaluation catalog](../../docs/evaluation/EVALUATION-CATALOG.md) to select checks.
The old tests/v06 layout no longer represents the current tree.
Infrastructure and live-model tests have additional runtime requirements.

The working tree can contain uncommitted red-team changes. Inspect Git before
attributing them to a release. Documentation does not prove that a live model,
Docker, or a cloud service has been exercised in the current session.
