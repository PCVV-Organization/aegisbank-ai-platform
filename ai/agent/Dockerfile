# syntax=docker/dockerfile:1.7
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AEGISBANK_ENV=staging \
    AEGISBANK_SESSION_DB_PATH=/tmp/aegisbank/sessions.db

WORKDIR /app

COPY ai/agent/pyproject.toml ai/agent/README.md ./
COPY ai/agent/src ./src
COPY ai/rag /build/aegisbank-rag
COPY services/mock-core-banking /build/mock-core-banking
COPY ai/rag/data /build/aegisbank-rag-data

RUN python -m pip install --no-cache-dir --disable-pip-version-check \
        /build/aegisbank-rag \
        /build/mock-core-banking \
        . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin aegisbank \
    && mkdir --parents /app/data /tmp/aegisbank \
    && python -c "from aegisbank_rag.constants import CORPUS_DIR; CORPUS_DIR.mkdir(parents=True, exist_ok=True)" \
    && cp --recursive /build/aegisbank-rag-data/corpus/. "$(python -c 'from aegisbank_rag.constants import CORPUS_DIR; print(CORPUS_DIR)')" \
    && chown --recursive aegisbank:aegisbank /app /tmp/aegisbank

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"

CMD ["python", "-m", "uvicorn", "aegisbank_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
