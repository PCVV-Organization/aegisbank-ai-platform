# ADR-010: Provider-agnostic LLM boundary

## Status

Accepted for the `v0.5` implementation; live-provider validation pending.

## Context

Grounded generation needs one language-model call after retrieval and context
construction. Binding the pipeline directly to one vendor SDK would mix
provider authentication, request syntax, model selection, and response parsing
with AegisBank's deterministic evidence rules. It would also force a network
dependency before a provider is explicitly authorized.

The current environment contains no configured AegisBank, OpenAI, Azure
OpenAI, Anthropic, Google, or Ollama provider/model variables. Creating an
account, resource, credential, or paid call is outside the authorized scope.

## Decision

Define a minimal `LLMProvider` boundary in `ai/rag` with:

- provider and model identity exposed as non-secret metadata;
- one `generate(LLMRequest) -> str` operation;
- a provider-neutral request carrying prompt version, system prompt, user
  payload, and response schema;
- no provider SDK, credential lookup, retry policy, tool call, agent, MCP, or
  HITL dependency in the core generation package.

Concrete network adapters are deferred until a provider and model are
explicitly authorized through the environment. Deterministic test providers
remain test-only and cannot be reported as live-model evaluation.

## Alternatives

- **Adopt a vendor SDK immediately:** rejected because no provider is
  configured or authorized and a speculative dependency has no current use.
- **Use the pre-existing Agent SDK decision:** rejected for this milestone
  because Agent, tools, MCP, and HITL are explicitly out of scope. ADR-003 is
  not activated or superseded by this decision.
- **Pass a bare callable:** rejected because provider/model metadata and a
  versioned structured request are required for reproducible evaluation.

## Consequences

- Grounding and citation validation remain deterministic and vendor-neutral.
- A later adapter can be replaced without changing retrieval, context, prompt,
  answer, or evaluation contracts.
- No live generation metric exists until an authorized adapter is configured
  and executed.
- Provider-specific structured-output guarantees, token limits, and failure
  behavior remain unvalidated.
