# Critical E2E Matrix

**E2E (End-to-End, extremo a extremo)** validates a complete workflow with local
synthetic dependencies. The dedicated suite is `ai/agent/tests/e2e/`; existing focused
acceptance suites are linked below to avoid duplicating every implementation detail.

| ID | Journey | Primary evidence |
|---|---|---|
| A | READ account routing -> `get_my_loans` -> answer | `test_critical_journeys.py` |
| B | `get_my_loans` -> `get_next_installment` -> answer | `test_critical_journeys.py` |
| C | RAG evidence -> grounded answer | `v09/test_knowledge_tool_routing.py` |
| D | RAG gap -> abstention | `v09/test_grounded_knowledge_routing.py` |
| E | WRITE -> MCP -> HITL reject -> zero side effects | `v07/test_mcp_hitl_acceptance.py` |
| F | HITL approve -> idempotent WRITE -> outbox -> consumer | `v08/test_reliability_e2e_acceptance.py` |
| G | HOTL kill-switch -> WRITE blocked | `v09/test_hotl_kill_switch.py` |
| H | retry, circuit breaker and DLQ | `v08/test_failure_injection.py`, `test_idempotent_consumer_dlq.py` |

All journeys use deterministic mocks or in-process components. No live cloud service is
required, and no test introduces a new WRITE capability.
