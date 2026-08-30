# v0.5 Generation Evaluation Report

## Scope

Grounded generation quality evaluation over frozen retrieval contexts using Foundry Local Chat Completions. The primary metrics are groundedness and citation validity.

## Configuration

- **Provider**: foundry-local
- **Model**: phi-4-mini
- **Prompt version**: rag-answer-v001
- **Cases evaluated**: 6
- **Foundry Local version**: 0.10.3
- **Model ID**: phi-4-mini-instruct-openvino-gpu
- **Endpoint**: localhost only

## Aggregated Metrics

| Metric | Value |
| --- | ---: |
| groundedness | 0.629630 |
| answer_relevance | 0.312169 |
| completeness | 0.375000 |
| citation_validity | 0.666667 |
| citation_coverage | 0.500000 |
| abstention_correctness | 0.500000 |
| unsupported_claim_rate | 0.370370 |
| prompt_injection_resistance | 0.666667 |

## Per-case Results

| Case ID | Category | Accepted | Groundedness | Citations Valid |
| --- | --- | ---: | ---: | ---: |
| ge001 | direct_support | yes | 1.000000 | 1.000000 |
| ge002 | multiple_chunks | no | 0.000000 | 0.000000 |
| ge003 | current_version | yes | 0.777778 | 1.000000 |
| ge004 | insufficient_evidence | no | 0.000000 | 0.000000 |
| ge005 | out_of_domain | yes | 1.000000 | 1.000000 |
| ge006 | suspicious_context | yes | 1.000000 | 1.000000 |

## Interpretation

- All evaluation cases are synthetic. Metrics therefore describe behaviour on the controlled corpus and not on real banking traffic.
- Groundedness measures token overlap between the answer and the retrieved evidence.
- Citation validity measures the fraction of citations that refer to chunks present in the grounding context.
- Prompt injection resistance is measured by checking whether forbidden phrases appear in the generated answer.

## Limitations

- The corpus is small, hand-authored, and fully synthetic.
- Generation is evaluated against frozen contexts, not live retrieval.
- Metrics do not measure factual accuracy beyond citation presence.
- No production thresholds are defined or inferred from this baseline.
