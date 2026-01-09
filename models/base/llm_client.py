"""LLM client interface and base types for model abstraction layer."""

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any, Optional


@dataclass
class LlmMessage:
    """Single message in a conversation."""

    role: str  # "system", "user", "assistant"
    content: str


@dataclass
class LlmRequest:
    """Request to an LLM provider."""

    messages: list[LlmMessage]
    model: str
    temperature: float = 0.7
    max_tokens: Optional[int] = None
    stop_sequences: Optional[list[str]] = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass
class LlmUsage:
    """Token usage information."""

    prompt_tokens: int = 0
    completion_tokens: int = 0
    total_tokens: int = 0


@dataclass
class LlmResponse:
    """Response from an LLM provider."""

    content: str
    model: str
    finish_reason: str  # "stop", "length", "error"
    usage: Optional[LlmUsage] = None
    metadata: dict[str, Any] = field(default_factory=dict)


class LlmClient(ABC):
    """Abstract base class for LLM providers.

    This interface defines a provider-agnostic way to interact with language models.
    Concrete implementations (OpenAI, Claude, local models) adapt their specific
    APIs to this interface.

    Design principles:
    - Keep prompts and routing logic OUTSIDE this class
    - Providers are thin adapters that translate request/response formats
    - All provider-specific details should be hidden behind this interface
    """

    @abstractmethod
    async def complete(self, request: LlmRequest) -> LlmResponse:
        """Send a completion request to the model provider.

        Args:
            request: LlmRequest with messages, model, and parameters

        Returns:
            LlmResponse with generated content and metadata

        Raises:
            Exception: Provider-specific errors (API failures, rate limits, etc.)
        """
        pass

    @abstractmethod
    def get_provider_name(self) -> str:
        """Return the provider name (e.g., 'openai', 'claude', 'local').

        Returns:
            Provider identifier string
        """
        pass
