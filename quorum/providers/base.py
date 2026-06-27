from __future__ import annotations

from abc import ABC, abstractmethod
from typing import Any


class LLMProvider(ABC):
    """Provider interface — OpenRouter is the default implementation."""

    @abstractmethod
    async def chat_completion(
        self,
        model: str,
        messages: list[dict[str, str]],
        *,
        stream: bool = False,
        max_tokens: int = 4096,
    ) -> dict[str, Any]:
        ...
