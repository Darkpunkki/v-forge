# Agent Framework & Local Provider Upgrade Path

_Status: Planned_
_Last updated: 2026-01-12_
_VF-304: Documented upgrade path for agent/local stubs_

## Overview

This document defines the upgrade path for converting MVP stub implementations into production-ready integrations. It covers:

- **Agent Framework Stubs** (MP-005): LangGraph, CrewAI, AutoGen adapters
- **Local Provider Stub** (MP-006): Ollama, llama.cpp, vLLM, MLX backends

Each section specifies scope, rollout guards, feature flags, and acceptance tests.

---

## 1. Agent Framework Adapters

### 1.1 Current State

**File:** `models/agent_framework_stubs.py`
**Audit ID:** MP-005

Three stub adapters exist:
- `LangGraphAdapter` — Raises `NotImplementedError`
- `CrewAIAdapter` — Raises `NotImplementedError`
- `AutoGenAdapter` — Raises `NotImplementedError`

All implement the `AgentFramework` interface defined in `models/agent_framework.py`.

### 1.2 Upgrade Priority

| Adapter | Priority | Rationale |
|---------|----------|-----------|
| LangGraph | High | Graph-based workflows align with TaskGraph model; good for complex stateful agents |
| CrewAI | Medium | Role-based multi-agent systems useful for specialized roles (worker/reviewer/fixer) |
| AutoGen | Low | Conversational agents less critical for current use case |

### 1.3 LangGraph Adapter Upgrade

#### Scope
- Implement `LangGraphAdapter.runTask()` using LangGraph's `StateGraph` API
- Map VibeForge `Task` to LangGraph nodes
- Support cycle detection and state persistence
- Emit events for graph state transitions

#### Feature Flag
```python
# In config or environment
ENABLE_LANGGRAPH_ADAPTER = os.getenv("VIBEFORGE_ENABLE_LANGGRAPH", "false").lower() == "true"
```

#### Rollout Guards
1. **Dependency gate**: Only enable if `langgraph` package is installed
2. **Fallback**: If LangGraph fails, fallback to `DirectLlmAdapter`
3. **Circuit breaker**: Disable after N consecutive failures in a session

#### Acceptance Tests
```python
# tests/test_langgraph_adapter.py

def test_langgraph_adapter_implements_interface():
    """Adapter must implement AgentFramework interface."""
    adapter = LangGraphAdapter()
    assert isinstance(adapter, AgentFramework)

async def test_langgraph_adapter_executes_simple_task():
    """Adapter must execute a simple task and return result."""
    adapter = LangGraphAdapter()
    task = Task(id="t1", role="worker", description="Generate hello world")
    result = await adapter.runTask(task, "worker", {})
    assert result.success is True
    assert result.output is not None

async def test_langgraph_adapter_handles_stateful_workflow():
    """Adapter must support multi-step stateful workflows."""
    # Test graph state persistence across nodes

def test_langgraph_adapter_emits_events():
    """Adapter must emit events for graph transitions."""
    # Verify event log receives LangGraph-specific events

def test_langgraph_adapter_fallback_on_failure():
    """Adapter must fallback to DirectLlmAdapter on LangGraph failure."""
    # Mock LangGraph error, verify fallback behavior
```

#### Implementation VF Tasks
- **VF-310**: Implement LangGraphAdapter with StateGraph support
- **VF-311**: Add LangGraph event emission and fallback logic
- **VF-312**: Integration tests for LangGraph workflows

---

### 1.4 CrewAI Adapter Upgrade

#### Scope
- Implement `CrewAIAdapter.runTask()` using CrewAI's `Crew` and `Agent` classes
- Map VibeForge roles to CrewAI agent configurations
- Support task delegation between agents
- Emit events for crew coordination

#### Feature Flag
```python
ENABLE_CREWAI_ADAPTER = os.getenv("VIBEFORGE_ENABLE_CREWAI", "false").lower() == "true"
```

#### Rollout Guards
1. **Dependency gate**: Only enable if `crewai` package is installed
2. **Fallback**: If CrewAI fails, fallback to `DirectLlmAdapter`
3. **Role validation**: Only use for supported roles (worker, reviewer, fixer)

#### Acceptance Tests
```python
# tests/test_crewai_adapter.py

def test_crewai_adapter_implements_interface():
    """Adapter must implement AgentFramework interface."""

async def test_crewai_adapter_executes_worker_task():
    """Adapter must execute worker role tasks."""

async def test_crewai_adapter_supports_delegation():
    """Adapter must support task delegation between agents."""

def test_crewai_adapter_role_mapping():
    """Adapter must map VibeForge roles to CrewAI configurations."""
```

#### Implementation VF Tasks
- **VF-315**: Implement CrewAIAdapter with role mapping
- **VF-316**: Add CrewAI delegation and event support

---

### 1.5 AutoGen Adapter Upgrade

#### Scope
- Implement `AutoGenAdapter.runTask()` using AutoGen's conversational API
- Support multi-turn agent conversations
- Enable code execution sandboxing

#### Feature Flag
```python
ENABLE_AUTOGEN_ADAPTER = os.getenv("VIBEFORGE_ENABLE_AUTOGEN", "false").lower() == "true"
```

#### Rollout Guards
1. **Dependency gate**: Only enable if `autogen` package is installed
2. **Sandbox enforcement**: Code execution must use safe executor
3. **Fallback**: If AutoGen fails, fallback to `DirectLlmAdapter`

#### Acceptance Tests
```python
# tests/test_autogen_adapter.py

def test_autogen_adapter_implements_interface():
    """Adapter must implement AgentFramework interface."""

async def test_autogen_adapter_executes_conversation():
    """Adapter must handle multi-turn conversations."""

def test_autogen_adapter_sandboxes_code():
    """Adapter must sandbox code execution."""
```

#### Implementation VF Tasks
- **VF-320**: Implement AutoGenAdapter with conversation support
- **VF-321**: Add AutoGen code sandboxing

---

## 2. Local Provider (Ollama/llama.cpp/vLLM/MLX)

### 2.1 Current State

**File:** `models/local/provider.py`
**Audit ID:** MP-006

The `LocalProvider` stub:
- Accepts `backend` parameter: "ollama", "llamacpp", "vllm", "mlx"
- Stores `model_name` and `base_url`
- Raises `NotImplementedError` on `complete()`

### 2.2 Upgrade Priority

| Backend | Priority | Rationale |
|---------|----------|-----------|
| Ollama | High | Most popular local model server; simple REST API |
| vLLM | Medium | OpenAI-compatible API; good for GPU servers |
| llama.cpp | Low | Requires native bindings; complex setup |
| MLX | Low | Apple Silicon only; niche use case |

### 2.3 Ollama Backend Upgrade

#### Scope
- Implement `LocalProvider.complete()` using Ollama REST API
- Support streaming responses
- Handle model availability detection
- Map LlmRequest to Ollama format

#### Feature Flag
```python
ENABLE_LOCAL_OLLAMA = os.getenv("VIBEFORGE_ENABLE_OLLAMA", "false").lower() == "true"
```

#### Rollout Guards
1. **Health check**: Verify Ollama server is reachable before use
2. **Model availability**: Check model exists via `/api/tags`
3. **Timeout**: Enforce request timeouts (default: 120s)
4. **Fallback**: If Ollama fails, fallback to OpenAI provider

#### Acceptance Tests
```python
# tests/test_local_ollama.py

def test_ollama_provider_implements_interface():
    """Provider must implement LlmClient interface."""
    provider = LocalProvider(backend="ollama")
    assert isinstance(provider, LlmClient)

async def test_ollama_provider_health_check():
    """Provider must detect Ollama server availability."""
    provider = LocalProvider(backend="ollama")
    is_healthy = await provider.health_check()
    # Test both healthy and unreachable scenarios

async def test_ollama_provider_model_availability():
    """Provider must verify model exists before use."""
    provider = LocalProvider(model_name="llama3", backend="ollama")
    exists = await provider.check_model_exists()

@pytest.mark.integration
async def test_ollama_provider_completes_request():
    """Provider must complete requests via Ollama API."""
    # Requires running Ollama server
    provider = LocalProvider(model_name="llama3", backend="ollama")
    request = LlmRequest(messages=[{"role": "user", "content": "Hello"}])
    response = await provider.complete(request)
    assert response.content is not None

async def test_ollama_provider_fallback_on_failure():
    """Provider must fallback to OpenAI on Ollama failure."""
```

#### Implementation VF Tasks
- **VF-330**: Implement Ollama backend with REST API client
- **VF-331**: Add Ollama health check and model detection
- **VF-332**: Add Ollama streaming support

---

### 2.4 vLLM Backend Upgrade

#### Scope
- Implement `LocalProvider.complete()` using OpenAI-compatible API
- Reuse OpenAI client with different base URL
- Support vLLM-specific parameters

#### Feature Flag
```python
ENABLE_LOCAL_VLLM = os.getenv("VIBEFORGE_ENABLE_VLLM", "false").lower() == "true"
```

#### Rollout Guards
1. **Health check**: Verify vLLM server is reachable
2. **Timeout**: Enforce request timeouts
3. **Fallback**: If vLLM fails, fallback to OpenAI provider

#### Acceptance Tests
```python
# tests/test_local_vllm.py

async def test_vllm_provider_uses_openai_compatible_api():
    """Provider must use OpenAI-compatible API format."""

@pytest.mark.integration
async def test_vllm_provider_completes_request():
    """Provider must complete requests via vLLM server."""
    # Requires running vLLM server
```

#### Implementation VF Tasks
- **VF-335**: Implement vLLM backend using OpenAI-compatible client
- **VF-336**: Add vLLM health check and fallback

---

### 2.5 llama.cpp Backend Upgrade (Deferred)

#### Scope
- Use `llama-cpp-python` bindings
- Support model loading and inference
- Handle GPU vs CPU execution

#### Implementation VF Tasks
- **VF-340**: Implement llama.cpp backend (post-MVP, deferred)

---

### 2.6 MLX Backend Upgrade (Deferred)

#### Scope
- Use `mlx-lm` package for Apple Silicon
- Support Metal GPU acceleration

#### Implementation VF Tasks
- **VF-345**: Implement MLX backend (post-MVP, deferred)

---

## 3. Feature Flag Registry

All feature flags should be registered in a central location for consistency:

```python
# vibeforge_api/config/feature_flags.py

from dataclasses import dataclass
import os

@dataclass
class FeatureFlags:
    """Centralized feature flag registry."""

    # Agent Framework Adapters
    langgraph_adapter: bool = False
    crewai_adapter: bool = False
    autogen_adapter: bool = False

    # Local Providers
    ollama_backend: bool = False
    vllm_backend: bool = False
    llamacpp_backend: bool = False
    mlx_backend: bool = False

    @classmethod
    def from_env(cls) -> "FeatureFlags":
        """Load flags from environment variables."""
        return cls(
            langgraph_adapter=os.getenv("VIBEFORGE_ENABLE_LANGGRAPH", "").lower() == "true",
            crewai_adapter=os.getenv("VIBEFORGE_ENABLE_CREWAI", "").lower() == "true",
            autogen_adapter=os.getenv("VIBEFORGE_ENABLE_AUTOGEN", "").lower() == "true",
            ollama_backend=os.getenv("VIBEFORGE_ENABLE_OLLAMA", "").lower() == "true",
            vllm_backend=os.getenv("VIBEFORGE_ENABLE_VLLM", "").lower() == "true",
            llamacpp_backend=os.getenv("VIBEFORGE_ENABLE_LLAMACPP", "").lower() == "true",
            mlx_backend=os.getenv("VIBEFORGE_ENABLE_MLX", "").lower() == "true",
        )
```

---

## 4. Recommended Implementation Sequence

Based on priority and dependencies:

### Phase 1: High Priority (Immediate Post-MVP)
1. **VF-330-332**: Ollama backend implementation
2. **VF-310-312**: LangGraph adapter implementation

### Phase 2: Medium Priority
3. **VF-335-336**: vLLM backend implementation
4. **VF-315-316**: CrewAI adapter implementation

### Phase 3: Low Priority (Deferred)
5. **VF-320-321**: AutoGen adapter implementation
6. **VF-340**: llama.cpp backend implementation
7. **VF-345**: MLX backend implementation

---

## 5. Cross-References

### MVP Placeholder Audit
- **MP-005** → Agent Framework Stubs → VF-310 through VF-321
- **MP-006** → Local Provider Stub → VF-330 through VF-345

### Stub File Annotations
The following files should be updated with links to this upgrade path:
- `models/agent_framework_stubs.py` — Add header reference to VF-310, VF-315, VF-320
- `models/local/provider.py` — Add header reference to VF-330, VF-335, VF-340, VF-345

---

## 6. Verification Hooks

Each implementation should include:

1. **Unit tests**: Interface compliance and mock scenarios
2. **Integration tests**: Real service connectivity (marked with `@pytest.mark.integration`)
3. **Feature flag tests**: Verify enable/disable behavior
4. **Fallback tests**: Verify graceful degradation to DirectLlmAdapter or OpenAI

Test markers for CI:
```python
# pytest.ini
[pytest]
markers =
    integration: marks tests as integration tests (deselect with '-m "not integration"')
    ollama: marks tests requiring Ollama server
    vllm: marks tests requiring vLLM server
    langgraph: marks tests requiring LangGraph package
    crewai: marks tests requiring CrewAI package
    autogen: marks tests requiring AutoGen package
```
