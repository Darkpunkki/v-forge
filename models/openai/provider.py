"""OpenAI provider implementation."""

import os
from typing import Optional

from openai import AsyncOpenAI
from openai.types.chat import ChatCompletion

from models.base import LlmClient, LlmMessage, LlmRequest, LlmResponse, LlmUsage


class OpenAiProvider(LlmClient):
    """OpenAI provider implementation using OpenAI Python SDK.

    This is a thin adapter that translates between our LlmRequest/LlmResponse
    types and OpenAI's chat completion API.

    Environment variables:
        OPENAI_API_KEY: OpenAI API key (required)
        OPENAI_BASE_URL: Custom base URL (optional)
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        base_url: Optional[str] = None,
        timeout: float = 60.0,
    ):
        """Initialize OpenAI provider.

        Args:
            api_key: OpenAI API key (defaults to OPENAI_API_KEY env var)
            base_url: Custom base URL (defaults to OPENAI_BASE_URL env var or OpenAI default)
            timeout: Request timeout in seconds
        """
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        self.base_url = base_url or os.getenv("OPENAI_BASE_URL")
        self.timeout = timeout

        if not self.api_key:
            raise ValueError(
                "OpenAI API key is required. Set OPENAI_API_KEY environment variable "
                "or pass api_key to constructor."
            )

        # Initialize async client
        client_kwargs = {"api_key": self.api_key, "timeout": timeout}
        if self.base_url:
            client_kwargs["base_url"] = self.base_url

        self.client = AsyncOpenAI(**client_kwargs)

    async def complete(self, request: LlmRequest) -> LlmResponse:
        """Send a completion request to OpenAI.

        Args:
            request: LlmRequest with messages and parameters

        Returns:
            LlmResponse with generated content

        Raises:
            Exception: OpenAI API errors (rate limits, invalid requests, etc.)
        """
        try:
            # Convert our LlmMessage format to OpenAI format
            openai_messages = [
                {"role": msg.role, "content": msg.content} for msg in request.messages
            ]

            # Build OpenAI request parameters
            completion_kwargs = {
                "model": request.model,
                "messages": openai_messages,
                "temperature": request.temperature,
            }

            if request.max_tokens is not None:
                completion_kwargs["max_tokens"] = request.max_tokens

            if request.stop_sequences:
                completion_kwargs["stop"] = request.stop_sequences

            # Call OpenAI API
            completion: ChatCompletion = await self.client.chat.completions.create(
                **completion_kwargs
            )

            # Extract response content
            choice = completion.choices[0]
            content = choice.message.content or ""
            finish_reason = choice.finish_reason or "stop"

            # Extract usage info
            usage = None
            if completion.usage:
                usage = LlmUsage(
                    prompt_tokens=completion.usage.prompt_tokens,
                    completion_tokens=completion.usage.completion_tokens,
                    total_tokens=completion.usage.total_tokens,
                )

            return LlmResponse(
                content=content,
                model=completion.model,
                finish_reason=finish_reason,
                usage=usage,
                metadata={"completion_id": completion.id},
            )

        except Exception as e:
            # Re-raise with provider context
            raise Exception(f"OpenAI API error: {str(e)}") from e

    def get_provider_name(self) -> str:
        """Return provider name."""
        return "openai"
