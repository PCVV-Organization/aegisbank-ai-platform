# AegisBank Agent v0.6

Single-agent orchestrator with read-only function tools for AegisBank AI Platform.

## Overview

v0.6 implements a deterministic single-agent that responds to customer queries
using only read-only tools. The agent:

- Uses `customer_id` from session context to enforce data ownership
- Selects from 4 read-only tools via OpenAI function-calling
- Enforces strict schema validation on all tool inputs
- Rejects unknown/invalid tools and write operations
- Bounded to 3 tool-call rounds per session
- Uses `tool_choice=auto` for model-driven tool selection

## Tool Allowlist

| Tool | Purpose |
|------|---------|
| `search_knowledge(query)` | RAG search over synthetic banking corpus |
| `get_my_loans()` | List loans for session customer |
| `get_loan_details(loan_id)` | Loan detail with ownership check |
| `get_next_installment(loan_id)` | Next installment with ownership check |

## Architecture

```
AgentOrchestrator
├── ToolRegistry (allowlist of 4 FunctionTool)
│   ├── SearchKnowledgeTool (reuses ai/rag retrieval)
│   ├── GetMyLoansTool (mock-core-banking)
│   ├── GetLoanDetailsTool (mock-core-banking + ownership)
│   └── GetNextInstallmentTool (mock-core-banking + ownership)
├── AgentContext (session_customer_id)
└── AgentExecutionResult (answer, tool_calls, rounds, success)
```

## Usage

```python
from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.tools.registry import ToolRegistry

registry = ToolRegistry()
orchestrator = AgentOrchestrator(registry=registry)

result = orchestrator.run("¿Cuáles son mis préstamos activos?", customer_id="CUST-0001")
print(result.answer)
```

## Evaluation

Six proxy metrics computed by the local deterministic harness:

| Metric | Description |
|--------|-------------|
| `tool_selection_accuracy` | Correct tool selected |
| `tool_input_accuracy` | Correct arguments provided |
| `tool_call_success` | Tool succeeded/failed as expected |
| `no_write_compliance` | Write intents rejected |
| `ownership_enforcement` | Cross-customer access denied |
| `task_completion_proxy` | Has answer + reasonable tool usage |

Run evaluation:

```bash
cd ai/agent
pytest tests/v06/ -v
```

## Files

```
ai/agent/
├── src/aegisbank_agent/
│   ├── agent.py          # AgentOrchestrator
│   ├── constants.py      # Path constants
│   ├── evaluation.py     # Deterministic evaluation harness
│   ├── prompts/
│   │   └── agent-system-v001.json
│   └── tools/
│       ├── base.py           # FunctionTool, AgentContext, ToolResult
│       ├── banking_tools.py  # Banking tools
│       ├── knowledge_tools.py # RAG search tool
│       └── registry.py       # ToolRegistry
├── data/
│   ├── agent-eval.jsonl  # Legacy eval cases
│   └── eval-cases.jsonl   # v0.6 synthetic dataset
├── tests/v06/
│   ├── test_registry.py
│   ├── test_schemas.py
│   ├── test_security.py
│   ├── test_ownership.py
│   ├── test_round_limit.py
│   ├── test_rag.py
│   ├── test_core_banking.py
│   ├── test_evaluation.py
│   └── test_reproducibility.py
└── pyproject.toml
```

## Constraints

- No Docker, Azure, az, MCP, HITL, worktrees, or write tools
- Uses existing `FoundryLocalProvider` and Chat Completions
- Reuses `ai/rag` without modifying corpus/retrieval/rag-answer-v001
- Mock Core Banking via in-memory SQLite with deterministic seed
- One live local evaluation over 15 synthetic cases is recorded in
  `reports/agent-live-metrics.json`; no cloud model or production threshold is
  implied.
