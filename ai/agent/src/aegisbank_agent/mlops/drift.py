"""Drift detection module for data, predictions, and model performance."""

from __future__ import annotations

import math
from collections import Counter
from dataclasses import dataclass
from enum import Enum
from typing import Any, Sequence


class DriftStatus(str, Enum):
    """Categorization of observed drift severity."""

    STABLE = "STABLE"  # PSI < 0.10
    WARNING = "WARNING"  # 0.10 <= PSI < 0.20
    DRIFT_DETECTED = "DRIFT_DETECTED"  # PSI >= 0.20


class DriftType(str, Enum):
    """Three distinct operational drift dimensions."""

    DATA_DRIFT = "DATA_DRIFT"
    PREDICTION_DRIFT = "PREDICTION_DRIFT"
    MODEL_PERFORMANCE_DRIFT = "MODEL_PERFORMANCE_DRIFT"


@dataclass(frozen=True, slots=True)
class DriftResult:
    drift_type: DriftType
    status: DriftStatus
    metric_name: str
    metric_value: float
    threshold: float
    drift_detected: bool
    details: dict[str, Any]


def calculate_psi_categorical(
    reference: Sequence[str],
    current: Sequence[str],
    epsilon: float = 1e-5,
) -> float:
    """Calculate Population Stability Index (PSI) between categorical distributions."""
    if not reference or not current:
        return 0.0

    all_categories = sorted(set(reference) | set(current))
    ref_counts = Counter(reference)
    cur_counts = Counter(current)

    ref_total = len(reference)
    cur_total = len(current)

    psi = 0.0
    for cat in all_categories:
        ref_prob = (ref_counts[cat] + epsilon) / (ref_total + epsilon * len(all_categories))
        cur_prob = (cur_counts[cat] + epsilon) / (cur_total + epsilon * len(all_categories))
        psi += (cur_prob - ref_prob) * math.log(cur_prob / ref_prob)

    return max(0.0, float(psi))


def calculate_psi_numeric(
    reference: Sequence[float],
    current: Sequence[float],
    num_bins: int = 5,
    epsilon: float = 1e-5,
) -> float:
    """Calculate Population Stability Index (PSI) on continuous numerical features."""
    if len(reference) < num_bins or len(current) < num_bins:
        return 0.0

    combined = sorted([*reference, *current])
    quantiles = [combined[int(i * (len(combined) - 1) / num_bins)] for i in range(1, num_bins)]

    def _bin_values(vals: Sequence[float]) -> list[int]:
        counts = [0] * (len(quantiles) + 1)
        for v in vals:
            placed = False
            for idx, q in enumerate(quantiles):
                if v <= q:
                    counts[idx] += 1
                    placed = True
                    break
            if not placed:
                counts[-1] += 1
        return counts

    ref_binned = _bin_values(reference)
    cur_binned = _bin_values(current)

    ref_total = len(reference)
    cur_total = len(current)
    bins_count = len(ref_binned)

    psi = 0.0
    for r_cnt, c_cnt in zip(ref_binned, cur_binned):
        ref_prob = (r_cnt + epsilon) / (ref_total + epsilon * bins_count)
        cur_prob = (c_cnt + epsilon) / (cur_total + epsilon * bins_count)
        psi += (cur_prob - ref_prob) * math.log(cur_prob / ref_prob)

    return max(0.0, float(psi))


def calculate_jsd(
    p_counts: Counter[str],
    q_counts: Counter[str],
    epsilon: float = 1e-6,
) -> float:
    """Calculate Jensen-Shannon Divergence (JSD) between two categorical distributions."""
    categories = sorted(set(p_counts.keys()) | set(q_counts.keys()))
    total_p = sum(p_counts.values()) or 1
    total_q = sum(q_counts.values()) or 1

    p = [(p_counts[c] + epsilon) / (total_p + epsilon * len(categories)) for c in categories]
    q = [(q_counts[c] + epsilon) / (total_q + epsilon * len(categories)) for c in categories]
    m = [0.5 * (pi + qi) for pi, qi in zip(p, q)]

    def _kl(a: list[float], b: list[float]) -> float:
        return sum(ai * math.log2(ai / bi) for ai, bi in zip(a, b))

    jsd = 0.5 * _kl(p, m) + 0.5 * _kl(q, m)
    return max(0.0, float(jsd))


def calculate_wasserstein_1d(
    reference: Sequence[float],
    current: Sequence[float],
) -> float:
    """Compute empirical 1-Wasserstein (Earth Mover's) distance between two continuous samples."""
    if not reference or not current:
        return 0.0

    u = sorted(reference)
    v = sorted(current)

    # Approximate via interpolated quantiles
    steps = 100
    w_sum = 0.0
    for i in range(steps):
        q = i / (steps - 1)
        u_val = u[int(q * (len(u) - 1))]
        v_val = v[int(q * (len(v) - 1))]
        w_sum += abs(u_val - v_val)

    return float(w_sum / steps)


class DriftDetector:
    """Comprehensive synthetic drift detector covering data, prediction, and performance drift."""

    def __init__(
        self,
        psi_warning_threshold: float = 0.10,
        psi_drift_threshold: float = 0.20,
        jsd_drift_threshold: float = 0.15,
        perf_drop_threshold: float = 0.05,
    ) -> None:
        self.psi_warning_threshold = psi_warning_threshold
        self.psi_drift_threshold = psi_drift_threshold
        self.jsd_drift_threshold = jsd_drift_threshold
        self.perf_drop_threshold = perf_drop_threshold

    def _status_for_psi(self, psi: float) -> DriftStatus:
        if psi >= self.psi_drift_threshold:
            return DriftStatus.DRIFT_DETECTED
        if psi >= self.psi_warning_threshold:
            return DriftStatus.WARNING
        return DriftStatus.STABLE

    def detect_data_drift(
        self,
        reference_prompts: Sequence[str],
        current_prompts: Sequence[str],
    ) -> DriftResult:
        """Detect covariate shift on prompt length and token length distributions."""
        ref_lens = [float(len(p)) for p in reference_prompts]
        cur_lens = [float(len(p)) for p in current_prompts]

        psi = calculate_psi_numeric(ref_lens, cur_lens)
        w_dist = calculate_wasserstein_1d(ref_lens, cur_lens)
        status = self._status_for_psi(psi)

        return DriftResult(
            drift_type=DriftType.DATA_DRIFT,
            status=status,
            metric_name="psi_prompt_length",
            metric_value=round(psi, 4),
            threshold=self.psi_drift_threshold,
            drift_detected=status == DriftStatus.DRIFT_DETECTED,
            details={
                "wasserstein_distance": round(w_dist, 4),
                "reference_mean_length": round(sum(ref_lens) / len(ref_lens), 2)
                if ref_lens
                else 0.0,
                "current_mean_length": round(sum(cur_lens) / len(cur_lens), 2) if cur_lens else 0.0,
                "reference_count": len(reference_prompts),
                "current_count": len(current_prompts),
            },
        )

    def detect_prediction_drift(
        self,
        reference_intents: Sequence[str],
        current_intents: Sequence[str],
    ) -> DriftResult:
        """Detect concept / prediction drift across intent predictions."""
        psi = calculate_psi_categorical(reference_intents, current_intents)
        jsd = calculate_jsd(Counter(reference_intents), Counter(current_intents))
        status = self._status_for_psi(psi)

        return DriftResult(
            drift_type=DriftType.PREDICTION_DRIFT,
            status=status,
            metric_name="psi_intent_distribution",
            metric_value=round(psi, 4),
            threshold=self.psi_drift_threshold,
            drift_detected=status == DriftStatus.DRIFT_DETECTED,
            details={
                "jensen_shannon_divergence": round(jsd, 4),
                "unique_reference_intents": len(set(reference_intents)),
                "unique_current_intents": len(set(current_intents)),
            },
        )

    def detect_performance_drift(
        self,
        baseline_accuracy: float,
        current_accuracy: float,
    ) -> DriftResult:
        """Detect model performance degradation between baseline and monitored period."""
        degradation = baseline_accuracy - current_accuracy
        drift_detected = degradation >= self.perf_drop_threshold

        if degradation >= self.perf_drop_threshold:
            status = DriftStatus.DRIFT_DETECTED
        elif degradation > 0.0:
            status = DriftStatus.WARNING
        else:
            status = DriftStatus.STABLE

        return DriftResult(
            drift_type=DriftType.MODEL_PERFORMANCE_DRIFT,
            status=status,
            metric_name="accuracy_degradation",
            metric_value=round(degradation, 4),
            threshold=self.perf_drop_threshold,
            drift_detected=drift_detected,
            details={
                "baseline_accuracy": round(baseline_accuracy, 4),
                "current_accuracy": round(current_accuracy, 4),
                "absolute_drop": round(max(0.0, degradation), 4),
            },
        )
