# Conversational Relevance and Intent Robustness (v0.13.0-R1 Snapshot)

> **Historical milestone:** `v0.13.0-R1 — Intent Robustness + Conversational Relevance Regression`.
> This record describes a previously addressed defect and regression contract. It is not proof of current behavior; verify current routing code and tests before relying on it.
> Spanish user utterances are intentionally preserved as test examples because the application evaluates Spanish-language requests.

## 1. Reported Defect

A manual end-to-end session found that two semantically equivalent Spanish utterances produced different tool behavior:

| User utterance | Tools executed | Recorded result |
|---|---|---|
| `Dame detalle de mi prestamo LOAN-0001` | `get_my_loans` + `get_loan_details` | Expected path |
| `Dame detalle de mi LOAN-0001` | 0; model emitted a pseudo-tool call | Defect |

The recorded root cause was a router condition that depended on the word `prestamo`. Without that keyword, `phi-4-mini` remained in automatic tool-selection mode and sometimes wrote a tool-call imitation as plain text instead of emitting a structured tool call.

Other reported issues were: greetings exposed internal categories; capability questions exposed internal tool names; and ambiguous complaint questions needed clarification to distinguish schema fields from policy requirements.

## 2. Recorded Routing Design

### 2.1. Deterministic loan ID extraction

The snapshot records `extract_loan_id(query)` in `ai/agent/src/aegisbank_agent/knowledge_routing.py`, using the case-insensitive expression `\\bLOAN-[0-9]{4}\\b` and returning canonical uppercase IDs. The expression was reused from the mock Core Banking contract.

### 2.2. Account-tool allowlist

The recorded `account_tool_allowlist(query)` behavior is:

1. An explicit `LOAN-XXXX` selects `get_loan_details`, plus `get_next_installment` when the utterance asks about an installment or due date.
2. `mis prestamos` / `mi prestamo` selects `get_my_loans`.
3. `proxima cuota` / `cuanto debo` selects `get_next_installment`.
4. A detail request without an ID first resolves the user's loans, then selects the requested loan detail.

`requires_account_data(query)` was also documented to return true for an explicit loan ID, even without the word `prestamo`. `classify_service_inquiry(query)` separates `DOMAIN_SCHEMA`, `RAG`, and `CLARIFICATION` paths for complaint-related questions.

### 2.3. Deterministic explicit-ID execution

The snapshot says the orchestrator directly executes the sole allowlisted account tool when an explicit loan ID is present and `get_my_loans` is not required. This avoids depending on model-generated structured tool calls. The result should be built from the actual Core Banking tool result, not pseudo-tool text.

Verify that this branch still exists in current `agent.py` and is covered by current tests before treating it as an active guarantee.

### 2.4. Greeting, capability, and clarification behavior

- Short greetings are detected without invoking tools and receive a fixed, customer-oriented response.
- Capability explanations should avoid exposing internal tool names or categories.
- Ambiguous requests should ask the user to clarify rather than choose an arbitrary interpretation or execute an arbitrary tool.

The historical record mentions prompt `agent-system-v003`; prompt versions and implementations may have changed.

## 3. Recorded Regression Tests

The snapshot points to `ai/agent/tests/v013r1/` and these suites:

- `test_routing_helpers.py` — loan ID, greeting, clarification, capability, and service-inquiry helpers.
- `test_orchestrator_intent_robustness.py` — paraphrase routing, pseudo-tool-call regression, greeting/capability behavior, ambiguity, and ownership.
- `test_intent_robustness_regression.py` — seven paraphrases, cross-customer ownership, multi-loan disambiguation, and prompt loading.

The historical command was `python scripts/quality_gate.py --gate-intent-robustness`. Run it only if it remains available in the current checkout; report fresh output separately from this record.

## 4. Recorded Design Decisions

1. Reuse the existing `extract_loan_id`, `IdempotencyGuard`, `AuditLogger`, metrics, logging, and tracing components.
2. Extend `account_tool_allowlist` and `requires_account_data` with entity-based detection rather than duplicating the routing contract.
3. Keep the loan ID extractor in the canonical routing module because the snapshot found no existing entity extractor.
4. When there is one safe allowlisted tool and an explicit ID, prefer deterministic execution over a model-generated pseudo-call.
5. Update tests that encode obsolete behavior; do not remove regression coverage merely to make a suite pass.

## 5. Recorded Status and Lessons

The snapshot labeled local intent robustness and local Event Grid handling as covered, while cloud Functions/Event Grid remained pending. These are historical labels, not fresh test evidence.

Lessons recorded for agent systems:

- Evaluate intent resolution and tool selection across the full conversation, not a single turn.
- Metamorphic paraphrase tests help detect semantic-routing regressions.
- Exact-keyword routing is brittle; deterministic entity extraction should be separate from natural-language phrasing.
- Convert manually discovered end-to-end failures into automated regressions, especially pseudo-tool-call behavior.
