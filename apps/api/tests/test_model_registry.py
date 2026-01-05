"""Tests for model provider registry."""

import pytest
from unittest.mock import patch

from models.registry import ModelProviderRegistry, get_model_registry
from models.openai import OpenAiProvider


class TestModelProviderRegistry:
    """Test ModelProviderRegistry."""

    def test_registry_initialization(self):
        """Test that registry initializes empty."""
        registry = ModelProviderRegistry()
        assert registry.list_providers() == []

    def test_register_provider(self):
        """Test registering a provider configuration."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai",
            {
                "type": "openai",
                "api_key": "test-key",
                "default_model": "gpt-4o-mini",
            },
        )
        assert "openai" in registry.list_providers()

    def test_get_provider_unknown(self):
        """Test getting unknown provider raises error."""
        registry = ModelProviderRegistry()
        with pytest.raises(ValueError, match="Unknown provider"):
            registry.get_provider("unknown")

    def test_get_provider_openai(self):
        """Test getting OpenAI provider."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai",
            {
                "type": "openai",
                "api_key": "test-key",
                "timeout": 30.0,
            },
        )

        provider = registry.get_provider("openai")
        assert isinstance(provider, OpenAiProvider)
        assert provider.get_provider_name() == "openai"

    def test_get_provider_caching(self):
        """Test that providers are cached after first access."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai",
            {"type": "openai", "api_key": "test-key"},
        )

        provider1 = registry.get_provider("openai")
        provider2 = registry.get_provider("openai")

        # Should return same instance
        assert provider1 is provider2

    def test_get_provider_with_env_var(self):
        """Test provider instantiation using environment variables."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai",
            {
                "type": "openai",
                # No API key in config, should use env var
            },
        )

        with patch.dict("os.environ", {"OPENAI_API_KEY": "env-test-key"}):
            provider = registry.get_provider("openai")
            assert provider.api_key == "env-test-key"

    def test_get_default_model(self):
        """Test getting default model for a provider."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai",
            {
                "type": "openai",
                "api_key": "test-key",
                "default_model": "gpt-4o",
            },
        )

        default_model = registry.get_default_model("openai")
        assert default_model == "gpt-4o"

    def test_get_default_model_none(self):
        """Test getting default model when not configured."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai",
            {"type": "openai", "api_key": "test-key"},
        )

        default_model = registry.get_default_model("openai")
        assert default_model is None

    def test_list_providers(self):
        """Test listing all registered providers."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "openai", {"type": "openai", "api_key": "key1"}
        )
        registry.register_provider(
            "openai-alt", {"type": "openai", "api_key": "key2"}
        )

        providers = registry.list_providers()
        assert set(providers) == {"openai", "openai-alt"}

    def test_unsupported_provider_type(self):
        """Test that unsupported provider types raise error."""
        registry = ModelProviderRegistry()
        registry.register_provider(
            "custom",
            {"type": "unsupported-type", "api_key": "test-key"},
        )

        with pytest.raises(Exception, match="Unsupported provider type"):
            registry.get_provider("custom")

    def test_get_model_registry_singleton(self):
        """Test global registry accessor."""
        registry1 = get_model_registry()
        registry2 = get_model_registry()

        # Should return same instance
        assert registry1 is registry2
