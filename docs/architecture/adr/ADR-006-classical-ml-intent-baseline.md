# ADR-006: Classical ML Intent Baseline

## Status

Accepted for `v0.3`.

## Context

The platform needs a measurable baseline for classifying synthetic Spanish
banking queries before considering more complex NLP systems. Without a classical
reference, later comparisons could add cost and risk without demonstrated value.

## Decision

Establish a reproducible TF-IDF plus Logistic Regression pipeline first. Compare
it with a deterministic `DummyClassifier` floor using group-aware cross-validation
and one frozen synthetic holdout evaluation. Keep the component offline and
independent from the Core Banking API.

## Alternatives

- **Rules only:** transparent but brittle, difficult to measure across linguistic
  variation, and not a learned baseline.
- **Transformer:** potentially stronger language representation but unnecessary
  complexity, compute, and dependency surface before a classical baseline exists.
- **LLM classifier:** adds external model behavior, cost, prompt sensitivity, and
  governance concerns that are outside `v0.3`.

## Consequences

- The experiment is small, local, inexpensive, and reconstructible from Git.
- Results provide a comparison point rather than a production claim.
- TF-IDF may depend heavily on lexical and template artifacts.
- Transformers and LLMs remain unimplemented and require later authorization.
