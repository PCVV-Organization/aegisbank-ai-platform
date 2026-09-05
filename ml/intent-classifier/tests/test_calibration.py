"""Unit tests for probabilistic calibration, Brier score, and ECE."""

from __future__ import annotations

import pytest

from aegisbank_intent_classifier.calibration import (
    brier_score_binary,
    brier_score_multiclass,
    calibration_summary,
    expected_calibration_error,
    multiclass_expected_calibration_error,
    reliability_diagram_bins,
)


def test_brier_score_binary() -> None:
    # Perfect predictions
    assert brier_score_binary([1, 0, 1], [1.0, 0.0, 1.0]) == pytest.approx(0.0)

    # Worst possible predictions
    assert brier_score_binary([1, 0], [0.0, 1.0]) == pytest.approx(1.0)

    # Moderate predictions: (0.8-1)^2 = 0.04, (0.2-0)^2 = 0.04 -> mean = 0.04
    assert brier_score_binary([1, 0], [0.8, 0.2]) == pytest.approx(0.04)


def test_brier_score_multiclass() -> None:
    # 3 classes: true classes are 0 and 2
    y_true = [0, 2]
    # Prediction 1: [0.9, 0.05, 0.05] -> squared error = 0.015
    # Prediction 2: [0.1, 0.1, 0.8]   -> 0.1^2 + 0.1^2 + (0.8-1)^2 = 0.01 + 0.01 + 0.04 = 0.06
    # Mean = (0.015 + 0.06) / 2 = 0.0375
    y_prob = [[0.9, 0.05, 0.05], [0.1, 0.1, 0.8]]
    assert brier_score_multiclass(y_true, y_prob) == pytest.approx(0.0375)


def test_expected_calibration_error() -> None:
    # Perfectly calibrated predictions
    y_true = [1, 1, 0, 0]
    y_prob = [0.9, 0.9, 0.1, 0.1]
    ece = expected_calibration_error(y_true, y_prob, n_bins=5)
    assert ece <= 0.15

    # Completely overconfident incorrect predictions
    y_bad = [0, 0, 0, 0]
    y_prob_bad = [0.99, 0.99, 0.99, 0.99]
    ece_bad = expected_calibration_error(y_bad, y_prob_bad, n_bins=5)
    assert ece_bad > 0.90


def test_multiclass_ece() -> None:
    y_true = [0, 1, 2]
    y_prob = [
        [0.85, 0.10, 0.05],  # Correct, conf 0.85
        [0.90, 0.05, 0.05],  # Incorrect (pred 0, actual 1), conf 0.90
        [0.05, 0.05, 0.90],  # Correct, conf 0.90
    ]
    ece = multiclass_expected_calibration_error(y_true, y_prob, n_bins=5)
    assert 0.0 <= ece <= 1.0


def test_calibration_summary_and_bins() -> None:
    y_true = [True, True, False, False, True, False]
    y_prob = [0.95, 0.80, 0.25, 0.10, 0.70, 0.40]

    bins = reliability_diagram_bins(y_true, y_prob, n_bins=5)
    assert len(bins) == 5
    assert sum(b.sample_count for b in bins) == len(y_true)

    summary = calibration_summary(y_true, y_prob, n_bins=5)
    assert "brier_score" in summary
    assert "expected_calibration_error" in summary
    assert summary["sample_size"] == 6
    assert len(summary["bins"]) == 5
