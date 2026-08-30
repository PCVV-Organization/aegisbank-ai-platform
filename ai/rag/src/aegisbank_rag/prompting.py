"""Versioned prompt loading and provider-neutral request construction."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Final

from aegisbank_rag.constants import GENERATION_PROMPT_PATH
from aegisbank_rag.context import GroundingContext
from aegisbank_rag.provider import LLMRequest

_PROMPT_VERSION: Final = re.compile(r"^rag-answer-v\d{3}$")
_PROMPT_FIELDS: Final = {
    "version",
    "purpose",
    "response_format",
    "evidence_rules",
    "abstention_rule",
    "abstention_answer",
    "restrictions",
    "system_prompt",
}


@dataclass(frozen=True, slots=True)
class PromptDefinition:
    version: str
    purpose: str
    response_format: dict[str, Any]
    evidence_rules: tuple[str, ...]
    abstention_rule: str
    abstention_answer: str
    restrictions: tuple[str, ...]
    system_prompt: str


def load_prompt(path: Path = GENERATION_PROMPT_PATH) -> PromptDefinition:
    payload = json.loads(path.read_text(encoding="utf-8"))
    if set(payload) != _PROMPT_FIELDS:
        raise ValueError(f"Prompt fields differ from contract: {sorted(payload)}")
    version = payload["version"]
    if not isinstance(version, str) or _PROMPT_VERSION.fullmatch(version) is None:
        raise ValueError(f"Invalid prompt version: {version!r}")
    system_prompt = payload["system_prompt"]
    if not isinstance(system_prompt, str) or version not in system_prompt:
        raise ValueError("System prompt must identify its prompt version")
    response_format = payload["response_format"]
    if not isinstance(response_format, dict):
        raise ValueError("response_format must be an object")
    return PromptDefinition(
        version=version,
        purpose=_required_text(payload, "purpose"),
        response_format=response_format,
        evidence_rules=_required_text_list(payload, "evidence_rules"),
        abstention_rule=_required_text(payload, "abstention_rule"),
        abstention_answer=_required_text(payload, "abstention_answer"),
        restrictions=_required_text_list(payload, "restrictions"),
        system_prompt=system_prompt,
    )


def build_llm_request(
    prompt: PromptDefinition,
    query: str,
    context: GroundingContext,
) -> LLMRequest:
    if not query.strip():
        raise ValueError("Query must not be empty")
    user_payload = {
        "context": context.as_dict(),
        "query": query.strip(),
    }
    return LLMRequest(
        prompt_version=prompt.version,
        system_prompt=prompt.system_prompt,
        user_prompt=json.dumps(
            user_payload,
            ensure_ascii=False,
            separators=(",", ":"),
            sort_keys=True,
        ),
        response_schema=prompt.response_format,
    )


def _required_text(payload: dict[str, Any], field: str) -> str:
    value = payload[field]
    if not isinstance(value, str) or not value.strip():
        raise ValueError(f"Prompt field {field} must be non-empty text")
    return value


def _required_text_list(payload: dict[str, Any], field: str) -> tuple[str, ...]:
    value = payload[field]
    if not isinstance(value, list) or not value:
        raise ValueError(f"Prompt field {field} must be a non-empty list")
    if any(not isinstance(item, str) or not item.strip() for item in value):
        raise ValueError(f"Prompt field {field} contains invalid text")
    return tuple(value)
