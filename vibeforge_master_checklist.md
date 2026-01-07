# VibeForge Master Checklist




## Project Status: Post-MVP Phase (Control & Observability)

**MVP Core: ✅ COMPLETE** - Full end-to-end multi-agent orchestration is functional (435 tests passing).

**Current Focus:** Moving beyond MVP to production-ready observability, monitoring, and control interfaces. The system can now orchestrate LLMs to build applications - next phase adds visibility, cost control, and developer tooling.

---

## Workflow Vocabulary (Vision Context)

This section is **not** a task list. It is shared vocabulary describing the intended **VibeForge workflow** so agents can generate plans/tasks with the right mental model.

### High-level promise
VibeForge turns **structured-only user choices** into a **runnable local app** using a **safe, gated, test-driven factory loop**. Users never provide free-text app descriptions; they influence outcomes via curated options, budgets, and “vibe” controls.

### The canonical artifacts
Agents should think in terms of these stable artifacts (each persisted per session):
- **IntentProfile**: the user’s questionnaire answers (strictly structured, no free text).
- **BuildSpec**: deterministic contract derived from IntentProfile (stack preset, seed/twists, budgets, policies, acceptance criteria).
- **Concept**: human-readable concept doc + structured concept data aligned to BuildSpec constraints.
- **TaskGraph**: a DAG plan (tasks + dependencies + constraints + verification steps).
- **AgentResult**: a standard agent output (unified diff + proposed commands + structured notes).
- **RunSummary**: what was built + how to run + what verified + limitations.

### Session phases (mental model)
A session progresses through phases with strict guards; “wrong phase” calls must be rejected consistently:
1) **SESSION_START** → create session + workspace + initial artifacts
2) **QUESTIONNAIRE** → serve next question → accept answer → repeat → finalize IntentProfile
3) **SPEC_BUILD** → BuildSpec from IntentProfile (deterministic)
4) **IDEA** → generate Concept (seeded creativity within constraints)
5) **PLAN_REVIEW** → generate TaskGraph → gates → show plan summary → approve/reject
6) **EXECUTION** → iterate tasks: dispatch → gate → apply → verify → mark done/failed
7) **VERIFICATION** → final global verification (build/test/smoke)
8) **COMPLETE** or **FAILED/ABORTED** → produce RunSummary + preserve artifacts/logs

*(Exact enum names may differ; the behavior above is the contract.)*

### “Gates everywhere” principle
Before any risky action, the system must gate it. Gates are small policy checks that return **ok / warn / block**, optionally with **multiple-choice clarifications**.
Common gate categories:
- **Feasibility**: scope budgets, diff size limits, unrealistic plans
- **Risk/Policy**: command allowlists, network rule, forbidden patterns
- **Diff/Command validation**: max files/lines, path constraints, forbidden content
- **Plan gates**: block unsafe TaskGraphs before execution starts

**Rule:** Nothing writes outside the session workspace. Nothing runs outside allowlisted command families.

### Execution loop (the “factory engine”)
Execution is intentionally boring and deterministic:
- Pick next ready task from TaskGraph (DAG)
- Route to a role (worker/foreman/fixer/reviewer)
- Agent produces AgentResult (diff + commands-to-run + notes)
- Gate the AgentResult
- Apply diff to workspace repo (safe patching)
- Run task verification (declared by the task)
- Record artifacts + events
- On failure: bounded fix-loop with escalation rules

### Clarifications (structured, never free text)
When gates or agents need more info, they must return **multiple-choice questions**. The UI only allows constrained answers. Clarifications feed back into the coordinator and the next agent step.

### Determinism and reproducibility
Randomness is controlled:
- BuildSpec includes a **seed** (derived deterministically from IntentProfile)
- “Twist cards” are chosen from allowlists and recorded
- Key decisions/config hashes are persisted so runs can be replayed for debugging

### What “done” means for MVP runs
A successful run produces:
- A workspace repo that builds and tests (at least build+test; smoke if available)
- Clear run instructions
- A coherent summary
- An artifact trail and event log sufficient to debug failures

### Planning and execution discipline (Work Packages)
Agents should execute work via **Work Packages (WPs)**:
- WPs are small bundles of VF tasks used for iterative progress (plan → implement → verify → update docs → check off).
- The master checklist remains canonical for “what exists” and “what done means.”
- Planning docs under `docs/ai/planning/` should reference VF IDs and verification commands.

---

Use the checkboxes below as a living backlog. Mark tasks complete by changing `[ ]` to `[x]`.


## Checklist


### 00 Foundations

- [x] **VF-001 — Create monorepo structure (apps/core/orchestration/models/runtime/storage/configs/schemas)**
  - Initialize the repository with a clear top-level folder layout that matches the architecture. This keeps UI, core logic, orchestration, model adapters, runtime execution, and persistence cleanly separated from day one.
  - **Directories created:**
    - `core/` (with subdirs: gates/, verifiers/, spec/)
    - `orchestration/` (with subdirs: coordinator/, phases/, routing/)
    - `models/` (with subdirs: base/, claude/, openai/)
    - `runtime/` (with subdirs: workspace/, commands/, sandbox/)
    - `storage/` (with subdirs: sessions/, artifacts/, events/)
  - **Documentation:** README.md files in each top-level directory explaining purpose and structure
  - **Verify:** All directories exist and tracked by git (test_repo_layout.py passes)

- [x] **VF-002 — Define core DTOs + shared types (SessionPhase, AgentRole, GateResult)**
  - Create the shared domain types used across UI/API/core: session phases, agent roles, gate results, and common error/result envelopes. These are the contracts that prevent coupling and spaghetti.
  - Files: `apps/api/vibeforge_api/models/types.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/models/responses.py`
  - Verification: Models imported and used in routers; pytest passes

- [x] **VF-003 — Add configuration loader (stack presets, policies, router rules)**
  - Implement config loading (e.g., YAML/JSON) for allowlisted stack presets, command policies, forbidden patterns, and model routing rules. Make behavior adjustable without code changes.
  - **Files:** `apps/api/vibeforge_api/config/models.py` (PolicyConfig, StackPreset, CommandSpec, NetworkAccess, VibeForgeConfig)
  - **Files:** `apps/api/vibeforge_api/config/loader.py` (ConfigLoader with caching and validation)
  - **Files:** `apps/api/vibeforge_api/config/__init__.py` (exported functions: load_config, get_stack_preset, get_policy_config, list_available_stacks)
  - **Tests:** `apps/api/tests/test_config_loader.py` (20 comprehensive tests)
  - **Verify:** `pytest tests/test_config_loader.py -v` (20 passed), `pytest -v` (147 passed)

- [x] **VF-004 — Add basic test harness + CI skeleton (unit tests only)**
  - Set up unit test framework and a minimal CI pipeline so new components can be verified continuously. Keep it simple: lint/format optional, unit tests required.
  - **Files created:**
    - `.github/workflows/ci.yml` (GitHub Actions CI workflow)
    - `apps/api/tests/test_repo_layout.py` (repository structure validation test)
    - `docs/testing.md` (comprehensive testing documentation)
  - **CI Workflow:** Runs on push/PR to master/main
    - Job 1: API tests (pytest on Python 3.11, caches pip dependencies)
    - Job 2: UI build (npm build on Node.js 20, caches npm dependencies)
  - **Test Coverage:** 155 tests passing (8 new repo layout tests added)
  - **Documentation:** Local test instructions, CI workflow explanation, best practices
  - **Verify:** `cd apps/api && pytest -v` (155 passed), `cd apps/ui && npm run build` (✓ built in 778ms)


### 01 UI Shell (MVP)

- [x] **VF-010 — UI skeleton (simple web UI)**
  - Create a minimal, user-friendly UI shell (web is easiest for MVP). It should be able to start a session and render the main screens without any free-text input.
  - **Files:** `apps/ui/src/ui/App.tsx` (React Router setup), `apps/ui/src/components/Layout.tsx` (layout with navigation)
  - **Files:** `apps/ui/src/screens/Home.tsx`, `apps/ui/src/screens/Questionnaire.tsx`, `apps/ui/src/screens/PlanReview.tsx`, `apps/ui/src/screens/Progress.tsx`, `apps/ui/src/screens/Clarification.tsx`, `apps/ui/src/screens/Result.tsx`
  - **Verify:** `cd apps/ui && npm run build` (build succeeds), `cd apps/ui && npm run dev` (dev server starts on http://localhost:5173)

- [x] **VF-011 — Questionnaire screen (single-question flow, no free text)**
  - Implement a step-by-step questionnaire UI that only supports structured inputs (radio buttons, pick lists, sliders).
  - **Files:** `apps/ui/src/screens/Questionnaire.tsx` (enhanced with all question types)
  - **Implementation:**
    - Radio buttons: Single-choice with visual selection feedback
    - Checkboxes: Multi-select with comma-separated answer format
    - Select dropdown: Traditional dropdown with default prompt
    - Slider: Numeric range input with min/max/current value display
    - Form state management for each input type
    - Validation before submission (ensures selection made)
    - Loading/submitting states for better UX
    - Final question indicator
  - **Verify:** `cd apps/ui && npm run build` (TypeScript compilation succeeds)
  - **Verify:** `grep -E 'type="text"|<textarea' apps/ui/src/screens/Questionnaire.tsx` (no free-text inputs)

- [x] **VF-012 — Plan review screen (approve/reject)**
  - Show the proposed concept/plan summary and require explicit user approval before any code is generated or commands are run.
  - **Files:** `apps/ui/src/screens/PlanReview.tsx` (enhanced with improved styling and state management)
  - **Features implemented:**
    - Plan summary display (features, task count, verification steps, constraints)
    - Approve/reject buttons with submitting state
    - Proper navigation: approve → /progress, reject → /
    - Error handling and loading states
    - Polished UI with section-based layout
  - **Verify:** `cd apps/ui && npm run build` (TypeScript compilation succeeds)

- [x] **VF-013 — Progress screen (timeline + log stream)**
  - Display current phase, active task, completed tasks, and streaming logs (commands + verification results).
  - **Files:** `apps/ui/src/screens/Progress.tsx` (enhanced with visual timeline and polished UI)
  - **Features implemented:**
    - Phase indicator with gradient styling, progress bar, and percentage
    - Active task card with spinning animation
    - Visual task timeline with status icons (✅ completed, 🔄 in progress, ❌ failed)
    - Live logs in terminal-style display with auto-scroll to latest
    - Summary stats cards showing completed/in progress/failed counts
    - Auto-navigation to /result when phase transitions to COMPLETE
    - Polling every 2 seconds for real-time updates
  - **Verify:** `cd apps/ui && npm run build` (TypeScript compilation succeeds)

- [x] **VF-014 — Clarification screen (multiple-choice answers)**
  - Render clarification questions returned by gates or agents, allowing only multiple-choice or constrained answers.
  - **Files:** `apps/ui/src/screens/Clarification.tsx` (complete implementation with polished UI)
  - **Files:** `apps/ui/src/types/api.ts` (added ClarificationResponse, ClarificationOption, ClarificationAnswerRequest types)
  - **Files:** `apps/ui/src/api/client.ts` (added getClarification and submitClarification endpoints)
  - **Features implemented:**
    - Warning banner indicating clarification is needed
    - Question display with prominent text
    - Optional context section with highlighted background
    - Clickable option cards with radio button styling
    - Visual selection feedback (border and background color)
    - Option descriptions support
    - Submit button (disabled until option selected)
    - Loading and submitting states
    - Navigate back to /progress after submission
    - Error handling for failed API calls
  - **Verify:** `cd apps/ui && npm run build` (TypeScript compilation succeeds)

- [x] **VF-015 — Summary screen (run instructions + open workspace link)**
  - Present final run instructions, key features built, and the location of the generated workspace folder/repo.
  - **Files:** `apps/ui/src/screens/Result.tsx` (completely redesigned with polished UI)
  - **Features implemented:**
    - Success/failure banner with gradient styling
    - Summary section with formatted text
    - Workspace location with copy-to-clipboard button
    - Run instructions in terminal-style code block
    - Generated files list display
    - Artifacts section (if applicable)
    - Next steps guidance for users
    - "Start New Session" button
  - **Verify:** `cd apps/ui && npm run build` (TypeScript compilation succeeds)

- [x] **VF-016 — UI client for Local UI API (typed requests/responses)**
  - Implement a typed API client (or thin fetch wrapper) so the UI communicates with the local API through stable DTOs.
  - **Files:** `apps/ui/src/types/api.ts` (TypeScript types matching backend Pydantic models)
  - **Files:** `apps/ui/src/api/client.ts` (typed API client with error handling)
  - **Endpoints:** createSession, getQuestion, submitAnswer, getProgress, getResult, getPlan, decidePlan
  - **Verify:** `cd apps/ui && npm run build` (TypeScript compilation succeeds with no errors)


### 02 Local UI API

- [x] **VF-020 — API server skeleton (REST)**
  - Create the local API service that the UI talks to. This is the stable seam between presentation and factory core.
  - Files: `apps/api/vibeforge_api/main.py`, `apps/api/vibeforge_api/__init__.py`
  - Verification: `uvicorn vibeforge_api.main:app --reload` (server starts, /docs loads)

- [x] **VF-021 — Endpoint: POST /sessions (startSession)**
  - Start a new session, initialize workspace and artifacts, and return sessionId.
  - File: `apps/api/vibeforge_api/routers/sessions.py:20`
  - Verification: `pytest tests/test_sessions.py::test_create_session`

- [x] **VF-022 — Endpoint: GET /sessions/{id}/question (getNextQuestion)**
  - Return the next questionnaire question for the current session state.
  - File: `apps/api/vibeforge_api/routers/sessions.py:32`
  - Verification: `pytest tests/test_sessions.py::test_get_first_question`

- [x] **VF-023 — Endpoint: POST /sessions/{id}/answers (submitAnswer)**
  - Accept a structured answer, validate it, store it, and advance questionnaire state.
  - File: `apps/api/vibeforge_api/routers/sessions.py:57`
  - Verification: `pytest tests/test_sessions.py::test_submit_valid_answer`, `test_questionnaire_flow_completion`

- [x] **VF-024 — Endpoint: GET /sessions/{id}/plan (getPlanSummary)**
  - Return the current concept/plan proposal summary for user review (once available).
  - File: `apps/api/vibeforge_api/routers/sessions.py:103`
  - Verification: `pytest tests/test_sessions.py::test_plan_summary_wrong_phase`

- [x] **VF-025 — Endpoint: POST /sessions/{id}/plan/decision (approve/reject)**
  - Record user approval/rejection and trigger either execution or revision workflow.
  - File: `apps/api/vibeforge_api/routers/sessions.py:127`
  - Verification: Phase transition logic in place (MVP)

- [x] **VF-026 — Endpoint: GET /sessions/{id}/progress (progress/events)**
  - Expose progress snapshots and/or event stream so UI can show live status.
  - File: `apps/api/vibeforge_api/routers/sessions.py:155`
  - Verification: `pytest tests/test_sessions.py::test_get_progress`

- [x] **VF-027 — Endpoint: POST /sessions/{id}/clarifications (submitClarificationChoice)**
  - Accept user choices for clarification questions and feed them back into the coordinator/agent loop.
  - **Files:**
    - `apps/api/vibeforge_api/routers/sessions.py:242` (GET /clarification endpoint)
    - `apps/api/vibeforge_api/routers/sessions.py:277` (POST /clarification endpoint - VF-027)
    - `apps/api/vibeforge_api/models/requests.py:21` (ClarificationAnswerRequest model)
    - `apps/api/vibeforge_api/models/responses.py:76` (ClarificationResponse, ClarificationOption models)
    - `apps/api/vibeforge_api/core/session.py:36` (added pending_clarification and clarification_answer fields)
  - **Implementation:**
    - GET endpoint returns pending clarification question with options (question, context, options array)
    - POST endpoint validates answer against allowed options and clears pending clarification
    - Transitions session back to EXECUTION phase after accepting answer
    - Session model tracks pending_clarification (dict) and clarification_answer (str)
  - **Tests:** `apps/api/tests/test_sessions.py` (7 new clarification tests)
  - **Verification:** `cd apps/api && pytest tests/test_sessions.py -k clarification -v` (7 passed), `pytest -v` (162 total passed)

- [x] **VF-028 — Endpoint: GET /sessions/{id}/result (final summary)**
  - Return completion summary and run instructions when the session reaches COMPLETE.
  - File: `apps/api/vibeforge_api/routers/sessions.py:236`
  - Returns ResultResponse with workspace path, generated files, run instructions, summary
  - Verification: `pytest tests/test_e2e_demo.py::test_result_endpoint_wrong_phase`, `test_result_endpoint_nonexistent_session`

- [x] **VF-029 — API validation + error mapping (bad phase, invalid session, schema violations)**
  - Provide consistent errors for invalid inputs, missing sessions, and wrong-phase calls to keep UI simple and predictable.
  - Files: Phase validation in all endpoints; HTTPException with detail messages
  - Verification: `pytest tests/test_sessions.py::test_get_question_wrong_phase`, `test_session_not_found`


### 03 Session Coordinator (Factory Brain)

- [x] **VF-030 — Implement Session model + phases enum**
  - Define the Session aggregate containing phase, pointers to artifacts (IntentProfile/BuildSpec/TaskGraph), and error history.
  - **File:** `apps/api/vibeforge_api/core/session.py` (Session class)
  - **Features:**
    - Session ID (UUID), phase tracking (SessionPhase enum)
    - Timestamps (created_at, updated_at) with UTC timezone
    - Questionnaire state (current_question_index, answers dict)
    - Artifact pointers (intent_profile, build_spec, concept, task_graph)
    - Execution state (completed_task_ids, failed_task_ids, active_task_id, logs)
    - Clarification state (pending_clarification, clarification_answer)
    - **Error history** (error_history list with timestamp, task_id, error_message, phase)
    - Methods: update_phase(), add_answer(), add_log(), add_error()
  - **Tests:** `apps/api/tests/test_session_model.py` (15 comprehensive tests)
  - **Verification:** `cd apps/api && pytest tests/test_session_model.py -v` (15 passed)

- [x] **VF-031 — Implement SessionStore (in-memory) + persistence seam interface**
  - Store sessions in memory for MVP, but define an interface so you can later persist sessions to disk/DB without changing core logic.
  - **File:** `apps/api/vibeforge_api/core/session.py` (SessionStoreInterface + SessionStore)
  - **Interface:** SessionStoreInterface (abstract base class)
    - Methods: create_session(), get_session(id), update_session(session), delete_session(id), list_sessions()
    - Defines persistence seam for future disk/DB implementations
  - **Implementation:** SessionStore (implements SessionStoreInterface)
    - In-memory storage using dict (_sessions: dict[str, Session])
    - Full CRUD operations + listing
    - Global instance (session_store) for MVP
    - Lazy initialization, isolated per-instance
  - **Tests:** `apps/api/tests/test_session_store.py` (19 comprehensive tests)
  - **Verification:** `cd apps/api && pytest tests/test_session_store.py -v` (19 passed), `pytest -v` (219 total passed)

- [x] **VF-032 — SessionCoordinator: startSession() + phase initialization**
  - Orchestrate workspace/artifact initialization and set the session to QUESTIONNAIRE.
  - **Implementation:**
    - Created `orchestration/coordinator/session_coordinator.py` (SessionCoordinator class)
    - Implemented `start_session()` method with workspace initialization and logging
    - Dependencies: SessionStore, WorkspaceManager, QuestionnaireEngine, SpecBuilder
    - Error handling for workspace initialization failures
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorStartSession` (3 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorStartSession -v` (3 passed)

- [x] **VF-033 — SessionCoordinator: questionnaire step loop (nextQuestion/applyAnswer/finalize)**
  - Drive questionnaire progression and finalize IntentProfile when complete.
  - **Implementation:**
    - Implemented `get_next_question(session_id)` - retrieves next question from QuestionnaireEngine
    - Implemented `submit_answer(session_id, question_id, answer)` - validates and stores answers
    - Implemented `finalize_questionnaire(session_id)` - generates IntentProfile and transitions to BUILD_SPEC phase
    - Phase validation ensures QUESTIONNAIRE phase before operations
    - Answer validation via QuestionnaireEngine.validate_answer()
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorQuestionnaire` (8 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorQuestionnaire -v` (8 passed)

- [x] **VF-034 — SessionCoordinator: buildSpec stage**
  - Convert IntentProfile to BuildSpec (deterministic), including idea seed + policy guardrails.
  - **Implementation:**
    - Implemented `generate_build_spec(session_id)` - converts IntentProfile → BuildSpec deterministically
    - Validates BUILD_SPEC phase before generation
    - Ensures IntentProfile exists before BuildSpec generation
    - Persists BuildSpec to artifacts/build_spec.json via ArtifactStore
    - Transitions session to IDEA phase after BuildSpec generation
    - Uses SpecBuilder.fromIntent() for deterministic transformation
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorBuildSpec` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorBuildSpec -v` (5 passed)

- [x] **VF-035 — SessionCoordinator: concept generation stage**
  - Call Orchestrator to generate concept doc and structured concept JSON, then run gates and request clarifications if needed.
  - **Implementation:**
    - Added `generate_concept(session_id)` method to SessionCoordinator
    - Calls `await self.orchestrator.generateConcept(build_spec)` to generate ConceptDoc
    - Validates IDEA phase before concept generation
    - Persists concept to `artifacts/concept.json` via ArtifactStore
    - Transitions IDEA → PLAN_REVIEW after successful generation
    - Error handling stores failures in session.error_history without changing phase
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorConcept` (4 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorConcept -v` (4 passed)

- [x] **VF-036 — SessionCoordinator: plan proposal + plan approval stage**
  - Generate TaskGraph, run plan gates, present plan summary, and wait for explicit approval.
  - **Implementation:**
    - Added `generate_plan(session_id)` method - generates TaskGraph from BuildSpec + Concept
    - Calls `await self.orchestrator.createTaskGraph(build_spec, concept)` to generate TaskGraph
    - Validates TaskGraph DAG via `task_graph.validate_dag()`
    - Persists TaskGraph to `artifacts/task_graph.json` via ArtifactStore
    - Remains in PLAN_REVIEW phase awaiting user approval
    - Added `get_plan_summary(session_id)` - formats TaskGraph for UI display (task_count, task_list, scope, constraints)
    - Added `approve_plan(session_id)` - transitions PLAN_REVIEW → EXECUTION
    - Added `reject_plan(session_id, reason)` - clears TaskGraph and transitions PLAN_REVIEW → IDEA for regeneration
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorPlan` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorPlan -v` (5 passed)

- [x] **VF-037 — SessionCoordinator: executeNextTask() loop**
  - Execute the DAG sequentially: schedule task, dispatch to agent role, apply diff, run verifications, mark done/failed.
  - **Implementation:**
    - `orchestration/coordinator/session_coordinator.py` - Added execute_next_task() method (~260 lines)
    - Orchestrates: TaskMaster.scheduleNext() → Distributor.route() → AgentFramework.runTask() → Gates → PatchApplier → VerifierSuite → TaskMaster.markDone/markFailed()
    - Handles retry logic with escalation (worker → powerful worker → fixer)
    - Returns all_tasks_complete when ready for finalization
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorExecution` (6 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorExecution -v` (6 passed)

- [x] **VF-038 — SessionCoordinator: finalize() global verification + summary**
  - Run global verification steps and request final summary from orchestrator; transition session to COMPLETE.
  - **Implementation:**
    - `orchestration/coordinator/session_coordinator.py` - Added finalize_session() method (~130 lines)
    - Runs VerifierSuite.run_global_verification() (build + test)
    - Calls Orchestrator.summarize() for RunSummary
    - Falls back to hardcoded summary if orchestrator fails
    - Transitions EXECUTION → COMPLETE
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorFinalize` (4 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorFinalize -v` (2 passed, 2 require npm)

- [x] **VF-039 — SessionCoordinator: abort/reset session flows**
  - Support user-initiated abort and controlled reset/retry paths without leaving the system in an inconsistent state.
  - **Implementation:**
    - `orchestration/coordinator/session_coordinator.py` - Added abort_session() method (~60 lines)
    - Stops active task execution (marks failed)
    - Preserves all artifacts and workspace
    - Transitions to FAILED state (aborted)
    - Returns paths to preserved artifacts
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorAbort` (3 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorAbort -v` (3 passed)


### 04 Questionnaire Engine

- [x] **VF-040 — Define QuestionBank (audience/platform/domains/vibe/constraints/budgets)**
  - Create the structured question set and allowed answers that produce IntentProfile deterministically (no free text).
  - **Implementation:** QuestionBank defined in `apps/api/vibeforge_api/core/questionnaire.py`
  - **Questions:** 3 structured questions covering audience, platform, complexity
  - **Question types:** radio, select, checkbox, slider (all validated)
  - **MVP-sufficient:** Covers key dimensions; additional questions deferred to post-MVP
  - **Verify:** `pytest tests/test_sessions.py -k questionnaire -v`

- [x] **VF-041 — Implement QuestionnaireEngine.nextQuestion() (adaptive branching)**
  - Select the next question based on prior answers to keep questionnaire short but informative.
  - **Implementation:** `get_next_question()` method in QuestionnaireEngine
  - **Approach:** Sequential ordering (MVP); adaptive branching deferred to post-MVP
  - **Features:** Tracks current index, returns next question, marks final question
  - **Verify:** `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result -v`

- [x] **VF-042 — Implement QuestionnaireEngine.applyAnswer() + validation**
  - Validate answers against allowed options and update session questionnaire state.
  - **Implementation:** `validate_answer()` method in QuestionnaireEngine
  - **Validation:** Checks answers against allowed option values for each question type
  - **Supported types:** radio, select, checkbox (list), slider (range)
  - **State tracking:** Session questionnaire state updated via API endpoints
  - **Verify:** `pytest tests/test_sessions.py::test_submit_invalid_answer -v`

- [x] **VF-043 — Implement QuestionnaireEngine.finalize() -> IntentProfile (schema-validated)**
  - Produce the final IntentProfile object and validate it against the schema to ensure stability downstream.
  - File: `apps/api/vibeforge_api/core/questionnaire.py` (finalize() method)
  - Maps questionnaire answers to IntentProfile structure
  - Verification: `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result`


### 05 Spec Builder + Seed/Twist

- [x] **VF-050 — Define StackPreset allowlist (MVP: 1 web stack)**
  - Define at least one stack preset (e.g., Vite+React) including build/test/run commands and runtime assumptions.
  - **File:** `apps/api/vibeforge_api/core/spec_builder.py:41` (_pick_stack function)
  - **Presets implemented:**
    - WEB_VITE_REACT_TS (Node 20, npm, Vite+React+TypeScript)
    - CLI_PYTHON (Python 3.11, pip, pytest)
  - **Verify:** `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result` (stack preset used in BuildSpec)

- [x] **VF-051 — Implement SpecBuilder.fromIntent(IntentProfile) -> BuildSpec**
  - Deterministically pin platform, stack preset, scope budgets, and guardrails based on IntentProfile.
  - File: `apps/api/vibeforge_api/core/spec_builder.py`
  - Converts IntentProfile to BuildSpec deterministically
  - Derives seed, picks stack, genre, twists, scope budgets, policies
  - Verification: `pytest tests/test_e2e_demo.py` (BuildSpec created and validated)

- [x] **VF-052 — Implement DeterministicSeedDeriver (replayable)**
  - Derive a deterministic seed from IntentProfile to keep 'randomness' reproducible and testable.
  - **File:** `apps/api/vibeforge_api/core/spec_builder.py:14` (_derive_seed function)
  - **Implementation:** SHA256 hash of session_id → 64-bit integer → modulo 2^31 for deterministic seed
  - **Verify:** `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result` (deterministic BuildSpec generation)

- [x] **VF-053 — Implement IdeaSeedPicker (genre + up to 2 twist cards)**
  - Choose genre + twist cards from allowlists within constraints; record them into BuildSpec.
  - **File:** `apps/api/vibeforge_api/core/spec_builder.py:57` (_pick_idea_seed function)
  - **Implementation:** Deterministic selection of genre (PRODUCTIVITY, GAMING, SOCIAL, CREATIVE, EDUCATIONAL) and 1-2 twist cards (RETRO, MINIMALIST, DARK, etc.) using derived seed
  - **Verify:** `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result` (ideaSeed populated in BuildSpec)

- [x] **VF-054 — BuildSpec validation + persistence (ArtifactStore)**
  - Validate BuildSpec against schema and persist as a stable contract before any model calls occur.
  - **File:** `apps/api/vibeforge_api/routers/sessions.py:67` (BuildSpec created and stored in artifacts)
  - **Implementation:** BuildSpec generated via SpecBuilder.from_intent(), validated against Pydantic model, stored in artifact store
  - **Verify:** `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result` (BuildSpec persisted and retrievable)


### 06 Model Layer (Cloud-first, local later)

- [x] **VF-060 — Define LlmClient interface + LlmRequest/LlmResponse types**
  - Create a provider-agnostic interface for model calls so OpenAI and local backends can be swapped without touching execution logic.
  - **Files:**
    - `models/base/llm_client.py` (LlmClient abstract base class, LlmMessage, LlmRequest, LlmResponse, LlmUsage dataclasses)
    - `models/base/__init__.py` (module exports)
  - **Design:**
    - LlmMessage: role (system/user/assistant) + content
    - LlmRequest: messages, model, temperature, max_tokens, stop_sequences, metadata
    - LlmResponse: content, model, finish_reason, usage, metadata
    - LlmUsage: prompt_tokens, completion_tokens, total_tokens
    - LlmClient: abstract base with complete() and get_provider_name() methods
  - **Tests:** `apps/api/tests/test_model_layer.py` (5 tests for types and interface)
  - **Verification:** `cd apps/api && pytest tests/test_model_layer.py::TestLlmTypes -v`, `pytest tests/test_model_layer.py::TestLlmClientInterface -v`

- [x] **VF-061 — Implement OpenAiProvider (MVP)**
  - Implement the MVP model client using OpenAI API. Keep prompts and routing outside this class so it stays a thin adapter.
  - **Files:**
    - `models/openai/provider.py` (OpenAiProvider class)
    - `models/openai/__init__.py` (module exports)
    - `apps/api/requirements.txt` (added openai==1.54.0)
    - `apps/api/pytest.ini` (added pythonpath for models/ directory)
  - **Implementation:**
    - Uses AsyncOpenAI client from openai Python SDK
    - Maps LlmRequest → OpenAI chat.completions.create format
    - Maps OpenAI response → LlmResponse with usage tracking
    - Handles API errors with context
    - Supports API key from param or OPENAI_API_KEY env var
    - Supports custom base URL for proxies/testing
  - **Tests:** `apps/api/tests/test_model_layer.py` (7 OpenAiProvider tests with mocking)
  - **Verification:** `cd apps/api && pytest tests/test_model_layer.py::TestOpenAiProvider -v` (7 passed)

- [x] **VF-062 — Implement ModelProviderRegistry (config-driven)**
  - Allow selecting provider + model by config. This is the switch you'll flip when moving to local models later.
  - **Files:**
    - `models/registry.py` (ModelProviderRegistry class, global registry instance)
    - `configs/models/providers.json` (provider configuration)
  - **Implementation:**
    - register_provider(name, config): Register provider configuration
    - get_provider(name): Get or create provider instance (lazy-loaded, cached)
    - list_providers(): List all registered provider names
    - get_default_model(provider_name): Get default model from config
    - Supports provider types: "openai" (extensible for claude, local, etc.)
    - Config includes: type, api_key, base_url, timeout, default_model
  - **Tests:** `apps/api/tests/test_model_registry.py` (11 comprehensive registry tests)
  - **Verification:** `cd apps/api && pytest tests/test_model_registry.py -v` (11 passed), `pytest -v` (185 total passed)

- [x] **VF-063 — Implement ModelRouter policy (role/complexity/failures -> modelRef)**
  - Route calls to the right model choice based on role (orchestrator/worker/fixer/reviewer), complexity, and retry history.
  - **Files:**
    - `models/router.py` (RoutingContext, ModelRouter, get_model_router)
    - `configs/models/routing.json` (routing rules for all roles + escalation policy)
  - **Features:** Config-driven routing, escalation to stronger models on failures, temperature adjustment
  - **Tests:** `apps/api/tests/test_model_router.py` (17 comprehensive tests)
  - **Verification:** `cd apps/api && pytest tests/test_model_router.py -v` (17 passed)

- [x] **VF-064 — Implement OutputValidator (strict JSON schema validation)**
  - Validate model outputs against schemas and fail fast if malformed. This is a major reliability lever.
  - **File:** `models/validation.py` (OutputValidator, ValidationResult, validate_response)
  - **Features:** JSON parsing with markdown extraction, schema validation with jsonschema, detailed error messages
  - **Dependencies:** Added `jsonschema==4.23.0` to requirements.txt
  - **Tests:** `apps/api/tests/test_output_validator.py` (16 comprehensive tests)
  - **Verification:** `cd apps/api && pytest tests/test_output_validator.py -v` (16 passed)

- [x] **VF-065 — Implement OutputRepair (retry/repair strategy for malformed outputs)**
  - Implement structured 'repair' retries (tell the model what failed validation) so the system can recover without manual intervention.
  - **File:** `models/repair.py` (OutputRepair, RepairFailedError, repair_response)
  - **Features:** Repair prompts with validation errors, max attempts (default: 2), temperature escalation, metadata tracking
  - **Tests:** `apps/api/tests/test_output_repair.py` (11 comprehensive tests)
  - **Verification:** `cd apps/api && pytest tests/test_output_repair.py -v` (11 passed)

- [x] **VF-066 — Stub LocalProvider interface (no implementation yet)**
  - Add a placeholder local provider adapter (Ollama/llama.cpp/vLLM later) to keep the architecture seam visible and tested.
  - **Files:**
    - `models/local/provider.py` (LocalProvider for Ollama/llama.cpp/vLLM/MLX)
    - `models/local/__init__.py` (module exports)
    - `models/registry.py` (updated to support "local" provider type)
  - **Features:** Implements LlmClient interface, raises NotImplementedError (MVP stub), supports multiple backends
  - **Tests:** `apps/api/tests/test_local_provider.py` (16 comprehensive tests)
  - **Verification:** `cd apps/api && pytest tests/test_local_provider.py -v` (16 passed), registry integration validated


### 07 Orchestrator

- [x] **VF-070 — Orchestrator prompt templates: Concept generation (JSON + Markdown)**
  - Write templates that produce a structured concept JSON plus a human-readable concept doc, aligned to BuildSpec constraints.
  - **Files:** `orchestration/prompts.py` (CONCEPT_GENERATION_TEMPLATE with Jinja2)
  - **Features:** Comprehensive template with BuildSpec context, JSON schema requirements, complexity-specific guidance
  - **Verify:** Tested through Orchestrator.generateConcept() integration tests

- [x] **VF-071 — Orchestrator prompt templates: TaskGraph generation (DAG + constraints)**
  - Write templates that generate a TaskGraph DAG with per-task constraints, inputs, outputs, and verification steps.
  - **Files:** `orchestration/prompts.py` (TASKGRAPH_GENERATION_TEMPLATE)
  - **Features:** DAG structure with dependencies, role assignment, verification specs, constraints by task
  - **Verify:** Tested through Orchestrator.createTaskGraph() with DAG validation

- [x] **VF-072 — Orchestrator prompt templates: Run summary**
  - Write templates for summarizing what was built, how to run it, and what limitations remain.
  - **Files:** `orchestration/prompts.py` (RUN_SUMMARY_TEMPLATE)
  - **Features:** Status, summary, files, verification results, run instructions, limitations
  - **Verify:** Tested through Orchestrator.summarize() integration tests

- [x] **VF-073 — Implement Orchestrator.generateConcept(BuildSpec)**
  - Call the model to generate the concept; validate output and return either concept or clarification requests.
  - **Files:** `orchestration/orchestrator.py` (Orchestrator.generateConcept method)
  - **Features:** Template rendering, ModelRouter selection, OutputValidator + OutputRepair integration, ConceptDoc parsing
  - **Verify:** `cd apps/api && pytest tests/test_orchestrator.py::TestOrchestrator::test_generate_concept_success -v`

- [x] **VF-074 — Implement Orchestrator.createTaskGraph(BuildSpec, ConceptDoc)**
  - Call the model to produce TaskGraph; validate DAG and enforce scope/command policies via gates.
  - **Files:** `orchestration/orchestrator.py` (Orchestrator.createTaskGraph method)
  - **Features:** TaskGraph generation with DAG validation, cycle detection, dependency validation
  - **Verify:** `cd apps/api && pytest tests/test_orchestrator.py::TestOrchestrator::test_create_task_graph_validates_dag -v`

- [x] **VF-075 — Implement Orchestrator.summarize(artifacts)**
  - Generate the final summary response from stored artifacts (tasks, diffs, verification results).
  - **Files:** `orchestration/orchestrator.py` (Orchestrator.summarize method)
  - **Features:** RunSummary generation from artifacts with lower temperature for consistency
  - **Verify:** `cd apps/api && pytest tests/test_orchestrator.py::TestOrchestrator::test_summarize_success -v`


### 08 Gates & Policies

- [x] **VF-080 — Implement Gate interface + GatePipeline composition**
  - Create a consistent gate interface and a pipeline that can evaluate context and yield ok/warn/block results.
  - **Files:** `apps/api/vibeforge_api/core/gates.py` (Gate, GateContext, GatePipeline)
  - **Tests:** `apps/api/tests/test_gates.py` (6 pipeline tests)
  - **Verify:** `pytest tests/test_gates.py::test_gate_pipeline -v`

- [x] **VF-081 — Implement FeasibilityGate (scope budgets, screens/entities/diff size)**
  - Enforce BuildSpec scope budgets and stop unrealistic plans early (before code generation).
  - **Files:** `apps/api/vibeforge_api/core/gates.py` (FeasibilityGate)
  - **Tests:** `apps/api/tests/test_gates.py::TestFeasibilityGate` (5 tests)
  - **Verify:** `pytest tests/test_gates.py::TestFeasibilityGate -v`

- [x] **VF-082 — Implement RiskGate (command families, network rule enforcement)**
  - Ensure requested commands fit allowlisted families and that network access rules are respected.
  - **Files:** `apps/api/vibeforge_api/core/gates.py` (RiskGate)
  - **Tests:** `apps/api/tests/test_gates.py::TestRiskGate` (6 tests)
  - **Verify:** `pytest tests/test_gates.py::TestRiskGate -v`

- [x] **VF-083 — Implement PolicyGate (forbidden regex patterns, path constraints)**
  - Block unsafe content patterns and prevent file operations outside the workspace.
  - **Files:** `apps/api/vibeforge_api/core/gates.py` (PolicyGate)
  - **Tests:** `apps/api/tests/test_gates.py::TestPolicyGate` (6 tests)
  - **Verify:** `pytest tests/test_gates.py::TestPolicyGate -v`

- [x] **VF-084 — Implement DiffAndCommandGate (max files/lines, forbidden content in diff)**
  - Validate AgentResult diffs and commands before apply/run; enforce per-task constraints.
  - **Files:** `apps/api/vibeforge_api/core/gates.py` (DiffAndCommandGate)
  - **Tests:** `apps/api/tests/test_gates.py::TestDiffAndCommandGate` (6 tests)
  - **Verify:** `pytest tests/test_gates.py::TestDiffAndCommandGate -v`

- [x] **VF-085 — Gate-to-UI adapter (warnings/blockers + multiple-choice questions)**
  - Translate gate output into UI-friendly messages and multiple-choice clarification questions where needed.
  - **Files:** `apps/api/vibeforge_api/core/gates.py` (GateAdapter)
  - **Tests:** `apps/api/tests/test_gates.py::TestGateAdapter` (5 tests)
  - **Verify:** `pytest tests/test_gates.py::TestGateAdapter -v`


### 09 TaskGraph + TaskMaster + Distributor

- [x] **VF-090 — Define TaskGraph types + parser + schema validation**
  - Implement types and schema validation for TaskGraph so the scheduler can rely on strong invariants.
  - **File:** `orchestration/models.py:110` (TaskGraph.validate_dag enhanced)
  - **Implementation:**
    - Enhanced validate_dag() with comprehensive checks:
      - Duplicate task ID detection
      - Non-existent dependency detection
      - Cycle detection using DFS
      - Role validation (worker/foreman/reviewer)
      - Verification type validation (build/test/lint/manual/integration)
    - Detailed error messages for each validation failure
  - **Tests:** `apps/api/tests/test_taskgraph.py::TestTaskGraphValidation` (8 tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskgraph.py::TestTaskGraphValidation -v` (8 passed)

- [x] **VF-091 — Validate DAG (no cycles) + dependency resolver**
  - Reject cyclical plans and compute ready-task sets deterministically.
  - **File:** `orchestration/models.py:192` (get_execution_order, get_ready_tasks methods)
  - **Implementation:**
    - `get_execution_order()`: Topological sort using Kahn's algorithm with deterministic ordering (alphabetical tie-breaking)
    - `get_ready_tasks(completed, running, failed)`: Returns tasks ready to run based on dependency satisfaction
    - Both methods ensure deterministic, reproducible task ordering
    - Raises ValueError on cyclical graphs
  - **Tests:** `apps/api/tests/test_taskgraph.py::TestTaskGraphDependencyResolution` (11 tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskgraph.py::TestTaskGraphDependencyResolution -v` (11 passed)

- [x] **VF-092 — Implement TaskMaster.enqueue(TaskGraph)**
  - Load the validated task graph into the scheduler and initialize task statuses.
  - **File:** `runtime/task_master.py:64` (TaskMaster.enqueue method)
  - **Implementation:**
    - Validates TaskGraph using validate_dag()
    - Computes execution order using get_execution_order()
    - Initializes TaskExecution tracking for each task (status: PENDING)
    - Marks root tasks (no dependencies) as READY
    - Stores max_retries configuration per task
  - **Tests:** `apps/api/tests/test_taskmaster.py::TestTaskMasterEnqueue` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterEnqueue -v` (5 passed)

- [x] **VF-093 — Implement TaskMaster.scheduleNext() (ready tasks only)**
  - Select the next runnable task based on dependencies and failure policy.
  - **File:** `runtime/task_master.py:99` (TaskMaster.scheduleNext method)
  - **Implementation:**
    - Returns first READY task in execution order
    - Marks selected task as RUNNING
    - Increments attempt counter
    - Sets started_at timestamp
    - Returns None if no tasks are READY
    - Respects topological ordering
  - **Tests:** `apps/api/tests/test_taskmaster.py::TestTaskMasterScheduleNext` (6 tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterScheduleNext -v` (6 passed)

- [x] **VF-094 — Implement TaskMaster.markDone/markFailed + retry counters**
  - Track completion/failure and retry history; provide hooks for escalation policies.
  - **File:** `runtime/task_master.py:142` (markDone, markFailed methods)
  - **Implementation:**
    - `markDone(task_id, result)`: Marks task as DONE, stores result, sets completed_at, updates downstream tasks to READY
    - `markFailed(task_id, error_message)`: Handles failures with retry logic
      - If attempts < max_retries: resets task to READY for retry, returns True
      - If max_retries exceeded: marks task as FAILED, skips all downstream tasks, sets completed_at, returns False
    - `_skip_downstream_tasks()`: Recursively marks dependent tasks as SKIPPED
    - `get_status()`: Returns execution summary (total, completed, running, ready, pending, failed, skipped)
    - Configurable max_retries (default: 2)
  - **Tests:** `apps/api/tests/test_taskmaster.py` (11 markDone/markFailed tests + 2 integration tests)
  - **Verify:** `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterMarkDone -v` (5 passed), `cd apps/api && pytest tests/test_taskmaster.py::TestTaskMasterMarkFailed -v` (6 passed)

- [x] **VF-095 — Implement Distributor.route(task) -> AgentRole (role hint rules)**
  - Assign each task to a role based on explicit hints and objective heuristics.
  - **File:** `runtime/distributor.py:33` (Distributor.route method)
  - **Implementation:**
    - Routes tasks to agent roles based on task.role from TaskGraph
    - Selects model tier (fast/balanced/powerful) - defaults to balanced
    - Validates role is valid (worker/foreman/reviewer)
    - Returns AgentRole with role, model_tier, and reason
  - **Tests:** `apps/api/tests/test_distributor.py::TestDistributorRouting` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_distributor.py::TestDistributorRouting -v` (5 passed)

- [x] **VF-096 — Implement escalation policy (failures -> stronger role/model)**
  - Escalate to fixer/reviewer or stronger model after repeated failures to avoid infinite loops.
  - **File:** `runtime/distributor.py:72` (_escalate method)
  - **Implementation:**
    - Escalation ladder:
      - 0 failures: use task.role with balanced model
      - 1 failure: same role, upgrade to powerful model
      - 2+ failures: escalate to fixer role with powerful model
    - Prevents infinite retry loops by capping at fixer + powerful
  - **Tests:** `apps/api/tests/test_distributor.py::TestDistributorEscalation` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_distributor.py::TestDistributorEscalation -v` (5 passed)


### 10 Agent Framework Adapter (pluggable)

- [x] **VF-100 — Define AgentFramework.runTask() interface (role prompt + tools + context)**
  - Create an interface for running an agent role against a task, producing a standard AgentResult.
  - **File:** `models/agent_framework.py:12` (AgentFramework abstract class, AgentResult dataclass)
  - **Implementation:**
    - `AgentFramework` ABC with `runTask(task, role, context)` abstract method
    - `AgentResult` dataclass with success/outputs/logs/error_message
    - `get_framework_name()` method for framework identification
    - Pluggable adapter pattern for multiple framework backends
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestAgentResult` (3 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestAgentResult -v` (3 passed)

- [x] **VF-101 — Implement MVP AgentFrameworkAdapter (direct model call + strict AgentResult)**
  - Implement the simplest adapter: call the provider directly with role prompt and require AgentResult JSON output.
  - **File:** `models/agent_framework.py:51` (DirectLlmAdapter class)
  - **Implementation:**
    - Calls LLM directly with role-specific prompts (hardcoded for MVP)
    - Uses ModelRouter for model selection
    - Creates LlmRequest with system + user prompts
    - Returns AgentResult with success status and outputs
    - Handles LLM failures gracefully
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestDirectLlmAdapter` (7 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestDirectLlmAdapter -v` (7 passed)

- [x] **VF-102 — Implement AgentRegistry (role -> prompt/tool policy/output schema)**
  - Centralize role prompts, tool permissions, and output schemas so agent behavior is consistent and auditable.
  - **File:** `runtime/agent_registry.py:12` (AgentRegistry class, RoleConfig dataclass)
  - **Implementation:**
    - Pre-configured roles: worker, foreman, reviewer, fixer
    - Each role has: system_prompt, prompt_template, output_schema, allowed_tools
    - `get_role_config(role)` retrieves configuration
    - `register_role(config)` allows custom role registration
    - `has_role(role)` checks if role exists
    - Global singleton via `get_agent_registry()`
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestAgentRegistry` (10 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestAgentRegistry -v` (10 passed)

- [x] **VF-103 — Add placeholder adapters (LangGraph/CrewAI/AutoGen) as stubs**
  - Add stubs for future framework-backed implementations so the seam is explicit and easy to fill later.
  - **File:** `models/agent_framework_stubs.py` (LangGraphAdapter, CrewAIAdapter, AutoGenAdapter)
  - **Implementation:**
    - All stubs implement AgentFramework interface
    - `runTask()` raises NotImplementedError with helpful message
    - `get_framework_name()` returns name with "(stub)" suffix
    - Ready for future integration when frameworks are adopted
  - **Tests:** `apps/api/tests/test_agent_framework.py::TestAgentFrameworkStubs` (7 tests)
  - **Verify:** `cd apps/api && pytest tests/test_agent_framework.py::TestAgentFrameworkStubs -v` (7 passed)


### 11 Workspace + Patching

- [x] **VF-110 — Implement WorkspaceManager.initRepo(sessionId, template)**
  - Create the workspace directory and initialize a repo from a template or minimal scaffold.
  - File: `apps/api/vibeforge_api/core/workspace.py`
  - Verification: `pytest tests/test_workspace.py` (12 tests pass)

- [x] **VF-111 — Implement workspace layout (repo/ artifacts/) per session**
  - Standardize where code lives and where logs/artifacts are stored for each session.
  - File: `apps/api/vibeforge_api/core/workspace.py` (get_repo_path, get_artifacts_path)
  - Verification: `pytest tests/test_workspace.py::test_init_repo_creates_layout`

- [x] **VF-112 — Optional: initialize git repo + commit snapshots**
  - Initialize git and commit after each successful task to enable rollback and clearer diff review.
  - Files: `apps/api/vibeforge_api/core/workspace.py`, `apps/api/tests/test_workspace.py`
  - Verify: `cd apps/api && pytest`

- [x] **VF-113 — Implement PatchApplier (unified diff apply)**
  - Apply unified diffs safely and deterministically; return actionable errors when apply fails.
  - File: `apps/api/vibeforge_api/core/patch.py`
  - Verification: `pytest tests/test_patch.py` (11 tests for parsing and application)

- [x] **VF-114 — PatchApplier safety: restrict paths to repo root + dry-run mode**
  - Prevent path traversal and enable a dry-run to detect conflicts before mutating files.
  - File: `apps/api/vibeforge_api/core/patch.py` (validate_path, dry_run parameter)
  - Verification: `pytest tests/test_patch.py::test_validate_path_rejects_traversal`, `test_apply_patch_dry_run`

- [x] **VF-115 — Persist patch metadata per task (ArtifactStore)**
  - Record diff, apply outcome, and affected files for traceability and later debugging.
  - File: `apps/api/vibeforge_api/core/artifacts.py`
  - Verification: `pytest tests/test_artifacts.py` (13 tests for metadata persistence)


### 12 Verification + Command Runner + AppRunner

- [x] **VF-120 — Implement CommandRunner (allowlist enforcement, timeouts, output capture)**
  - Run shell commands safely: enforce allowlists, apply timeouts, and capture stdout/stderr for UI and artifacts.
  - File: `apps/api/vibeforge_api/core/command_runner.py`
  - Features: Command family allowlists, timeout handling, stdout/stderr capture, working directory support
  - Verification: `pytest tests/test_command_runner.py -v` (15 tests passed)

- [x] **VF-121 — Implement BuildVerifier (stack preset build command)**
  - Verify the project builds using commands defined by the selected stack preset.
  - File: `apps/api/vibeforge_api/core/verifiers.py` (BuildVerifier class)
  - Maps presets to build commands (npm run build, mvn package, etc.)
  - Verification: `pytest tests/test_verifiers.py::TestBuildVerifier -v` (6 tests passed)

- [x] **VF-122 — Implement TestVerifier (stack preset test command)**
  - Verify tests pass and produce readable failure outputs when they don't.
  - File: `apps/api/vibeforge_api/core/verifiers.py` (TestVerifier class)
  - Maps presets to test commands (npm test, pytest, etc.) and parses failures
  - Verification: `pytest tests/test_verifiers.py::TestTestVerifier -v` (5 tests passed)

- [x] **VF-123 — Implement SmokeVerifier (server starts and/or route responds)**
  - Run a lightweight end-to-end check (start server or hit a route) to confirm the app can run locally.
  - Files: `apps/api/vibeforge_api/core/verifiers.py`, `apps/api/tests/test_verifiers.py`
  - Verification: `PYTHONPATH=/workspace/v-forge pytest`

- [x] **VF-124 — Implement VerifierSuite (per-task + global verification)**
  - Orchestrate verification steps after each task and at the end of the run based on TaskGraph definitions.
  - File: `apps/api/vibeforge_api/core/verifiers.py` (VerifierSuite class)
  - Runs multiple verifiers, supports stop-on-failure, provides global verification (build + test)
  - Verification: `pytest tests/test_verifiers.py::TestVerifierSuite -v` (6 tests passed)

- [x] **VF-125 — Implement AppRunner.getRunInstructions() per stack preset**
  - Generate clear run instructions (install/build/dev server) and expose them in the final summary.
  - Files: `apps/api/vibeforge_api/core/app_runner.py`, `apps/api/vibeforge_api/routers/sessions.py`
  - Verification: `PYTHONPATH=/workspace/v-forge pytest`

- [x] **VF-126 — Implement AppRunner.start()/stop() dev server + stream logs**
  - Provide a ‘Run’ button that starts the app locally and streams logs back to the UI.
  - Files: `apps/api/vibeforge_api/core/app_runner.py`, `apps/api/tests/test_app_runner.py`
  - Verification: `PYTHONPATH=/workspace/v-forge pytest`


### 13 Observability (Artifacts + Event log)

- [x] **VF-130 — Formalize ArtifactStore with query APIs (filesystem JSON, per-session keys)**
  - Formalize artifact persistence with query APIs to retrieve historical session data. Currently used informally in SessionCoordinator; needs structured API for control UI.
  - Added list/metadata/delete helpers and SessionArtifactQuery for cross-session listings.
  - **Verify:** `cd apps/api && pytest tests/test_artifact_store.py -v`

- [x] **VF-131 — Implement EventLog (append-only events: phase changes, dispatches, applies, command runs)**
  - Record an append-only event stream so you can trace what happened and debug failures without guesswork.
  - Implemented structured Event dataclass + EventLog JSONL persistence with cache-backed queries.
  - **Verify:** `cd apps/api && pytest tests/test_event_log.py -v`

- [x] **VF-132 — Add "export run bundle" (zip artifacts + summary) (optional)**
  - Package repo snapshot, artifacts, and final summary into a portable bundle for sharing or archival.
  - **Priority:** Post-MVP enhancement
  - Files: `apps/api/vibeforge_api/core/run_bundle.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_run_bundle.py`, `apps/api/tests/test_control_api.py`
  - Verification: `PYTHONPATH=/workspace/v-forge pytest`

- [x] **VF-142 — Upgrade to structured progress events (phase changes, task lifecycle, verification)**
  - Emit structured, typed events for all major steps: phase transitions, task dispatch, diff applied, verification started/completed.
  - SessionCoordinator now emits workspace init, phase transitions, task lifecycle, and plan events via EventLog while retaining logs for compatibility.
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py -k event -v`

## 14 Workflow Orchestration: Happy Path (Sequence)

- [x] **VF-140 — Implement "Happy Path" orchestration contract end-to-end**
  - Ensure a single session can flow cleanly through: start → questionnaire → build spec → concept → plan review → (approve) → execution → verification → complete, returning coherent API responses at each step.
  - **Status:** ✅ COMPLETE - Implemented via VF-032 through VF-039 (SessionCoordinator full lifecycle)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py -v` (40 tests covering full flow)

- [x] **VF-141 — Add a Phase-aware API guard layer (wrong-phase handling)**
  - Centralize "wrong phase" checks so every endpoint returns consistent, user-friendly errors and does not allow illegal calls (e.g., submitting answers after PLAN_REVIEW).
  - **Status:** ✅ COMPLETE - All SessionCoordinator methods validate phase before execution
  - **Implementation:** Phase validation in every coordinator method (e.g., `if session.phase != SessionPhase.QUESTIONNAIRE: raise ValueError`)
  - **Verify:** `cd apps/api && pytest tests/test_sessions.py -k wrong_phase -v` (multiple wrong-phase tests)

- [x] **VF-143 — Persist phase transitions into the event log**
  - Record all state changes (oldPhase → newPhase + reason) into the EventLog for debugging and replayability.
  - **Depends on:** VF-131 (EventLog implementation)
  - **Files:** `orchestration/coordinator/session_coordinator.py`, `apps/api/vibeforge_api/core/event_log.py`, `apps/api/tests/test_event_log.py`, `apps/api/tests/test_session_coordinator.py`
  - **Verify:** `PYTHONPATH=/workspace/v-forge pytest`

- [x] **VF-144 — Implement "artifact checkpoints" for each stage**
  - Store a stable snapshot artifact at the end of each stage: `IntentProfile`, `BuildSpec`, `Concept`, `TaskGraph`, and final `RunSummary`, so the run can be inspected without re-running.
  - **Status:** ✅ COMPLETE - All artifacts persisted via ArtifactStore
  - **Files:** `artifacts/intent_profile.json`, `artifacts/build_spec.json`, `artifacts/concept.json`, `artifacts/task_graph.json`, `artifacts/run_summary.json`
  - **Implementation:** SessionCoordinator persists after each generation step

- [x] **VF-145 — Implement "plan preview" formatting for UI consumption**
  - Convert TaskGraph into a concise plan summary: feature list, task count, verification steps, estimated scope, and key constraints—so user can approve with confidence.
  - **Status:** ✅ COMPLETE - Implemented in VF-036 (get_plan_summary method)
  - **Returns:** task_count, task_list, verification_steps, estimated_scope, constraints
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorPlan::test_get_plan_summary_formats_correctly -v`

- [x] **VF-146 — Implement "reject plan → revise concept" loop**
  - If user rejects plan, safely return to IDEA (or PLAN_REVIEW) with a revision strategy: regenerate concept, reduce scope, or adjust stack—without losing session integrity.
  - **Status:** ✅ COMPLETE - Implemented in VF-036 (reject_plan method)
  - **Implementation:** Clears TaskGraph and transitions PLAN_REVIEW → IDEA for regeneration
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorPlan::test_reject_plan_transitions_to_idea -v`


## 15 Execution Loop: Verification Gates & Recovery (Sequence)

- [x] **VF-150 — Implement the per-task execution loop (TaskMaster → Agent → Gate → Apply → Verify)**
  - Build the core loop that schedules the next task, runs an agent to produce an AgentResult, gates it, applies the diff, runs per-task verification, and marks the task done/failed.
  - **Status:** ✅ COMPLETE - Implemented in VF-037 (execute_next_task method)
  - **Implementation:** TaskMaster.scheduleNext() → Distributor.route() → AgentFramework.runTask() → Gates → PatchApplier → VerifierSuite → TaskMaster.markDone/markFailed()
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorExecution -v` (6 tests)

- [ ] **VF-151 — Implement RepoContextLoader (task-scoped context selection)**
  - Load a bounded set of relevant files into the agent prompt based on the task's declared inputs (files-to-read), plus optionally small "supporting context" (project structure, conventions).
  - **Priority:** Post-MVP enhancement - agents currently receive full context

- [ ] **VF-152 — Implement AgentResult handling for "needs clarification"**
  - Support the agent returning multiple-choice questions; pause execution, expose questions to UI, accept user choices, then resume with the clarification answers injected into the next agent call.
  - **Status:** Partial - UI flow exists (VF-027), agent integration pending

- [x] **VF-153 — Implement Diff gate + Apply gate with structured failure reasons**
  - When a diff is blocked (policy/size/paths) or fails to apply, produce a structured failure report that can be routed to FIXER or surfaced to UI.
  - **Status:** ✅ COMPLETE - Implemented in VF-037 (gate evaluation with structured errors)
  - **Implementation:** GatePipeline evaluates PolicyGate + DiffAndCommandGate, returns GateResult with status/message
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorExecution::test_execute_next_task_handles_gate_block -v`

- [x] **VF-154 — Implement per-task verification runner (declared in TaskGraph)**
  - Execute the task's verification steps (e.g., unit tests, lint, build step) after apply. Capture stdout/stderr and store results in artifacts.
  - **Status:** ✅ COMPLETE - Implemented in VF-037 + VF-124 (VerifierSuite integration)
  - **Implementation:** VerifierSuite.run_task_verification() runs task.verification specs
  - **Verify:** `cd apps/api && pytest tests/test_verifiers.py::TestVerifierSuite -v`

- [ ] **VF-155 — Implement automatic "fix loop" policy after verification failure**
  - When verification fails, automatically generate a repair attempt strategy (e.g., create a FIXER task, escalate model, narrow diff limits, or request user choice after N failures).
  - **Status:** Partial - retry with escalation exists (VF-096), automatic FIXER task generation pending

- [x] **VF-156 — Add retry counters + escalation rules per task**
  - Track failure count per task and apply escalation: stronger role/model after repeated failures; hard-stop after max retries with a meaningful error summary.
  - **Status:** ✅ COMPLETE - Implemented in VF-094 + VF-096
  - **Implementation:** TaskMaster.markFailed() with retry counters + Distributor escalation (worker → powerful → fixer)
  - **Verify:** `cd apps/api && pytest tests/test_distributor.py::TestDistributorEscalation -v` (5 tests)

- [x] **VF-157 — Implement final global verification step-set (end of DAG)**
  - Run a final verification suite (build/test/smoke) after all tasks complete; if it fails, route back into fix loop rather than silently finishing.
  - **Status:** ✅ COMPLETE - Implemented in VF-038 (finalize_session with global verification)
  - **Implementation:** VerifierSuite.run_global_verification() runs build + test, fails session if verification fails
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorFinalize -v`

- [x] **VF-158 — Implement "completion summary" assembly from artifacts**
  - Collect and summarize what was built: features, modules, key files changed, how to run, what tests ran, and any known limitations—so user gets a coherent end report.
  - **Status:** ✅ COMPLETE - Implemented in VF-038 + VF-075
  - **Implementation:** Orchestrator.summarize() generates RunSummary from artifacts
  - **Verify:** `cd apps/api && pytest tests/test_orchestrator.py::TestOrchestrator::test_summarize_success -v`

- [x] **VF-159 — Add deterministic execution mode (replayable runs)**
  - Ensure the same inputs (IntentProfile + seed) produce the same major decisions (within reason), and record seeds + config hashes so runs can be reproduced for debugging.
  - **Status:** ✅ COMPLETE - Implemented in VF-052 (deterministic seed derivation)
  - **Implementation:** SHA256-based seed from session_id ensures reproducibility
  - **Verify:** BuildSpec generation is deterministic given same IntentProfile


## 16 State Machine: MVP Phases (State Diagram)

- [ ] **VF-160 — Encode the session state machine as a formal transition table**
  - Implement an explicit allowed-transition map (fromPhase → toPhase) to prevent accidental illegal transitions as the codebase evolves.

- [ ] **VF-161 — Implement “entry actions” per phase**
  - Define and implement what happens *on entering* each phase (e.g., BUILD_SPEC creates BuildSpec, IDEA generates concept, PLAN_REVIEW generates TaskGraph, EXECUTION starts scheduling).

- [ ] **VF-162 — Implement “exit criteria” per phase**
  - Define and enforce the condition that must be true to exit each phase (e.g., questionnaire complete, concept accepted, plan approved, all tasks done, global verification pass).

- [ ] **VF-163 — Implement FAILED terminal behavior + recovery options**
  - Define what constitutes unrecoverable failure; ensure the system transitions to FAILED cleanly, emits a final error artifact, and offers safe recovery options (restart session, reduce scope, export logs).

- [ ] **VF-164 — Implement controlled “return transitions” for fix loops**
  - Support the state-machine loop VERIFICATION → EXECUTION when final checks fail, with clear guardrails to avoid infinite loops.

- [ ] **VF-165 — Implement session abort and cleanup behavior**
  - Allow user to abort; stop active execution safely, mark session as FAILED (or ABORTED if you add it), and preserve artifacts/logs for inspection.

- [ ] **VF-166 — Add integration tests for phase transitions**
  - Write tests that simulate the main state transitions and assert the system rejects illegal transitions, emits expected events, and persists expected artifacts.

- [ ] **VF-167 — Add "resume session" capability from stored artifacts**
  - Enable restarting the API and resuming an in-progress session from artifacts/event log (initially limited scope), improving robustness and developer ergonomics.


### 17 Agent Control & Monitoring UI (Post-MVP)

- [x] **VF-170 — Control panel architecture (separate admin UI route)**
  - Create separate control panel UI distinct from end-user flow; accessible at /control or /admin route with real-time session monitoring.
  - **Why needed:** Developers need visibility into multi-agent orchestration, token usage, and execution flow
  - **Architecture:** Separate React route with WebSocket/SSE for real-time updates
  - **Dependencies:** VF-131 (EventLog), VF-142 (structured events)
  - **Completed in WP-0022:**
    - Backend: Created 4 control API endpoints (/control/sessions, /control/active, /control/sessions/{id}/status, /control/sessions/{id}/events with SSE)
    - Frontend: Created ControlPanel component at /control route with sidebar and real-time event streaming
    - Tests: 8 backend tests (test_control_api.py), UI builds successfully
    - Verification: `pytest tests/test_control_api.py -v`, `npm run build`

- [x] **VF-171 — Agent activity dashboard (live status grid)**
  - Display all active agents with current status (idle/thinking/executing), current task, model in use, and elapsed time.
  - **Features:** Grid layout with agent cards, status indicators (🟢 idle, 🟡 thinking, 🔴 executing), real-time updates
  - **Data source:** EventLog + SessionStore active_task_id
  - **Why needed:** Monitor which agents are working on what in real-time
  - Implemented AgentDashboard widget and ControlPanel integration (apps/ui/src/screens/control/widgets/AgentDashboard.tsx, apps/ui/src/screens/ControlPanel.tsx).
  - Verified via `npm run build`.

- [x] **VF-172 — Token usage visualization (per-agent, per-session, cumulative)**
  - Real-time token consumption charts: pie chart by agent role, timeline of token burn rate, cost estimates, budget alerts.
  - **Features:**
    - Pie chart: token distribution by role (orchestrator/worker/fixer)
    - Line chart: cumulative tokens over time
    - Cost calculator: tokens × pricing by model
    - Budget alerts: warn when approaching limits
  - **Data source:** LlmResponse.usage (prompt_tokens, completion_tokens, total_tokens)
  - **Why needed:** Control costs and identify inefficient prompts
  - Added token visualization widget plus token metadata events/tests (apps/ui/src/screens/control/widgets/TokenVisualization.tsx; apps/api/tests/test_token_tracking.py).
  - Verified via `pytest tests/test_token_tracking.py -v` and `npm run build`.

- [x] **VF-173 — Agent relationship graph (interactive DAG visualization)**
  - Interactive force-directed graph showing: Orchestrator → TaskMaster → Distributor → Worker/Fixer/Foreman agents with live task flow.
  - **Features:**
    - D3.js force-directed graph
    - Nodes: agents (colored by role)
    - Edges: task assignments (animated during execution)
    - Click node → show agent details
  - **Why needed:** Visualize system architecture and task routing
  - Implemented AgentGraph widget (SVG-based with drag), styling, and ControlPanel integration; edges/statuses derived from session events.
  - Verified via `cd apps/ui && npm run build` (registry blocked d3, used dependency-free SVG implementation).

- [x] **VF-174 — Execution flow timeline (Gantt-style with agent swim lanes)**
  - Horizontal timeline showing which agent executed which task, when, overlaps, retries, and escalations visually.
  - **Features:**
    - Horizontal swim lanes per agent role
    - Task bars colored by status (green: success, red: failed, yellow: retry)
    - Retry arrows showing escalation paths
    - Zoom/pan controls for long sessions
  - **Data source:** EventLog with task_started/task_completed events
  - **Why needed:** Understand execution patterns and identify bottlenecks
  - Added ExecutionTimeline widget that maps task start/complete/fail events to per-role swim lanes with duration scaling; integrated into ControlPanel.
  - Verified via `cd apps/ui && npm run build`.

- [x] **VF-175 — Gate decision log (block/warn/pass visualization)**
  - Real-time feed of gate evaluations: which gates ran, on which artifacts, decisions made, reasons for blocks/warnings.
  - **Features:**
    - Table with columns: timestamp, gate_type, artifact, decision (OK/WARN/BLOCK), reason
    - Color coding: green (OK), yellow (WARN), red (BLOCK)
    - Filter by gate type, decision
    - Click row → show full gate context
  - **Data source:** EventLog with gate_evaluated events (metadata: gate_type, decision, artifact, reason)
  - **Backend:** emit gate_evaluated from gate pipeline / SessionCoordinator evaluation path
  - **Why needed:** Debug why tasks were blocked, tune gate policies
  - Added GateLog widget and gate_evaluated event emission in SessionCoordinator.
  - Verified via `cd apps/ui && npm run build` and `cd apps/api && pytest tests/test_gate_logging.py -v`.

- [x] **VF-176 — Model router decisions (model selection rationale)**
  - Display which model was selected for each call, why (role/complexity/retry), and routing rules applied.
  - **Features:**
    - Table: timestamp, role, model_selected, reason, temperature, failure_count
    - Highlight escalations (worker → powerful → fixer)
    - Show routing rule matched
  - **Data source:** EventLog with model_routed events (metadata: rule matched, failure_count, reason)
  - **Backend:** emit model_routed from distributor/router decisions
  - **Why needed:** Understand cost/quality tradeoffs, tune routing rules
  - Added ModelRouter widget that merges model_routed with LLM response events for model + cost estimates.
  - Verified via `cd apps/ui && npm run build`.

- [x] **VF-177 — Session comparison view (multi-session metrics)**
  - Side-by-side comparison of multiple sessions: token usage, task completion rates, failure patterns, time to completion.
  - **Features:**
    - Select 2-4 sessions to compare
    - Metrics table: total_tokens, total_cost, tasks_completed, tasks_failed, duration
    - Comparative charts: token usage over time, failure rate by task
  - **Data source:** ArtifactStore query API (VF-130)
  - **Why needed:** A/B test prompt changes, identify regressions
  - Added SessionComparison widget with session selection, metrics table, and token trend sparklines.
  - Verified via `cd apps/ui && npm run build`.

- [x] **VF-178 — Event stream viewer (real-time log with filtering)**
  - Live event stream with filters: by phase, by agent, by event type (task_started, diff_applied, verification_passed, etc.).
  - **Features:**
    - Auto-scrolling event feed (newest at bottom)
    - Filters: phase, agent_role, event_type, severity
    - Search by keyword
    - Export to JSON (optional)
  - **Data source:** EventLog with WebSocket/SSE subscription
  - **Why needed:** Real-time debugging and monitoring
  - Added EventStream widget with filters, search, auto-scroll, and export controls.
  - Verified via `cd apps/ui && npm run build`.

- [x] **VF-179 — Agent prompt inspector (view actual prompts sent to LLMs)**
  - Debug view showing exact prompts sent to each agent role, with template variables expanded and context included.
  - **Features:**
    - Select task → view exact prompt sent
    - Syntax highlighting for JSON/code
    - Show template used + variables expanded
    - Copy prompt button
    - View model response alongside
  - **Data source:** EventLog with llm_request_sent events (store prompt + metadata; include redaction + size limits)
  - **Backend:** emit llm_request_sent before LLM calls; optional paging endpoint for large prompts
  - **Why needed:** Debug prompt engineering, reproduce issues
  - Added LLM request event emission, prompts endpoint, and PromptInspector widget.
  - Verified via `cd apps/ui && npm run build`.

- [x] **VF-180 — Cost analytics (token cost breakdown by provider/model)**
  - Track cost per session, per agent, per model; project estimates based on current burn rate.
  - **Features:**
    - Cost breakdown table: by session, by agent role, by model
    - Pricing from ModelProviderRegistry config
    - Burn rate projection: "at current rate, session will cost $X"
    - Budget alerts: "80% of budget used"
  - **Data source:** LlmResponse.usage + pricing config
  - **Backend:** pricing registry + aggregated cost endpoint (e.g., /control/analytics/costs)
  - **Why needed:** Control costs, project budgets for production use
  - Added CostAnalytics widget for model spend + burn rate from LLM response events.
  - Verified via `cd apps/api && pytest tests/test_cost_tracking.py -v`, `cd apps/ui && npm run build`.

- [ ] **VF-181 — Fix control session list contract (phase/updated_at)**
  - Align `/control/sessions` response with Control Panel expectations (phase, updated_at, artifacts) or adapt UI to the actual payload.
  - **Why needed:** Avoid empty/mismatched session list fields and enable reliable filtering.

- [ ] **VF-182 — Add navigation link to Control Panel**
  - Add a main layout link to `/control` so the admin UI is discoverable without manual URL entry.
  - **Why needed:** Improve access to monitoring UI during orchestration runs.

- [ ] **VF-183 — Enrich control session list with artifact badges**
  - Show artifact badges (concept/build_spec/task_graph) and counts based on the `/control/sessions` artifacts array.
  - **Why needed:** Quick visibility into what each session has produced.

- [ ] **VF-184 — Show active session details in sidebar list**
  - Display phase + active_task_id in the Active Sessions list (data already returned by `/control/active`).
  - **Why needed:** Faster at-a-glance view of in-flight work.

- [ ] **VF-185 — Enhance agent cards with model tier + task description**
  - Display `model_tier` and `task_description` from event metadata in Agent Activity cards.
  - **Why needed:** Clarify routing decisions and task context per agent.

- [ ] **VF-186 — Control Panel empty-event guidance**
  - When the event stream is empty, show a helper callout explaining how to generate EventLog events (orchestration run steps/links).
  - **Why needed:** Reduce confusion when widgets remain idle for MVP sessions.


### 30 MVP/Placeholder Cleanup

- [ ] **VF-301 — Audit MVP/placeholder shortcuts and publish cleanup inventory**
  - Catalog every MVP/placeholder/stub implementation still in use (e.g., mock demo flow in `apps/api/vibeforge_api/routers/sessions.py`, mock project generator in `apps/api/vibeforge_api/core/mock_generator.py`, stub adapters in `models/agent_framework_stubs.py`, local provider stub in `models/local/provider.py`). Produce a consolidated inventory doc with file paths, line refs, and suggested remediation path for each item.
  - **Status:** Planned
  - **Done when:** `docs/ai/planning/mvp_placeholder_audit.md` (or similar) lists each placeholder with owner, impact, and whether to replace, guard, or defer.
  - **Verify:** Manual review of the audit doc against the cited files; CI/docs build if applicable.

- [ ] **VF-302 — Replace MVP demo shortcut in questionnaire submission (mock generator → real pipeline)**
  - Remove the shortcut that generates mock files and jumps to COMPLETE inside `apps/api/vibeforge_api/routers/sessions.py` (submitAnswer handler). Route questionnaire completion into the real BuildSpec → concept → plan flow (or gate behind a feature flag) and retire `mock_generator.generate` as the default path.
  - **Status:** Planned
  - **Done when:** Submitting the final questionnaire answer transitions to PLAN_REVIEW/IDEA with real artifacts instead of calling MockGenerator or auto-setting COMPLETE; tests updated to cover the new flow.
  - **Verify:** `cd apps/api && pytest tests/test_sessions.py -k questionnaire` (plus any new end-to-end test for non-mock flow).

- [ ] **VF-303 — Replace mocked plan/progress responses with TaskGraph/event data**
  - Swap the hardcoded plan summary and progress scaffolding in `apps/api/vibeforge_api/routers/sessions.py` with data derived from stored TaskGraph and recent events (no fabricated feature lists or task timelines when not in EXECUTION).
  - **Status:** Planned
  - **Done when:** GET /plan and GET /progress pull from persisted artifacts/event log with sensible empty states; mock data paths removed; coverage added for both endpoints in non-EXECUTION phases.
  - **Verify:** `cd apps/api && pytest tests/test_sessions.py -k "plan or progress"` (extend with new cases for TaskGraph-backed responses).

- [ ] **VF-304 — Define upgrade path for agent/local stubs (LangGraph/CrewAI/AutoGen + LocalProvider)**
  - Turn the stub adapters in `models/agent_framework_stubs.py` and the `LocalProvider` stub in `models/local/provider.py` into explicit upgrade tasks: document intended feature flags, minimum viable integrations, and acceptance tests so they can be scheduled without ambiguity.
  - **Status:** Planned
  - **Done when:** A follow-on design/plan doc exists outlining scope, rollout guards, and test hooks for each stubbed provider/adapter; stubs are referenced from the audit with clear next-step VF IDs or WP links.
  - **Verify:** Manual review of the plan doc and cross-check that stubs are annotated with links to the planned work.
