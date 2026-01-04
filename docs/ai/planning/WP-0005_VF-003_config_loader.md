# WP-0005 — Configuration Loader

## VF Tasks Included
- VF-003: Add configuration loader (stack presets, policies, router rules)

## Goal
Load stack presets, command policies, and routing rules from config files so platform behavior can be adjusted without code changes.

## Ordered Execution Steps

### 1. Define configuration schemas and sample files
- Draft YAML/JSON schemas for stack presets, command policies (allow/deny lists, timeouts), forbidden patterns, and router rules.
- Add representative sample configs under `configs/` for API and agent components.
- Include defaults for safe operation (e.g., deny network commands unless explicitly allowed).

### 2. Implement config models and validation
- Create typed models (e.g., Pydantic/dataclass) for each config section with defaulting and strict validation.
- Validate presence of required fields (ids, commands, risk levels, routing targets) and reject unknown keys.
- Files: `apps/api/vibeforge_api/config/models.py` (or similar)

### 3. Build configuration loader utilities
- Implement loader that reads YAML/JSON from `configs/` with environment override support (e.g., path/env var).
- Provide helper to merge default + environment-specific configs.
- Expose accessors for stack presets, command policies, forbidden patterns, and router rules.
- Files: `apps/api/vibeforge_api/config/loader.py`

### 4. Integrate loader with core services
- Wire loader outputs into command runner/verifier allowlists and gate policies.
- Update dependency injection or module-level references so UI/API can query current presets and policies.
- Add lightweight API endpoint or internal function to surface active configuration for debugging (read-only).
- Files: `apps/api/vibeforge_api/core/command_runner.py`, `apps/api/vibeforge_api/core/gates.py`, `apps/api/vibeforge_api/routers/`

## Done Means...

### Verification Commands
1. `cd apps/api && pytest tests/test_config_loader.py -v`
2. `cd apps/api && pytest tests/test_command_runner.py -k config -v`
3. `cd apps/api && pytest tests/test_gates.py -k config -v`
4. Manual: load sample config and confirm parsed presets/policies/routers match expected structures.

### Task Checklist
- [ ] VF-003: Configuration schemas and samples added
  - Schemas cover stack presets, command policies, forbidden patterns, router rules
  - Sample files live in `configs/` with safe defaults
  - Verified by schema validation tests
- [ ] VF-003: Loader and validation implemented
  - Loader reads YAML/JSON with env override support
  - Invalid configs raise structured errors
  - Verified by `pytest tests/test_config_loader.py -v`
- [ ] VF-003: Core wired to configuration outputs
  - Command runner/verifiers consume loaded allowlists and policies
  - Gates read forbidden patterns and routing rules
  - Read-only inspection endpoint/helper exposes active config
  - Verified by targeted tests in command runner and gates suites

## Implementation Notes
- Keep config format additive: unknown keys should fail fast to avoid silent drift.
- Provide deterministic defaults for seeds/timeouts when values are missing.
- Avoid global mutable state; prefer passing parsed config objects into services during initialization.
- Consider caching parsed configs with explicit reload method for future hot-reload support.
