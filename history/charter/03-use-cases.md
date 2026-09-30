# 03 - Use Cases

| Field | Value |
| --- | --- |
| Project | AegisBank AI Platform |
| Milestone | `v0.1.0 - Project Charter` |
| Status | Ready for review |
| Data classification | Synthetic only |

## Shared Rules

These rules apply to every use case:

- All people, identities, products, accounts, loans, installments, and records are fictitious.
- Authentication, authorization, policy, validation, and business rules are deterministic.
- The LLM may interpret, retrieve, draft, and select an allowed tool; it cannot authorize an operation.
- A response must not imply that AegisBank is a real bank or that information is financial advice.
- Correlation and trace identifiers follow every implemented execution boundary.
- Audit and telemetry records minimize data and do not store secrets or full prompts by default.
- If required evidence, authorization, or dependency health is insufficient, the safe outcome is denial, abstention, or a degraded response.

For UC-004, a **material edit** changes any field included in the approved action
digest, including requester, category, complaint body, attachments, or routing
metadata. A non-material edit is limited to presentation that leaves the digest
and business effect unchanged.

Quality thresholds marked `TBD after baseline` must be established through the
procedure in [05 - Success criteria](05-success-criteria.md), not chosen to make a
single run pass.

## UC-001 - Product Question Through RAG

### Actor

Synthetic customer.

### Preconditions

- The request is within the fictitious banking domain.
- An authorized corpus exists with document identity, version, validity dates, status, and source metadata.
- Only active and currently effective sources are eligible for retrieval.
- The RAG and policy components are healthy or can return a controlled degraded outcome.

### Happy Path

1. The customer asks a product, fee, requirement, policy, or FAQ question.
2. Input controls classify the request and isolate untrusted instructions from source content.
3. Retrieval searches only the authorized, effective corpus.
4. The system evaluates whether retrieved evidence is sufficient.
5. Aegis generates an answer constrained to that evidence.
6. The response identifies its sources and their versions.
7. Retrieval, generation, policy, latency, correlation, and trace metadata are recorded with data minimization.

### Alternative Path

- If the request is ambiguous, Aegis asks a bounded clarification question.
- If multiple current sources apply, Aegis synthesizes them and cites each material source.
- If an obsolete source is retrieved, lifecycle filtering excludes it and records the exclusion for diagnostics.
- If the question is unsupported but safe, the flow transitions to UC-005.

### Failure Path

- If retrieval is unavailable, Aegis does not answer from model memory as if the answer were authoritative.
- If generation fails after successful retrieval, the system returns a controlled error with a correlation identifier.
- If sources conflict, Aegis reports the conflict or abstains; it does not silently choose one.
- If malicious source text attempts to override system or tool policy, it is treated as untrusted data and cannot authorize an action.

### Security Considerations

- Corpus ingestion and source status are controlled; arbitrary user content is not automatically trusted as knowledge.
- Retrieved text cannot override system, identity, authorization, approval, or tool policy.
- Product answers do not expose synthetic customer data or call write tools.
- Citations use stable document identifiers and do not reveal restricted storage locations or credentials.

### Audit Requirements

- Intent and policy outcome.
- Prompt and agent version identifiers, not unrestricted prompt content.
- Retrieved document IDs, versions, lifecycle status, and retrieval scores.
- Evidence-sufficiency and abstention decision.
- Response/citation status, latency, correlation ID, and trace ID.

### Acceptance Criteria

- Every material factual claim in a supported answer maps to an eligible cited source.
- No obsolete or unauthorized document is presented as current evidence.
- Insufficient evidence produces UC-005 rather than an unsupported answer.
- Retrieval and generation quality are measured separately on a versioned dataset.
- Citation correctness and groundedness thresholds are `TBD after baseline`; HITL and authorization are not applicable because this use case is read-only.
- An evaluator can reconstruct the source-selection decision from minimized audit metadata.

## UC-002 - Synthetic Installment Inquiry

### Actor

Authenticated synthetic customer.

### Preconditions

- The synthetic identity is authenticated and bound to one allowed synthetic customer profile.
- A read-only installment tool/API contract is available.
- Authorization policy permits only the requested customer's records.
- The mock dependency is healthy or has a defined degraded response.

### Happy Path

1. The customer asks when the next simulated installment is due.
2. Aegis identifies an `account_query` intent and proposes the read-only tool.
3. Deterministic policy validates identity, resource ownership, tool scope, and input schema.
4. The tool returns only the minimum installment fields needed for the answer.
5. Aegis explains the due date and amount as simulated data.
6. The call and answer are correlated, traced, and audited.

### Alternative Path

- If more than one simulated loan is eligible, Aegis asks the customer to choose using non-sensitive labels.
- If no future installment exists, Aegis reports that result without inventing a date or amount.
- If the question is general rather than customer-specific, the request is routed to UC-001.

### Failure Path

- Invalid or unauthorized resource identifiers are rejected without confirming whether another record exists.
- A timeout or transient dependency error follows the approved bounded retry policy only when the operation is safe to retry.
- Persistent failure transitions to UC-006.
- Invalid tool output is rejected and cannot be rendered as trusted customer information.

### Security Considerations

- Read scope is least privilege and bound to the authenticated synthetic subject.
- The model cannot substitute a different customer ID or broaden query scope.
- Tool arguments and results are schema-validated.
- Only minimum necessary simulated fields are returned to the model and user.

### Audit Requirements

- Synthetic actor and subject identifiers or approved pseudonymous references.
- Intent, selected tool, policy decision, argument hash, result hash/status, and tool version.
- Dependency outcome, retry count if any, latency, correlation ID, and trace ID.
- No unrestricted account payload in the audit record.

### Acceptance Criteria

- Authorized requests return the correct fixture-backed due date and amount.
- Cross-customer and malformed requests are denied without record-existence leakage.
- Tool input and output pass their contracts.
- No write or approval flow is invoked.
- The E2E path preserves correlation and trace context.

## UC-003 - Synthetic Loan Inquiry

### Actor

Authenticated synthetic customer.

### Preconditions

- The synthetic identity and customer-resource binding are valid.
- A read-only loan-summary tool/API contract is available.
- Synthetic loan fixtures have deterministic balances and status.

### Happy Path

1. The customer asks for the outstanding amount or status of a simulated loan.
2. Aegis classifies the request as `account_query` and selects the loan-summary read tool.
3. Deterministic policy validates subject, scope, resource, and tool arguments.
4. The tool returns a minimal, schema-valid simulated summary.
5. Aegis presents the result with an explicit fictitious-data qualifier.
6. The execution is audited and traced.

### Alternative Path

- If several simulated loans exist, Aegis requests a safe disambiguation.
- If the loan is closed, Aegis reports the fixture status rather than calculating an unsupported balance.
- Product terms or fee explanations are routed to UC-001 and cited from the corpus.

### Failure Path

- Missing, malformed, or unauthorized IDs fail closed.
- Inconsistent tool output is quarantined as an integration error.
- Transient and persistent failures follow UC-006 behavior.
- Aegis does not estimate a balance when the source system cannot provide one.

### Security Considerations

- Identity and authorization execute outside the LLM.
- The tool cannot enumerate customers or loans.
- Responses and telemetry expose only the minimum synthetic fields required.
- Read annotations are not treated as a security boundary by themselves; server-side policy remains authoritative.

### Audit Requirements

- Actor/subject reference, intent, tool and contract version, policy result, and execution status.
- Argument/result hashes or approved summaries rather than unrestricted payloads.
- Dependency health decision, latency, correlation ID, and trace ID.

### Acceptance Criteria

- Results exactly match authorized synthetic fixtures.
- Unauthorized access and enumeration attempts are denied and tested.
- General knowledge and customer-data claims retain separate evidence paths.
- No write, approval, or financial transaction occurs.
- Contract, integration, and E2E tests cover success, empty, unauthorized, invalid, and degraded outcomes.

## UC-004 - Create A Complaint With HITL

### Actor

Authenticated synthetic customer as requester; authorized human as approver.

### Preconditions

- The requester and synthetic customer context are authenticated and authorized.
- Complaint categories and required fields are defined by deterministic business rules.
- The write tool/API accepts an `Idempotency-Key` and has proven duplicate protection.
- Approval is explicit, time-bounded, and bound to the exact proposed action and payload digest.
- Audit and persistence are available; messaging may be introduced in its approved phase.

### Happy Path

1. The customer asks to register a fictitious complaint.
2. Aegis classifies `service_request`, obtains only required context, and drafts the complaint.
3. Validation and policy evaluate the proposed action outside the LLM.
4. The system shows the exact proposed effect and asks for explicit approval.
5. The human approves without changing the approved payload.
6. The system revalidates identity, policy, approval binding/expiry, schema, and business rules.
7. The write tool calls the mock banking API with an `Idempotency-Key`.
8. One service-request record is persisted and receives one stable business identifier.
9. The eventual messaging design emits `ServiceRequestCreated` without creating a second business record.
10. The system records minimized approval, execution, event, audit, correlation, and trace evidence.
11. Aegis returns the stable fictitious request identifier and status.

### Alternative Path

- The human rejects the proposal; no write occurs and the rejection is audited.
- The human edits material content; the old approval is invalidated and a new proposal requires approval.
- The same approved request is repeated with the same idempotency key; the existing identifier is returned.
- Validation requests missing information before an approval can be granted.
- A non-material presentation correction may be allowed only if policy explicitly defines it and the action digest remains unchanged.

### Failure Path

- Missing, expired, mismatched, or rejected approval fails closed before tool execution.
- Authorization or business-rule failure is never retried.
- A known transient error may be retried only after idempotency is proven and within bounded policy.
- If the response is lost after persistence, replaying the same idempotency key returns the existing record.
- If event publication fails after persistence, recovery must not recreate the complaint; the reliability design records and repairs the pending event.
- A persistent dependency failure opens the circuit and returns a controlled outcome under UC-006.

### Security Considerations

- The LLM cannot approve, forge, reuse, or widen an approval.
- Approval is bound to actor, action, payload digest, policy version, and expiry.
- Authorization is checked again immediately before execution to prevent time-of-check/time-of-use bypass.
- Tool schema, server-side policy, business rules, and idempotency are enforced independently of prompts.
- Complaint text is minimized/redacted in telemetry; secrets and unnecessary personal data are prohibited.
- Operators can disable the write tool or suspend execution.

### Audit Requirements

- Proposal ID and digest, synthetic requester, approver reference, approval result, timestamp, and expiry.
- Identity, policy, authorization, validation, and business-rule versions/outcomes.
- Idempotency-key hash, tool/API version, business identifier, execution status, and error code.
- Event ID/status when messaging exists.
- Agent/model/prompt versions, latency, correlation ID, and trace ID.
- No raw secret, token, unrestricted prompt, or unnecessary complaint payload.

### Acceptance Criteria

- Zero writes occur without valid explicit approval in the complete negative test suite.
- Zero writes occur when deterministic authorization or validation denies the action.
- Replays with the same idempotency key produce one business record and the same identifier.
- A material edit invalidates prior approval and requires a new approval.
- Retry tests demonstrate idempotent behavior before retry is enabled.
- The approved success flow produces one reconstructable business outcome, event state, audit chain, and user response.
- Contract and E2E tests cover approve, reject, edit, expire, duplicate, timeout-before-write, timeout-after-write, and persistent failure.

## UC-005 - Abstain For Insufficient Evidence

### Actor

Any user of Aegis.

### Preconditions

- The request requires factual support from the authorized corpus or a controlled data source.
- Evidence sufficiency and policy rules are available.

### Happy Path

1. Retrieval or tool evidence is missing, insufficient, conflicting, obsolete, unauthorized, or below the established threshold.
2. Aegis states that it cannot answer reliably from the available authorized information.
3. The response does not fill the gap from unsupported model memory.
4. When safe, Aegis suggests a bounded clarification or an approved escalation path.
5. The reason category and evidence metadata are audited without exposing restricted content.

### Alternative Path

- A clarification produces a supported query and routes back to UC-001, UC-002, or UC-003.
- Conflicting sources are identified transparently and sent for source-governance review.
- An unsupported request outside the project boundary is declined without implying future support.

### Failure Path

- If the model attempts to answer despite an abstention decision, output controls block or replace the response.
- If the evidence service is unavailable, unavailability is not misrepresented as proof that no answer exists.
- Repeated unsupported requests do not relax policy or tool permissions.

### Security Considerations

- Abstention must not disclose hidden policies, prompts, restricted source content, or another synthetic customer's data.
- Prompt injection cannot redefine the sufficiency threshold or authorize an ungrounded answer.
- Escalation suggestions cannot invoke a write without the UC-004 approval path.

### Audit Requirements

- Intent, evidence category, eligible source/tool set, sufficiency decision, and reason code.
- Prompt/policy/retrieval versions, output-control result, correlation ID, and trace ID.
- No chain-of-thought or unrestricted prompt capture.

### Acceptance Criteria

- The versioned evaluation set contains answerable, unanswerable, conflicting, obsolete, and adversarial cases.
- Every case classified as insufficient by policy produces an abstention or bounded clarification.
- The system does not cite irrelevant evidence merely to avoid abstaining.
- Abstention correctness thresholds are `TBD after baseline` and become release gates after approval.
- Human reviewers can distinguish correct abstention, false refusal, and unsupported answer rates.

## UC-006 - Degraded External Dependency

### Actor

Synthetic customer; operator as HOTL supervisor.

### Preconditions

- A controlled dependency simulator can produce transient errors, timeouts, malformed responses, and persistent failures.
- Operations are classified by read/write semantics, idempotency, retry eligibility, timeout, and fallback policy.
- Retry and circuit-breaker policies have bounded configuration and observable state.

### Happy Path

1. A dependency call encounters a classified transient failure.
2. The system records the attempt and applies only the operation-specific bounded retry policy.
3. Backoff and jitter are applied where appropriate.
4. A later attempt succeeds within the request's time budget.
5. The user receives one logical result and operators can see the recovered failure without duplicate business effects.

### Alternative Path

- A non-transient failure fails immediately without retry.
- Repeated failures cross the configured threshold and open the circuit.
- While open, calls fail fast with a controlled response.
- After the recovery interval, limited half-open probes determine whether the circuit closes or reopens.
- A read may use a documented safe fallback; a write never fabricates success.

### Failure Path

- Retry exhaustion returns a controlled degraded response with a correlation identifier.
- A write with unknown outcome is reconciled by idempotency key before any new attempt.
- Malformed success responses are treated as integration failures, not trusted results.
- Failure of observability or audit on a protected write fails according to the future approved safety policy; it is never silently ignored.

### Security Considerations

- Dependency degradation cannot bypass identity, authorization, approval, validation, or evidence controls.
- Error responses avoid stack traces, secrets, internal topology, and record-existence leakage.
- Retry budgets prevent resource exhaustion; circuit state changes are operator-visible.
- Operators can suspend the agent or disable a tool during an incident.

### Audit Requirements

- Dependency and operation class, attempt count, timeout, retry reason, and final outcome.
- Circuit state transition, threshold/config version, recovery probe, and operator action if any.
- Idempotency reference for writes, error code, latency, correlation ID, and trace ID.
- Metrics distinguish initial failure, recovered request, exhausted retry, open-circuit rejection, and duplicate prevention.

### Acceptance Criteria

- Tests prove that only classified transient failures are retried and all retries are bounded.
- Write retry tests prove idempotency and no duplicate business record.
- Circuit tests cover `CLOSED`, `OPEN`, and `HALF_OPEN` transitions and fail-fast behavior.
- Persistent failures do not trigger unbounded calls or cascading resource exhaustion in the test scenario.
- Users receive truthful degraded outcomes and operators can reconstruct the incident.
- Recovery metrics and policy thresholds are `TBD after baseline` where workload evidence is required.

## Use-Case Traceability

| Use case | Capability | Primary milestone | Critical control |
| --- | --- | --- | --- |
| UC-001 | Grounded product answer | `v0.4` | Authorized current sources and citations |
| UC-002 | Synthetic installment read | `v0.5` | Subject-bound read authorization |
| UC-003 | Synthetic loan read | `v0.5` | Least-privilege tool contract |
| UC-004 | Complaint write | `v0.6`/`v0.7` | HITL, deterministic authorization, and idempotency |
| UC-005 | Safe abstention | `v0.4`/`v0.8` | Evidence sufficiency and output guardrail |
| UC-006 | Dependency degradation | `v0.7` | Failure classification, bounded retry, and circuit breaker |
