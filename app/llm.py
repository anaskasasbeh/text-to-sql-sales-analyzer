"""Call the Groq API (OpenAI-compatible) and map its errors to simple exceptions."""

from __future__ import annotations

import logging
from dataclasses import dataclass

import openai

from app.config import GROQ_BASE_URL

logger = logging.getLogger(__name__)


class LLMError(RuntimeError):
    """Base class for problems talking to the model."""


class LLMNotConfigured(LLMError):
    """No API key, or the key was rejected."""


class LLMRateLimited(LLMError):
    """Groq's free-tier limit was reached."""

    def __init__(self, message: str, retry_after: float | None, daily: bool) -> None:
        super().__init__(message)
        self.retry_after = retry_after
        self.daily = daily


class LLMUnavailable(LLMError):
    """Network error, timeout or server error."""


@dataclass
class LLMReply:
    text: str
    prompt_tokens: int
    completion_tokens: int
    finish_reason: str


class GroqClient:
    """Small wrapper around the OpenAI SDK pointed at Groq."""

    def __init__(
        self,
        api_key: str,
        model: str,
        reasoning_effort: str = "low",
        max_completion_tokens: int = 1024,
        timeout_seconds: float = 30.0,
    ) -> None:
        self.model = model
        self.reasoning_effort = reasoning_effort
        self.max_completion_tokens = max_completion_tokens
        self._client = (
            openai.OpenAI(
                api_key=api_key,
                base_url=GROQ_BASE_URL,
                timeout=timeout_seconds,
                max_retries=0,  # Retries are handled by the caller.
            )
            if api_key
            else None
        )

    @property
    def configured(self) -> bool:
        return self._client is not None

    def complete(self, messages: list[dict[str, str]]) -> LLMReply:
        """Send the conversation and return the model's answer text."""
        if self._client is None:
            raise LLMNotConfigured("GROQ_API_KEY is not set.")
        try:
            response = self._client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0,
                reasoning_effort=self.reasoning_effort,
                max_completion_tokens=self.max_completion_tokens,
                extra_body={"include_reasoning": False},
            )
        except openai.RateLimitError as error:
            raise _rate_limit_error(error) from error
        except openai.AuthenticationError as error:
            raise LLMNotConfigured("Groq rejected the API key.") from error
        except (openai.APIConnectionError, openai.APIStatusError) as error:
            logger.warning("Groq request failed: %s", error)
            raise LLMUnavailable("The model service is not reachable right now.") from error

        choice = response.choices[0]
        usage = response.usage
        return LLMReply(
            text=choice.message.content or "",
            prompt_tokens=usage.prompt_tokens if usage else 0,
            completion_tokens=usage.completion_tokens if usage else 0,
            finish_reason=choice.finish_reason or "",
        )


def _rate_limit_error(error: openai.RateLimitError) -> LLMRateLimited:
    """Read Groq's 429 response: is it the per-minute or the per-day limit?"""
    message = str(error)
    retry_after: float | None = None
    header = error.response.headers.get("retry-after") if error.response is not None else None
    if header:
        try:
            retry_after = float(header)
        except ValueError:
            retry_after = None
    daily = "per day" in message.lower()
    logger.warning("Groq rate limit (daily=%s, retry_after=%s): %s", daily, retry_after, message)
    return LLMRateLimited(message, retry_after=retry_after, daily=daily)
