from pathlib import Path

import pytest

from aegisbank_intent_classifier.dataset import IntentExample, generate_records, write_dataset


@pytest.fixture(scope="session")
def records() -> list[IntentExample]:
    return generate_records()


@pytest.fixture()
def dataset_files(tmp_path: Path) -> tuple[Path, Path]:
    dataset_path = tmp_path / "intent_dataset.jsonl"
    manifest_path = tmp_path / "dataset-manifest.json"
    write_dataset(dataset_path, manifest_path)
    return dataset_path, manifest_path
