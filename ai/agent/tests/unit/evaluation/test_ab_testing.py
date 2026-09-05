"""Unit tests for A/B testing and statistical significance testing."""

from __future__ import annotations

import pytest

from aegisbank_agent.evaluation.ab_testing import (
    bootstrap_paired_confidence_interval,
    mcnemar_test,
)

pytestmark = pytest.mark.unit


def test_mcnemar_test_identical_samples() -> None:
    base = [True, True, False, False, True]
    cand = [True, True, False, False, True]

    res = mcnemar_test(base, cand)
    assert res["statistic"] == 0.0
    assert res["p_value"] == 1.0
    assert res["statistically_significant"] is False
    assert res["contingency_table"]["baseline_only"] == 0
    assert res["contingency_table"]["candidate_only"] == 0


def test_mcnemar_test_significant_difference() -> None:
    # 25 discordant pairs where candidate solved what baseline missed
    base = [False] * 25 + [True] * 25
    cand = [True] * 25 + [True] * 25

    res = mcnemar_test(base, cand)
    assert res["statistic"] > 3.841  # Critical value for alpha = 0.05
    assert res["p_value"] < 0.001
    assert res["statistically_significant"] is True
    assert res["effect_size_cohens_g"] > 0.4


def test_bootstrap_paired_confidence_interval_bounds() -> None:
    base = [False] * 10 + [True] * 20
    cand = [True] * 10 + [True] * 20

    delta, ci_low, ci_high = bootstrap_paired_confidence_interval(
        base,
        cand,
        confidence=0.95,
        n_resamples=500,
        seed=42,
    )

    assert delta == pytest.approx(10 / 30, abs=0.01)
    assert ci_low <= delta <= ci_high
    assert ci_low > 0.0  # Significant improvement strictly greater than 0
