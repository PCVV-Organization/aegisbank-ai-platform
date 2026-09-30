"""Unit tests for Azure AI Foundry / Azure OpenAI cloud provider and dotenv safety."""

from __future__ import annotations

from unittest.mock import MagicMock

import pytest

from aegisbank_rag.azure_foundry import AzureFoundryProvider, resolve_azure_endpoint
from aegisbank_rag.provider import LLMProvider, LLMRequest


def test_azure_foundry_provider_satisfies_protocol() -> None:
    fake_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"analysis": "grounded_response", "citations": ["DOC-001"]}'
    fake_client.chat.completions.create.return_value.choices = [mock_choice]

    provider = AzureFoundryProvider(
        endpoint="https://aegisbank-ai.cognitiveservices.azure.com",
        deployment_name="phi-4-mini",
        client=fake_client,
    )

    assert isinstance(provider, LLMProvider)
    assert provider.provider_name == "azure-foundry"
    assert provider.model_name == "phi-4-mini"
    assert provider.endpoint == "https://aegisbank-ai.cognitiveservices.azure.com"

    request = LLMRequest(
        prompt_version="v1",
        system_prompt="You are a banking assistant.",
        user_prompt="Explain DELINQUENT loan status.",
        response_schema={},
    )

    result = provider.generate(request)
    assert "grounded_response" in result
    fake_client.chat.completions.create.assert_called_once()


def test_azure_foundry_provider_cleans_markdown_fences() -> None:
    fake_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '```json\n{"status": "DELINQUENT", "citations": ["DOC-001"]}\n```'
    fake_client.chat.completions.create.return_value.choices = [mock_choice]

    provider = AzureFoundryProvider(
        endpoint="https://aegisbank-ai.cognitiveservices.azure.com",
        deployment_name="phi-4-mini",
        client=fake_client,
    )

    request = LLMRequest(
        prompt_version="v1",
        system_prompt="sys",
        user_prompt="usr",
        response_schema={},
    )

    result = provider.generate(request)
    assert result.startswith("{")
    assert "```" not in result


def test_azure_foundry_provider_rejects_empty_response() -> None:
    fake_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = "   "
    fake_client.chat.completions.create.return_value.choices = [mock_choice]

    provider = AzureFoundryProvider(
        endpoint="https://aegisbank-ai.cognitiveservices.azure.com",
        deployment_name="phi-4-mini",
        client=fake_client,
    )

    request = LLMRequest(
        prompt_version="v1",
        system_prompt="sys",
        user_prompt="usr",
        response_schema={},
    )

    with pytest.raises(ValueError, match="empty response"):
        provider.generate(request)


def test_azure_foundry_provider_requires_https_endpoint() -> None:
    provider = AzureFoundryProvider(
        endpoint="http://insecure.cognitiveservices.azure.com",
        deployment_name="phi-4-mini",
    )
    request = LLMRequest(
        prompt_version="v1",
        system_prompt="sys",
        user_prompt="usr",
        response_schema={},
    )
    with pytest.raises(ValueError, match="must use https"):
        provider.generate(request)


def test_resolve_azure_endpoint_rejects_missing_or_insecure_values(monkeypatch) -> None:
    monkeypatch.delenv("AZURE_OPENAI_ENDPOINT", raising=False)
    monkeypatch.delenv("AEGISBANK_FOUNDRY_ENDPOINT", raising=False)

    with pytest.raises(RuntimeError, match="required"):
        resolve_azure_endpoint()
    with pytest.raises(ValueError, match="https"):
        resolve_azure_endpoint("http://insecure.cognitiveservices.azure.com")


def test_azure_provider_uses_shared_client_factory(monkeypatch) -> None:
    fake_client = MagicMock()
    mock_choice = MagicMock()
    mock_choice.message.content = '{"answer": "ok"}'
    fake_client.chat.completions.create.return_value.choices = [mock_choice]
    factory = MagicMock(return_value=fake_client)
    monkeypatch.setattr("aegisbank_rag.azure_foundry.create_azure_openai_client", factory)

    provider = AzureFoundryProvider(
        endpoint="https://aegisbank-ai.cognitiveservices.azure.com",
        deployment_name="test-deployment",
    )

    assert provider.generate(LLMRequest("v1", "sys", "usr", {})) == '{"answer": "ok"}'
    factory.assert_called_once_with(
        endpoint="https://aegisbank-ai.cognitiveservices.azure.com",
        api_version="2024-10-21",
        credential=None,
        timeout=45.0,
        max_retries=2,
    )
