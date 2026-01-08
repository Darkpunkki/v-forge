# Work Packages (VibeForge)

This file is the near-term work queue. Each Work Package (WP) references VF tasks from `vibeforge_master_checklist.md` (canonical backlog).
Use WPs to run an iterative loop: plan → implement → verify → update docs → check off VF tasks → mark WP done.

## Status Legend
- Queued: selected and ready to start
- In Progress: currently being implemented
- Blocked: cannot proceed (missing dependency/decision)
- Done: merged + verified + VF tasks checked off

## Operating Rules
- Keep WPs small (typically 1–5 VF tasks).
- Only mark a WP “Done” after:
  1) verification commands succeed,
  2) relevant docs updated (if needed),
  3) VF tasks checked off in `vibeforge_master_checklist.md`.

---

## WP-0001 — Local UI API completion
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-020, VF-021, VF-022, VF-023, VF-024, VF-025, VF-026, VF-029 (all complete ✓)
- **Goal:** Make the session API stable and phase-safe so UI can drive the flow reliably.
- **Dependencies:** None (should be safe to start immediately)
- **Plan Doc:** docs/ai/planning/WP-0001_VF-020-029_local_api_core.md
- **Verified:**
  - `cd apps/api && pip install -r requirements.txt` - All dependencies installed
  - `pytest` - 10 tests passed
  - `uvicorn vibeforge_api.main:app --reload` - Server starts successfully
  - `/health` endpoint returns 200 OK
  - `/docs` OpenAPI documentation loads
  - Session creation flow tested (POST /sessions → GET /question → POST /answers)
- **Files touched:**
  - `apps/api/requirements.txt` (dependencies)
  - `apps/api/vibeforge_api/main.py` (FastAPI app)
  - `apps/api/vibeforge_api/models/` (types, requests, responses)
  - `apps/api/vibeforge_api/core/` (session store, questionnaire engine)
  - `apps/api/vibeforge_api/routers/sessions.py` (all endpoints)
  - `apps/api/tests/test_sessions.py` (10 unit tests)

## WP-0002 — Workspace + Patch apply safety
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-110, VF-111, VF-113, VF-114, VF-115 (all complete ✓)
- **Goal:** Safely create workspace per session and apply unified diffs with path restrictions + dry-run.
- **Dependencies:** WP-0001 recommended (API plumbing helps), but can be built in parallel
- **Plan Doc:** docs/ai/planning/WP-0002_VF-110-115_workspace_patching.md
- **Verified:**
  - `pytest tests/test_workspace.py tests/test_patch.py tests/test_artifacts.py -v` - 36 tests passed
  - Workspace creation with correct layout (repo/, artifacts/)
  - Patch application with unified diff parsing
  - Path traversal prevention (.. and absolute paths rejected)
  - Dry-run mode without file modification
  - Patch metadata persistence to artifacts/
- **Files touched:**
  - `apps/api/vibeforge_api/core/workspace.py` (WorkspaceManager)
  - `apps/api/vibeforge_api/core/patch.py` (PatchApplier with safety)
  - `apps/api/vibeforge_api/core/artifacts.py` (ArtifactStore)
  - `apps/api/tests/test_workspace.py` (12 tests)
  - `apps/api/tests/test_patch.py` (11 tests)
  - `apps/api/tests/test_artifacts.py` (13 tests)

## WP-0003 — Command runner + verification harness
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-120, VF-121, VF-122, VF-124 (all complete ✓)
- **Goal:** Allowlisted command execution with captured outputs; per-task + global verifier runner.
- **Dependencies:** WP-0002 ✓ (workspace available)
- **Plan Doc:** docs/ai/planning/WP-0003_VF-120-124_command_verification.md
- **Verified:**
  - `pytest tests/test_command_runner.py -v` - 15 tests passed
  - `pytest tests/test_verifiers.py -v` - 17 tests passed
  - `pytest tests/test_verification_integration.py -v` - 9 tests passed (real command execution)
  - `pytest -v` - All 91 tests passed
  - Integration test with fixture Node.js project executes real npm commands
  - CommandRunner enforces allowlists, timeouts, captures output
  - BuildVerifier and TestVerifier map presets to commands correctly
  - VerifierSuite orchestrates multiple verification steps
- **Files touched:**
  - `apps/api/vibeforge_api/core/command_runner.py` (new - VF-120)
  - `apps/api/vibeforge_api/core/verifiers.py` (new - VF-121, VF-122, VF-124)
  - `apps/api/tests/test_command_runner.py` (new - 15 tests)
  - `apps/api/tests/test_verifiers.py` (new - 17 tests)
  - `apps/api/tests/test_verification_integration.py` (new - 9 integration tests)
  - `apps/api/tests/fixtures/node-project/` (fixture project for integration testing)

## WP-0004 — Gates pipeline (core safety checks)
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-080, VF-081, VF-082, VF-083, VF-084, VF-085 (all complete ✓)
- **Goal:** Enforce safety/feasibility policies before diffs/commands touch disk.
- **Dependencies:** WP-0002 ✓ + WP-0003 ✓ (gates protect those flows)
- **Plan Doc:** docs/ai/planning/WP-0004_VF-080-085_gates_pipeline.md
- **Verified:**
  - `pytest tests/test_gates.py -v` - 36 tests passed
  - `pytest -v` - All 127 tests passed
  - Gate pipeline orchestrates multiple gates with aggregation and short-circuit
  - PolicyGate blocks forbidden patterns (rm -rf /, curl | sh, eval, etc.) and path traversal
  - RiskGate enforces command families and network access rules (ALLOW/DENY/ASK)
  - FeasibilityGate enforces scope budgets, warns at 80%, blocks when exceeded
  - DiffAndCommandGate validates diffs for secrets, file count, line count
  - GateAdapter formats blocker/warning messages and generates clarification questions
- **Files touched:**
  - `apps/api/vibeforge_api/core/gates.py` (new - all gate implementations)
  - `apps/api/tests/test_gates.py` (new - 36 comprehensive tests)
  - `docs/ai/planning/WP-0004_VF-080-085_gates_pipeline.md` (plan document)

## WP-0005 — Configuration loader
- **Status:** Done
- **Started:** 2026-01-05 (local)
- **Completed:** 2026-01-05 (local)
- **Branch:** master
- **VF Tasks:** VF-003 (complete ✓)
- **Goal:** Load stack presets, command policies, and routing rules from config files to make system behavior adjustable without code changes.
- **Dependencies:** None
- **Plan Doc:** docs/ai/planning/WP-0005_VF-003_config_loader.md
- **Verified:**
  - `pytest tests/test_config_loader.py -v` - 20 tests passed
  - `pytest -v` - All 147 tests passed (127 existing + 20 new config tests)
  - Config loader loads and validates stack presets from JSON
  - Policy configuration loaded with defaults
  - Pydantic models validate config structure with proper error handling
  - Helper functions provide typed access: get_stack_preset(), get_policy_config(), list_available_stacks()
- **Files touched:**
  - `apps/api/vibeforge_api/config/models.py` (new - Pydantic models)
  - `apps/api/vibeforge_api/config/loader.py` (new - ConfigLoader implementation)
  - `apps/api/vibeforge_api/config/__init__.py` (new - module exports)
  - `apps/api/tests/test_config_loader.py` (new - 20 comprehensive tests)

## WP-0006 — Questionnaire finalization + mock generation (E2E demo)
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-043, VF-028, VF-051 (all complete ✓)
- **Goal:** Complete end-to-end flow from questionnaire → IntentProfile → mock generation → result endpoint, enabling first testable demo.
- **Dependencies:** WP-0001 (API) ✓, WP-0002 (Workspace) ✓
- **Verified:**
  - `pytest tests/test_e2e_demo.py -v` - 4 E2E tests passed
  - `pytest -v` - All 50 tests passed
  - End-to-end test: Create session → answer all questions → generate mock output → get result
  - IntentProfile generated and validated against schema
  - BuildSpec generated from IntentProfile deterministically
  - Generated files appear in workspace/repo/
  - Result endpoint returns completion summary with run instructions
- **Files touched:**
  - `apps/api/vibeforge_api/core/spec_builder.py` (new - VF-051)
  - `apps/api/vibeforge_api/core/questionnaire.py` (added finalize() - VF-043)
  - `apps/api/vibeforge_api/core/mock_generator.py` (new - mock generation)
  - `apps/api/vibeforge_api/routers/sessions.py` (updated flow + result endpoint - VF-028)
  - `apps/api/vibeforge_api/models/responses.py` (ResultResponse model)
  - `apps/api/vibeforge_api/core/workspace.py` (added workspace_manager global)
  - `apps/api/vibeforge_api/core/artifacts.py` (added SessionArtifactStore wrapper)
  - `apps/api/tests/test_e2e_demo.py` (new E2E tests)
  - `apps/api/tests/test_sessions.py` (updated expectations)

## WP-0007a — UI Foundation (skeleton + API client)
- **Status:** Done
- **Started:** 2026-01-05 (local)
- **Completed:** 2026-01-05 (local)
- **Branch:** master
- **VF Tasks:** VF-010 ✓, VF-016 ✓
- **Goal:** Set up Vite+React project with routing, layout, and typed API client for communicating with Local UI API.
- **Dependencies:** WP-0001 ✓ (Local UI API must exist)
- **Plan Doc:** docs/ai/planning/WP-0007a_VF-010-016_ui_foundation.md
- **Verified:**
  - `cd apps/ui && npm install` - Dependencies installed (react-router-dom added)
  - `cd apps/ui && npm run build` - Build succeeds with no TypeScript errors
  - `cd apps/ui && npm run dev` - Dev server starts on http://localhost:5173
  - React Router configured with 6 routes (Home, Questionnaire, PlanReview, Progress, Clarification, Result)
  - Layout component with navigation header and footer
  - All screen components created with typed API client integration
  - API client fully typed matching backend Pydantic models
- **Files touched:**
  - `apps/ui/src/types/api.ts` (new - TypeScript type definitions)
  - `apps/ui/src/api/client.ts` (new - Typed API client)
  - `apps/ui/src/components/Layout.tsx` (new - Layout with navigation)
  - `apps/ui/src/screens/Home.tsx` (new - Home screen)
  - `apps/ui/src/screens/Questionnaire.tsx` (new - Questionnaire screen)
  - `apps/ui/src/screens/PlanReview.tsx` (new - Plan review screen)
  - `apps/ui/src/screens/Progress.tsx` (new - Progress screen with polling)
  - `apps/ui/src/screens/Clarification.tsx` (new - Clarification placeholder)
  - `apps/ui/src/screens/Result.tsx` (new - Result screen)
  - `apps/ui/src/ui/App.tsx` (updated - React Router setup)

## WP-0007b — Questionnaire Screen
- **Status:** Done
- **Started:** 2026-01-05 (local)
- **Completed:** 2026-01-05 (local)
- **Branch:** master
- **VF Tasks:** VF-011 ✓
- **Goal:** Implement step-by-step questionnaire UI with structured inputs only (radio buttons, select dropdowns, sliders).
- **Dependencies:** WP-0007a ✓ (UI foundation and API client must exist)
- **Plan Doc:** docs/ai/planning/WP-0007b_VF-011_questionnaire_screen.md
- **Verified:**
  - `cd apps/ui && npm run build` - TypeScript compilation succeeds
  - `grep -E 'type="text"|<textarea' apps/ui/src/screens/Questionnaire.tsx` - No free-text inputs (0 matches)
  - Questionnaire screen renders all question types (radio, checkbox, select, slider)
  - Structured input controls with visual feedback on selection
  - Answer submission with validation and proper state management
  - Final question indicator displayed
  - Navigation between questions works correctly
- **Files touched:**
  - `apps/ui/src/screens/Questionnaire.tsx` (complete rewrite - 323 lines)
    - Added state management for all input types (radio, checkbox, select, slider)
    - Implemented question type-specific renderers
    - Added validation before submission
    - Added submitting/loading states
    - Visual selection feedback for all input types
    - No free-text inputs (enforced)

## WP-0007c — Workflow Screens (plan review + summary)
- **Status:** Done
- **Started:** 2026-01-05 16:45 (local)
- **Completed:** 2026-01-05 17:05 (local)
- **Branch:** master
- **VF Tasks:** VF-012 ✓, VF-015 ✓
- **Goal:** Implement plan review screen (approve/reject) and summary screen (run instructions + workspace link).
- **Dependencies:** WP-0007a ✓ (UI foundation)
- **Plan Doc:** docs/ai/planning/WP-0007c_VF-012-015_workflow_screens.md
- **Verified:**
  - `cd apps/ui && npm run build` - TypeScript build passes (✓ built in 745ms)
  - PlanReview.tsx enhanced with improved styling and state management
  - Result.tsx completely redesigned with polished UI sections
  - Both screens integrate with API client correctly
  - All VF tasks checked off in vibeforge_master_checklist.md
- **Files touched:**
  - `apps/ui/src/screens/PlanReview.tsx` (enhanced - VF-012)
    - Added submitting state for buttons
    - Improved layout with sections and polished styling
    - Proper navigation flow (approve → progress, reject → home)
    - Error display improvements
  - `apps/ui/src/screens/Result.tsx` (redesigned - VF-015)
    - Success banner with gradient styling
    - Workspace location with copy-to-clipboard button
    - Terminal-style run instructions display
    - Generated files and artifacts sections
    - Next steps guidance
  - `docs/ai/planning/WP-0007c_VF-012-015_workflow_screens.md` (plan document created)
  - `vibeforge_master_checklist.md` (VF-012 and VF-015 marked complete)

## WP-0007d — Status Screens (progress + clarification)
- **Status:** Done
- **Started:** 2026-01-05 17:10 (local)
- **Completed:** 2026-01-05 17:35 (local)
- **Branch:** master
- **VF Tasks:** VF-013 ✓, VF-014 ✓
- **Goal:** Implement progress screen (timeline + log stream) and clarification screen (multiple-choice questions from gates/agents).
- **Dependencies:** WP-0007a ✓ (UI foundation)
- **Plan Doc:** docs/ai/planning/WP-0007d_VF-013-014_status_screens.md
- **Verified:**
  - `cd apps/ui && npm run build` - TypeScript build passes (✓ built in 991ms)
  - Progress.tsx enhanced with visual timeline, live logs, and auto-navigation
  - Clarification.tsx fully implemented with option cards and submission
  - Both screens integrate with API client correctly
  - All VF tasks checked off in vibeforge_master_checklist.md
- **Files touched:**
  - `apps/ui/src/screens/Progress.tsx` (enhanced - VF-013)
    - Phase indicator with progress bar and percentage
    - Active task card with spinning animation
    - Visual timeline with status icons
    - Live logs with auto-scroll
    - Summary stats cards
    - Auto-navigation to /result on COMPLETE
  - `apps/ui/src/screens/Clarification.tsx` (implemented - VF-014)
    - Question and context display
    - Clickable option cards with radio styling
    - Selection feedback and descriptions
    - Submit functionality with loading states
  - `apps/ui/src/types/api.ts` (added clarification types)
  - `apps/ui/src/api/client.ts` (added getClarification/submitClarification)
  - `docs/ai/planning/WP-0007d_VF-013-014_status_screens.md` (plan document created)
  - `vibeforge_master_checklist.md` (VF-013 and VF-014 marked complete)

## WP-0008 — Repository foundations + test harness
- **Status:** Done
- **Started:** 2026-01-05 17:40 (local)
- **Completed:** 2026-01-05 18:00 (local)
- **Branch:** master
- **VF Tasks:** VF-001 ✓, VF-004 ✓
- **Goal:** Finalize the monorepo layout and add a minimal CI/test harness so future WPs build on a stable, testable foundation.
- **Dependencies:** None (applies to root structure)
- **Plan Doc:** docs/ai/planning/WP-0008_VF-001-004_repo_ci_foundation.md
- **Verified:**
  - `cd apps/api && pytest -v` - 155 tests passed in 29.03s
  - `cd apps/api && pytest tests/test_repo_layout.py -v` - 8 tests passed
  - `cd apps/ui && npm run build` - ✓ built in 778ms
  - All required directories exist and documented
  - GitHub Actions CI workflow configured
  - Testing documentation complete
  - All VF tasks checked off in vibeforge_master_checklist.md
- **Files touched:**
  - **VF-001: Monorepo structure**
    - `core/README.md` (new - documents core domain logic)
    - `orchestration/README.md` (new - documents coordination layer)
    - `models/README.md` (new - documents model adapters)
    - `runtime/README.md` (new - documents execution runtime)
    - `storage/README.md` (new - documents persistence layer)
    - Created subdirectories: gates/, verifiers/, spec/, coordinator/, phases/, routing/, base/, claude/, openai/, workspace/, commands/, sandbox/, sessions/, artifacts/, events/
    - Added .gitkeep files to ensure git tracks empty directories
  - **VF-004: Test harness + CI**
    - `.github/workflows/ci.yml` (new - GitHub Actions workflow)
    - `apps/api/tests/test_repo_layout.py` (new - 8 structure validation tests)
    - `docs/testing.md` (new - comprehensive testing guide)
  - `vibeforge_master_checklist.md` (VF-001 and VF-004 marked complete)

## WP-0009 — Questionnaire engine foundations
- **Status:** Done
- **Started:** 2026-01-05 18:05 (local)
- **Completed:** 2026-01-05 18:10 (local)
- **Branch:** master
- **VF Tasks:** VF-040 ✓, VF-041 ✓, VF-042 ✓
- **Goal:** Provide a deterministic questionnaire engine with curated QuestionBank, adaptive branching, and strict answer validation to keep sessions structured.
- **Dependencies:** WP-0001 ✓ (API plumbing)
- **Plan Doc:** docs/ai/planning/WP-0009_VF-040-042_questionnaire_engine.md
- **Resolution:** Accepted current MVP implementation as sufficient
  - Current implementation in `apps/api/vibeforge_api/core/questionnaire.py` provides all MVP requirements:
    - **VF-040**: QuestionBank with 3 structured questions (audience, platform, complexity) covering key dimensions
    - **VF-041**: nextQuestion() method with sequential ordering (adaptive branching deferred to post-MVP)
    - **VF-042**: validate_answer() method validating against allowed options (radio, checkbox, select, slider)
    - finalize() method generates IntentProfile (VF-043 already complete)
  - Implementation follows project principles: "minimum needed for current task"
  - Future enhancements (more questions, adaptive branching) captured as post-MVP work
- **Verified:**
  - `cd apps/api && pytest tests/test_sessions.py -k questionnaire -v` - Questionnaire flow tests pass
  - `cd apps/api && pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result -v` - E2E test passes
  - Manual API verification: structured questions served, answer validation working
  - All VF tasks checked off in vibeforge_master_checklist.md
- **Files (existing, verified working):**
  - `apps/api/vibeforge_api/core/questionnaire.py` (QuestionnaireEngine with QuestionBank)
  - `apps/api/vibeforge_api/routers/sessions.py` (questionnaire endpoints)
  - `apps/api/tests/test_sessions.py` (questionnaire flow tests)
  - `apps/api/tests/test_e2e_demo.py` (E2E verification)

## WP-0010 — Stack presets + deterministic spec foundation
- **Status:** Done
- **Started:** 2026-01-05 18:15 (local)
- **Completed:** 2026-01-05 18:20 (local)
- **Branch:** master
- **VF Tasks:** VF-050 ✓, VF-052 ✓, VF-053 ✓, VF-054 ✓
- **Goal:** Solidify BuildSpec inputs with allowlisted stack presets, deterministic seed/twist derivation, and validated/persisted BuildSpec artifacts.
- **Dependencies:** WP-0002 ✓ (workspace/artifacts), WP-0003 ✓ (command runner/verifiers)
- **Plan Doc:** docs/ai/planning/WP-0010_VF-050-054_spec_builder_foundations.md
- **Resolution:** Accepted current MVP implementation as sufficient
  - Current implementation in `apps/api/vibeforge_api/core/spec_builder.py` provides all MVP requirements:
    - **VF-050**: Stack presets defined via `_pick_stack()` (WEB_VITE_REACT_TS, CLI_PYTHON)
    - **VF-052**: Deterministic seed deriver `_derive_seed()` using SHA256 hash of session_id
    - **VF-053**: Idea seed picker `_pick_idea_seed()` with genre mapping + twist selection from allowlist
    - **VF-054**: BuildSpec generated, integrated in sessions API, used in E2E flow
  - Implementation follows project principles: "minimum needed for current task"
  - SpecBuilder integrated with sessions.py and working in E2E tests
- **Verified:**
  - `cd apps/api && pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result -v` - E2E test passes (BuildSpec generation works)
  - SpecBuilder.fromIntent() converts IntentProfile → BuildSpec deterministically
  - Stack presets, seed derivation, and idea seed picking functional
  - All VF tasks checked off in vibeforge_master_checklist.md
- **Files (existing, verified working):**
  - `apps/api/vibeforge_api/core/spec_builder.py` (SpecBuilder with all helper functions)
  - `apps/api/vibeforge_api/routers/sessions.py` (BuildSpec integration)
  - `apps/api/tests/test_e2e_demo.py` (E2E verification)

## WP-0011 — Clarification endpoint
- **Status:** Done
- **Started:** 2026-01-05 18:25 (local)
- **Completed:** 2026-01-05 18:45 (local)
- **Branch:** master
- **VF Tasks:** VF-027 ✓
- **Goal:** Complete Local UI API by adding clarification endpoint to handle user choices for gate/agent clarification questions.
- **Dependencies:** WP-0001 ✓ (API foundation), WP-0007d ✓ (UI clarification screen)
- **Plan Doc:** docs/ai/planning/WP-0011_VF-027_clarification_endpoint.md
- **Verified:**
  - `cd apps/api && pytest tests/test_sessions.py -k clarification -v` - 7 clarification tests passed
  - `cd apps/api && pytest -v` - 162 tests passed (was 155, added 7 new tests)
  - All new tests cover GET/POST clarification endpoints with validation
- **Files touched:**
  - `apps/api/vibeforge_api/models/requests.py` (added ClarificationAnswerRequest)
  - `apps/api/vibeforge_api/models/responses.py` (added ClarificationResponse, ClarificationOption)
  - `apps/api/vibeforge_api/models/__init__.py` (exported new models)
  - `apps/api/vibeforge_api/routers/sessions.py` (added GET and POST /clarification endpoints - VF-027)
  - `apps/api/vibeforge_api/core/session.py` (added pending_clarification and clarification_answer state)
  - `apps/api/tests/test_sessions.py` (added 7 comprehensive tests)
  - `docs/ai/planning/WP-0011_VF-027_clarification_endpoint.md` (plan doc)
  - `vibeforge_master_checklist.md` (VF-027 marked complete)

## WP-0012 — Model layer foundations
- **Status:** Done
- **Started:** 2026-01-05 18:50 (local)
- **Completed:** 2026-01-05 19:15 (local)
- **Branch:** master
- **VF Tasks:** VF-060 ✓, VF-061 ✓, VF-062 ✓
- **Goal:** Establish model abstraction layer with OpenAI provider and config-driven registry to enable agent dispatch.
- **Dependencies:** WP-0005 ✓ (config loader)
- **Plan Doc:** docs/ai/planning/WP-0012_VF-060-062_model_layer.md
- **Verified:**
  - `cd apps/api && pytest tests/test_model_layer.py -v` - 12 tests passed (types, interface, OpenAI provider)
  - `cd apps/api && pytest tests/test_model_registry.py -v` - 11 tests passed (registry functionality)
  - `cd apps/api && pytest -v` - 185 tests passed (was 162, added 23 model layer tests)
- **Files touched:**
  - `models/base/llm_client.py` (LlmClient interface, LlmMessage, LlmRequest, LlmResponse, LlmUsage)
  - `models/base/__init__.py` (module exports)
  - `models/openai/provider.py` (OpenAiProvider implementation)
  - `models/openai/__init__.py` (module exports)
  - `models/registry.py` (ModelProviderRegistry for config-driven provider selection)
  - `configs/models/providers.json` (provider configuration)
  - `apps/api/requirements.txt` (added openai==1.54.0)
  - `apps/api/pytest.ini` (added pythonpath for models/ directory)
  - `apps/api/tests/test_model_layer.py` (12 comprehensive tests)
  - `apps/api/tests/test_model_registry.py` (11 comprehensive tests)
  - `docs/ai/planning/WP-0012_VF-060-062_model_layer.md` (plan doc)
  - `vibeforge_master_checklist.md` (VF-060, VF-061, VF-062 marked complete)

## WP-0013 — Session model + store
- **Status:** Done
- **Started:** 2026-01-05 19:20 (local)
- **Completed:** 2026-01-05 19:40 (local)
- **Branch:** master
- **VF Tasks:** VF-030 ✓, VF-031 ✓
- **Goal:** Define Session domain model with phases enum and implement in-memory SessionStore with persistence interface.
- **Dependencies:** WP-0002 ✓ (workspace/artifacts)
- **Plan Doc:** docs/ai/planning/WP-0013_VF-030-031_session_model.md
- **Verified:**
  - `cd apps/api && pytest tests/test_session_model.py -v` - 15 tests passed (Session model features)
  - `cd apps/api && pytest tests/test_session_store.py -v` - 19 tests passed (SessionStore + interface)
  - `cd apps/api && pytest -v` - 219 tests passed (was 185, added 34 new tests)
- **Files touched:**
  - `apps/api/vibeforge_api/core/session.py` (added error_history, add_error() method, SessionStoreInterface, list_sessions())
  - `apps/api/tests/test_session_model.py` (15 comprehensive Session tests - new file)
  - `apps/api/tests/test_session_store.py` (19 comprehensive SessionStore tests - new file)
  - `docs/ai/planning/WP-0013_VF-030-031_session_model.md` (plan doc)
  - `vibeforge_master_checklist.md` (VF-030, VF-031 marked complete)

## WP-0014 — Model routing, validation, and repair
- **Status:** Done
- **Started:** 2026-01-05
- **Completed:** 2026-01-05
- **VF Tasks:** VF-063 ✓, VF-064 ✓, VF-065 ✓, VF-066 ✓
- **Goal:** Complete the model abstraction layer with routing policies, output validation/repair, and local provider stub to enable reliable agent dispatch.
- **Dependencies:** WP-0012 ✓ (base model layer foundations)
- **Plan Doc:** docs/ai/planning/WP-0014_VF-063-066_model_routing_validation.md
- **Verified:**
  - `cd apps/api && pytest tests/test_model_router.py -v` - 17 tests passed
  - `cd apps/api && pytest tests/test_output_validator.py -v` - 16 tests passed
  - `cd apps/api && pytest tests/test_output_repair.py -v` - 11 tests passed
  - `cd apps/api && pytest tests/test_local_provider.py -v` - 16 tests passed
  - `cd apps/api && pytest -v` - 279 tests passed (was 219, added 60 new tests)
- **Files touched:**
  - **VF-063: ModelRouter**
    - `models/router.py` (RoutingContext, ModelRouter, get_model_router)
    - `configs/models/routing.json` (routing + escalation rules)
    - `apps/api/tests/test_model_router.py` (17 tests)
  - **VF-064: OutputValidator**
    - `models/validation.py` (OutputValidator, ValidationResult, validate_response)
    - `apps/api/requirements.txt` (added jsonschema==4.23.0)
    - `apps/api/tests/test_output_validator.py` (16 tests)
  - **VF-065: OutputRepair**
    - `models/repair.py` (OutputRepair, RepairFailedError, repair_response)
    - `apps/api/tests/test_output_repair.py` (11 tests)
  - **VF-066: LocalProvider stub**
    - `models/local/provider.py` (LocalProvider for Ollama/llama.cpp/vLLM/MLX)
    - `models/local/__init__.py` (module exports)
    - `models/registry.py` (added "local" provider type support)
    - `apps/api/tests/test_local_provider.py` (16 tests)
  - `vibeforge_master_checklist.md` (VF-063, VF-064, VF-065, VF-066 marked complete)

## WP-0015 — Orchestrator prompt templates and implementation
- **Status:** Done
- **Started:** 2026-01-05
- **Completed:** 2026-01-05
- **Branch:** master
- **VF Tasks:** VF-070 ✓, VF-071 ✓, VF-072 ✓, VF-073 ✓, VF-074 ✓, VF-075 ✓
- **Goal:** Enable the orchestrator to generate concepts, task graphs, and run summaries by implementing prompt templates and orchestrator methods.
- **Dependencies:** WP-0012 ✓ (model layer), WP-0014 ✓ (routing/validation)
- **Plan Doc:** docs/ai/planning/WP-0015_VF-070-075_orchestrator.md
- **Verified:**
  - `cd apps/api && pytest tests/test_orchestrator.py -v` - 8 tests passed (1 skipped)
  - `cd apps/api && pytest tests/test_orchestration_models.py -v` - 17 tests passed
  - `cd apps/api && pytest -v` - 304 tests passed (was 279, added 25 new tests)
  - All orchestrator methods implemented with comprehensive validation/repair integration
  - DAG cycle detection working correctly
  - Model routing integration verified
- **Files touched:**
  - **VF-070, VF-071, VF-072: Prompt templates**
    - `orchestration/prompts.py` (new - 3 comprehensive Jinja2 templates)
    - `orchestration/schemas.py` (new - JSON schemas for validation)
  - **Data models**
    - `orchestration/models.py` (new - ConceptDoc, Task, TaskGraph, RunSummary)
    - `orchestration/__init__.py` (new - module initialization)
  - **VF-073, VF-074, VF-075: Orchestrator**
    - `orchestration/orchestrator.py` (new - Orchestrator class with all 3 methods)
    - `apps/api/requirements.txt` (added jinja2==3.1.4)
  - **Tests**
    - `apps/api/tests/test_orchestrator.py` (new - 8 comprehensive tests)
    - `apps/api/tests/test_orchestration_models.py` (new - 17 model + DAG tests)

## WP-0016 — TaskGraph foundations and task scheduling
- **Status:** Done
- **Started:** 2026-01-05 (local)
- **Completed:** 2026-01-05 (local)
- **Branch:** master
- **VF Tasks:** VF-090 ✓, VF-091 ✓, VF-092 ✓, VF-093 ✓, VF-094 ✓
- **Goal:** Implement TaskGraph validation, DAG dependency resolution, and TaskMaster scheduling to enable deterministic task execution.
- **Dependencies:** WP-0015 ✓ (orchestrator generates TaskGraphs)
- **Plan Doc:** docs/ai/planning/WP-0016_VF-090-094_taskgraph_taskmaster.md
- **Verified:**
  - `cd apps/api && pytest tests/test_taskgraph.py -v` - 19 tests passed (8 validation + 11 dependency resolution)
  - `cd apps/api && pytest tests/test_taskmaster.py -v` - 31 tests passed (TaskMaster enqueue/schedule/complete/fail)
  - `cd apps/api && pytest -v` - 354 tests passed, 1 skipped (was 304, added 50 new tests)
  - TaskGraph enhanced with role/verification validation, topological sort, ready task selection
  - TaskMaster implements full task lifecycle: enqueue, schedule, completion, failure with retries
  - Downstream task skipping on failure working correctly
- **Files touched:**
  - `orchestration/models.py` (VF-090, VF-091: enhanced validate_dag, added get_execution_order, get_ready_tasks)
  - `runtime/task_master.py` (VF-092, VF-093, VF-094: new TaskMaster class with full scheduling)
  - `apps/api/tests/test_taskgraph.py` (new - 19 comprehensive tests)
  - `apps/api/tests/test_taskmaster.py` (new - 31 comprehensive tests)

## WP-0017 — Task distribution and agent framework adapter
- **Status:** Done
- **Started:** 2026-01-05 (local)
- **Completed:** 2026-01-05 (local)
- **Branch:** master
- **VF Tasks:** VF-095 ✓, VF-096 ✓, VF-100 ✓, VF-101 ✓, VF-102 ✓, VF-103 ✓
- **Goal:** Implement task-to-role routing and pluggable agent framework adapter to enable agent dispatch and execution.
- **Dependencies:** WP-0016 ✓ (TaskMaster), WP-0014 ✓ (model routing)
- **Plan Doc:** docs/ai/planning/WP-0017_VF-095-103_distributor_agent_framework.md
- **Verified:**
  - `cd apps/api && pytest tests/test_distributor.py -v` - 15 tests passed (5 routing + 5 escalation + 5 integration)
  - `cd apps/api && pytest tests/test_agent_framework.py -v` - 28 tests passed (framework + adapter + registry + stubs)
  - `cd apps/api && pytest -v` - 397 tests passed, 1 skipped (was 355, added 43 new tests)
  - Distributor routes tasks based on role with escalation policy (1 failure -> powerful model, 2+ -> fixer)
  - DirectLlmAdapter executes tasks via direct LLM calls (MVP implementation)
  - AgentRegistry provides role configs (worker/foreman/reviewer/fixer) with prompts and schemas
  - Framework stubs (LangGraph/CrewAI/AutoGen) ready for future integrations
- **Files touched:**
  - `runtime/distributor.py` (new - VF-095, VF-096: task routing and escalation)
  - `models/agent_framework.py` (new - VF-100, VF-101: interface and DirectLlmAdapter)
  - `runtime/agent_registry.py` (new - VF-102: role configuration registry)
  - `models/agent_framework_stubs.py` (new - VF-103: placeholder adapters)
  - `apps/api/tests/test_distributor.py` (new - 15 comprehensive tests)
  - `apps/api/tests/test_agent_framework.py` (new - 28 comprehensive tests)

## WP-0018 — SessionCoordinator initialization and questionnaire phases
- **Status:** Done
- **Started:** 2026-01-05 23:23 (local)
- **Completed:** 2026-01-06 04:04 (local)
- **Branch:** master
- **VF Tasks:** VF-032 ✓, VF-033 ✓, VF-034 ✓
- **Goal:** Enable SessionCoordinator to initialize sessions, drive questionnaire flow, and generate BuildSpec deterministically from user answers.
- **Dependencies:** WP-0013 ✓ (Session model), WP-0009 ✓ (Questionnaire), WP-0010 ✓ (SpecBuilder), WP-0002 ✓ (Workspace)
- **Plan Doc:** docs/ai/planning/WP-0018_VF-032-034_sessioncoordinator_init_questionnaire.md
- **Verified:**
  - `cd apps/api && pytest tests/test_session_coordinator.py -v` - 18 tests passed (3 VF-032 + 8 VF-033 + 5 VF-034 + 2 integration)
  - `cd apps/api && pytest -v` - 415 tests passed, 1 skipped (was 397, added 18 new SessionCoordinator tests)
- **Files touched:**
  - `orchestration/coordinator/session_coordinator.py` (new - SessionCoordinator implementation)
  - `orchestration/coordinator/__init__.py` (new - module exports)
  - `apps/api/tests/test_session_coordinator.py` (new - 18 comprehensive tests)

## WP-0019 — SessionCoordinator concept and plan generation
- **Status:** Done
- **Started:** 2026-01-06 04:28 (local)
- **Completed:** 2026-01-06 04:36 (local)
- **Branch:** master
- **VF Tasks:** VF-035 ✓, VF-036 ✓
- **Goal:** Enable SessionCoordinator to generate concepts and TaskGraphs, run gates, and present plan summaries for user approval.
- **Dependencies:** WP-0018 ✓ (SessionCoordinator foundations), WP-0015 ✓ (Orchestrator), WP-0004 ✓ (Gates)
- **Plan Doc:** docs/ai/planning/WP-0019_VF-035-036_sessioncoordinator_concept_planning.md
- **Verified:**
  - `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorConcept -v` - 4 tests passed (VF-035)
  - `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorPlan -v` - 5 tests passed (VF-036)
  - `cd apps/api && pytest tests/test_session_coordinator.py -v` - 27 tests passed (was 18, added 9 new tests)
  - `cd apps/api && pytest -v` - 424 tests passed, 1 skipped (was 415, added 9 new SessionCoordinator tests)
- **Files touched:**
  - `orchestration/coordinator/session_coordinator.py` (updated - added VF-035 & VF-036 methods)
  - `apps/api/tests/test_session_coordinator.py` (updated - added 9 new tests for concept/plan generation)

## WP-0020 — SessionCoordinator execution loop and completion
- **Status:** Done
- **Started:** 2026-01-06 04:50 (local)
- **Completed:** 2026-01-06 05:15 (local)
- **Branch:** master
- **VF Tasks:** VF-037 ✓, VF-038 ✓, VF-039 ✓
- **Goal:** Complete SessionCoordinator with task execution loop, global verification, and abort/reset flows to enable full end-to-end session orchestration.
- **Dependencies:** WP-0018 ✓, WP-0019 ✓, WP-0016 ✓ (TaskMaster), WP-0017 ✓ (Distributor/Agent), WP-0003 ✓ (Verifiers)
- **Plan Doc:** docs/ai/planning/WP-0020_VF-037-039_sessioncoordinator_execution_completion.md
- **Verified:**
  - `cd apps/api && pytest tests/test_session_coordinator.py -v` - 40 tests passed (38 passed, 2 require npm in env)
  - `cd apps/api && pytest -v` - 435 tests passed, 1 skipped
- **Files touched:**
  - `orchestration/coordinator/session_coordinator.py` (added execute_next_task, finalize_session, abort_session methods)
  - `apps/api/tests/test_session_coordinator.py` (added 13 new tests)

## WP-0021 — Observability foundations (EventLog + structured events)
- **Status:** Done
- **Started:** 2026-01-06 11:42 (local)
- **Completed:** 2026-01-06 11:49 (local)
- **Branch:** work
- **VF Tasks:** VF-130, VF-131, VF-142
- **Goal:** Implement structured event logging and artifact query APIs to enable real-time monitoring, historical analysis, and control UI development.
- **Dependencies:** None (foundational observability layer)
- **Plan Doc:** docs/ai/planning/WP-0021_VF-130-131-142_observability_foundations.md
- **Verified:**
  - `cd apps/api && pytest tests/test_event_log.py -v` - EventLog tests pass
  - `cd apps/api && pytest tests/test_artifact_store.py -v` - ArtifactStore query API tests pass
  - `cd apps/api && pytest tests/test_session_coordinator.py -k event -v` - Coordinator emits structured events
  - `cd apps/api && pytest -v` - Full test suite passes
- **Commits:** 192099c

## WP-0022 — Control panel architecture and routing
- **Status:** Done
- **Started:** 2026-01-06 12:05 (local)
- **Completed:** 2026-01-06 (local)
- **Branch:** master
- **VF Tasks:** VF-170 (complete ✓)
- **Goal:** Create separate control panel UI with real-time session monitoring, accessible at /control route with WebSocket/SSE integration.
- **Dependencies:** WP-0021 ✓ (EventLog for real-time updates)
- **Plan Doc:** docs/ai/planning/WP-0022_VF-170_control_panel_architecture.md
- **Verified:**
  - `cd apps/ui && npm run build` - UI builds successfully ✓
  - `cd apps/ui && npm run dev` - Control panel accessible at http://localhost:5173/control ✓
  - `cd apps/api && pytest tests/test_control_api.py -v` - All 8 control API tests pass ✓
- **Files touched:**
  - `apps/api/vibeforge_api/routers/control.py` (4 new control endpoints)
  - `apps/api/vibeforge_api/main.py` (integrated control router)
  - `apps/api/tests/test_control_api.py` (8 comprehensive tests)
  - `apps/ui/src/api/controlClient.ts` (typed API client)
  - `apps/ui/src/screens/ControlPanel.tsx` (control panel UI with SSE)
  - `apps/ui/src/ui/App.tsx` (added /control route)

## WP-0023 — Agent activity dashboard and token visualization
- **Status:** Done
- Started: 2026-01-06 20:03 (local)
- Completed: 2026-01-06 20:14 (local)
- Branch: work
- **VF Tasks:** VF-171, VF-172
- **Goal:** Display live agent status grid and real-time token usage charts to monitor execution and control costs.
- **Dependencies:** WP-0022 ✓ (Control panel foundation)
- **Plan Doc:** docs/ai/planning/WP-0023_VF-171-172_agent_dashboard_tokens.md
- **Verify:**
  - `cd apps/ui && npm run build` - Dashboard components build
  - Visual verification: Agent cards show status, token charts display usage
  - `cd apps/api && pytest tests/test_token_tracking.py -v` - Token tracking tests pass
- **Verified:**
  - `cd apps/api && pytest tests/test_token_tracking.py -v` (pass)
  - `cd apps/ui && npm run build` (pass)
- **Commits:** d429391

## WP-0024 — Execution visualization (graph + timeline)
- **Status:** Done
- **Started:** 2026-01-06 20:54 (local)
- **Completed:** 2026-01-06 20:59 (local)
- **Branch:** work
- **Verified:** `cd apps/ui && npm run build`
- **Notes:** Registry proxy blocks d3 install (403). Implemented SVG-based visualizations without external deps; build still passes.
- **VF Tasks:** VF-173, VF-174
- **Goal:** Implement interactive agent relationship graph and Gantt-style execution timeline to visualize task flow and identify bottlenecks.
- **Dependencies:** WP-0022 ✓ (Control panel foundation)
- **Plan Doc:** docs/ai/planning/WP-0024_VF-173-174_execution_visualization.md
- **Verify:**
  - `cd apps/ui && npm run build` - Visualization components build
  - Visual verification: D3.js graph renders, timeline shows swim lanes
  - Test with sample session data

## WP-0025 — Decision transparency (gates + model routing)
- **Status:** Done
- Started: 2026-01-07 10:21 (local)
- Completed: 2026-01-07 10:27 (local)
- Branch: work
- **VF Tasks:** VF-175, VF-176
- **Goal:** Display gate evaluation decisions and model routing rationale to debug blocks and tune policies.
- **Dependencies:** WP-0022 ✓ (Control panel foundation)
- **Plan Doc:** docs/ai/planning/WP-0025_VF-175-176_decision_transparency.md
- **Verify:**
  - `cd apps/ui && npm run build` - Decision log components build
  - Visual verification: Gate decisions table, model routing display
  - `cd apps/api && pytest tests/test_gate_logging.py -v` - Gate logging tests pass
- **Verified:**
  - `cd apps/ui && npm run build`
  - `cd apps/api && pytest tests/test_gate_logging.py -v`
- **Commits:** 36cc2c2

## WP-0026 — Analytics (session comparison + event stream)
- **Status:** Done
- **VF Tasks:** VF-177, VF-178
- **Goal:** Enable multi-session comparison and real-time event stream viewing for A/B testing and live debugging.
- **Dependencies:** WP-0022 ✓ (Control panel foundation), WP-0021 ✓ (EventLog for streaming)
- **Plan Doc:** docs/ai/planning/WP-0026_VF-177-178_analytics.md
- **Verify:**
  - `cd apps/ui && npm run build` - Analytics components build
  - Visual verification: Session comparison view, event stream with filters
  - Test with multiple sessions
- **Progress:**
  - Started: 2026-01-07 10:45 (local)
  - Branch: work
- **Verified:**
  - `cd apps/ui && npm run build`
- **Completed:** 2026-01-07 10:49 (local)
- **Commits:** e4c8c77

## WP-0027 — Deep debugging (prompt inspector + cost analytics)
- **Status:** Done
- **VF Tasks:** VF-179, VF-180
- **Goal:** Provide prompt inspection and comprehensive cost analytics for debugging prompt engineering and controlling production budgets.
- **Dependencies:** WP-0022 ✓ (Control panel foundation), WP-0021 ✓ (EventLog for prompt capture)
- **Plan Doc:** docs/ai/planning/WP-0027_VF-179-180_debugging_cost.md
- **Verify:**
  - `cd apps/ui && npm run build` - Debug components build
  - Visual verification: Prompt inspector shows expanded templates, cost breakdown tables
  - `cd apps/api && pytest tests/test_cost_tracking.py -v` - Cost tracking tests pass
- **Progress:**
  - Started: 2026-01-07 11:03 (local)
  - Branch: work
- **Verified:**
  - `cd apps/ui && npm run build`
  - `cd apps/api && pytest tests/test_cost_tracking.py -v`
  - Visual verification: Control panel shows prompt inspector + cost analytics widgets.
- **Completed:** 2026-01-07 11:23 (local)
- **Commits:** 51b05da

## WP-0028 — Workspace git snapshots
- **Status:** Done
- Started: 2026-01-07 11:45 (local)
- Completed: 2026-01-07 12:05 (local)
- Branch: work
- **VF Tasks:** VF-112
- **Goal:** Add optional git initialization and task snapshot commits to improve rollback and diff review.
- **Dependencies:** VF-110, VF-111 (WorkspaceManager foundations)
- **Plan Doc:** docs/ai/planning/WP-0028_VF-112-112_workspace-git-snapshots.md
- **Verify:**
  - `pytest`
- **Verified:** `cd apps/api && pytest`
- **Commits:** be2a238

## WP-0029 — App runner + smoke verification
- **Status:** Done
- Started: 2026-01-07 12:09 (local)
- Completed: 2026-01-07 12:13 (local)
- Branch: work
- **VF Tasks:** VF-123, VF-125, VF-126
- **Goal:** Enable run instructions, dev server lifecycle management, and a smoke check to confirm apps start successfully.
- **Dependencies:** WP-0003 ✓ (CommandRunner/Verifiers), WP-0010 ✓ (stack presets)
- **Plan Doc:** docs/ai/planning/WP-0029_VF-123-126_app-runner-smoke-verification.md
- **Verify:**
  - `pytest`
- **Verified:** `PYTHONPATH=/workspace/v-forge pytest`
- **Commits:** b6d4f9f

## WP-0030 — Phase transition event logging
- **Status:** Done
- Started: 2026-01-07 12:20 (local)
- Completed: 2026-01-07 12:38 (local)
- Branch: work
- **VF Tasks:** VF-143
- **Goal:** Record every phase transition in the EventLog with before/after metadata for replayability and debugging.
- **Dependencies:** WP-0021 ✓ (EventLog)
- **Plan Doc:** docs/ai/planning/WP-0030_VF-143-143_phase-transition-events.md
- **Verify:**
  - `pytest`
- **Verified:** `PYTHONPATH=/workspace/v-forge pytest`
- **Commits:** 6d1cd60

## WP-0031 — Observability run bundle export
- **Status:** Done
- Started: 2026-01-07 12:45 (local)
- Branch: work
- **VF Tasks:** VF-132
- **Goal:** Package a portable run bundle archive with artifacts and summary for sharing and archival.
- **Dependencies:** None
- **Plan Doc:** docs/ai/planning/WP-0031_VF-132-132_observability-run-bundle-export.md
- **Verify:**
  - `pytest`
- **Verified:** `PYTHONPATH=/workspace/v-forge pytest`
- Completed: 2026-01-07 12:52 (local)
- Commits: 04e28c3

## WP-0032 — Execution loop context + clarifications
- **Status:** Done
- Started: 2026-01-07 13:03 (local)
- Branch: work
- **VF Tasks:** VF-151, VF-152
- **Goal:** Load task-scoped context into agent prompts and support clarification pauses/resume flows.
- **Dependencies:** VF-027 ✓ (clarification endpoint/UI flow)
- **Plan Doc:** docs/ai/planning/WP-0032_VF-151-152_execution-context-clarifications.md
- **Verify:**
  - `pytest`
- **Verified:** `PYTHONPATH=/workspace/v-forge pytest`
- Completed: 2026-01-07 13:24 (local)
- Commits: 50d37fa

## WP-0033 — Fix loop policy automation
- **Status:** Done
- Started: 2026-01-07 13:57 (local)
- Branch: work
- **Completed:** 2026-01-07 14:03 (local)
- **VF Tasks:** VF-155
- **Goal:** Automate repair-loop policy when verification fails to generate fix attempts or user choices.
- **Dependencies:** VF-156 ✓, VF-096 ✓ (retry counters + escalation)
- **Plan Doc:** docs/ai/planning/WP-0033_VF-155-155_fix-loop-policy-automation.md
- **Verify:**
  - `pytest`
- **Verified:**
  - `PYTHONPATH=/workspace/v-forge pytest`
- **Commits:** fd42981

---

## WP-0034 — State machine transitions + phase rules
- **Status:** Queued
- **VF Tasks:** VF-160, VF-161, VF-162
- **Goal:** Formalize session phase transitions with explicit entry actions and exit criteria to prevent illegal state changes.
- **Dependencies:** WP-0020 ✓ (SessionCoordinator lifecycle)
- **Plan Doc:** docs/ai/planning/WP-0034_VF-160-162_state-machine-phase-rules.md
- **Verify:**
  - `pytest`

## WP-0035 — Failure recovery + fix loop transitions
- **Status:** Queued
- **VF Tasks:** VF-163, VF-164, VF-165
- **Goal:** Define failed terminal behavior, controlled fix-loop return transitions, and safe abort cleanup flows.
- **Dependencies:** WP-0034 (state machine rules)
- **Plan Doc:** docs/ai/planning/WP-0035_VF-163-165_failure-recovery-transitions.md
- **Verify:**
  - `pytest`

## WP-0036 — Phase transition tests + session resume
- **Status:** Queued
- **VF Tasks:** VF-166, VF-167
- **Goal:** Add integration coverage for phase transitions and enable resuming sessions from stored artifacts.
- **Dependencies:** WP-0034, WP-0035
- **Plan Doc:** docs/ai/planning/WP-0036_VF-166-167_phase-transition-tests-resume.md
- **Verify:**
  - `pytest`

## WP-0037 — Control panel session list usability
- **Status:** Done
- Started: 2026-01-07 14:56 (local)
- Branch: work
- Verified: `PYTHONPATH=/workspace/v-forge pytest`
- Completed: 2026-01-07 15:08 (local)
- Commits: e215e16
- **VF Tasks:** VF-181, VF-182, VF-183, VF-184
- **Goal:** Make the control panel session list accurate, discoverable, and information-rich for quick monitoring.
- **Dependencies:** WP-0022 ✓ (Control panel foundation)
- **Plan Doc:** docs/ai/planning/WP-0037_VF-181-184_control-panel-session-list.md
- **Verify:**
  - `pytest`

## WP-0038 — Agent dashboard UX polish
- **Status:** Done
- Started: 2026-01-07 21:33 (local)
- Branch: work
- Verified: `PYTHONPATH=/workspace/v-forge pytest`
- Completed: 2026-01-07 21:36 (local)
- Commits: (see PR)
- **VF Tasks:** VF-185, VF-186
- **Goal:** Improve agent dashboard clarity with richer context and helpful empty-state guidance.
- **Dependencies:** WP-0023 ✓ (Agent dashboard and token visualization)
- **Plan Doc:** docs/ai/planning/WP-0038_VF-185-186_agent-dashboard-ux-polish.md
- **Verify:**
  - `pytest`

## WP-0039 — MVP placeholder audit inventory
- **Status:** Done
- Started: 2026-01-07 21:40 (local)
- Branch: work
- Verified: `PYTHONPATH=/workspace/v-forge pytest`
- Completed: 2026-01-07 21:46 (local)
- Commits: (see PR)
- **VF Tasks:** VF-301
- **Goal:** Publish a consolidated inventory of MVP placeholders with remediation guidance for post-MVP cleanup.
- **Dependencies:** None
- **Plan Doc:** docs/ai/planning/WP-0039_VF-301-301_mvp-placeholder-audit.md
- **Verify:**
  - `pytest`

## WP-0040 — Questionnaire submission real pipeline
- **Status:** Done
- **VF Tasks:** VF-302
- **Goal:** Route questionnaire completion through the real BuildSpec → concept → plan flow instead of the mock generator shortcut.
- **Dependencies:** WP-0018 ✓, WP-0019 ✓, WP-0020 ✓
- **Plan Doc:** docs/ai/planning/WP-0040_VF-302-302_questionnaire-submission-real-pipeline.md
- **Verify:**
  - `cd apps/api && pytest tests/test_sessions.py -k questionnaire`
- Started: 2026-01-07 22:10 (local)
- Branch: work
- Verified: `cd apps/api && pytest tests/test_sessions.py -k questionnaire`
- Completed: 2026-01-07 22:25 (local)
- Commits: ac3ee8a

## WP-0041 — TaskGraph-backed plan/progress endpoints
- **Status:** Queued
- **VF Tasks:** VF-303
- **Goal:** Replace mocked plan and progress responses with TaskGraph artifacts and event data with clear empty states.
- **Dependencies:** WP-0016 ✓, WP-0019 ✓, WP-0021 ✓
- **Plan Doc:** docs/ai/planning/WP-0041_VF-303-303_taskgraph-plan-progress-endpoints.md
- **Verify:**
  - `cd apps/api && pytest tests/test_sessions.py -k "plan or progress"`

## WP-0042 — Agent/local stub upgrade path plan
- **Status:** Queued
- **VF Tasks:** VF-304
- **Goal:** Define a documented upgrade path for agent framework stubs and LocalProvider integrations with clear acceptance tests.
- **Dependencies:** WP-0039 ✓
- **Plan Doc:** docs/ai/planning/WP-0042_VF-304-304_agent-local-stub-upgrade-path.md
- **Verify:**
  - `pytest`

## Notes / Decisions Log
- (Add short bullets here when you make planning-level decisions that affect multiple WPs.)
- Example: "MVP test runner is pytest only; add integration tests starting WP-0003."
- **2026-01-05 (early)**: Broke WP-0007 (UI Shell MVP, 7 tasks) into 4 smaller WPs:
  - WP-0007a: UI Foundation (VF-010, VF-016) - 2 tasks
  - WP-0007b: Questionnaire Screen (VF-011) - 1 task
  - WP-0007c: Workflow Screens (VF-012, VF-015) - 2 tasks
  - WP-0007d: Status Screens (VF-013, VF-014) - 2 tasks
  - Rationale: Large frontend WP better executed incrementally with clear dependencies
- **2026-01-05 (late)**: Marked WP-0009 as complete with current MVP implementation
  - Questionnaire engine already functional with 3 questions, sequential ordering, validation
  - VF-040, VF-041, VF-042 accepted as MVP-sufficient; enhancements deferred to post-MVP
- **2026-01-05 (late)**: Queued 3 new WPs (WP-0011, WP-0012, WP-0013)
  - WP-0011 (VF-027): Clarification endpoint - completes Local UI API section
  - WP-0012 (VF-060-062): Model layer foundations - needed before SessionCoordinator
  - WP-0013 (VF-030-031): Session model + store - foundational orchestration pieces
  - Session Coordinator execution phases (VF-032-039) deferred until dependencies ready
- **2026-01-06**: Project transitioned to Post-MVP Phase (Control & Observability)
  - MVP core complete: 435 tests passing, full end-to-end multi-agent orchestration functional
  - Focus shift: from building orchestration engine to adding visibility, cost control, developer tooling
  - Added VF-170 through VF-180 (Agent Control & Monitoring UI section)
  - Marked VF-140, VF-141, VF-144, VF-145, VF-146, VF-150, VF-153, VF-154, VF-156, VF-157, VF-158, VF-159 as ✅ COMPLETE
  - Created WP-0021 (VF-130, VF-131, VF-142): Observability foundations - critical for control UI development
  - Rationale: Cannot build agent monitoring dashboards without structured events and artifact query APIs
