"""Retrieval and grounded-generation foundations for AegisBank RAG."""

from aegisbank_rag.embedding import EmbeddingModel, LocalDenseEmbeddingModel
from aegisbank_rag.pgvector_retriever import PgVectorRetriever

__all__ = [
    "EmbeddingModel",
    "LocalDenseEmbeddingModel",
    "PgVectorRetriever",
]

__version__ = "0.5.0.dev0"
