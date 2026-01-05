"""Local model provider stub.

VF-066: Placeholder implementation for local models (Ollama/llama.cpp/vLLM).
Not implemented in MVP, but exists to make the architecture seam visible and testable.
"""

from typing import Optional

from models.base.llm_client import LlmClient, LlmRequest, LlmResponse


class LocalProvider(LlmClient):
    """Stub for local model providers (Ollama/llama.cpp/vLLM).

    VF-066: Not implemented in MVP. Raises NotImplementedError on use.
    Exists to:
    1. Make the architecture seam visible
    2. Allow registry to recognize "local" provider type
    3. Enable future local model integration without changing interfaces
    4. Provide a testable stub for interface compliance

    Future implementation will support:
    - Ollama (REST API)
    - llama.cpp (via llama-cpp-python)
    - vLLM (OpenAI-compatible API)
    - MLX (Apple Silicon)
    """

    def __init__(
        self,
        model_name: str = "llama-3",
        base_url: Optional[str] = None,
        backend: str = "ollama"
    ):
        """Initialize local provider stub.

        Args:
            model_name: Name of local model (e.g., "llama-3", "mistral")
            base_url: Base URL for local server (default: http://localhost:11434 for Ollama)
            backend: Backend type ("ollama", "llamacpp", "vllm", "mlx")
        """
        self.model_name = model_name
        self.base_url = base_url or self._get_default_url(backend)
        self.backend = backend

    def _get_default_url(self, backend: str) -> str:
        """Get default URL for backend type.

        Args:
            backend: Backend type

        Returns:
            Default base URL
        """
        defaults = {
            "ollama": "http://localhost:11434",
            "llamacpp": "http://localhost:8080",
            "vllm": "http://localhost:8000",
            "mlx": "http://localhost:5000"
        }
        return defaults.get(backend, "http://localhost:11434")

    async def complete(self, request: LlmRequest) -> LlmResponse:
        """Execute completion request (NOT IMPLEMENTED IN MVP).

        Args:
            request: LLM request

        Returns:
            LLM response

        Raises:
            NotImplementedError: Always raised in MVP
        """
        raise NotImplementedError(
            f"LocalProvider not implemented in MVP. "
            f"Attempted to use {self.backend} backend with model {self.model_name}. "
            f"Please use OpenAI provider instead, or implement local provider support."
        )

    def get_provider_name(self) -> str:
        """Get provider name.

        Returns:
            Provider name ("local")
        """
        return "local"

    def get_backend_type(self) -> str:
        """Get backend type.

        Returns:
            Backend type (ollama, llamacpp, vllm, mlx)
        """
        return self.backend


# Future implementation notes:
#
# For Ollama backend:
# - Use httpx to call http://localhost:11434/api/generate
# - Convert LlmRequest messages to Ollama format
# - Stream responses if needed
#
# For llama.cpp backend:
# - Use llama-cpp-python bindings
# - Load model locally
# - Generate responses via Python API
#
# For vLLM backend:
# - Use OpenAI-compatible API
# - Similar implementation to OpenAiProvider
# - Point to http://localhost:8000/v1
#
# For MLX backend:
# - Use mlx-lm Python package
# - Run models on Apple Silicon GPUs
# - Optimized for M1/M2/M3 chips
