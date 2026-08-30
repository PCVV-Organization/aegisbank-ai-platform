"""Provider-agnostic boundary for grounded generation."""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass
from typing import Any


@dataclass(frozen=True, slots=True)
class LLMRequest:
    """Provider-neutral request containing the complete prompt contract."""

    prompt_version: str
    system_prompt: str
    user_prompt: str
    response_schema: dict[str, Any]


class LLMProvider(ABC):
    """Minimal LLM boundary; concrete network adapters belong behind it."""

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @property
    @abstractmethod
    def model_name(self) -> str: ...

    @abstractmethod
    def generate(self, request: LLMRequest) -> str:
        """Return one raw JSON response for a provider-neutral request."""
