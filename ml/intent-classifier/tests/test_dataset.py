import json
from collections import Counter, defaultdict
from hashlib import sha256

import pytest

from aegisbank_intent_classifier.constants import (
    DATASET_MANIFEST_PATH,
    DATASET_PATH,
    LABELS,
    PROHIBITED_FIELDS,
)
from aegisbank_intent_classifier.dataset import (
    DatasetValidationError,
    IntentExample,
    build_manifest,
    generate_records,
    load_dataset,
    load_manifest,
    serialize_records,
    validate_dataset,
)


def test_dataset_has_exact_balanced_counts(records) -> None:
    assert LABELS == (
        "informational",
        "account_query",
        "service_request",
        "sensitive_action",
        "unsupported",
    )
    assert len(records) == 500
    assert Counter(record.label for record in records) == Counter({label: 100 for label in LABELS})
    assert Counter(record.split for record in records) == Counter({"train": 400, "holdout": 100})


def test_template_groups_have_four_examples_and_never_cross_splits(records) -> None:
    grouped = defaultdict(list)
    for record in records:
        grouped[record.template_group_id].append(record)

    assert len(grouped) == 125
    assert all(len(group_records) == 4 for group_records in grouped.values())
    assert all(
        len({record.split for record in group_records}) == 1 for group_records in grouped.values()
    )
    assert all(
        len({record.label for record in group_records}) == 1 for group_records in grouped.values()
    )

    for label in LABELS:
        label_groups = {record.template_group_id for record in records if record.label == label}
        train_groups = {
            record.template_group_id
            for record in records
            if record.label == label and record.split == "train"
        }
        holdout_groups = label_groups - train_groups
        assert len(label_groups) == 25
        assert len(train_groups) == 20
        assert len(holdout_groups) == 5
        assert train_groups.isdisjoint(holdout_groups)


def test_dataset_ids_text_and_labels_are_unique_and_allowed(records) -> None:
    ids = [record.example_id for record in records]
    texts = [record.text for record in records]
    assert len(ids) == len(set(ids))
    assert len(texts) == len(set(texts))
    assert {record.label for record in records} == set(LABELS)
    assert all(record.text and record.text == record.text.strip() for record in records)


def test_generation_is_byte_deterministic_and_valid_utf8() -> None:
    first = serialize_records(generate_records())
    second = serialize_records(generate_records())
    assert first == second
    assert sha256(first).hexdigest() == sha256(second).hexdigest()
    assert first.decode("utf-8", errors="strict")


def test_manifest_sha_and_dataset_validation_match(dataset_files) -> None:
    dataset_path, manifest_path = dataset_files
    records, dataset_bytes = load_dataset(dataset_path)
    manifest = load_manifest(manifest_path)
    summary = validate_dataset(records, dataset_bytes, manifest)

    assert manifest == build_manifest(records, dataset_bytes)
    assert manifest["sha256"] == sha256(dataset_bytes).hexdigest()
    assert summary["record_count"] == 500
    assert summary["group_leakage"] == 0
    assert summary["duplicate_texts"] == 0


def test_versioned_dataset_matches_generator_and_manifest() -> None:
    generated_bytes = serialize_records(generate_records())
    versioned_records, versioned_bytes = load_dataset(DATASET_PATH)
    manifest = load_manifest(DATASET_MANIFEST_PATH)

    assert versioned_bytes == generated_bytes
    assert manifest == build_manifest(versioned_records, versioned_bytes)
    assert manifest["sha256"] == sha256(generated_bytes).hexdigest()


def test_prohibited_or_unexpected_fields_are_rejected() -> None:
    base = {
        "example_id": "EX-0001",
        "text": "Texto sintético",
        "label": "informational",
        "template_group_id": "informational_test_01",
        "split": "train",
    }
    for prohibited in PROHIBITED_FIELDS:
        payload = {**base, prohibited: "synthetic-placeholder"}
        with pytest.raises(DatasetValidationError, match="Prohibited dataset fields"):
            IntentExample.from_dict(payload)


def test_invalid_jsonl_shape_is_not_silently_accepted(tmp_path) -> None:
    dataset_path = tmp_path / "invalid.jsonl"
    dataset_path.write_text(json.dumps({"text": "missing fields"}) + "\n", encoding="utf-8")
    with pytest.raises(DatasetValidationError, match="Dataset fields must be"):
        load_dataset(dataset_path)
