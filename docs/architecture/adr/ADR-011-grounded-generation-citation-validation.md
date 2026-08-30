# ADR-011: Grounded generation with citation validation

## Status

Accepted for the `v0.5` implementation; live-model effectiveness pending.

## Context

Retrieval v0.4 returns candidate chunks with provenance, but an LLM can still
invent facts or chunk identifiers, cite obsolete evidence, follow malicious
instructions embedded in retrieved text, or answer despite insufficient
evidence. Prompt instructions alone cannot enforce these invariants.

Generation quality must also be measured separately from the frozen v0.4
retrieval benchmark. Reusing prompt-development examples as the final
generation evaluation set would leak evaluation targets into prompt design.

## Decision

Use the following generation boundary:

`query -> v0.4 Retriever -> deterministic context -> LLMProvider -> strict answer validation`

The implementation must:

- retain `document_id`, `version`, `chunk_id`, and `source` in canonical JSON
  context;
- treat retrieved text as untrusted evidence and place the instruction to
  ignore document-borne commands in the versioned system prompt;
- exclude non-active hits from generation context;
- require exactly `answer`, `citations`, and `abstained` in provider output;
- reject duplicate, empty, or invented citations and require at least one
  retrieved citation for every non-abstained answer;
- abstain deterministically without calling an LLM when no active context
  exists;
- leave sufficiency judgments for non-empty context under the prompt rule,
  without inventing an unmeasured score threshold;
- keep prompt-development and held-out generation-evaluation datasets
  disjoint;
- evaluate generation against frozen contexts so retrieval quality is not
  silently re-measured or tuned.

The prompt is stored centrally as `prompts/rag-answer-v001.json`. Source code
constructs data payloads but contains no alternative answer prompt.

## Evaluation

The deterministic harness defines lexical proxy measurements for
groundedness, answer relevance, completeness, citation validity, citation
coverage, abstention correctness, unsupported-claim rate, and prompt-injection
resistance. These are baseline measurements, not production thresholds.

The held-out cases cover direct support, multiple chunks, active versus
superseded versions, insufficient evidence, an out-of-domain query, and a
synthetic retrieval hit containing a malicious instruction. The adversarial
hit belongs only to generation evaluation and does not modify the v0.4 corpus.

## Alternatives

- **Trust model-generated citations:** rejected because chunk provenance is a
  deterministic invariant and can be checked after generation.
- **Strip suspicious text heuristically:** rejected because filtering can
  destroy legitimate evidence and cannot identify every injection. Context is
  instead labeled untrusted and output remains constrained and validated.
- **Tune a retrieval or confidence threshold on the held-out set:** rejected
  because it would contaminate evaluation and retrospectively alter v0.4.
- **Use an LLM judge as the only evaluator:** deferred because no live provider
  is authorized and judge variance would remove deterministic reproducibility.

## Consequences

- Accepted answers cannot cite a chunk absent from the actual supplied
  context.
- Superseded evidence cannot pass through the default context builder.
- Malformed or invented provider output is rejected rather than repaired.
- Prompt-injection resistance is a defense-in-depth prompt property, not a
  claim of complete security; it still requires live adversarial evaluation.
- Generation metrics remain unavailable until a real provider is authorized.
