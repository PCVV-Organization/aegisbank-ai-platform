# AegisBank AI Platform — Semantic Routing & Least Agency Architecture

> **Boundary Principle:** *The LLM interprets and proposes; deterministic identity, policy, authorization, validation, and business rules decide.*

---

## 1. Problem Statement & The "Keyword Regex" Antipattern

In early iterations of AegisBank's conversational router (`knowledge_routing.py`), the principle of Least Agency was initially implemented by attempting to reduce the tool allowlist to a single tool prior to model execution.

While effective for structured shortcuts, extending this approach to natural language created a critical architectural defect:
* The deterministic router attempted to anticipate every variation of payment schedule inquiries (`"cuándo vence"`, `"qué día pago"`, `"fecha de pago"`, `"cuándo tengo que pagarlo"`) via a growing catalog of regular expressions (`_PAYMENT_DATE_PATTERNS`).
* If a customer phrased an installment question using syntax not covered by the regex, the router fell back to forcing `get_loan_details`.
* The LLM was blinded: even though it understood that the user was asking for a payment due date, the allowlist prohibited it from calling `get_next_installment`.

This demonstrated the **"Regex NLP Creep" Antipattern**: attempting to solve natural language understanding (NLU) by writing handwritten `if/else` keyword trees rather than using model-driven semantic interpretation.

---

## 2. The Architectural Boundary

The architecture separates responsibilities across two distinct domains:

```text
               USER CONVERSATIONAL QUERY
        "¿LOAN-0001 cuándo tengo que pagarlos?"
                         │
                         ▼
        ┌───────────────────────────────────┐
        │     DETERMINISTIC SECURITY GATE   │
        │  1. Session Authentication        │
        │  2. Tenant Boundary Isolation     │
        │  3. Least Agency Tool Envelope:   │
        │     - get_loan_details            │
        │     - get_next_installment        │
        │     (NO write tools, NO admin)    │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │       LLM / FUNCTION CALLING      │
        │  Interprets intent & proposes:    │
        │  Tool: get_next_installment       │
        │  Args: {"loan_id": "LOAN-0001"}   │
        └─────────────────┬─────────────────┘
                          │
                          ▼
        ┌───────────────────────────────────┐
        │    DETERMINISTIC POLICY & IDOR    │
        │  1. JSON Schema validation        │
        │  2. Ownership check:              │
        │     loan.customer_id == session   │
        │  3. Read vs Write dispatch        │
        └─────────────────┬─────────────────┘
                          │
                          ▼
            Core Banking API / SQLite
```

### Deterministic Responsibilities (Zero-Tolerance)
* **Authentication & Tenant Isolation**: Verifies caller `customer_id`.
* **Tool Envelope Restriction (Least Agency)**: If the query is an account inquiry, write tools (`create_service_request`) and foreign tools are strictly excluded from the offered set.
* **Ownership Invariant (IDOR Defense)**: `ToolRegistry` and `OwnershipGuard` verify that `loan.customer_id == session.customer_id` prior to database execution.
* **Human-in-the-Loop (HITL)**: All state mutations require an out-of-band `ApprovalRequest` with SHA-256 digest validation.

### Probabilistic / Semantic Responsibilities (LLM & Classifiers)
* **Intent & Linguistic Disambiguation**: Understanding paraphrases such as *"¿cuándo me toca pagar?"*, *"¿qué día vence mi cuota?"*, or *"¿cuándo tengo que abonar a LOAN-0001?"*.
* **Tool Selection within Bounded Set**: Selecting between `get_loan_details` and `get_next_installment` based on the user's semantic goal.
* **Argument Extraction**: Extracting canonical entity parameters from conversational context.
* **Natural Grounded Generation**: Explaining the resulting data concisely in conversational language with verified facts.

---

## 3. Fast-Path Optimization vs. Semantic Dispatch

To maintain sub-5ms latency for structured queries while providing robust natural language coverage, routing uses a two-tier mechanism:

| Query Type | Routing Path | Tools Offered | Model Rounds | Latency Target |
|---|---|---|---|---|
| **Explicit Detail Shortcut** (e.g. `"Detalle de LOAN-0001"`, `"Muéstrame LOAN-0001"`, `"Saldo LOAN-0002"`) | Deterministic Fast-Path (`has_explicit_loan_detail_intent`) | `["get_loan_details"]` (prefetched) | 0 rounds | $< 5$ ms |
| **Natural Language Loan Inquiry** (e.g. `"¿LOAN-0001 cuándo tengo que pagarlo?"`) | Semantic Tool Proposal | `["get_loan_details", "get_next_installment"]` | 1 round | Model-dependent |
| **Comparative Query** (e.g. `"¿cuál préstamo tiene más saldo?"`) | Deterministic Multi-Step Plan | `["get_my_loans", "get_next_installment"]` | 0 rounds | $< 10$ ms |
| **Social / Capability** (e.g. `"Hola"`, `"¿qué puedes hacer?"`) | Guardrail Abstention | `[]` (zero tools) | 0 rounds | $< 1$ ms |

---

## 4. Regression & Invariant Verification

The semantic routing contract is verified by automated suites:
1. `test_metamorphic_paraphrase_matrix_loan_details`: Asserts that all 10 explicit loan detail paraphrases route deterministically without pseudo-tool-calls.
2. `test_ambiguous_loan_question_uses_bounded_semantic_tool_proposal`: Asserts that open natural language questions offer the bounded read set `["get_loan_details", "get_next_installment"]` and the model selects `get_next_installment`.
3. `test_explicit_loan_detail_remains_a_zero_round_fast_path`: Asserts 0 model rounds for explicit commands.
4. `test_payment_imperative_never_exposes_a_money_movement_tool`: Asserts that payment imperatives never expose money transfer or payment execution tools.
