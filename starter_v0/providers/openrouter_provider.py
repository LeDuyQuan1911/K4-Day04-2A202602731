from __future__ import annotations

import os

from providers.openai_provider import OpenAIProvider


class OpenRouterProvider(OpenAIProvider):
    """OpenRouter uses an OpenAI-compatible Chat Completions surface."""

    def __init__(self) -> None:
        max_tokens = int(os.getenv("OPENROUTER_MAX_TOKENS", "1024"))
        if max_tokens <= 0:
            raise ValueError("OPENROUTER_MAX_TOKENS must be a positive integer")
        super().__init__(
            api_key_env="OPENROUTER_API_KEY",
            base_url=os.getenv("OPENROUTER_BASE_URL", "https://openrouter.ai/api/v1"),
            default_model="openai/gpt-4o-mini",
            max_tokens=max_tokens,
        )
