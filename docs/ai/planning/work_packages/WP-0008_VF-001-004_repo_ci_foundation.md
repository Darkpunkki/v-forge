# WP-0008 — Repository foundations + test harness

## VF Tasks Included
- VF-001: Create monorepo structure (apps/core/orchestration/models/runtime/storage/configs)
- VF-004: Add basic test harness + CI skeleton (unit tests only)

## Goal
Solidify the repository layout and add a minimal-yet-reliable test harness/CI skeleton so subsequent components have a stable foundation.

## Ordered Execution Steps

### 1. Audit and finalize monorepo layout
- Validate current top-level folders match the intended architecture (apps/core/orchestration/models/runtime/storage/configs/schemas/docs).
- Add missing README stubs per major folder explaining purpose and boundaries.
- Ensure python/JS package scaffolds exist where applicable (e.g., `apps/api`, future `apps/ui`).

### 2. Establish baseline tooling configuration
- Add/verify Python test dependencies (pytest + plugins) and JS test placeholders if UI scaffold exists.
- Configure lint/format placeholders (ruff/black/isort or eslint/prettier) but keep optional per VF-004 scope.
- Create shared test utilities folder (e.g., `apps/api/tests/conftest.py` for fixtures).

### 3. Implement CI/test runner skeleton
- Add minimal CI workflow (GitHub Actions) that runs unit tests for available packages (start with API).
- Provide developer scripts in repo root (`make test`, or `justfile`/npm scripts) to mirror CI steps locally.
- Document how to run tests locally in root README or dedicated `docs/ai/testing/` note.

### 4. Seed initial tests and guardrails
- Add smoke/unit tests validating current repo layout invariants (folders present, configs readable).
- Ensure existing test suites run under new harness without regressions.
- Add coverage thresholds or reporting hooks if straightforward; otherwise capture as future enhancement note.

## Done Means...

### Verification Commands
1. `cd apps/api && pytest -v`
2. `cd apps/api && pytest tests/test_repo_layout.py -v` (new layout guard)
3. `gh workflow run` or `act -j test` (if available) to dry-run CI workflow
4. Manual: confirm root `README.md`/docs mention how to run tests locally
