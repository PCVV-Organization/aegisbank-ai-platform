# ADR-012: Single-agent orchestrator with read-only function tools

## Status

Accepted for `v0.6` implementation.

## Context

v0.5 established grounded generation with citation validation over a synthetic
banking corpus. The next milestone requires an agent that can converse with a
customer, select the correct read-only tool for each intent, enforce customer
ownership boundaries, and reject any write operations.

The agent must:
- Run as a single orchestrator (no multi-agent flows)
- Use a deterministic session context that persists `customer_id` across all
  tool calls
- Expose only the four read-only tools: `search_knowledge`, `get_my_loans`,
  `get_loan_details`, `get_next_installment`
- Enforce strict schema validation on all tool inputs
- Reject unknown or invalid tool names at the registry level
- Bound the number of tool-call rounds
- Use `tool_choice=auto` to let the model decide whether to call a tool
- Reuse the existing `ai/rag` retrieval infrastructure without modifying
  corpus, retrieval, or `rag-answer-v001`
- Use the existing `mock-core-banking` in-memory database via the repository
  pattern with deterministic seed data
- Provide a deterministic local evaluation harness for six proxy metrics:
  tool selection accuracy, tool input accuracy, tool call success,
  no-write compliance, ownership enforcement, and task completion proxy

## Decision

The agent implementation follows these decisions:

### Agent Architecture

```
User Message -> AgentOrchestrator.run(customer_id)
  -> loads system prompt (agent-system-v001.json)
  -> creates AgentContext(session_customer_id=customer_id)
  -> builds messages list with system + user
  -> loops up to max_rounds calling chat completions
    -> tool_choice="auto"
    -> if no tool_calls: return answer
    -> for each tool_call:
       -> registry.execute(tool_name, arguments, context)
       -> appends tool result to messages
    -> if rounds exhausted: return error answer
```

### Tool Registry

The `ToolRegistry` class maintains a strict allowlist of `FunctionTool`
instances. The default set is exactly:
- `SearchKnowledgeTool` — wraps `aegisbank_rag` hybrid_rrf retriever
- `GetMyLoansTool` — lists loans for session customer
- `GetLoanDetailsTool` — loan detail with ownership check
- `GetNextInstallmentTool` — next installment with ownership check

Unknown tool names return a `ToolResult` with `success=False` and an error
message listing the allowed tools. Tool execution wraps exceptions in a
`ToolResult` with `success=False`.

### Schema Validation

Each tool defines a JSON Schema in `parameters_schema`. The tool implementation
validates inputs before database access. Rejected inputs return `success=False`
with a descriptive error message.

### Ownership Enforcement

`GetLoanDetailsTool` and `GetNextInstallmentTool` verify that
`loan.customer_id == context.session_customer_id` before returning data.
Cross-customer access returns `success=False` with
"no pertenece" or "acceso denegado" in the error.

### RAG Reuse

`SearchKnowledgeTool` loads the existing `ai/rag` corpus and retrievers on
initialization. The tool calls `retriever.search(query, top_k=3)` and formats
the hits. No modifications are made to `ai/rag` source, corpus files, or
`rag-answer-v001.json`.

### Core Banking Mock

Banking tools use `mock-core-banking` `Database("sqlite:///:memory:")` created
per-tool-instance, populated by `seed_database()`. The seed data is
deterministic (fixed timestamps, fixed IDs). The in-memory database ensures
isolation between test runs.

### Evaluation Harness

`evaluation.py` provides:
- `load_eval_cases(path)` — loads JSONL evaluation cases
- Per-metric evaluator functions (tool selection, input, call success,
  no-write compliance, ownership enforcement, task completion proxy)
- `compute_aggregate(results, metric)` — aggregates pass/fail counts and rate
- `run_local_evaluation(cases, mock_client, registry)` — deterministic
  end-to-end evaluation returning per-case details and aggregate metrics

### Metrics

| Metric | Description |
|--------|-------------|
| tool_selection_accuracy | Correct tool name selected vs expected |
| tool_input_accuracy | Correct arguments provided vs expected |
| tool_call_success | Tool succeeded/failed as expected |
| no_write_compliance | Write intents rejected with read-only message |
| ownership_enforcement | Cross-customer access properly denied |
| task_completion_proxy | Has answer and reasonable tool call count |

## Evaluation

Synthetic JSONL dataset (`eval-cases.jsonl`) contains 15 cases covering:
- RAG queries
- Loan listing, details, and installment queries
- Cross-customer ownership attempts
- Invalid loan ID formats
- Write intent attempts (claim, transfer, create)
- Direct chat with no tool needed

Each case carries one or more metric tags. The harness computes per-metric
pass/fail counts and rates using a mock client for deterministic testing. A
separate one-time local Foundry evaluation is recorded outside this deterministic
test harness.

## Alternatives

- **Function calling with forced tool choice:** rejected because
  `tool_choice=auto` allows the model to abstain when appropriate (e.g.,
  greeting or write intent).
- **Write tools with guardrails:** rejected because write tools introduce
  state-change risk and require additional safety evaluation. The project
  charter limits this milestone to read-only operations.
- **Dynamic tool registration:** rejected because a static allowlist is
  auditable and matches the minimal-modularity principle.
- **TestClient from FastAPI for banking tools:** deferred because the current
  repository pattern with in-memory database provides equivalent determinism
  with less coupling.

## Consequences

- The agent can only read; no state changes are possible through agent tools.
- Customer data isolation is enforced at the tool level, not just at the API
  level.
- Evaluation is fully deterministic and reproducible without network access.
- RAG retrieval behavior is preserved as-is; the agent only consumes it.
- The agent prompt is versioned (`agent-system-v001`) to allow future updates
  without breaking existing sessions.
- Six proxy metrics enable rapid iteration on tool selection and argument
  construction without live model evaluation.
