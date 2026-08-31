# ADR-013: Deterministic Tool Authorization and Ownership Boundary

## Status

Accepted for `v0.6`.

## Context

The agent interacts with synthetic core banking records and general knowledge. In financial and conversational AI architectures, LLMs cannot be treated as authorization decision-makers. Allowing the model to specify customer identities or to execute unconstrained actions introduces high security risks (such as unauthorized cross-customer data access, prompt injection overrides, or inadvertent state mutations).

For milestone `v0.6.0 — Single Agent + Read-Only Function Tools`, the system requires strict, non-bypassable controls ensuring:
1. The authenticated customer identity is deterministic and immutable.
2. Only verified read-only function tools can be executed.
3. Access to customer-specific resources enforces resource ownership before data is returned.
4. No write or state-changing operations are exposed or executable by the agent.

## Decision

Implement deterministic authorization and customer ownership validation in the agent runtime:

1. **Session Context Invariant**:
   - `AgentContext(session_customer_id: str)` is instantiated at the session boundary.
   - The LLM never provides or alters the `customer_id`.

2. **Strict Tool Allowlist**:
   - The `ToolRegistry` enforces an explicit allowlist of registered `FunctionTool` instances:
     - `search_knowledge(query: str)`
     - `get_my_loans()`
     - `get_loan_details(loan_id: str)`
     - `get_next_installment(loan_id: str)`
   - Any unknown tool name or unauthorized function call is rejected with `success=False` and an explicit error message.

3. **Deterministic Resource Ownership Check**:
   - For resource-specific tools (`get_loan_details`, `get_next_installment`), the repository layer checks:
     `loan.customer_id == context.session_customer_id`
   - If the loan belongs to another synthetic customer, the tool returns `success=False` with an ownership denial message.

4. **Zero Write Exposure**:
   - No write tools (such as service requests, transfers, or updates) are registered or made available in tool definitions sent to the LLM.

## Consequences

### Positive
- Cross-customer access attempts are deterministically blocked regardless of prompt injection or model hallucination.
- Identity cannot be forged by model output.
- Complete auditability of every tool execution via structured `ToolCallRecord`.

### Negative
- Multi-customer delegated access scenarios require future explicit authorization frameworks.
