"""Deterministic policy for grounding banking knowledge questions before generation."""

from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass
from typing import Any

_POLICY_TERMS = (
    "politica",
    "requisito",
    "comision",
    "tasa",
    "interes",
    "plazo",
    "condicion",
    "producto",
    "credito",
)
_PRODUCT_ANCHORS = ("vehicular", "hipotecario", "personal", "negocio", "capital de trabajo")
_STOPWORDS = {"cual", "cuales", "para", "los", "las", "del", "una", "un", "que"}


def _normalize(value: str) -> str:
    folded = unicodedata.normalize("NFKD", value.casefold())
    return "".join(char for char in folded if not unicodedata.combining(char))


def requires_authorized_knowledge(query: str) -> bool:
    """Return true only for factual banking policy/product questions."""
    normalized = _normalize(query)
    return any(term in normalized for term in _POLICY_TERMS)


def has_sufficient_evidence(query: str, data: Any) -> bool:
    """Reject generic hits when a product-specific fact was not retrieved."""
    hits = data.get("hits", []) if isinstance(data, dict) else []
    if not hits:
        return False
    corpus_text = _normalize(" ".join(str(hit) for hit in hits))
    normalized_query = _normalize(query)
    for anchor in _PRODUCT_ANCHORS:
        if anchor in normalized_query and anchor not in corpus_text:
            return False
    terms = {
        token
        for token in re.findall(r"[a-z0-9]+", normalized_query)
        if len(token) > 3 and token not in _STOPWORDS
    }
    return len(terms.intersection(set(re.findall(r"[a-z0-9]+", corpus_text)))) >= 2


@dataclass(frozen=True)
class KnowledgeRoutingDecision:
    required: bool
    sufficient: bool
    result: Any = None
