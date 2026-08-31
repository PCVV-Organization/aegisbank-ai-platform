"""RAG knowledge search function tool."""

from __future__ import annotations

from typing import Any

from aegisbank_rag.chunking import chunk_corpus
from aegisbank_rag.constants import CORPUS_DIR
from aegisbank_rag.corpus import load_corpus
from aegisbank_rag.evaluation import build_active_corpus, make_retrievers
from aegisbank_rag.retriever import Retriever

from .base import AgentContext, FunctionTool, ToolResult


class SearchKnowledgeTool(FunctionTool):
    """Tool to search authorized synthetic banking knowledge base."""

    def __init__(self, retriever: Retriever | None = None) -> None:
        if retriever is None:
            raw_docs = load_corpus(CORPUS_DIR)
            active_docs = build_active_corpus(raw_docs)
            chunks = chunk_corpus(active_docs)
            retrievers = make_retrievers()
            retriever_inst = retrievers["hybrid_rrf"]
            retriever_inst.fit(chunks)
            self._retriever = retriever_inst
        else:
            self._retriever = retriever

    @property
    def name(self) -> str:
        return "search_knowledge"

    @property
    def description(self) -> str:
        return (
            "Busca información oficial en las políticas, requisitos y documentación "
            "general de AegisBank (por ejemplo: requisitos para créditos, tasas, plazos)."
        )

    @property
    def parameters_schema(self) -> dict[str, Any]:
        return {
            "type": "object",
            "properties": {
                "query": {
                    "type": "string",
                    "description": "Texto o pregunta de búsqueda sobre el conocimiento bancario.",
                }
            },
            "required": ["query"],
            "additionalProperties": False,
        }

    def execute(self, arguments: dict[str, Any], context: AgentContext) -> ToolResult:
        query = arguments.get("query")
        if not isinstance(query, str) or not query.strip():
            return ToolResult(
                tool_name=self.name,
                success=False,
                error="El parámetro 'query' es obligatorio y no puede estar vacío.",
            )

        hits = self._retriever.search(query.strip(), top_k=3)
        formatted_hits = [
            {
                "chunk_id": h.chunk_id,
                "title": h.title,
                "topic": h.topic,
                "content": h.content,
                "document_id": h.document_id,
                "version": h.document_version,
            }
            for h in hits
        ]
        return ToolResult(
            tool_name=self.name,
            success=True,
            data={"hits": formatted_hits, "total_found": len(formatted_hits)},
        )
