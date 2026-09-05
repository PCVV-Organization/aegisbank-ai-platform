"""A/B testing harness and paired statistical hypothesis testing for agent variants."""

from __future__ import annotations

import math
import random
from dataclasses import dataclass
from typing import Any, Sequence

from aegisbank_agent.agent import AgentOrchestrator
from aegisbank_agent.evaluation.evaluators import (
    EvalCase,
    evaluate_case,
)


@dataclass(frozen=True, slots=True)
class ContingencyTable:
    """2x2 contingency table for paired binary evaluation."""

    both_passed: int  # a
    baseline_passed_candidate_failed: int  # b
    baseline_failed_candidate_passed: int  # c
    both_failed: int  # d

    @property
    def total(self) -> int:
        return (
            self.both_passed
            + self.baseline_passed_candidate_failed
            + self.baseline_failed_candidate_passed
            + self.both_failed
        )

    @property
    def discordant_count(self) -> int:
        return self.baseline_passed_candidate_failed + self.baseline_failed_candidate_passed


def mcnemar_test(
    baseline_passed: Sequence[bool],
    candidate_passed: Sequence[bool],
    continuity_correction: bool = True,
) -> dict[str, Any]:
    """Execute McNemar's test for paired nominal data with Edwards continuity correction.

    H0: The marginal probabilities of success for baseline and candidate are equal (P(b) == P(c)).
    H1: Candidate performance differs significantly from baseline.
    """
    if len(baseline_passed) != len(candidate_passed):
        raise ValueError("Baseline and candidate must have identical sample sizes.")

    a = sum(1 for b, c in zip(baseline_passed, candidate_passed) if b and c)
    b = sum(1 for b, c in zip(baseline_passed, candidate_passed) if b and not c)
    c = sum(1 for b, c in zip(baseline_passed, candidate_passed) if not b and c)
    d = sum(1 for b, c in zip(baseline_passed, candidate_passed) if not b and not c)

    discordant = b + c
    if discordant == 0:
        return {
            "statistic": 0.0,
            "p_value": 1.0,
            "effect_size_cohens_g": 0.0,
            "contingency_table": {
                "both_passed": a,
                "baseline_only": b,
                "candidate_only": c,
                "both_failed": d,
            },
            "statistically_significant": False,
        }

    if continuity_correction:
        diff = max(0.0, abs(b - c) - 1.0)
        chi2 = (diff**2) / discordant
    else:
        chi2 = ((b - c) ** 2) / discordant

    # For 1 degree of freedom: p-value = 1 - erf(sqrt(chi2 / 2)) = erfc(sqrt(chi2 / 2))
    p_value = math.erfc(math.sqrt(chi2 / 2.0))

    # Cohen's g for McNemar: g = |(b / (b + c)) - 0.5|
    cohens_g = abs((c / discordant) - 0.5)

    return {
        "statistic": round(chi2, 4),
        "p_value": round(p_value, 6),
        "effect_size_cohens_g": round(cohens_g, 4),
        "contingency_table": {
            "both_passed": a,
            "baseline_only": b,
            "candidate_only": c,
            "both_failed": d,
        },
        "statistically_significant": p_value < 0.05,
    }


def bootstrap_paired_confidence_interval(
    baseline_passed: Sequence[bool],
    candidate_passed: Sequence[bool],
    confidence: float = 0.95,
    n_resamples: int = 1000,
    seed: int = 42,
) -> tuple[float, float, float]:
    """Compute non-parametric bootstrap confidence interval for paired accuracy delta.

    Returns:
        tuple of (point_estimate_delta, ci_lower, ci_upper)
    """
    n = len(baseline_passed)
    if n == 0 or len(candidate_passed) != n:
        raise ValueError("Invalid sample sizes for paired bootstrap.")

    base_arr = [1.0 if x else 0.0 for x in baseline_passed]
    cand_arr = [1.0 if x else 0.0 for x in candidate_passed]

    point_delta = (sum(cand_arr) - sum(base_arr)) / n

    rng = random.Random(seed)
    sampled_deltas: list[float] = []

    pairs = list(zip(base_arr, cand_arr))
    for _ in range(n_resamples):
        sample = [rng.choice(pairs) for _ in range(n)]
        b_mean = sum(p[0] for p in sample) / n
        c_mean = sum(p[1] for p in sample) / n
        sampled_deltas.append(c_mean - b_mean)

    sampled_deltas.sort()
    alpha = 1.0 - confidence
    lower_idx = max(0, int((alpha / 2.0) * n_resamples))
    upper_idx = min(n_resamples - 1, int((1.0 - (alpha / 2.0)) * n_resamples) - 1)

    return (
        round(point_delta, 4),
        round(sampled_deltas[lower_idx], 4),
        round(sampled_deltas[upper_idx], 4),
    )


class ABExperimentHarness:
    """Executes paired A/B evaluation between baseline and candidate orchestrators."""

    def __init__(
        self,
        baseline_orchestrator: AgentOrchestrator,
        candidate_orchestrator: AgentOrchestrator,
    ) -> None:
        self.baseline = baseline_orchestrator
        self.candidate = candidate_orchestrator

    def run(
        self,
        cases: list[EvalCase],
        n_resamples: int = 1000,
        seed: int = 42,
    ) -> dict[str, Any]:
        """Run A/B evaluation across all cases and perform statistical tests."""
        baseline_results = [evaluate_case(self.baseline, c) for c in cases]
        candidate_results = [evaluate_case(self.candidate, c) for c in cases]

        # Extract boolean vector for task completion
        base_completion = [r["task_completed"] for r in baseline_results]
        cand_completion = [r["task_completed"] for r in candidate_results]

        # Extract boolean vector for tool selection
        base_selection = [r["selection_correct"] for r in baseline_results]
        cand_selection = [r["selection_correct"] for r in candidate_results]

        mcnemar_completion = mcnemar_test(base_completion, cand_completion)
        mcnemar_selection = mcnemar_test(base_selection, cand_selection)

        delta, ci_low, ci_high = bootstrap_paired_confidence_interval(
            base_completion,
            cand_completion,
            n_resamples=n_resamples,
            seed=seed,
        )

        base_acc = sum(1 for x in base_completion if x) / len(cases) if cases else 0.0
        cand_acc = sum(1 for x in cand_completion if x) / len(cases) if cases else 0.0

        return {
            "sample_size": len(cases),
            "baseline_accuracy": round(base_acc, 4),
            "candidate_accuracy": round(cand_acc, 4),
            "accuracy_delta": delta,
            "bootstrap_ci_95": {"lower": ci_low, "upper": ci_high},
            "mcnemar_task_completion": mcnemar_completion,
            "mcnemar_tool_selection": mcnemar_selection,
            "recommendation": (
                "PROMOTE" if delta >= 0.0 and ci_low >= -0.05 and cand_acc >= base_acc else "REJECT"
            ),
        }
