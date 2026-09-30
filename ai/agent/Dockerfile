# syntax=docker/dockerfile:1.7
FROM python:3.14-slim AS runtime

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    AEGISBANK_ENV=staging

WORKDIR /app

COPY pyproject.toml README.md ./
COPY src ./src

RUN python -m pip install --no-cache-dir --disable-pip-version-check . \
    && useradd --create-home --uid 10001 --shell /usr/sbin/nologin aegisbank \
    && mkdir --parents /app/data /tmp/aegisbank \
    && chown --recursive aegisbank:aegisbank /app /tmp/aegisbank

USER 10001:10001
EXPOSE 8000

HEALTHCHECK --interval=10s --timeout=3s --start-period=10s --retries=5 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://127.0.0.1:8000/health/live', timeout=2)"

CMD ["python", "-m", "uvicorn", "aegisbank_agent.api:app", "--host", "0.0.0.0", "--port", "8000"]
