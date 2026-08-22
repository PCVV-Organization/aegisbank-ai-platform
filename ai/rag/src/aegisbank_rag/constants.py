"""Frozen constants for the v0.4 retrieval foundation."""

from pathlib import Path

EXPERIMENT_NAME: str = "aegisbank-synthetic-spanish-rag-retrieval"
EXPERIMENT_VERSION: str = "0.4.0"
RANDOM_STATE: int = 42
PRIMARY_METRIC: str = "ndcg_at_5"
DEFAULT_K: int = 5
RRF_K: int = 60
LSA_COMPONENTS: int = 64

COMPONENT_ROOT: Path = Path(__file__).resolve().parents[2]
CORPUS_DIR: Path = COMPONENT_ROOT / "data" / "corpus"
CORPUS_MANIFEST_PATH: Path = COMPONENT_ROOT / "data" / "corpus-manifest.json"
QUERIES_PATH: Path = COMPONENT_ROOT / "data" / "queries.jsonl"
QRELS_PATH: Path = COMPONENT_ROOT / "data" / "qrels.json"
METRICS_PATH: Path = COMPONENT_ROOT / "reports" / "retrieval-metrics.json"
REPORT_PATH: Path = COMPONENT_ROOT / "reports" / "retrieval-report.md"

REQUIRED_DOCUMENT_FIELDS = (
    "document_id",
    "version",
    "effective_from",
    "effective_to",
    "status",
    "source",
    "title",
    "topic",
    "body",
)

ALLOWED_STATUSES = ("draft", "active", "superseded", "retired")
ALLOWED_TOPICS = (
    "creditos",
    "cuotas",
    "comisiones",
    "productos",
    "reclamos",
    "politicas",
)
