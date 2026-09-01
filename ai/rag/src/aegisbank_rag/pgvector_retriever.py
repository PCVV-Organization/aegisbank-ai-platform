"""PostgreSQL + pgvector retriever adapter for AegisBank RAG.

Implements the canonical Retriever interface with vector similarity search,
relational metadata filtering, HNSW and IVFFlat index strategies, and EXPLAIN ANALYZE
query plan telemetry.
"""

from __future__ import annotations

import json
import os
import re
from collections.abc import Sequence
from dataclasses import dataclass, field
from typing import Any

import psycopg
from pgvector.psycopg import register_vector
from psycopg import sql

from aegisbank_rag.chunking import Chunk
from aegisbank_rag.embedding import EmbeddingModel, LocalDenseEmbeddingModel
from aegisbank_rag.retriever import RetrievalHit, Retriever

DEFAULT_PG_URL = "postgresql://aegisuser:AegisBankPgVector2026!@127.0.0.1:5432/aegisbank_rag"


@dataclass
class PgVectorRetriever(Retriever):
    """Retriever adapter backed by PostgreSQL with pgvector extension."""

    name: str = "pgvector_embedding"
    connection_string: str = field(
        default_factory=lambda: os.environ.get("AEGISBANK_PGVECTOR_URL", DEFAULT_PG_URL)
    )
    embedding_model: EmbeddingModel = field(default_factory=LocalDenseEmbeddingModel)
    table_name: str = "rag_chunks"

    def __post_init__(self) -> None:
        if not re.fullmatch(r"[A-Za-z_][A-Za-z0-9_]*", self.table_name):
            raise ValueError("table_name must be a safe SQL identifier")

    def _get_connection(self) -> psycopg.Connection:
        """Establish a psycopg connection with pgvector type registration."""
        if not self.connection_string.strip():
            raise RuntimeError("AEGISBANK_PGVECTOR_URL is required for PostgreSQL access")
        conn = psycopg.connect(self.connection_string)
        register_vector(conn)
        return conn

    def initialize_schema(self) -> None:
        """Create extension, table and base relational indexes idempotently."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("CREATE EXTENSION IF NOT EXISTS vector;")
                create_table_stmt = sql.SQL(
                    """
                    CREATE TABLE IF NOT EXISTS {table} (
                        chunk_id VARCHAR(64) PRIMARY KEY,
                        document_id VARCHAR(64) NOT NULL,
                        document_version VARCHAR(32) NOT NULL,
                        status VARCHAR(32) NOT NULL,
                        effective_from DATE NOT NULL,
                        effective_to DATE,
                        source VARCHAR(255) NOT NULL,
                        topic VARCHAR(64) NOT NULL,
                        title VARCHAR(255) NOT NULL,
                        content TEXT NOT NULL,
                        metadata JSONB NOT NULL DEFAULT '{{}}'::jsonb,
                        embedding vector({dim}) NOT NULL,
                        embedding_model_id VARCHAR(64) NOT NULL,
                        created_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                        updated_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
                    );
                    """
                ).format(
                    table=sql.Identifier(self.table_name),
                    dim=sql.SQL(str(int(self.embedding_model.dimension))),
                )
                cur.execute(create_table_stmt)  # nosec B608

                idx_status = sql.SQL(
                    "CREATE INDEX IF NOT EXISTS idx_rag_chunks_status_topic "
                    "ON {table} (status, topic);"
                ).format(table=sql.Identifier(self.table_name))
                cur.execute(idx_status)  # nosec B608

                idx_doc = sql.SQL(
                    "CREATE INDEX IF NOT EXISTS idx_rag_chunks_doc_ver "
                    "ON {table} (document_id, document_version);"
                ).format(table=sql.Identifier(self.table_name))
                cur.execute(idx_doc)  # nosec B608

                idx_model = sql.SQL(
                    "CREATE INDEX IF NOT EXISTS idx_rag_chunks_model "
                    "ON {table} (embedding_model_id);"
                ).format(table=sql.Identifier(self.table_name))
                cur.execute(idx_model)  # nosec B608
            conn.commit()

    def create_hnsw_index(self, m: int = 16, ef_construction: int = 64) -> None:
        """Create HNSW index for cosine distance similarity."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                stmt = sql.SQL(
                    """
                    CREATE INDEX IF NOT EXISTS idx_rag_chunks_hnsw
                    ON {table} USING hnsw (embedding vector_cosine_ops)
                    WITH (m = {m_val}, ef_construction = {ef_val});
                    """
                ).format(
                    table=sql.Identifier(self.table_name),
                    m_val=sql.SQL(str(int(m))),
                    ef_val=sql.SQL(str(int(ef_construction))),
                )
                cur.execute(stmt)  # nosec B608
            conn.commit()

    def create_ivfflat_index(self, lists: int = 4) -> None:
        """Create IVFFlat index for cosine distance similarity."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                stmt = sql.SQL(
                    """
                    CREATE INDEX IF NOT EXISTS idx_rag_chunks_ivfflat
                    ON {table} USING ivfflat (embedding vector_cosine_ops)
                    WITH (lists = {lists_val});
                    """
                ).format(
                    table=sql.Identifier(self.table_name),
                    lists_val=sql.SQL(str(int(lists))),
                )
                cur.execute(stmt)  # nosec B608
            conn.commit()

    def drop_vector_indexes(self) -> None:
        """Drop all ANN indexes to fall back to Exact Nearest Neighbor search."""
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute("DROP INDEX IF EXISTS idx_rag_chunks_hnsw;")
                cur.execute("DROP INDEX IF EXISTS idx_rag_chunks_ivfflat;")
            conn.commit()

    def fit(self, chunks: Sequence[Chunk]) -> None:
        """Encode and idempotently ingest chunks into PostgreSQL."""
        if not chunks:
            return

        self.initialize_schema()

        # Fit embedding model on chunk contents
        contents = [c.content for c in chunks]
        self.embedding_model.fit(contents)
        embeddings = self.embedding_model.encode(contents)

        select_stmt = sql.SQL(
            "SELECT content, embedding_model_id FROM {table} WHERE chunk_id = %s"
        ).format(table=sql.Identifier(self.table_name))

        insert_stmt = sql.SQL(
            """
            INSERT INTO {table} (
                chunk_id, document_id, document_version, status,
                effective_from, effective_to, source, topic,
                title, content, metadata, embedding,
                embedding_model_id, updated_at
            ) VALUES (
                %s, %s, %s, %s,
                %s, %s, %s, %s,
                %s, %s, %s::jsonb, %s::vector,
                %s, NOW()
            )
            ON CONFLICT (chunk_id) DO NOTHING;
            """
        ).format(table=sql.Identifier(self.table_name))

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                for chunk, emb in zip(chunks, embeddings, strict=True):
                    # Enforce dimension check
                    if len(emb) != self.embedding_model.dimension:
                        msg = (
                            f"Vector dimension mismatch: expected "
                            f"{self.embedding_model.dimension}, got {len(emb)}"
                        )
                        raise ValueError(msg)

                    metadata_json = json.dumps(
                        {
                            "char_count": len(chunk.content),
                            "word_count": len(chunk.content.split()),
                        }
                    )

                    cur.execute(select_stmt, (chunk.chunk_id,))  # nosec B608
                    existing = cur.fetchone()
                    if existing is not None:
                        if (
                            existing[0] != chunk.content
                            or existing[1] != self.embedding_model.model_id
                        ):
                            raise ValueError(
                                f"Incompatible existing chunk_id {chunk.chunk_id}; "
                                "use a new id for content or model changes"
                            )
                        continue

                    cur.execute(
                        insert_stmt,  # nosec B608
                        (
                            chunk.chunk_id,
                            chunk.document_id,
                            chunk.document_version,
                            chunk.status,
                            chunk.effective_from,
                            chunk.effective_to,
                            chunk.source,
                            chunk.topic,
                            chunk.title,
                            chunk.content,
                            metadata_json,
                            emb,
                            self.embedding_model.model_id,
                        ),
                    )
            conn.commit()

    def search(
        self,
        query: str,
        *,
        top_k: int = 5,
        status_filter: str | None = "active",
        topic_filter: str | None = None,
        min_score: float = 0.0,
    ) -> list[RetrievalHit]:
        """Perform vector similarity search with parameterized metadata filters."""
        if not query.strip():
            raise ValueError("Query must not be empty")

        query_vec = self.embedding_model.encode_one(query)

        search_stmt = sql.SQL(
            """
            SELECT
                chunk_id,
                document_id,
                document_version,
                title,
                topic,
                content,
                source,
                status,
                effective_from::text,
                effective_to::text,
                1.0 - (embedding <=> %(query_vec)s::vector) AS score
            FROM {table}
            WHERE (%(status_filter)s::text IS NULL OR status = %(status_filter)s::text)
              AND (%(topic_filter)s::text IS NULL OR topic = %(topic_filter)s::text)
              AND effective_from <= CURRENT_DATE
              AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
              AND embedding_model_id = %(model_id)s::text
            ORDER BY embedding <=> %(query_vec)s::vector ASC
            LIMIT %(top_k)s::int;
            """
        ).format(table=sql.Identifier(self.table_name))

        hits: list[RetrievalHit] = []
        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    search_stmt,  # nosec B608
                    {
                        "query_vec": query_vec,
                        "status_filter": status_filter,
                        "topic_filter": topic_filter,
                        "model_id": self.embedding_model.model_id,
                        "top_k": top_k,
                    },
                )
                rows = cur.fetchall()

                for rank, row in enumerate(rows, start=1):
                    score = float(row[10])
                    if score < min_score:
                        continue
                    hits.append(
                        RetrievalHit(
                            chunk_id=row[0],
                            document_id=row[1],
                            document_version=row[2],
                            title=row[3],
                            topic=row[4],
                            content=row[5],
                            source=row[6],
                            status=row[7],
                            effective_from=row[8],
                            effective_to=row[9],
                            score=score,
                            rank=rank,
                            retrieval_method=self.name,
                        )
                    )

        return hits

    def explain_query(
        self,
        query: str,
        *,
        top_k: int = 5,
        status_filter: str | None = "active",
        topic_filter: str | None = None,
    ) -> list[dict[str, Any]]:
        """Retrieve the EXPLAIN query plan for telemetry and inspection."""
        query_vec = self.embedding_model.encode_one(query)

        explain_stmt = sql.SQL(
            """
            EXPLAIN (ANALYZE, BUFFERS, FORMAT JSON)
            SELECT
                chunk_id, document_id, title,
                1.0 - (embedding <=> %(query_vec)s::vector) AS score
            FROM {table}
            WHERE (%(status_filter)s::text IS NULL OR status = %(status_filter)s::text)
              AND (%(topic_filter)s::text IS NULL OR topic = %(topic_filter)s::text)
              AND effective_from <= CURRENT_DATE
              AND (effective_to IS NULL OR effective_to >= CURRENT_DATE)
              AND embedding_model_id = %(model_id)s::text
            ORDER BY embedding <=> %(query_vec)s::vector ASC
            LIMIT %(top_k)s::int;
            """
        ).format(table=sql.Identifier(self.table_name))

        with self._get_connection() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    explain_stmt,  # nosec B608
                    {
                        "query_vec": query_vec,
                        "status_filter": status_filter,
                        "topic_filter": topic_filter,
                        "model_id": self.embedding_model.model_id,
                        "top_k": top_k,
                    },
                )
                plan = cur.fetchone()
                if plan and isinstance(plan[0], list):
                    return plan[0]
                elif plan and isinstance(plan[0], dict):
                    return [plan[0]]
                return []
