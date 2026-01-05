# WP-0012 — Model layer foundations

## VF Tasks Included
- VF-060: Define LlmClient interface + LlmRequest/LlmResponse types
- VF-061: Implement OpenAiProvider (MVP)
- VF-062: Implement ModelProviderRegistry (config-driven)

## Goal
Establish the model abstraction layer with a provider-agnostic interface, OpenAI provider implementation, and config-driven registry. This enables agent dispatch and future support for local models.

## Dependencies
- WP-0005 ✓ (config loader available)

## Execution Plan

### 1. VF-060: Define LlmClient interface + LlmRequest/LlmResponse types
- Create `models/base/` directory structure (from monorepo layout)
- Define `LlmRequest` type (messages, model, temperature, max_tokens, etc.)
- Define `LlmResponse` type (content, usage, model, finish_reason)
- Define `LlmClient` abstract base class with async `complete()` method
- Keep this provider-agnostic (no OpenAI-specific details)

### 2. VF-061: Implement OpenAiProvider (MVP)
- Create `models/claude/` or `models/openai/` directory (choose one for MVP)
- Implement `OpenAiProvider` class extending `LlmClient`
- Use `openai` Python SDK for API calls
- Map LlmRequest → OpenAI chat completion format
- Map OpenAI response → LlmResponse
- Handle errors (API failures, rate limits, invalid keys)
- Add OpenAI API key to config or environment variables

### 3. VF-062: Implement ModelProviderRegistry (config-driven)
- Create `ModelProviderRegistry` class
- Load provider configurations from config (via config loader from WP-0005)
- Support registering providers by name (e.g., "openai", "claude", "local")
- Provide `get_provider(name: str) -> LlmClient` method
- Support provider instantiation from config (API keys, base URLs, etc.)

### 4. Write tests
- test_llm_client_interface (abstract methods defined)
- test_openai_provider_request_mapping
- test_openai_provider_response_mapping
- test_openai_provider_error_handling
- test_model_registry_get_provider
- test_model_registry_unknown_provider

### 5. Add config support
- Add model provider config schema (if not already in configs/)
- Document required environment variables (OPENAI_API_KEY)

## Done Means
- [x] VF-060: LlmClient interface + request/response types defined
  - **Files:** `models/base/llm_client.py`, `models/base/__init__.py`
  - **Types:** LlmMessage, LlmRequest, LlmResponse, LlmUsage, LlmClient (abstract)
  - **Verification:** Abstract interface defined, all tests pass

- [x] VF-061: OpenAiProvider implemented
  - **Files:** `models/openai/provider.py`, `models/openai/__init__.py`, `apps/api/requirements.txt` (added openai==1.54.0)
  - **Implementation:** AsyncOpenAI client, request/response mapping, error handling
  - **Verification:** 12 provider tests pass, mocked API calls work

- [x] VF-062: ModelProviderRegistry implemented
  - **Files:** `models/registry.py`, `configs/models/providers.json`
  - **Features:** Config-driven provider selection, lazy loading, caching, default model support
  - **Verification:** 11 registry tests pass, provider instantiation from config works

## Verification Commands
```bash
cd apps/api && pytest tests/test_model_layer.py -v
cd apps/api && pytest tests/test_model_registry.py -v
cd apps/api && pytest -v
```

## Notes
- Keep prompts and routing logic OUTSIDE the provider classes
- Providers are thin adapters that just translate request/response formats
- Config-driven design allows swapping providers without code changes
- For MVP, focus on OpenAI; local model support is post-MVP
