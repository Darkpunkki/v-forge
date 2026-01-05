"""Model provider registry for config-driven provider selection."""

from typing import Dict, Optional

from models.base import LlmClient
from models.openai import OpenAiProvider


class ModelProviderRegistry:
    """Registry for managing LLM providers.

    This class allows selecting and instantiating providers based on configuration.
    It acts as the switch point for swapping between OpenAI, Claude, local models, etc.

    Design principles:
    - Config-driven: Provider selection and configuration come from external config
    - Lazy initialization: Providers are created on-demand, not at startup
    - Extensible: Easy to add new providers without changing core logic
    """

    def __init__(self):
        """Initialize the registry."""
        self._providers: Dict[str, LlmClient] = {}
        self._provider_configs: Dict[str, dict] = {}

    def register_provider(self, name: str, config: dict):
        """Register a provider configuration.

        Args:
            name: Provider name (e.g., "openai", "claude", "local")
            config: Provider configuration dict with keys:
                - type: Provider type ("openai", "claude", etc.)
                - api_key: API key (optional, can use env var)
                - base_url: Custom base URL (optional)
                - timeout: Request timeout (optional)
                - default_model: Default model to use (optional)
        """
        self._provider_configs[name] = config

    def get_provider(self, name: str) -> LlmClient:
        """Get a provider instance by name.

        Providers are lazy-loaded and cached after first access.

        Args:
            name: Provider name registered via register_provider()

        Returns:
            LlmClient instance

        Raises:
            ValueError: If provider name is not registered
            Exception: If provider instantiation fails
        """
        # Return cached provider if available
        if name in self._providers:
            return self._providers[name]

        # Check if provider is registered
        if name not in self._provider_configs:
            available = ", ".join(self._provider_configs.keys())
            raise ValueError(
                f"Unknown provider '{name}'. Available providers: {available}"
            )

        # Instantiate provider based on config
        config = self._provider_configs[name]
        provider_type = config.get("type", name)

        try:
            if provider_type == "openai":
                provider = OpenAiProvider(
                    api_key=config.get("api_key"),
                    base_url=config.get("base_url"),
                    timeout=config.get("timeout", 60.0),
                )
            else:
                raise ValueError(f"Unsupported provider type: {provider_type}")

            # Cache and return
            self._providers[name] = provider
            return provider

        except Exception as e:
            raise Exception(f"Failed to instantiate provider '{name}': {str(e)}") from e

    def list_providers(self) -> list[str]:
        """List all registered provider names.

        Returns:
            List of provider names
        """
        return list(self._provider_configs.keys())

    def get_default_model(self, provider_name: str) -> Optional[str]:
        """Get the default model for a provider.

        Args:
            provider_name: Provider name

        Returns:
            Default model name or None
        """
        config = self._provider_configs.get(provider_name, {})
        return config.get("default_model")


# Global registry instance (MVP: singleton)
model_registry = ModelProviderRegistry()


def get_model_registry() -> ModelProviderRegistry:
    """Get the global model provider registry.

    Returns:
        ModelProviderRegistry instance
    """
    return model_registry
