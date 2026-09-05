"""Taxonomy of errors and confusion matrix for AegisBank AI evaluation."""

from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
from typing import Any


class ErrorType(str, Enum):
    """Structured error taxonomy for AI evaluation failures."""

    INTENT_MISCLASSIFICATION = "INTENT_MISCLASSIFICATION"
    UNEXPECTED_TOOL = "UNEXPECTED_TOOL"
    TOOL_OMISSION = "TOOL_OMISSION"
    PARAM_MISMATCH = "PARAM_MISMATCH"
    OWNERSHIP_LEAK = "OWNERSHIP_LEAK"
    ABSTRACTION_LEAK = "ABSTRACTION_LEAK"
    UNSUPPORTED_CLAIM = "UNSUPPORTED_CLAIM"
    HALLUCINATED_ID = "HALLUCINATED_ID"
    FAILED_CALL = "FAILED_CALL"
    UNAUTHORIZED_WRITE = "UNAUTHORIZED_WRITE"
    MISSED_ABSTENTION = "MISSED_ABSTENTION"
    UNKNOWN_FAILURE = "UNKNOWN_FAILURE"


@dataclass(frozen=True, slots=True)
class EvaluationFailure:
    """Detailed record of a single evaluation failure."""

    case_id: str
    error_type: ErrorType
    message: str = ""
    actual_value: Any = None
    expected_value: Any = None
    expected: Any = None
    observed: Any = None
    detail: str | None = None

    def is_critical(self) -> bool:
        """Indicate whether this failure represents a severe security or policy violation."""
        return self.error_type in (
            ErrorType.UNAUTHORIZED_WRITE,
            ErrorType.OWNERSHIP_LEAK,
            ErrorType.UNEXPECTED_TOOL,
            ErrorType.HALLUCINATED_ID,
        )


class ConfusionMatrix:
    """Tracks expected vs actual classification pairs for tools or intents."""

    def __init__(self, labels: list[str] | None = None) -> None:
        self._labels: set[str] = set(labels) if labels else set()
        self._matrix: dict[str, dict[str, int]] = {}

    def record(self, expected: str, actual: str) -> None:
        exp = expected or "NONE"
        act = actual or "NONE"
        self._labels.add(exp)
        self._labels.add(act)

        if exp not in self._matrix:
            self._matrix[exp] = {}
        self._matrix[exp][act] = self._matrix[exp].get(act, 0) + 1

    def record_true_positive(self, label: str) -> None:
        self.record(label, label)

    def record_false_positive(self, label: str, actual_label: str = "OTHER") -> None:
        self.record(actual_label, label)

    def record_false_negative(self, label: str, predicted_label: str = "OTHER") -> None:
        self.record(label, predicted_label)

    def precision(self, label: str) -> float:
        tp = self._matrix.get(label, {}).get(label, 0)
        col_total = sum(row.get(label, 0) for row in self._matrix.values())
        return float(tp / col_total) if col_total > 0 else 0.0

    def recall(self, label: str) -> float:
        tp = self._matrix.get(label, {}).get(label, 0)
        row_total = sum(self._matrix.get(label, {}).values())
        return float(tp / row_total) if row_total > 0 else 0.0

    def f1(self, label: str) -> float:
        p = self.precision(label)
        r = self.recall(label)
        return float((2 * p * r) / (p + r)) if (p + r) > 0 else 0.0

    def to_dict(self) -> dict[str, dict[str, int]]:
        result: dict[str, dict[str, int]] = {}
        sorted_labels = sorted(self._labels)
        for exp in sorted_labels:
            result[exp] = {}
            for act in sorted_labels:
                result[exp][act] = self._matrix.get(exp, {}).get(act, 0)
        return result

    @property
    def total_count(self) -> int:
        return sum(sum(row.values()) for row in self._matrix.values())

    @property
    def diagonal_count(self) -> int:
        return sum(self._matrix.get(lbl, {}).get(lbl, 0) for lbl in self._labels)

    @property
    def accuracy(self) -> float:
        tot = self.total_count
        return float(self.diagonal_count / tot) if tot > 0 else 0.0
