import pytest

from aegisbank_rag.constants import CORPUS_DIR
from aegisbank_rag.corpus import load_corpus


@pytest.fixture(scope="session")
def documents():
    return load_corpus(CORPUS_DIR)


@pytest.fixture(scope="session")
def active_documents(documents):
    from datetime import date

    from aegisbank_rag.corpus import filter_active

    return filter_active(documents, cutoff=date.fromisoformat("2026-12-31"))


@pytest.fixture(scope="session")
def chunks(documents):
    from aegisbank_rag.chunking import chunk_corpus

    return chunk_corpus(documents)


@pytest.fixture(scope="session")
def chunk_index(chunks):
    return {chunk.chunk_id: chunk for chunk in chunks}


@pytest.fixture(scope="session")
def queries():
    from aegisbank_rag.evaluation import load_queries

    return load_queries()


@pytest.fixture(scope="session")
def qrels():
    from aegisbank_rag.evaluation import load_qrels

    return load_qrels()
