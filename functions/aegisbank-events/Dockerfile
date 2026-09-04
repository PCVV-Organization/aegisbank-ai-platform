# syntax=docker/dockerfile:1.7
# AegisBank Functions runtime image for v0.13.1 live E2E acceptance.
#
# Extends the official Microsoft image
# `mcr.microsoft.com/azure-functions/python:4-python3.14` because it ships
# the Functions host AND the Python 3.14 worker bundled (which is the
# version missing from the Windows Core Tools installer — see
# docs/quality/V0131-RUNTIME-EVIDENCE.md). The image is otherwise bare-bones;
# we install the project's Python dependencies with pip so the runtime is
# self-contained.
#
# Build context: repository root. All paths below are relative to the root.
#
# References:
#   - https://learn.microsoft.com/en-us/azure/azure-functions/functions-deploy-container
#   - https://learn.microsoft.com/en-us/azure/azure-functions/functions-how-to-custom-container

ARG PYTHON_IMAGE=mcr.microsoft.com/azure-functions/python:4-python3.14

FROM ${PYTHON_IMAGE} AS build
USER root

WORKDIR /build

# Copy source packages from the host repository so we can install them
# as Python packages without going through PyPI.
COPY services/mock-core-banking /build/mock_core_banking
COPY ai/rag /build/aegisbank_rag
COPY ai/agent /build/aegisbank_agent

RUN python -m pip install --no-cache-dir \
        "azure-functions==2.3.0" \
        "jsonschema==4.26.0" \
        "opentelemetry-api==1.44.0" \
        "opentelemetry-sdk==1.44.0" \
        "pydantic==2.13.4" \
        "sqlalchemy==2.0.52" \
        "azure-servicebus==7.14.3" \
    && python -m pip install --no-cache-dir --no-deps \
        /build/mock_core_banking \
        /build/aegisbank_rag \
        /build/aegisbank_agent \
    && rm -rf /root/.cache

WORKDIR /home/site/wwwroot

# Copy contracts so schema validation works inside the container.
COPY contracts ./contracts

# Copy the Function App entry point.
COPY functions/aegisbank-events/function_app.py ./function_app.py
COPY functions/aegisbank-events/service_request_handler.py ./service_request_handler.py
COPY functions/aegisbank-events/cloud_event.py ./cloud_event.py
COPY functions/aegisbank-events/host.json ./host.json
COPY functions/aegisbank-events/local.settings.example.json ./local.settings.json
COPY functions/aegisbank-events/samples ./samples

# Pre-seed local secrets so the Functions Host can authorize webhooks locally.
RUN mkdir -p /home/site/secrets \
    && echo '{"masterKey":{"name":"master","value":"aegisbank-local-master-key","encrypted":false},"functionKeys":[{"name":"default","value":"aegisbank-local-function-key","encrypted":false}],"systemKeys":[{"name":"eventgridextensionconfig_extension","value":"aegisbank-local-eventgrid-key","encrypted":false}]}' > /home/site/secrets/host.json

ENV PYTHONUNBUFFERED=1 \
    AzureWebJobsScriptRoot=/home/site/wwwroot \
    FUNCTIONS_WORKER_RUNTIME=python \
    AZURE_FUNCTIONS_ENVIRONMENT=Development \
    AzureWebJobsSecretStorageType=Files \
    FUNCTIONS_SECRETS_PATH=/home/site/secrets \
    AzureFunctionsWebHost__SecretsPath=/home/site/secrets \
    AzureWebJobsStorage="" \
    AEGISBANK_FUNCTION_IDEMPOTENCY_DATABASE_URL="sqlite:///:memory:"

EXPOSE 80
