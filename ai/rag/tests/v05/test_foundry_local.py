import subprocess

import pytest

from aegisbank_rag.foundry_local import (
    BASE_URL_ENV,
    DEFAULT_MODEL_ALIAS,
    PROVIDER_NAME,
    ChatAPI,
    ChatCompletionsAPI,
    FoundryLocalProvider,
    ModelsAPI,
    resolve_foundry_base_url,
)
from aegisbank_rag.provider import LLMProvider, LLMRequest


class _FakeResponse:
    def __init__(self, content: str) -> None:
        self.content = content


class _FakeCompletions:
    def __init__(self, output_text: str) -> None:
        self._output_text = output_text
        self.calls: list[dict[str, str]] = []

    def create(self, *, model: str, messages: list[dict[str, str]]) -> object:
        self.calls.append({"model": model, "messages": str(messages)})
        return type(
            "Completion",
            (),
            {"choices": [type("Choice", (), {"message": _FakeResponse(self._output_text)})()]},
        )()


class _FakeChat:
    completions: ChatCompletionsAPI

    def __init__(self, output_text: str) -> None:
        self.completions = _FakeCompletions(output_text)


class _FakeModelEntry:
    def __init__(self, model_id: str) -> None:
        self.id = model_id


class _FakeModelList:
    def __init__(self, data: list[_FakeModelEntry]) -> None:
        self.data = data


class _FakeModels:
    def __init__(self, model_ids: list[str]) -> None:
        self._model_ids = model_ids

    def list(self) -> _FakeModelList:
        return _FakeModelList([_FakeModelEntry(model_id) for model_id in self._model_ids])


class _FakeClient:
    chat: ChatAPI
    models: ModelsAPI

    def __init__(self, chat: ChatAPI, models: ModelsAPI) -> None:
        self.chat = chat
        self.models = models


def _request() -> LLMRequest:
    return LLMRequest(
        prompt_version="rag-answer-v001",
        system_prompt="system contract",
        user_prompt="user payload",
        response_schema={},
    )


def test_provider_is_a_llm_provider_implementation() -> None:
    client = _FakeClient(_FakeChat("{}"), _FakeModels(["phi-4-mini-instruct-openvino-gpu"]))

    provider = FoundryLocalProvider(base_url="http://127.0.0.1:39839/v1", client=client)

    assert isinstance(provider, LLMProvider)
    assert provider.provider_name == PROVIDER_NAME == "foundry-local"
    assert provider.model_name == DEFAULT_MODEL_ALIAS == "phi-4-mini"
    assert provider.base_url == "http://127.0.0.1:39839/v1"


def test_generate_forwards_contract_and_returns_raw_text() -> None:
    raw = '{"answer":"ok","citations":[],"abstained":true}'
    chat = _FakeChat(raw)
    client = _FakeClient(chat, _FakeModels(["phi-4-mini-instruct-openvino-gpu"]))
    provider = FoundryLocalProvider(base_url="http://127.0.0.1:39839/v1", client=client)

    assert provider.generate(_request()) == raw
    assert isinstance(chat.completions, _FakeCompletions)
    assert chat.completions.calls == [
        {
            "model": "phi-4-mini",
            "messages": "[{'role': 'system', 'content': 'system contract'}, "
            "{'role': 'user', 'content': 'user payload'}]",
        }
    ]


def test_served_model_ids_lists_runtime_models() -> None:
    client = _FakeClient(_FakeChat("{}"), _FakeModels(["phi-4-mini-instruct-openvino-gpu"]))

    provider = FoundryLocalProvider(base_url="http://127.0.0.1:39839/v1", client=client)

    assert provider.served_model_ids() == ["phi-4-mini-instruct-openvino-gpu"]


def test_resolve_base_url_prefers_env_override() -> None:
    url = resolve_foundry_base_url(env={BASE_URL_ENV: "http://127.0.0.1:1234/v1"})

    assert url == "http://127.0.0.1:1234/v1"


def test_resolve_base_url_reads_server_status() -> None:
    def runner(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(
            args,
            0,
            stdout='{"running":true,"webUrls":["http://127.0.0.1:39839"]}',
            stderr="",
        )

    assert resolve_foundry_base_url(env={}, runner=runner) == "http://127.0.0.1:39839/v1"


def test_resolve_base_url_requires_exposed_url() -> None:
    def runner(*args: str, **kwargs: object) -> subprocess.CompletedProcess[str]:
        return subprocess.CompletedProcess(args, 0, stdout='{"running":false}', stderr="")

    with pytest.raises(RuntimeError, match="did not expose an endpoint URL"):
        resolve_foundry_base_url(env={}, runner=runner)
