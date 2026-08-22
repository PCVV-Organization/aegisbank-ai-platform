from hashlib import sha256

from aegisbank_intent_classifier.dataset import generate_records, serialize_records
from aegisbank_intent_classifier.evaluation import (
    classification_metrics,
    confusion_matrix_data,
    cross_validation_splits,
    partition_records,
)
from aegisbank_intent_classifier.pipeline import build_pipeline


def test_dataset_hash_and_fold_assignment_are_reproducible() -> None:
    first_records = generate_records()
    second_records = generate_records()
    first_bytes = serialize_records(first_records)
    second_bytes = serialize_records(second_records)
    first_train, _ = partition_records(first_records)
    second_train, _ = partition_records(second_records)

    assert first_bytes == second_bytes
    assert sha256(first_bytes).hexdigest() == sha256(second_bytes).hexdigest()
    assert cross_validation_splits(first_train) == cross_validation_splits(second_train)


def test_train_only_predictions_and_metrics_are_reproducible(records) -> None:
    train_records, _ = partition_records(records)
    train_indices, validation_indices = cross_validation_splits(train_records)[0]
    train_texts = [train_records[index].text for index in train_indices]
    train_labels = [train_records[index].label for index in train_indices]
    validation_texts = [train_records[index].text for index in validation_indices]
    expected = [train_records[index].label for index in validation_indices]

    first = build_pipeline().fit(train_texts, train_labels)
    second = build_pipeline().fit(train_texts, train_labels)
    first_predictions = first.predict(validation_texts).tolist()
    second_predictions = second.predict(validation_texts).tolist()

    assert first_predictions == second_predictions
    assert classification_metrics(expected, first_predictions) == classification_metrics(
        expected, second_predictions
    )
    assert confusion_matrix_data(expected, first_predictions) == confusion_matrix_data(
        expected, second_predictions
    )
