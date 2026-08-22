from pathlib import Path
from typing import Final

EXPERIMENT_NAME: Final = "aegisbank-synthetic-spanish-intent-baseline"
EXPERIMENT_VERSION: Final = "0.3.0"
GENERATION_VERSION: Final = "1.0.0"
RANDOM_STATE: Final = 42
PRIMARY_METRIC: Final = "macro_f1"

LABELS: Final[tuple[str, ...]] = (
    "informational",
    "account_query",
    "service_request",
    "sensitive_action",
    "unsupported",
)

GROUPS_PER_CLASS: Final = 25
TRAIN_GROUPS_PER_CLASS: Final = 20
HOLDOUT_GROUPS_PER_CLASS: Final = 5
VARIATIONS_PER_GROUP: Final = 4
EXPECTED_RECORD_COUNT: Final = 500
EXPECTED_TRAIN_COUNT: Final = 400
EXPECTED_HOLDOUT_COUNT: Final = 100

HYPOTHESIS: Final = (
    "H1: A TF-IDF + Logistic Regression pipeline will clearly outperform a trivial "
    "baseline in macro-F1 on synthetic banking queries across five intent classes."
)

PROHIBITED_FIELDS: Final[frozenset[str]] = frozenset(
    {
        "dni",
        "document_number",
        "card_number",
        "cvv",
        "password",
        "real_account_number",
        "email",
        "phone",
        "biometric",
    }
)

TFIDF_CONFIGURATION: Final = {
    "lowercase": True,
    "ngram_range": (1, 2),
    "min_df": 1,
    "max_df": 1.0,
    "sublinear_tf": True,
    "norm": "l2",
    "stop_words": None,
    "token_pattern": r"(?u)\b\w\w+\b",
}

LOGISTIC_REGRESSION_CONFIGURATION: Final = {
    "C": 1.0,
    "l1_ratio": 0.0,
    "solver": "lbfgs",
    "max_iter": 1000,
    "tol": 1e-4,
    "random_state": RANDOM_STATE,
}

DUMMY_CONFIGURATION: Final = {
    "strategy": "most_frequent",
    "random_state": RANDOM_STATE,
}

CV_CONFIGURATION: Final = {
    "n_splits": 5,
    "shuffle": True,
    "random_state": RANDOM_STATE,
}

COMPONENT_ROOT: Final = Path(__file__).resolve().parents[2]
DATASET_PATH: Final = COMPONENT_ROOT / "data" / "intent_dataset.jsonl"
DATASET_MANIFEST_PATH: Final = COMPONENT_ROOT / "data" / "dataset-manifest.json"
METRICS_PATH: Final = COMPONENT_ROOT / "reports" / "baseline-metrics.json"
BASELINE_REPORT_PATH: Final = COMPONENT_ROOT / "reports" / "baseline-report.md"
