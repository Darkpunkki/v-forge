# WP-0014 — Model routing, validation, and repair

## VF Tasks Included
- VF-063: Implement ModelRouter policy (role/complexity/failures → modelRef)
- VF-064: Implement OutputValidator (strict JSON schema validation)
- VF-065: Implement OutputRepair (retry/repair strategy for malformed outputs)
- VF-066: Stub LocalProvider interface (no implementation yet)

## Goal
Complete the model abstraction layer with routing policies, output validation/repair, and local provider stub to enable reliable agent dispatch for the orchestrator and agent framework.

## Dependencies
- WP-0012 ✓ (base model layer: LlmClient interface, OpenAiProvider, ModelProviderRegistry)

## Current State Analysis

From WP-0012, we have:
- ✓ LlmClient interface with complete() and get_provider_name()
- ✓ LlmRequest/LlmResponse dataclasses
- ✓ OpenAiProvider implementation
- ✓ ModelProviderRegistry for config-driven provider selection

**Gaps identified:**
1. **No routing logic** - Currently no way to select model based on role, complexity, or failure history
2. **No output validation** - Responses not validated against JSON schemas
3. **No repair strategy** - Malformed outputs cause failures instead of repair attempts
4. **No local provider stub** - Architecture seam not visible for future local model support

## Execution Plan

### 1. Implement ModelRouter (VF-063)
Create `models/router.py` with routing policy that selects models based on:
- **AgentRole** (orchestrator/worker/foreman/fixer/reviewer)
- **Complexity level** (simple/medium/complex)
- **Failure count** (escalate to stronger models on retries)

Design:
```python
@dataclass
class RoutingContext:
    role: str  # "orchestrator", "worker", "fixer", "reviewer"
    complexity: str  # "simple", "medium", "complex"
    failure_count: int = 0
    metadata: Optional[dict] = None

class ModelRouter:
    def __init__(self, routing_config: dict):
        # Load routing rules from config

    def select_model(self, context: RoutingContext) -> tuple[str, str]:
        # Returns (provider_name, model_name)
        # Apply routing rules based on context
```

**Routing rules** (from config):
- orchestrator → gpt-4o or gpt-4o-mini
- worker (simple) → gpt-4o-mini
- worker (complex) → gpt-4o
- fixer (failure_count=0) → gpt-4o-mini
- fixer (failure_count≥1) → gpt-4o
- reviewer → gpt-4o

### 2. Implement OutputValidator (VF-064)
Create `models/validation.py` with strict JSON schema validation:

Design:
```python
class OutputValidator:
    def validate(self, response: LlmResponse, schema: dict) -> ValidationResult:
        # Parse response.content as JSON
        # Validate against JSON schema
        # Return ValidationResult with errors if any

@dataclass
class ValidationResult:
    valid: bool
    parsed_output: Optional[dict] = None
    errors: list[str] = field(default_factory=list)
```

Features:
- JSON parsing with clear error messages
- JSON schema validation using jsonschema library
- Detailed error reporting (path to invalid field, expected vs actual)

### 3. Implement OutputRepair (VF-065)
Create `models/repair.py` with retry/repair strategy:

Design:
```python
class OutputRepair:
    def __init__(self, llm_client: LlmClient, max_repair_attempts: int = 2):
        self.llm_client = llm_client
        self.max_repair_attempts = max_repair_attempts

    async def repair(
        self,
        original_request: LlmRequest,
        failed_response: LlmResponse,
        validation_errors: list[str],
        schema: dict,
    ) -> LlmResponse:
        # Build repair prompt explaining validation errors
        # Ask model to fix the output
        # Retry with validation
```

**Repair strategy:**
1. First attempt: Tell model what validation failed, ask to fix output
2. Second attempt: Simplify request or add more constraints
3. After max attempts: Raise ValidationError with all attempts logged

### 4. Stub LocalProvider (VF-066)
Create `models/local/provider.py` with placeholder implementation:

Design:
```python
class LocalProvider(LlmClient):
    """Stub for local model providers (Ollama/llama.cpp/vLLM).

    Not implemented in MVP. Raises NotImplementedError.
    Exists to make the architecture seam visible and testable.
    """

    def __init__(self, model_name: str = "llama-3", base_url: Optional[str] = None):
        self.model_name = model_name
        self.base_url = base_url or "http://localhost:11434"

    async def complete(self, request: LlmRequest) -> LlmResponse:
        raise NotImplementedError("LocalProvider not implemented in MVP")

    def get_provider_name(self) -> str:
        return "local"
```

This stub:
- Implements the LlmClient interface
- Documents the future integration point
- Allows registry to recognize "local" type
- Tests can verify interface compliance

### 5. Write comprehensive tests

**test_model_router.py:**
- Test routing for each role/complexity combination
- Test escalation on failure_count increase
- Test config loading and validation
- Test fallback to default model

**test_output_validator.py:**
- Test valid JSON validation passes
- Test invalid JSON fails with clear errors
- Test schema violations detected
- Test missing required fields
- Test type mismatches

**test_output_repair.py:**
- Test successful repair after validation failure
- Test repair with max attempts exhausted
- Test repair prompt construction
- Test repair with different error types

**test_local_provider.py:**
- Test LocalProvider interface compliance
- Test NotImplementedError raised
- Test registry can instantiate LocalProvider
- Test provider name returned correctly

## Done Means
- [x] VF-063: ModelRouter implemented
  - **File:** `models/router.py` (RoutingContext, ModelRouter, get_model_router)
  - **Config:** `configs/models/routing.json` (routing rules + escalation rules)
  - **Features:** Role/complexity/failure routing, config-driven rules, escalation temperature
  - **Tests:** `apps/api/tests/test_model_router.py` (17 comprehensive tests)
  - **Verification:** All routing tests passed - routing selects correct models for different contexts

- [x] VF-064: OutputValidator implemented
  - **File:** `models/validation.py` (OutputValidator, ValidationResult, validate_response)
  - **Features:** JSON parsing, schema validation, detailed error reporting, markdown extraction
  - **Tests:** `apps/api/tests/test_output_validator.py` (16 comprehensive tests)
  - **Verification:** All validation tests passed - catches all schema violations

- [x] VF-065: OutputRepair implemented
  - **File:** `models/repair.py` (OutputRepair, RepairFailedError, repair_response)
  - **Features:** Repair retries with validation errors, max attempts, logging, temperature escalation
  - **Tests:** `apps/api/tests/test_output_repair.py` (11 comprehensive tests)
  - **Verification:** All repair tests passed - recovers from validation failures

- [x] VF-066: LocalProvider stub implemented
  - **File:** `models/local/provider.py` (LocalProvider for Ollama/llama.cpp/vLLM/MLX)
  - **Features:** LlmClient interface, NotImplementedError, future-ready, registry integration
  - **Tests:** `apps/api/tests/test_local_provider.py` (16 comprehensive tests)
  - **Verification:** All stub tests passed - interface compliance validated

**Total tests:** 279 (was 219, added 60 new tests)
**All tests passing:** ✓

## Verification Commands
```bash
cd apps/api && pytest tests/test_model_router.py -v
cd apps/api && pytest tests/test_output_validator.py -v
cd apps/api && pytest tests/test_output_repair.py -v
cd apps/api && pytest tests/test_local_provider.py -v
cd apps/api && pytest -v
```

## Notes
- ModelRouter uses config file `configs/models/routing.json` (to be created)
- OutputValidator requires jsonschema library (add to requirements.txt)
- OutputRepair is async to support async LLM calls
- LocalProvider is intentionally incomplete (MVP stub only)
