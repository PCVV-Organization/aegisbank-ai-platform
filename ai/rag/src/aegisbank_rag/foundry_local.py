"""Foundry Local adapter behind the provider-agnostic LLM boundary."""

from __future__ import annotations

import json
import os
import shutil
import subprocess
from typing import Any, Protocol, cast

from openai import OpenAI

from aegisbank_rag.provider import LLMProvider, LLMRequest

PROVIDER_NAME: str = "foundry-local"
DEFAULT_MODEL_ALIAS: str = "phi-4-mini"
BASE_URL_ENV: str = "AEGISBANK_FOUNDRY_LOCAL_BASE_URL"
_PLACEHOLDER_API_KEY: str = "none"


class ChatCompletionsAPI(Protocol):
    def create(self, *, model: str, messages: list[dict[str, str]]) -> Any: ...


class ModelsAPI(Protocol):
    def list(self) -> Any: ...


class ChatAPI(Protocol):
    completions: ChatCompletionsAPI


class OpenAIClient(Protocol):
    chat: ChatAPI
    models: ModelsAPI


def check_foundry_health(base_url: str, timeout: float = 1.0) -> bool:
    """Check if the local Foundry / OpenAI endpoint is actively responding."""
    import urllib.request

    url = f"{base_url.rstrip('/')}/models"
    try:
        req = urllib.request.Request(url, headers={"Authorization": "Bearer none"})
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return resp.status == 200
    except Exception:
        return False


def resolve_foundry_base_url(
    *,
    env: dict[str, str] | None = None,
    runner: Any = subprocess.run,
) -> str:
    """Resolve the local OpenAI-compatible endpoint without hardcoding a port."""
    environment = os.environ if env is None else env
    override = environment.get(BASE_URL_ENV, "").strip()
    if override:
        return override
    if runner is subprocess.run and shutil.which("foundry") is None:
        raise RuntimeError("CLI 'foundry' no encontrado en PATH")
    try:
        completed = runner(
            ["foundry", "server", "status", "-o", "json"],
            capture_output=True,
            text=True,
            check=True,
        )
        payload = json.loads(completed.stdout)
    except (OSError, subprocess.CalledProcessError, json.JSONDecodeError) as exc:
        raise RuntimeError(
            "Foundry Local no está disponible; ejecuta 'foundry model list' y reintenta"
        ) from exc
    urls = payload.get("webUrls") if isinstance(payload, dict) else None
    if not isinstance(urls, list) or not urls:
        raise RuntimeError("Foundry Local server status did not expose an endpoint URL")
    endpoint = str(urls[0]).rstrip("/")
    return endpoint if endpoint.endswith("/v1") else f"{endpoint}/v1"


class FoundryLocalProvider(LLMProvider):
    """OpenAI Chat Completions adapter for the local Foundry runtime."""

    def __init__(
        self,
        *,
        model: str = DEFAULT_MODEL_ALIAS,
        base_url: str | None = None,
        client: OpenAIClient | None = None,
    ) -> None:
        self._model = model
        self._base_url = base_url or resolve_foundry_base_url()
        self._client = client or cast(
            OpenAIClient,
            OpenAI(base_url=self._base_url, api_key=_PLACEHOLDER_API_KEY),
        )

    @property
    def provider_name(self) -> str:
        return PROVIDER_NAME

    @property
    def model_name(self) -> str:
        return self._model

    @property
    def base_url(self) -> str:
        return self._base_url

    def served_model_ids(self) -> list[str]:
        return [entry.id for entry in self._client.models.list().data]

    def generate(self, request: LLMRequest) -> str:
        response = self._client.chat.completions.create(
            model=self._model,
            messages=[
                {"role": "system", "content": request.system_prompt},
                {"role": "user", "content": request.user_prompt},
            ],
        )
        content = response.choices[0].message.content
        if not isinstance(content, str) or not content.strip():
            raise ValueError("Foundry Local returned an empty response")
        return _clean_json_response(content)


def _clean_json_response(content: str) -> str:
    cleaned = content.lstrip("\ufeff").strip()
    if cleaned.startswith("```"):
        lines = cleaned.splitlines()
        if lines and lines[0].strip().startswith("```"):
            lines = lines[1:]
        if lines and lines[-1].strip() == "```":
            lines = lines[:-1]
        cleaned = "\n".join(lines).strip()
    return cleaned
