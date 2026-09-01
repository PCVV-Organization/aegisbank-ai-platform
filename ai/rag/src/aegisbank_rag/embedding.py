"""Local reproducible embedding generator for AegisBank RAG.

Provides deterministic dense vectors for PostgreSQL + pgvector vector storage
and similarity search without external cloud dependencies.
"""

from __future__ import annotations

from collections.abc import Sequence
from dataclasses import dataclass
from typing import Protocol

import numpy as np
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize

from aegisbank_rag.constants import LSA_COMPONENTS, RANDOM_STATE
from aegisbank_rag.lexical import LEXICAL_VECTORIZER


class EmbeddingModel(Protocol):
    model_id: str
    dimension: int

    def fit(self, texts: Sequence[str]) -> None: ...
    def encode(self, texts: Sequence[str]) -> list[list[float]]: ...
    def encode_one(self, text: str) -> list[float]: ...


@dataclass
class LocalDenseEmbeddingModel:
    """Deterministic local dense embedding model based on TF-IDF and Truncated SVD (LSA)."""

    model_id: str = "aegisbank-lsa-32"
    dimension: int = LSA_COMPONENTS  # 32
    normalize_embeddings: bool = True

    def __post_init__(self) -> None:
        self._vectorizer = TfidfVectorizer(**LEXICAL_VECTORIZER)
        self._svd: TruncatedSVD | None = None
        self._is_fitted: bool = False

    def fit(self, texts: Sequence[str]) -> None:
        """Fit vocabulary and projection matrix over the training corpus."""
        tfidf = self._vectorizer.fit_transform(texts)
        n_components = min(self.dimension, max(1, min(tfidf.shape) - 1))
        self._svd = TruncatedSVD(
            n_components=n_components,
            random_state=RANDOM_STATE,
            algorithm="randomized",
            n_iter=5,
            tol=0.0,
        )
        self._svd.fit(tfidf)
        self._is_fitted = True

    def encode(self, texts: Sequence[str]) -> list[list[float]]:
        """Transform text sequence into normalized float vectors."""
        if not self._is_fitted or self._svd is None:
            # Fit on the provided texts if not previously fitted
            self.fit(texts)

        assert self._svd is not None
        tfidf = self._vectorizer.transform(texts)
        reduced = self._svd.transform(tfidf)
        # Pad to self.dimension if vocabulary was smaller
        if reduced.shape[1] < self.dimension:
            pad_width = self.dimension - reduced.shape[1]
            reduced = np.pad(reduced, ((0, 0), (0, pad_width)), mode="constant")
        elif reduced.shape[1] > self.dimension:
            reduced = reduced[:, : self.dimension]

        if self.normalize_embeddings:
            reduced = normalize(reduced, norm="l2", axis=1)

        return [[float(v) for v in row] for row in reduced]

    def encode_one(self, text: str) -> list[float]:
        """Transform a single text into a normalized float vector."""
        return self.encode([text])[0]
