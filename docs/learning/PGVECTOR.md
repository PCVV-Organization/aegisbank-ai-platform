# v0.12: PostgreSQL + pgvector Data Foundation

This is a local, synthetic-data laboratory. It demonstrates a relational database
extended with vectors; it does not claim Azure production parity.

## Concepts

| Concept | Definition, internal mechanism, AegisBank use | Alternative, risks, Mibanco/AI-200, maturity |
|---|---|---|
| DBMS/RDBMS | Database Management System / sistema gestor; Relational DBMS stores typed tables, rows and columns. PostgreSQL is the RDBMS used by `PgVectorRetriever`. | SQL Server or document stores may fit other workloads; schema drift and unbounded connections are risks. Maps to SQL/data design. `LAB-COVERED`. |
| Schema/table/row | A schema namespaces tables; `rag_chunks` has one row per chunk, with PK `chunk_id`, metadata and embedding. | JSON-only storage loses constraints; missing PKs create duplicates. `LOCAL-PGVECTOR-COVERED`. |
| PK/FK/transaction/ACID | Primary key identifies a row; foreign key links rows; a transaction commits all or none. ACID means Atomicity, Consistency, Isolation, Durability. Ingestion commits a complete batch or rolls back. | Eventual stores trade constraints for scale; partial ingestion is a retrieval integrity risk. Core backend skill and AI-200 data domain. `LAB-COVERED`. |
| Index/query plan | An index avoids scanning every row. `EXPLAIN (ANALYZE, BUFFERS)` reports estimated cost, actual time, rows and buffer access. | A tiny corpus may choose sequential scan; never claim enterprise throughput from this lab. `LAB-COVERED`. |
| Embedding/vector | An embedding maps text to a fixed-length numeric vector; this lab reuses deterministic TF-IDF + Truncated SVD LSA (`aegisbank-lsa-32`/configured dimension), normalized to unit L2 norm. | A neural embedding model can improve semantics but adds model supply-chain/compute concerns. Do not treat phi-4-mini as an embedding model. `LAB-COVERED`. |
| Vector database/pgvector | pgvector adds PostgreSQL `vector(N)` and distance operators. `PgVectorRetriever` stores and ranks chunks while preserving relational metadata. | A dedicated vector DB may scale independently; it would duplicate retrieval ownership here. AI-200 vector/RAG domain. `LOCAL-PGVECTOR-COVERED`. |
| Cosine/L2/inner product | Cosine compares direction; L2 compares Euclidean distance; inner product multiplies coordinates. The adapter uses cosine distance `<=>`. | Metric must match embedding normalization and index operator class. Wrong dimension/metric corrupts ranking. `LAB-COVERED`. |
| Exact NN/ANN | Exact nearest-neighbor compares every candidate and is the recall baseline. ANN (Approximate NN) prunes candidates for latency. | Exact is fine for small corpora; ANN trades recall for speed. `LAB-COVERED`. |
| HNSW/IVFFlat | HNSW (Hierarchical Navigable Small World) uses a layered graph (`m`, `ef_construction`, `ef_search`). IVFFlat (Inverted File Flat) partitions vectors into lists (`lists`, `probes`). | HNSW uses more memory; IVFFlat needs useful clustering. DiskANN is Azure-only here: `DISKANN_AZURE_CLOUD_PENDING`. `LAB-COVERED` when executed. |
| Metadata filter | SQL predicates enforce `status`, `topic`, effective dates and embedding model before ranking. Superseded documents are excluded deterministically. | LLM filtering is unsafe; missing predicates can surface obsolete policy. Banking authorization and AI-200 RAG filter skill. `LAB-COVERED`. |
| Connection/pool | A connection is a DB session; a pool reuses bounded sessions. The adapter uses explicit psycopg connections and closes them per operation; production pooling is future work. | One connection per request has overhead; an unbounded pool can exhaust PostgreSQL. `PROD-PARTIAL`. |
| RAG/vector store | Retrieval-Augmented Generation fetches evidence before generation. The adapter extends the existing `Retriever`; it does not create a second RAG engine or own chunking/evaluation. | Keyword retrieval remains useful and is the historical baseline. Mibanco AI engineering and AI-200 RAG alignment. `LOCAL-PGVECTOR-COVERED`. |
| Migration | A migration is a versioned schema change. This lab's idempotent `initialize_schema()` is a local bootstrap, not a production migration history. | Alembic migrations are appropriate before deployment; ad-hoc destructive DDL risks data loss. `CLOUD-PENDING`. |

## Flow and Evaluation

`authorized corpus -> canonical chunking -> deterministic embedding -> PostgreSQL ->
PgVectorRetriever -> existing RAG evaluation`. The same qrels and queries are used for
`lexical_tfidf`, `dense_local_lsa`, `hybrid_rrf` and `pgvector_embedding`; nDCG@5, MRR@5,
Precision@5 and Recall@5 are measurements, not a promise that vectors win.

Cosmos DB/Change Feed and Redis/cache are documented as future micro-hitos only and are
not implemented here.
