# ADR-007: Group-Aware Synthetic Evaluation

## Status

Accepted for `v0.3`.

## Context

Each synthetic intent template produces four close variations. A random
sample-level split could place variations from one source template in both train
and evaluation data, creating artificial leakage and inflated metrics.

## Decision

Assign every record a `template_group_id` and keep each group wholly within TRAIN
or HOLDOUT. Use `StratifiedGroupKFold` with the group ID during TRAIN-only
cross-validation. Assert an empty group intersection in every split and fold.

## Alternatives

- **Random sample split:** rejected because paraphrases could cross boundaries.
- **Stratified split without groups:** preserves class ratios but not template
  isolation.
- **No holdout:** rejected because CV alone would not provide a final frozen
  assessment.

## Consequences

- Evaluation better reflects generalization to unseen synthetic template groups.
- Fewer independent groups are available than raw example counts suggest.
- Group-aware splitting does not eliminate broader generator artifacts.
- Holdout discipline and the fixed primary metric must be documented and audited.
