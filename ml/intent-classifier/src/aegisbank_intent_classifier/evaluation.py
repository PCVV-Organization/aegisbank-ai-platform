from __future__ import annotations

import json
import platform
from collections.abc import Callable, Sequence
from importlib.metadata import version
from pathlib import Path
from statistics import fmean, pstdev
from typing import Any, cast

from sklearn.dummy import DummyClassifier
from sklearn.metrics import (
    accuracy_score,
    classification_report,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.pipeline import Pipeline

from aegisbank_intent_classifier.constants import (
    BASELINE_REPORT_PATH,
    CV_CONFIGURATION,
    EXPERIMENT_NAME,
    EXPERIMENT_VERSION,
    HYPOTHESIS,
    LABELS,
    METRICS_PATH,
    PRIMARY_METRIC,
    RANDOM_STATE,
)
from aegisbank_intent_classifier.dataset import IntentExample
from aegisbank_intent_classifier.pipeline import (
    build_dummy_classifier,
    build_pipeline,
    dummy_configuration,
    pipeline_configuration,
)

METRIC_NAMES = (
    "accuracy",
    "macro_precision",
    "macro_recall",
    "macro_f1",
    "weighted_f1",
)


def partition_records(
    records: Sequence[IntentExample],
) -> tuple[list[IntentExample], list[IntentExample]]:
    train = [record for record in records if record.split == "train"]
    holdout = [record for record in records if record.split == "holdout"]
    return train, holdout


def build_cv_splitter() -> StratifiedGroupKFold:
    return StratifiedGroupKFold(**CV_CONFIGURATION)


def cross_validation_splits(
    train_records: Sequence[IntentExample],
) -> list[tuple[list[int], list[int]]]:
    texts = [record.text for record in train_records]
    labels = [record.label for record in train_records]
    groups = [record.template_group_id for record in train_records]
    splits: list[tuple[list[int], list[int]]] = []

    for train_indices, validation_indices in build_cv_splitter().split(
        texts, labels, groups=groups
    ):
        fold_train_groups = {groups[index] for index in train_indices}
        fold_validation_groups = {groups[index] for index in validation_indices}
        overlap = fold_train_groups & fold_validation_groups
        if overlap:
            raise ValueError(f"Cross-validation group leakage detected: {sorted(overlap)}")
        splits.append((train_indices.tolist(), validation_indices.tolist()))

    return splits


def classification_metrics(expected: Sequence[str], predicted: Sequence[str]) -> dict[str, float]:
    macro_precision, macro_recall, macro_f1, _ = precision_recall_fscore_support(
        expected,
        predicted,
        labels=LABELS,
        average="macro",
        zero_division=cast(str, 0),
    )
    return {
        "accuracy": _round_metric(accuracy_score(expected, predicted)),
        "macro_precision": _round_metric(macro_precision),
        "macro_recall": _round_metric(macro_recall),
        "macro_f1": _round_metric(macro_f1),
        "weighted_f1": _round_metric(
            f1_score(
                expected,
                predicted,
                labels=LABELS,
                average="weighted",
                zero_division=cast(str, 0),
            )
        ),
    }


def per_class_metrics(
    expected: Sequence[str], predicted: Sequence[str]
) -> dict[str, dict[str, float | int]]:
    raw_scores = precision_recall_fscore_support(
        expected,
        predicted,
        labels=LABELS,
        average=None,
        zero_division=cast(str, 0),
    )
    precision, recall, f1, support = cast(
        tuple[Sequence[float], Sequence[float], Sequence[float], Sequence[int]],
        raw_scores,
    )
    return {
        label: {
            "precision": _round_metric(float(precision[index])),
            "recall": _round_metric(float(recall[index])),
            "f1": _round_metric(float(f1[index])),
            "support": int(support[index]),
        }
        for index, label in enumerate(LABELS)
    }


def confusion_matrix_data(
    expected: Sequence[str], predicted: Sequence[str]
) -> dict[str, list[Any]]:
    return {
        "labels": list(LABELS),
        "matrix": confusion_matrix(expected, predicted, labels=LABELS).tolist(),
    }


def evaluate_cross_validation(
    train_records: Sequence[IntentExample],
    estimator_factory: Callable[[], Pipeline | DummyClassifier] = build_pipeline,
) -> dict[str, Any]:
    texts = [record.text for record in train_records]
    labels = [record.label for record in train_records]
    groups = [record.template_group_id for record in train_records]
    folds: list[dict[str, Any]] = []

    for fold_number, (train_indices, validation_indices) in enumerate(
        cross_validation_splits(train_records), start=1
    ):
        estimator = estimator_factory()
        estimator.fit(
            [texts[index] for index in train_indices],
            [labels[index] for index in train_indices],
        )
        predictions = estimator.predict([texts[index] for index in validation_indices])
        expected = [labels[index] for index in validation_indices]
        train_groups = {groups[index] for index in train_indices}
        validation_groups = {groups[index] for index in validation_indices}
        folds.append(
            {
                "fold": fold_number,
                "group_overlap": len(train_groups & validation_groups),
                "metrics": classification_metrics(expected, [str(p) for p in predictions]),
                "train_group_count": len(train_groups),
                "train_size": len(train_indices),
                "validation_group_count": len(validation_groups),
                "validation_size": len(validation_indices),
            }
        )

    aggregate = {
        metric_name: {
            "mean": _round_metric(fmean(fold["metrics"][metric_name] for fold in folds)),
            "std": _round_metric(pstdev(fold["metrics"][metric_name] for fold in folds)),
        }
        for metric_name in METRIC_NAMES
    }
    return {
        "aggregate": aggregate,
        "folds": folds,
        "group_leakage_count": sum(fold["group_overlap"] for fold in folds),
        "splitter": {
            "groups": "template_group_id",
            "n_splits": CV_CONFIGURATION["n_splits"],
            "random_state": CV_CONFIGURATION["random_state"],
            "shuffle": CV_CONFIGURATION["shuffle"],
            "type": "StratifiedGroupKFold",
        },
    }


def run_frozen_experiment(records: Sequence[IntentExample], dataset_sha256: str) -> dict[str, Any]:
    train_records, holdout_records = partition_records(records)
    cv_result = evaluate_cross_validation(train_records)
    dummy_cv_result = evaluate_cross_validation(train_records, build_dummy_classifier)

    pipeline = build_pipeline()
    pipeline.fit(
        [record.text for record in train_records],
        [record.label for record in train_records],
    )
    holdout_predictions = [
        str(p) for p in pipeline.predict([record.text for record in holdout_records])
    ]
    holdout_expected = [record.label for record in holdout_records]

    dummy = build_dummy_classifier()
    dummy.fit(
        [record.text for record in train_records],
        [record.label for record in train_records],
    )
    dummy_predictions = [str(p) for p in dummy.predict([record.text for record in holdout_records])]

    report = classification_report(
        holdout_expected,
        holdout_predictions,
        labels=LABELS,
        target_names=LABELS,
        output_dict=True,
        zero_division=cast(str, 0),
    )
    matrix = confusion_matrix_data(holdout_expected, holdout_predictions)
    misclassified = [
        {
            "example_id": record.example_id,
            "expected_label": record.label,
            "predicted_label": predicted,
            "synthetic_text": record.text,
        }
        for record, predicted in zip(holdout_records, holdout_predictions, strict=True)
        if record.label != predicted
    ]

    return {
        "classification_report": _normalize_numbers(report),
        "confusion_matrix": matrix,
        "cross_validation": cv_result,
        "dataset_sha256": dataset_sha256,
        "dataset_size": len(records),
        "dummy_baseline": {
            "configuration": dummy_configuration(),
            "cross_validation": dummy_cv_result,
            "holdout": classification_metrics(holdout_expected, dummy_predictions),
        },
        "experiment_name": EXPERIMENT_NAME,
        "experiment_version": EXPERIMENT_VERSION,
        "holdout": {
            "evaluated_once_after_configuration_freeze": True,
            "metrics": classification_metrics(holdout_expected, holdout_predictions),
            "misclassified_count": len(misclassified),
            "misclassified_examples": misclassified,
            "per_class": per_class_metrics(holdout_expected, holdout_predictions),
            "post_holdout_tuning": False,
        },
        "holdout_size": len(holdout_records),
        "hypothesis": HYPOTHESIS,
        "labels": list(LABELS),
        "pipeline_configuration": pipeline_configuration(),
        "primary_metric": PRIMARY_METRIC,
        "python_version": platform.python_version(),
        "random_state": RANDOM_STATE,
        "scikit_learn_version": version("scikit-learn"),
        "software": {
            "numpy": version("numpy"),
            "scipy": version("scipy"),
        },
        "train_size": len(train_records),
    }


def write_evaluation_reports(
    metrics: dict[str, Any],
    metrics_path: Path = METRICS_PATH,
    report_path: Path = BASELINE_REPORT_PATH,
) -> None:
    metrics_path.parent.mkdir(parents=True, exist_ok=True)
    report_path.parent.mkdir(parents=True, exist_ok=True)
    metrics_path.write_text(
        json.dumps(metrics, ensure_ascii=False, indent=2, sort_keys=True) + "\n",
        encoding="utf-8",
        newline="\n",
    )
    report_path.write_text(
        render_baseline_report(metrics),
        encoding="utf-8",
        newline="\n",
    )


def render_baseline_report(metrics: dict[str, Any]) -> str:
    dummy_holdout = metrics["dummy_baseline"]["holdout"]
    cv = metrics["cross_validation"]["aggregate"]
    holdout = metrics["holdout"]["metrics"]
    per_class = metrics["holdout"]["per_class"]
    matrix = metrics["confusion_matrix"]
    errors = metrics["holdout"]["misclassified_examples"]

    lines = [
        "# v0.3 Intent Classification Baseline Report",
        "",
        "## Scope",
        "",
        "This is a reproducible classical ML baseline over a small synthetic Spanish corpus.",
        "It is not production-ready and does not authorize any banking action.",
        "",
        "## Frozen Protocol",
        "",
        f"- Primary metric: `{metrics['primary_metric']}`",
        f"- Random state: `{metrics['random_state']}`",
        "- Pipeline: word TF-IDF plus Logistic Regression",
        "- Holdout evaluated once after configuration freeze",
        "- Post-holdout tuning: none",
        "",
        "## Dummy Baseline Holdout",
        "",
        "| Metric | Value |",
        "| --- | ---: |",
    ]
    lines.extend(f"| {name} | {value:.6f} |" for name, value in dummy_holdout.items())
    lines.extend(
        [
            "",
            "## TF-IDF + Logistic Regression Cross-validation",
            "",
            "| Metric | Mean | Std |",
            "| --- | ---: | ---: |",
        ]
    )
    lines.extend(
        f"| {name} | {values['mean']:.6f} | {values['std']:.6f} |" for name, values in cv.items()
    )
    lines.extend(
        [
            "",
            "## Holdout Results",
            "",
            "| Metric | Value |",
            "| --- | ---: |",
        ]
    )
    lines.extend(f"| {name} | {value:.6f} |" for name, value in holdout.items())
    lines.extend(
        [
            "",
            "## Per-class Results",
            "",
            "| Label | Precision | Recall | F1 | Support |",
            "| --- | ---: | ---: | ---: | ---: |",
        ]
    )
    lines.extend(
        (
            f"| {label} | {values['precision']:.6f} | {values['recall']:.6f} | "
            f"{values['f1']:.6f} | {values['support']} |"
        )
        for label, values in per_class.items()
    )
    lines.extend(
        [
            "",
            "## Confusion Matrix",
            "",
            "Label order: " + ", ".join(f"`{label}`" for label in matrix["labels"]),
            "",
            "```json",
            json.dumps(matrix["matrix"], ensure_ascii=False),
            "```",
            "",
            "## Error Analysis",
            "",
        ]
    )
    if errors:
        for error in errors:
            lines.extend(
                [
                    f"### {error['example_id']}",
                    "",
                    f"- Expected: `{error['expected_label']}`",
                    f"- Predicted: `{error['predicted_label']}`",
                    f"- Synthetic text: {error['synthetic_text']}",
                    "",
                ]
            )
    else:
        lines.extend(
            [
                "No holdout examples were misclassified. This result is likely influenced by",
                "the balanced, template-generated corpus and must not be generalized to real",
                "traffic.",
                "",
            ]
        )
    lines.extend(
        [
            "## Limitations",
            "",
            "The corpus is synthetic, balanced, small, predominantly Spanish, and generated from",
            "controlled templates. It contains no production traffic or real customer behavior.",
            "Generator artifacts and domain simplification can inflate apparent performance.",
            "The probabilities exposed by Logistic Regression were not calibrated or interpreted",
            "as confidence. No production suitability is claimed.",
            "",
        ]
    )
    return "\n".join(lines)


def _round_metric(value: Any) -> float:
    return round(float(value), 12)


def _normalize_numbers(value: Any) -> Any:
    if isinstance(value, dict):
        return {key: _normalize_numbers(item) for key, item in value.items()}
    if isinstance(value, list):
        return [_normalize_numbers(item) for item in value]
    if isinstance(value, float):
        return _round_metric(value)
    return value
