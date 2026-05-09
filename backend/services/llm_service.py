from __future__ import annotations

import logging
import time
from functools import lru_cache
from typing import TypeVar

from pydantic import BaseModel

from backend.services.config import get_settings

logger = logging.getLogger(__name__)

ModelT = TypeVar("ModelT", bound=BaseModel)


class LLMService:
    def __init__(self) -> None:
        self.settings = get_settings()
        self._client = None
        self._disabled_reason: str | None = None
        self._cooldown_until = 0.0

        if not self.settings.enable_llm:
            self._disabled_reason = "LLM integration disabled by ENABLE_LLM."
            return

        if not self.settings.openai_api_key:
            self._disabled_reason = "OPENAI_API_KEY is not configured."
            return

        try:
            import httpx
            from openai import OpenAI

            # Keep failures snappy so the triage workflow can continue on safe fallbacks.
            http_client = httpx.Client(
                timeout=self.settings.openai_timeout_seconds,
                trust_env=self.settings.openai_trust_env,
            )
            self._client = OpenAI(
                api_key=self.settings.openai_api_key,
                max_retries=0,
                timeout=self.settings.openai_timeout_seconds,
                http_client=http_client,
            )
        except Exception as exc:  # pragma: no cover - defensive import guard
            self._disabled_reason = f"OpenAI client unavailable: {exc}"

    @property
    def available(self) -> bool:
        if self._client is None:
            return False
        if self._cooldown_until and time.monotonic() < self._cooldown_until:
            return False
        return True

    @property
    def unavailable_reason(self) -> str:
        return self._disabled_reason or "LLM unavailable."

    def structured_completion(
        self,
        *,
        system_prompt: str,
        user_prompt: str,
        schema_model: type[ModelT],
        max_output_tokens: int = 700,
    ) -> tuple[ModelT | None, str | None]:
        if self._client is None:
            return None, self.unavailable_reason

        if self._cooldown_until and time.monotonic() < self._cooldown_until:
            return None, self.unavailable_reason

        try:
            parse_method = getattr(self._client.responses, "parse", None)
            if parse_method is None:
                return None, "OpenAI SDK does not expose responses.parse; upgrade the openai package."

            response = parse_method(
                model=self.settings.openai_model,
                instructions=system_prompt,
                input=user_prompt,
                text_format=schema_model,
                text={"verbosity": "medium"},
                temperature=0.2,
                max_output_tokens=max_output_tokens,
            )
            parsed = getattr(response, "output_parsed", None)
            if parsed is None:
                return None, "The model did not return structured output."
            self._disabled_reason = None
            return parsed, None
        except Exception as exc:  # pragma: no cover - network/runtime defensive guard
            self._disabled_reason = f"OpenAI request failed: {exc}"
            self._cooldown_until = time.monotonic() + 30
            logger.warning("Structured OpenAI request failed: %s", exc)
            return None, f"OpenAI request failed: {exc}"


@lru_cache
def get_llm_service() -> LLMService:
    return LLMService()
