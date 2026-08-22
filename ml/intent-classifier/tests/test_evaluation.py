from aegisbank_intent_classifier.constants import LABELS
from aegisbank_intent_classifier.evaluation import (
    METRIC_NAMES,
    classification_metrics,
    confusion_matrix_data,
    cross_validation_splits,
    evaluate_cross_validation,
    partition_records,
    per_class_metrics,
)


def test_cross_validation_has_five_group_isolated_folds(records) -> None:
    train_records, _ = partition_records(records)
    groups = [record.template_group_id for record in train_records]
    splits = cross_validation_splits(train_records)

    assert len(splits) == 5
    for train_indices, validation_indices in splits:
        train_groups = {groups[index] for index in train_indices}
        validation_groups = {groups[index] for index in validation_indices}
        assert train_groups.isdisjoint(validation_groups)


def test_cross_validation_reports_required_metrics(records) -> None:
    train_records, _ = partition_records(records)
    result = evaluate_cross_validation(train_records)

    assert len(result["folds"]) == 5
    assert result["group_leakage_count"] == 0
    assert set(result["aggregate"]) == set(METRIC_NAMES)
    assert all(set(values) == {"mean", "std"} for values in result["aggregate"].values())


def test_partition_preserves_frozen_holdout_size_without_evaluating_it(records) -> None:
    train_records, holdout_records = partition_records(records)
    assert len(train_records) == 400
    assert len(holdout_records) == 100
    assert {record.template_group_id for record in train_records}.isdisjoint(
        {record.template_group_id for record in holdout_records}
    )


def test_metric_and_confusion_contracts_use_all_five_labels() -> None:
    expected = list(LABELS) * 2
    predicted = list(LABELS) + [LABELS[0]] * 5
    metrics = classification_metrics(expected, predicted)
    by_class = per_class_metrics(expected, predicted)
    matrix = confusion_matrix_data(expected, predicted)

    assert set(metrics) == set(METRIC_NAMES)
    assert set(by_class) == set(LABELS)
    assert matrix["labels"] == list(LABELS)
    assert len(matrix["matrix"]) == 5
    assert all(len(row) == 5 for row in matrix["matrix"])
