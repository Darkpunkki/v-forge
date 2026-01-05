"""Tests for LocalProvider stub (VF-066)."""

import pytest

from models.base.llm_client import LlmClient, LlmRequest, LlmMessage
from models.local import LocalProvider
from models.registry import ModelProviderRegistry


class TestLocalProvider:
    """Test LocalProvider stub implementation."""

    def test_local_provider_initialization(self):
        """Test VF-066: LocalProvider can be instantiated."""
        provider = LocalProvider()

        assert provider.model_name == "llama-3"
        assert provider.base_url == "http://localhost:11434"
        assert provider.backend == "ollama"

    def test_local_provider_custom_model(self):
        """Test LocalProvider with custom model name."""
        provider = LocalProvider(model_name="mistral")

        assert provider.model_name == "mistral"

    def test_local_provider_custom_url(self):
        """Test LocalProvider with custom base URL."""
        provider = LocalProvider(base_url="http://localhost:8080")

        assert provider.base_url == "http://localhost:8080"

    def test_local_provider_custom_backend(self):
        """Test LocalProvider with different backend types."""
        backends = ["ollama", "llamacpp", "vllm", "mlx"]

        for backend in backends:
            provider = LocalProvider(backend=backend)
            assert provider.backend == backend

    def test_local_provider_default_urls(self):
        """Test that each backend has appropriate default URL."""
        provider_ollama = LocalProvider(backend="ollama")
        provider_llamacpp = LocalProvider(backend="llamacpp")
        provider_vllm = LocalProvider(backend="vllm")
        provider_mlx = LocalProvider(backend="mlx")

        assert provider_ollama.base_url == "http://localhost:11434"
        assert provider_llamacpp.base_url == "http://localhost:8080"
        assert provider_vllm.base_url == "http://localhost:8000"
        assert provider_mlx.base_url == "http://localhost:5000"

    def test_local_provider_implements_llm_client(self):
        """Test VF-066: LocalProvider implements LlmClient interface."""
        provider = LocalProvider()

        assert isinstance(provider, LlmClient)

    def test_local_provider_get_provider_name(self):
        """Test VF-066: provider name is 'local'."""
        provider = LocalProvider()

        assert provider.get_provider_name() == "local"

    def test_local_provider_get_backend_type(self):
        """Test get_backend_type method."""
        provider = LocalProvider(backend="ollama")

        assert provider.get_backend_type() == "ollama"

    @pytest.mark.asyncio
    async def test_local_provider_complete_not_implemented(self):
        """Test VF-066: complete() raises NotImplementedError in MVP."""
        provider = LocalProvider()
        request = LlmRequest(
            messages=[LlmMessage(role="user", content="Hello")],
            model="llama-3"
        )

        with pytest.raises(NotImplementedError) as exc_info:
            await provider.complete(request)

        error_msg = str(exc_info.value)
        assert "LocalProvider not implemented in MVP" in error_msg

    @pytest.mark.asyncio
    async def test_local_provider_error_includes_backend_info(self):
        """Test that NotImplementedError includes backend information."""
        provider = LocalProvider(model_name="mistral", backend="ollama")
        request = LlmRequest(
            messages=[LlmMessage(role="user", content="Hello")],
            model="mistral"
        )

        with pytest.raises(NotImplementedError) as exc_info:
            await provider.complete(request)

        error_msg = str(exc_info.value)
        assert "ollama" in error_msg
        assert "mistral" in error_msg

    def test_local_provider_in_registry(self):
        """Test VF-066: LocalProvider can be registered and instantiated via registry."""
        registry = ModelProviderRegistry()

        registry.register_provider("local", {
            "type": "local",
            "model_name": "llama-3",
            "backend": "ollama"
        })

        provider = registry.get_provider("local")

        assert isinstance(provider, LocalProvider)
        assert provider.get_provider_name() == "local"

    def test_local_provider_registry_with_llamacpp(self):
        """Test registering LocalProvider with llama.cpp backend."""
        registry = ModelProviderRegistry()

        registry.register_provider("local-cpp", {
            "type": "local",
            "model_name": "llama-3",
            "backend": "llamacpp",
            "base_url": "http://localhost:8080"
        })

        provider = registry.get_provider("local-cpp")

        assert isinstance(provider, LocalProvider)
        assert provider.backend == "llamacpp"
        assert provider.base_url == "http://localhost:8080"

    def test_local_provider_registry_with_vllm(self):
        """Test registering LocalProvider with vLLM backend."""
        registry = ModelProviderRegistry()

        registry.register_provider("local-vllm", {
            "type": "local",
            "model_name": "mistral",
            "backend": "vllm"
        })

        provider = registry.get_provider("local-vllm")

        assert isinstance(provider, LocalProvider)
        assert provider.backend == "vllm"

    def test_local_provider_registry_caching(self):
        """Test that registry caches LocalProvider instances."""
        registry = ModelProviderRegistry()

        registry.register_provider("local", {
            "type": "local",
            "model_name": "llama-3"
        })

        provider1 = registry.get_provider("local")
        provider2 = registry.get_provider("local")

        assert provider1 is provider2  # Same instance (cached)

    def test_local_provider_multiple_instances_independent(self):
        """Test that multiple LocalProvider instances are independent."""
        provider1 = LocalProvider(model_name="llama-3", backend="ollama")
        provider2 = LocalProvider(model_name="mistral", backend="vllm")

        assert provider1.model_name != provider2.model_name
        assert provider1.backend != provider2.backend
        assert provider1.base_url != provider2.base_url

    def test_local_provider_interface_compliance(self):
        """Test that LocalProvider has all required LlmClient methods."""
        provider = LocalProvider()

        # Check that all abstract methods are implemented
        assert hasattr(provider, "complete")
        assert callable(provider.complete)
        assert hasattr(provider, "get_provider_name")
        assert callable(provider.get_provider_name)
