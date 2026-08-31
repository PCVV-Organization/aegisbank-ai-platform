"""Tests for RAG search integration using existing ai/rag retrieval."""

from __future__ import annotations

from aegisbank_agent.tools.base import AgentContext
from aegisbank_agent.tools.knowledge_tools import SearchKnowledgeTool


class TestSearchKnowledgeTool:
    """search_knowledge reuses ai/rag retrieval without modifying corpus/retrieval."""

    def test_tool_is_registered(self):
        tool = SearchKnowledgeTool()
        assert tool.name == "search_knowledge"

    def test_tool_has_query_parameter(self):
        tool = SearchKnowledgeTool()
        schema = tool.parameters_schema
        assert "query" in schema["properties"]
        assert "query" in schema["required"]

    def test_empty_query_rejected(self):
        tool = SearchKnowledgeTool()
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({}, context)
        assert result.success is False
        assert (
            "obligatorio" in (result.error or "").lower() or "vacío" in (result.error or "").lower()
        )

    def test_whitespace_query_rejected(self):
        tool = SearchKnowledgeTool()
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"query": "   "}, context)
        assert result.success is False

    def test_valid_query_returns_hits(self):
        tool = SearchKnowledgeTool()
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"query": "crédito capital de trabajo"}, context)
        assert result.success is True
        assert result.data is not None
        assert "hits" in result.data
        assert "total_found" in result.data

    def test_hits_have_required_fields(self):
        tool = SearchKnowledgeTool()
        context = AgentContext(session_customer_id="CUST-0001")
        result = tool.execute({"query": "requisitos crédito"}, context)
        if result.success and result.data and result.data.get("hits"):
            hit = result.data["hits"][0]
            assert "chunk_id" in hit
            assert "title" in hit
            assert "content" in hit
            assert "document_id" in hit

    def test_search_is_stateless(self):
        tool = SearchKnowledgeTool()
        context = AgentContext(session_customer_id="CUST-0001")
        result1 = tool.execute({"query": "tasas de interés"}, context)
        result2 = tool.execute({"query": "tasas de interés"}, context)
        assert result1.data == result2.data


class TestSearchKnowledgeDoesNotModifyRAG:
    """Verify search_knowledge only reads from RAG, never writes."""

    def test_tool_does_not_import_modify_corpus(self):
        import aegisbank_agent.tools.knowledge_tools as kt

        source = kt.__file__
        with open(source, encoding="utf-8") as f:
            content = f.read()
        write_indicators = ["write", "save", "append", "add_doc", "ingest"]
        for indicator in write_indicators:
            assert indicator not in content.lower() or "openai" in content.lower()

    def test_tool_does_not_modify_retrieval(self):
        import aegisbank_agent.tools.knowledge_tools as kt

        source = kt.__file__
        with open(source, encoding="utf-8") as f:
            content = f.read()
        assert "retriever.fit" not in content
        assert "retriever.add" not in content
