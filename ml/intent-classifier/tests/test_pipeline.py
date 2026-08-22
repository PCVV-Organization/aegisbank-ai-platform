import warnings

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from aegisbank_intent_classifier.constants import LABELS
from aegisbank_intent_classifier.evaluation import partition_records
from aegisbank_intent_classifier.pipeline import build_pipeline


def test_pipeline_contains_frozen_tfidf_and_logistic_regression() -> None:
    pipeline = build_pipeline()
    assert isinstance(pipeline, Pipeline)
    assert list(pipeline.named_steps) == ["tfidf", "classifier"]
    assert isinstance(pipeline.named_steps["tfidf"], TfidfVectorizer)
    assert isinstance(pipeline.named_steps["classifier"], LogisticRegression)
    assert pipeline.named_steps["tfidf"].ngram_range == (1, 2)
    assert pipeline.named_steps["classifier"].solver == "lbfgs"
    assert pipeline.named_steps["classifier"].l1_ratio == 0.0


def test_pipeline_fit_predict_and_predict_proba_use_allowed_labels(records) -> None:
    train_records, _ = partition_records(records)
    pipeline = build_pipeline()
    pipeline.fit(
        [record.text for record in train_records],
        [record.label for record in train_records],
    )

    texts = [record.text for record in train_records[:10]]
    predictions = pipeline.predict(texts)
    probabilities = pipeline.predict_proba(texts)

    assert set(predictions).issubset(LABELS)
    assert probabilities.shape == (10, 5)
    assert all(abs(float(row.sum()) - 1.0) < 1e-12 for row in probabilities)


def test_frozen_pipeline_fits_without_deprecation_or_convergence_warnings(records) -> None:
    train_records, _ = partition_records(records)
    with warnings.catch_warnings(record=True) as caught:
        warnings.simplefilter("always")
        build_pipeline().fit(
            [record.text for record in train_records],
            [record.label for record in train_records],
        )

    assert caught == []
