"""Tests for model layer base types and OpenAI provider."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch

from models.base import LlmClient, LlmMessage, LlmRequest, LlmResponse, LlmUsage
from models.openai import OpenAiProvider


class TestLlmTypes:
    """Test LLM request/response types."""

    def test_llm_message_creation(self):
        """Test LlmMessage dataclass."""
        msg = LlmMessage(role="user", content="Hello")
        assert msg.role == "user"
        assert msg.content == "Hello"

    def test_llm_request_creation(self):
        """Test LlmRequest dataclass with defaults."""
        messages = [LlmMessage(role="user", content="Test")]
        req = LlmRequest(messages=messages, model="gpt-4")
        assert req.messages == messages
        assert req.model == "gpt-4"
        assert req.temperature == 0.7  # default
        assert req.max_tokens is None  # default

    def test_llm_response_creation(self):
        """Test LlmResponse dataclass."""
        usage = LlmUsage(prompt_tokens=10, completion_tokens=20, total_tokens=30)
        resp = LlmResponse(
            content="Test response",
            model="gpt-4",
            finish_reason="stop",
            usage=usage,
        )
        assert resp.content == "Test response"
        assert resp.model == "gpt-4"
        assert resp.finish_reason == "stop"
        assert resp.usage.total_tokens == 30


class TestLlmClientInterface:
    """Test LlmClient abstract base class."""

    def test_llm_client_is_abstract(self):
        """Test that LlmClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            LlmClient()

    def test_llm_client_has_abstract_methods(self):
        """Test that LlmClient defines abstract methods."""
        assert hasattr(LlmClient, "complete")
        assert hasattr(LlmClient, "get_provider_name")


class TestOpenAiProvider:
    """Test OpenAI provider implementation."""

    def test_openai_provider_requires_api_key(self):
        """Test that OpenAiProvider requires API key."""
        with patch.dict("os.environ", {}, clear=True):
            with pytest.raises(ValueError, match="API key is required"):
                OpenAiProvider()

    def test_openai_provider_accepts_api_key_param(self):
        """Test that OpenAiProvider accepts API key as parameter."""
        provider = OpenAiProvider(api_key="test-key")
        assert provider.api_key == "test-key"
        assert provider.get_provider_name() == "openai"

    def test_openai_provider_uses_env_var(self):
        """Test that OpenAiProvider uses OPENAI_API_KEY env var."""
        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-key"}):
            provider = OpenAiProvider()
            assert provider.api_key == "env-key"

    def test_openai_provider_accepts_base_url(self):
        """Test that OpenAiProvider accepts custom base URL."""
        provider = OpenAiProvider(api_key="test-key", base_url="https://custom.api")
        assert provider.base_url == "https://custom.api"

    @pytest.mark.asyncio
    async def test_openai_provider_complete_request_mapping(self):
        """Test that OpenAiProvider correctly maps LlmRequest to OpenAI format."""
        provider = OpenAiProvider(api_key="test-key")

        # Mock the OpenAI client
        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(
                message=MagicMock(content="Test response"),
                finish_reason="stop",
            )
        ]
        mock_completion.model = "gpt-4o-mini"
        mock_completion.id = "test-id"
        mock_completion.usage = MagicMock(
            prompt_tokens=10, completion_tokens=20, total_tokens=30
        )

        provider.client.chat.completions.create = AsyncMock(
            return_value=mock_completion
        )

        # Create request
        messages = [
            LlmMessage(role="system", content="You are a helpful assistant"),
            LlmMessage(role="user", content="Hello"),
        ]
        request = LlmRequest(
            messages=messages,
            model="gpt-4o-mini",
            temperature=0.5,
            max_tokens=100,
        )

        # Execute
        response = await provider.complete(request)

        # Verify OpenAI API was called with correct format
        provider.client.chat.completions.create.assert_called_once()
        call_kwargs = provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["model"] == "gpt-4o-mini"
        assert call_kwargs["temperature"] == 0.5
        assert call_kwargs["max_tokens"] == 100
        assert len(call_kwargs["messages"]) == 2
        assert call_kwargs["messages"][0]["role"] == "system"
        assert call_kwargs["messages"][1]["content"] == "Hello"

        # Verify response mapping
        assert response.content == "Test response"
        assert response.model == "gpt-4o-mini"
        assert response.finish_reason == "stop"
        assert response.usage.total_tokens == 30

    @pytest.mark.asyncio
    async def test_openai_provider_handles_api_errors(self):
        """Test that OpenAiProvider properly handles API errors."""
        provider = OpenAiProvider(api_key="test-key")

        # Mock API error
        provider.client.chat.completions.create = AsyncMock(
            side_effect=Exception("API rate limit exceeded")
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="Test")],
            model="gpt-4o-mini",
        )

        # Should raise exception with context
        with pytest.raises(Exception, match="OpenAI API error"):
            await provider.complete(request)

    @pytest.mark.asyncio
    async def test_openai_provider_handles_stop_sequences(self):
        """Test that stop sequences are passed to OpenAI API."""
        provider = OpenAiProvider(api_key="test-key")

        mock_completion = MagicMock()
        mock_completion.choices = [
            MagicMock(message=MagicMock(content="Test"), finish_reason="stop")
        ]
        mock_completion.model = "gpt-4o-mini"
        mock_completion.id = "test-id"
        mock_completion.usage = None

        provider.client.chat.completions.create = AsyncMock(
            return_value=mock_completion
        )

        request = LlmRequest(
            messages=[LlmMessage(role="user", content="Test")],
            model="gpt-4o-mini",
            stop_sequences=["END", "STOP"],
        )

        await provider.complete(request)

        call_kwargs = provider.client.chat.completions.create.call_args.kwargs
        assert call_kwargs["stop"] == ["END", "STOP"]
