"""Retrieval and grounded-generation foundations for AegisBank RAG."""

from aegisbank_rag.cache import RedisCacheManager
from aegisbank_rag.embedding import EmbeddingModel, LocalDenseEmbeddingModel
from aegisbank_rag.pgvector_retriever import PgVectorRetriever
from aegisbank_rag.redis_retriever import RedisVectorRetriever

__all__ = [
    "EmbeddingModel",
    "LocalDenseEmbeddingModel",
    "PgVectorRetriever",
    "RedisCacheManager",
    "RedisVectorRetriever",
]

__version__ = "0.5.0.dev0"
