"""Unit tests for synthetic drift detection (data, prediction, performance)."""

from __future__ import annotations

import pytest

from aegisbank_agent.mlops.drift import (
    DriftDetector,
    DriftStatus,
    DriftType,
    calculate_psi_categorical,
    calculate_psi_numeric,
    calculate_wasserstein_1d,
)

pytestmark = pytest.mark.unit


def test_psi_categorical_stability_and_shift() -> None:
    # Identical distributions should yield ~0 PSI
    ref = ["LOAN_DETAILS", "LOAN_DETAILS", "GET_MY_LOANS", "GREETING"] * 10
    cur_stable = ["LOAN_DETAILS", "LOAN_DETAILS", "GET_MY_LOANS", "GREETING"] * 10
    psi_stable = calculate_psi_categorical(ref, cur_stable)
    assert psi_stable == pytest.approx(0.0, abs=0.01)

    # Severe category shift
    cur_shifted = ["UNSUPPORTED_WRITE"] * 30 + ["GREETING"] * 10
    psi_shifted = calculate_psi_categorical(ref, cur_shifted)
    assert psi_shifted > 0.20


def test_psi_numeric_and_wasserstein() -> None:
    ref = [10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 25.0] * 5
    cur_stable = [10.0, 12.0, 15.0, 18.0, 20.0, 22.0, 25.0] * 5
    cur_shifted = [80.0, 95.0, 110.0, 120.0, 130.0, 140.0, 150.0] * 5

    psi_stable = calculate_psi_numeric(ref, cur_stable)
    psi_shifted = calculate_psi_numeric(ref, cur_shifted)
    assert psi_stable < 0.10
    assert psi_shifted > 0.20

    w_dist = calculate_wasserstein_1d(ref, cur_shifted)
    assert w_dist > 50.0


def test_drift_detector_classifications() -> None:
    detector = DriftDetector()

    # Data drift
    ref_prompts = ["Dame mi saldo", "Cuánto debo", "Mis préstamos"] * 10
    shifted_prompts = [
        "Por favor redacte una carta sumamente extensa con cláusulas jurídicas "
        "para el crédito hipotecario"
    ] * 30
    res_data = detector.detect_data_drift(ref_prompts, shifted_prompts)
    assert res_data.drift_type == DriftType.DATA_DRIFT
    assert res_data.drift_detected is True

    # Prediction drift
    ref_intents = ["LOAN_DETAILS", "LOANS_LIST", "GREETING"] * 15
    cur_intents = ["LOAN_DETAILS", "LOANS_LIST", "GREETING"] * 15
    res_pred = detector.detect_prediction_drift(ref_intents, cur_intents)
    assert res_pred.drift_type == DriftType.PREDICTION_DRIFT
    assert res_pred.status == DriftStatus.STABLE
    assert res_pred.drift_detected is False

    # Performance drift
    res_perf_ok = detector.detect_performance_drift(0.95, 0.94)
    assert res_perf_ok.drift_detected is False

    res_perf_drop = detector.detect_performance_drift(0.95, 0.85)
    assert res_perf_drop.drift_detected is True
    assert res_perf_drop.status == DriftStatus.DRIFT_DETECTED
