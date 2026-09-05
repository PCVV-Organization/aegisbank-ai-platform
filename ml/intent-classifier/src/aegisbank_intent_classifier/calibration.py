"""Probabilistic calibration and reliability analysis for banking intent classification."""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class CalibrationBin:
    bin_index: int
    bin_lower: float
    bin_upper: float
    sample_count: int
    mean_confidence: float
    accuracy: float


def brier_score_binary(
    y_true: Sequence[int | bool],
    y_prob: Sequence[float],
) -> float:
    """Compute binary Brier score: mean squared error of probability predictions."""
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("Inputs must be non-empty and of equal length.")

    n = len(y_true)
    total_sq_err = sum(
        (float(prob) - (1.0 if actual else 0.0)) ** 2 for actual, prob in zip(y_true, y_prob)
    )
    return float(total_sq_err / n)


def brier_score_multiclass(
    y_true: Sequence[int],
    y_prob: Sequence[Sequence[float]],
) -> float:
    """Compute multiclass Brier score across K classes."""
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("Inputs must be non-empty and of equal length.")

    n = len(y_true)
    total_error = 0.0
    for actual_idx, probs in zip(y_true, y_prob):
        for k, p in enumerate(probs):
            target = 1.0 if k == actual_idx else 0.0
            total_error += (p - target) ** 2

    return float(total_error / n)


def expected_calibration_error(
    y_true: Sequence[int | bool],
    y_prob: Sequence[float],
    n_bins: int = 10,
) -> float:
    """Compute Expected Calibration Error (ECE) for binary predictions."""
    bins = reliability_diagram_bins(y_true, y_prob, n_bins=n_bins)
    n = len(y_true)
    if n == 0:
        return 0.0

    ece = sum(
        (b.sample_count / n) * abs(b.accuracy - b.mean_confidence)
        for b in bins
        if b.sample_count > 0
    )
    return float(ece)


def multiclass_expected_calibration_error(
    y_true: Sequence[int],
    y_prob: Sequence[Sequence[float]],
    n_bins: int = 10,
) -> float:
    """Compute ECE using top-1 (winner-take-all) confidence and accuracy."""
    if not y_true or len(y_true) != len(y_prob):
        raise ValueError("Inputs must be non-empty and of equal length.")

    top_confidences: list[float] = []
    top_correct: list[bool] = []

    for actual_idx, probs in zip(y_true, y_prob):
        max_prob = max(probs)
        pred_idx = list(probs).index(max_prob)
        top_confidences.append(max_prob)
        top_correct.append(pred_idx == actual_idx)

    return expected_calibration_error(top_correct, top_confidences, n_bins=n_bins)


def reliability_diagram_bins(
    y_true: Sequence[int | bool],
    y_prob: Sequence[float],
    n_bins: int = 10,
) -> list[CalibrationBin]:
    """Partition predictions into uniform probability bins and compute empirical accuracy."""
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must have matching lengths.")

    step = 1.0 / n_bins
    bins: list[CalibrationBin] = []

    for i in range(n_bins):
        lower = i * step
        upper = (i + 1) * step

        # Include 1.0 in the last bin
        if i == n_bins - 1:
            indices = [idx for idx, p in enumerate(y_prob) if lower <= p <= upper]
        else:
            indices = [idx for idx, p in enumerate(y_prob) if lower <= p < upper]

        sample_count = len(indices)
        if sample_count > 0:
            mean_conf = sum(y_prob[idx] for idx in indices) / sample_count
            accuracy = sum(1.0 if y_true[idx] else 0.0 for idx in indices) / sample_count
        else:
            mean_conf = (lower + upper) / 2.0
            accuracy = 0.0

        bins.append(
            CalibrationBin(
                bin_index=i,
                bin_lower=round(lower, 4),
                bin_upper=round(upper, 4),
                sample_count=sample_count,
                mean_confidence=round(mean_conf, 4),
                accuracy=round(accuracy, 4),
            )
        )

    return bins


def calibration_summary(
    y_true: Sequence[int | bool],
    y_prob: Sequence[float],
    n_bins: int = 10,
) -> dict[str, Any]:
    """Generate complete calibration summary report."""
    bs = brier_score_binary(y_true, y_prob)
    ece = expected_calibration_error(y_true, y_prob, n_bins=n_bins)
    bins = reliability_diagram_bins(y_true, y_prob, n_bins=n_bins)

    return {
        "brier_score": round(bs, 4),
        "expected_calibration_error": round(ece, 4),
        "n_bins": n_bins,
        "sample_size": len(y_true),
        "bins": [
            {
                "bin_index": b.bin_index,
                "range": f"[{b.bin_lower:.2f}, {b.bin_upper:.2f}]",
                "sample_count": b.sample_count,
                "mean_confidence": b.mean_confidence,
                "accuracy": b.accuracy,
            }
            for b in bins
        ],
    }
