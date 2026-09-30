"""Azure AI Foundry / Azure OpenAI adapters for cloud environments.

The module owns the Azure OpenAI client construction used by both the generic
RAG boundary and the tool-capable application orchestrator.  Azure imports are
lazy so local development remains offline and does not require cloud packages.
"""

from __future__ import annotations

import os
from typing import Any

from aegisbank_rag.foundry_local import _clean_json_response
from aegisbank_rag.provider import LLMProvider, LLMRequest

PROVIDER_NAME: str = "azure-foundry"
DEFAULT_DEPLOYMENT_NAME: str = "phi-4-mini"
DEFAULT_API_VERSION: str = "2024-10-21"


def resolve_azure_endpoint(endpoint: str | None = None) -> str:
    """Return a normalized HTTPS Azure OpenAI endpoint without logging it."""
    resolved = (
        endpoint
        or os.getenv("AZURE_OPENAI_ENDPOINT")
        or os.getenv("AEGISBANK_FOUNDRY_ENDPOINT")
        or ""
    ).rstrip("/")
    if not resolved:
        raise RuntimeError(
            "AZURE_OPENAI_ENDPOINT or AEGISBANK_FOUNDRY_ENDPOINT is required in cloud"
        )
    if not resolved.startswith("https://"):
        raise ValueError("Azure OpenAI endpoint must use https in cloud environments")
    return resolved


def create_azure_openai_client(
    *,
    endpoint: str | None = None,
    api_version: str | None = None,
    credential: Any = None,
    timeout: float = 45.0,
    max_retries: int = 2,
) -> Any:
    """Create the shared Entra-authenticated Azure OpenAI chat client.

    ``DefaultAzureCredential`` selects the managed identity in Azure.  It can
    also use an explicitly configured developer credential during an approved
    cloud integration test; no static API key is accepted by this boundary.
    """
    from azure.identity import (
        DefaultAzureCredential,
        ManagedIdentityCredential,
        get_bearer_token_provider,
    )
    from openai import AzureOpenAI

    resolved_endpoint = resolve_azure_endpoint(endpoint)
    if credential is None:
        env = os.getenv("AEGISBANK_ENV", "").strip().lower()
        if env in {"production", "staging"}:
            client_id = os.getenv("AZURE_CLIENT_ID")
            cred = (
                ManagedIdentityCredential(client_id=client_id)
                if client_id
                else ManagedIdentityCredential()
            )
        else:
            cred = DefaultAzureCredential()
    else:
        cred = credential
    token_provider = get_bearer_token_provider(
        cred,
        "https://cognitiveservices.azure.com/.default",
    )
    return AzureOpenAI(
        azure_endpoint=resolved_endpoint,
        azure_ad_token_provider=token_provider,
        api_version=api_version or os.getenv("AZURE_OPENAI_API_VERSION") or DEFAULT_API_VERSION,
        timeout=timeout,
        max_retries=max_retries,
    )


class AzureFoundryProvider(LLMProvider):
    """Azure AI Foundry / Azure OpenAI implementation of ``LLMProvider``."""

    def __init__(
        self,
        endpoint: str | None = None,
        deployment_name: str | None = None,
        api_version: str | None = None,
        credential: Any = None,
        client: Any = None,
        timeout: float = 45.0,
        max_retries: int = 2,
    ) -> None:
        self._endpoint = (
            endpoint
            or os.getenv("AZURE_OPENAI_ENDPOINT")
            or os.getenv("AEGISBANK_FOUNDRY_ENDPOINT")
            or ""
        ).rstrip("/")
        self._deployment = (
            deployment_name
            or os.getenv("AZURE_OPENAI_DEPLOYMENT_NAME")
            or os.getenv("AEGISBANK_FOUNDRY_DEPLOYMENT_NAME")
            or DEFAULT_DEPLOYMENT_NAME
        )
        self._api_version = (
            api_version or os.getenv("AZURE_OPENAI_API_VERSION") or DEFAULT_API_VERSION
        )
        self._credential = credential
        self._client = client
        self._timeout = timeout
        self._max_retries = max_retries

    @property
    def provider_name(self) -> str:
        return PROVIDER_NAME

    @property
    def model_name(self) -> str:
        return self._deployment

    @property
    def endpoint(self) -> str:
        return self._endpoint

    @property
    def api_version(self) -> str:
        return self._api_version

    def _get_client(self) -> Any:
        if self._client is None:
            self._client = create_azure_openai_client(
                endpoint=self._endpoint,
                api_version=self._api_version,
                credential=self._credential,
                timeout=self._timeout,
                max_retries=self._max_retries,
            )
        return self._client

    def generate(self, request: LLMRequest) -> str:
        response = self._get_client().chat.completions.create(
            model=self._deployment,
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Azure Foundry returned an empty response")
        return _clean_json_response(content)
