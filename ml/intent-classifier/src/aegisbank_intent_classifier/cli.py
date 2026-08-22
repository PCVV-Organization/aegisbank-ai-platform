from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path
from typing import Any

from aegisbank_intent_classifier.constants import (
    BASELINE_REPORT_PATH,
    DATASET_MANIFEST_PATH,
    DATASET_PATH,
    LABELS,
    METRICS_PATH,
)
from aegisbank_intent_classifier.dataset import (
    DatasetValidationError,
    load_dataset,
    load_manifest,
    validate_dataset,
    validate_dataset_files,
    write_dataset,
)
from aegisbank_intent_classifier.evaluation import (
    partition_records,
    run_frozen_experiment,
    write_evaluation_reports,
)
from aegisbank_intent_classifier.pipeline import predict_intent


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="aegisbank-intent",
        description="Synthetic Spanish banking intent-classification baseline",
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    generate_parser = subparsers.add_parser("generate", help="regenerate dataset and manifest")
    _add_dataset_paths(generate_parser)
    generate_parser.set_defaults(handler=_handle_generate)

    validate_parser = subparsers.add_parser("validate", help="validate dataset invariants")
    _add_dataset_paths(validate_parser)
    validate_parser.set_defaults(handler=_handle_validate)

    evaluate_parser = subparsers.add_parser(
        "evaluate", help="run the frozen CV and one-time holdout experiment"
    )
    _add_dataset_paths(evaluate_parser)
    evaluate_parser.add_argument("--metrics-output", type=Path, default=METRICS_PATH)
    evaluate_parser.add_argument("--report-output", type=Path, default=BASELINE_REPORT_PATH)
    evaluate_parser.set_defaults(handler=_handle_evaluate)

    predict_parser = subparsers.add_parser(
        "predict", help="fit on TRAIN and classify one local text"
    )
    predict_parser.add_argument("text")
    _add_dataset_paths(predict_parser)
    predict_parser.set_defaults(handler=_handle_predict)

    return parser


def main(argv: list[str] | None = None) -> int:
    parser = build_parser()
    args = parser.parse_args(argv)
    try:
        return int(args.handler(args))
    except (DatasetValidationError, FileNotFoundError, ValueError) as exc:
        print(f"ERROR: {exc}", file=sys.stderr)
        return 2


def _add_dataset_paths(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--dataset", type=Path, default=DATASET_PATH)
    parser.add_argument("--manifest", type=Path, default=DATASET_MANIFEST_PATH)


def _handle_generate(args: argparse.Namespace) -> int:
    manifest = write_dataset(args.dataset, args.manifest)
    _print_json({"result": "generated", **manifest})
    return 0


def _handle_validate(args: argparse.Namespace) -> int:
    summary = validate_dataset_files(args.dataset, args.manifest)
    _print_json({"result": "valid", **summary})
    return 0


def _handle_evaluate(args: argparse.Namespace) -> int:
    records, dataset_bytes = load_dataset(args.dataset)
    manifest = load_manifest(args.manifest)
    summary = validate_dataset(records, dataset_bytes, manifest)
    metrics = run_frozen_experiment(records, summary["sha256"])
    write_evaluation_reports(metrics, args.metrics_output, args.report_output)
    _print_json(
        {
            "cross_validation_macro_f1": metrics["cross_validation"]["aggregate"]["macro_f1"],
            "dataset_sha256": metrics["dataset_sha256"],
            "holdout": metrics["holdout"]["metrics"],
            "misclassified_count": metrics["holdout"]["misclassified_count"],
            "result": "evaluated",
        }
    )
    return 0


def _handle_predict(args: argparse.Namespace) -> int:
    records, dataset_bytes = load_dataset(args.dataset)
    manifest = load_manifest(args.manifest)
    validate_dataset(records, dataset_bytes, manifest)
    train_records, _ = partition_records(records)
    prediction = predict_intent(args.text, train_records)
    if prediction not in LABELS:
        raise ValueError("Model returned a label outside the frozen taxonomy")
    _print_json(
        {
            "label": prediction,
            "model": "TF-IDF + LogisticRegression baseline",
            "text": args.text,
        }
    )
    return 0


def _print_json(payload: dict[str, Any]) -> None:
    print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))


if __name__ == "__main__":
    raise SystemExit(main())
