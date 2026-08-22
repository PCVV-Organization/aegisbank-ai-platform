from collections.abc import Sequence

from sklearn.dummy import DummyClassifier
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline

from aegisbank_intent_classifier.constants import (
    DUMMY_CONFIGURATION,
    LOGISTIC_REGRESSION_CONFIGURATION,
    TFIDF_CONFIGURATION,
)
from aegisbank_intent_classifier.dataset import IntentExample


def build_pipeline() -> Pipeline:
    return Pipeline(
        steps=[
            ("tfidf", TfidfVectorizer(**TFIDF_CONFIGURATION)),
            ("classifier", LogisticRegression(**LOGISTIC_REGRESSION_CONFIGURATION)),
        ]
    )


def build_dummy_classifier() -> DummyClassifier:
    return DummyClassifier(**DUMMY_CONFIGURATION)


def pipeline_configuration() -> dict[str, object]:
    tfidf = dict(TFIDF_CONFIGURATION)
    tfidf["ngram_range"] = list(TFIDF_CONFIGURATION["ngram_range"])
    return {
        "steps": ["TfidfVectorizer", "LogisticRegression"],
        "tfidf": tfidf,
        "logistic_regression": dict(LOGISTIC_REGRESSION_CONFIGURATION),
    }


def dummy_configuration() -> dict[str, object]:
    return {"type": "DummyClassifier", **DUMMY_CONFIGURATION}


def train_pipeline(records: Sequence[IntentExample]) -> Pipeline:
    if not records:
        raise ValueError("At least one training record is required")
    estimator = build_pipeline()
    estimator.fit([record.text for record in records], [record.label for record in records])
    return estimator


def predict_intent(text: str, train_records: Sequence[IntentExample]) -> str:
    normalized_text = text.strip()
    if not normalized_text:
        raise ValueError("Prediction text must not be empty")
    estimator = train_pipeline(train_records)
    return str(estimator.predict([normalized_text])[0])
