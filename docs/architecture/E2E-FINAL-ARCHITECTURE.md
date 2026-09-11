# AegisBank v1.0 End-to-End Architecture

```text
User
  -> AgentOrchestrator
     -> deterministic routing and ownership policy
     -> RAG Retriever / banking READ tools / MCP boundary
     -> grounded response + OTel span + redacted audit event

WRITE request
  -> HITLApprovalManager
  -> HOTLSupervisor gate
  -> IdempotencyGuard
  -> Core Banking transaction + OutboxRepository
  -> LocalMessageBus / IdempotentConsumer
  -> completion or DeadLetterQueue
```

## Trust and Evidence Boundaries

1. The user prompt is untrusted input; deterministic policy decides whether
   private banking data may be accessed.
2. Retrieved documents are untrusted evidence; citation and groundedness checks
   decide whether the agent answers or abstains.
3. The LLM may propose a tool call, but registry, authorization, ownership,
   validation, HITL, HOTL, idempotency, and business rules decide execution.
4. A WRITE cannot reach the core banking repository without explicit approval
   bound to the exact payload digest and a live HOTL safety state.
5. The outbox is the transaction boundary for event publication; consumers are
   idempotent and poison messages go to a DLQ.

Canonical implementations are listed in
`docs/architecture/CANONICAL-COMPONENTS.md`; ownership is defined by
`docs/engineering/OWNERSHIP-MAP.md`.
