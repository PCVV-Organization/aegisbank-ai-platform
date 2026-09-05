"""Reproducible classical ML baseline for synthetic banking intents."""

from aegisbank_intent_classifier.calibration import (
    brier_score_binary,
    brier_score_multiclass,
    calibration_summary,
    expected_calibration_error,
    multiclass_expected_calibration_error,
    reliability_diagram_bins,
)

__version__ = "0.3.0"

__all__ = [
    "brier_score_binary",
    "brier_score_multiclass",
    "calibration_summary",
    "expected_calibration_error",
    "multiclass_expected_calibration_error",
    "reliability_diagram_bins",
]
