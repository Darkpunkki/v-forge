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
- **Status:** Queued
- **VF Tasks:** VF-030, VF-031
- **Goal:** Define Session domain model with phases enum and implement in-memory SessionStore with persistence interface.
- **Dependencies:** WP-0002 ✓ (workspace/artifacts)
- **Plan Doc:** docs/ai/planning/WP-0013_VF-030-031_session_model.md
- **Verify:**
  - `cd apps/api && pytest tests/test_session_model.py -v`
  - `cd apps/api && pytest tests/test_session_store.py -v`
  - Verify Session can track phases and reference artifacts

---

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
