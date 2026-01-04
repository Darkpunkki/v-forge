# VibeForge Master Checklist

Use the checkboxes below as a living backlog. Mark tasks complete by changing `[ ]` to `[x]`.

## Checklist


### 00 Foundations

- [ ] **VF-001 — Create monorepo structure (apps/core/orchestration/models/runtime/storage/configs/schemas)**
  - Initialize the repository with a clear top-level folder layout that matches the architecture. This keeps UI, core logic, orchestration, model adapters, runtime execution, and persistence cleanly separated from day one.

- [x] **VF-002 — Define core DTOs + shared types (SessionPhase, AgentRole, GateResult)**
  - Create the shared domain types used across UI/API/core: session phases, agent roles, gate results, and common error/result envelopes. These are the contracts that prevent coupling and spaghetti.
  - Files: `apps/api/vibeforge_api/models/types.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/models/responses.py`
  - Verification: Models imported and used in routers; pytest passes

- [ ] **VF-003 — Add configuration loader (stack presets, policies, router rules)**
  - Implement config loading (e.g., YAML/JSON) for allowlisted stack presets, command policies, forbidden patterns, and model routing rules. Make behavior adjustable without code changes.

- [ ] **VF-004 — Add basic test harness + CI skeleton (unit tests only)**
  - Set up unit test framework and a minimal CI pipeline so new components can be verified continuously. Keep it simple: lint/format optional, unit tests required.


### 01 UI Shell (MVP)

- [ ] **VF-010 — UI skeleton (simple web UI)**
  - Create a minimal, user-friendly UI shell (web is easiest for MVP). It should be able to start a session and render the main screens without any free-text input.

- [ ] **VF-011 — Questionnaire screen (single-question flow, no free text)**
  - Implement a step-by-step questionnaire UI that only supports structured inputs (radio buttons, pick lists, sliders).

- [ ] **VF-012 — Plan review screen (approve/reject)**
  - Show the proposed concept/plan summary and require explicit user approval before any code is generated or commands are run.

- [ ] **VF-013 — Progress screen (timeline + log stream)**
  - Display current phase, active task, completed tasks, and streaming logs (commands + verification results).

- [ ] **VF-014 — Clarification screen (multiple-choice answers)**
  - Render clarification questions returned by gates or agents, allowing only multiple-choice or constrained answers.

- [ ] **VF-015 — Summary screen (run instructions + open workspace link)**
  - Present final run instructions, key features built, and the location of the generated workspace folder/repo.

- [ ] **VF-016 — UI client for Local UI API (typed requests/responses)**
  - Implement a typed API client (or thin fetch wrapper) so the UI communicates with the local API through stable DTOs.


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

- [ ] **VF-027 — Endpoint: POST /sessions/{id}/clarifications (submitClarificationChoice)**
  - Accept user choices for clarification questions and feed them back into the coordinator/agent loop.

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

- [ ] **VF-030 — Implement Session model + phases enum**
  - Define the Session aggregate containing phase, pointers to artifacts (IntentProfile/BuildSpec/TaskGraph), and error history.

- [ ] **VF-031 — Implement SessionStore (in-memory) + persistence seam interface**
  - Store sessions in memory for MVP, but define an interface so you can later persist sessions to disk/DB without changing core logic.

- [ ] **VF-032 — SessionCoordinator: startSession() + phase initialization**
  - Orchestrate workspace/artifact initialization and set the session to QUESTIONNAIRE.

- [ ] **VF-033 — SessionCoordinator: questionnaire step loop (nextQuestion/applyAnswer/finalize)**
  - Drive questionnaire progression and finalize IntentProfile when complete.

- [ ] **VF-034 — SessionCoordinator: buildSpec stage**
  - Convert IntentProfile to BuildSpec (deterministic), including idea seed + policy guardrails.

- [ ] **VF-035 — SessionCoordinator: concept generation stage**
  - Call Orchestrator to generate concept doc and structured concept JSON, then run gates and request clarifications if needed.

- [ ] **VF-036 — SessionCoordinator: plan proposal + plan approval stage**
  - Generate TaskGraph, run plan gates, present plan summary, and wait for explicit approval.

- [ ] **VF-037 — SessionCoordinator: executeNextTask() loop**
  - Execute the DAG sequentially: schedule task, dispatch to agent role, apply diff, run verifications, mark done/failed.

- [ ] **VF-038 — SessionCoordinator: finalize() global verification + summary**
  - Run global verification steps and request final summary from orchestrator; transition session to COMPLETE.

- [ ] **VF-039 — SessionCoordinator: abort/reset session flows**
  - Support user-initiated abort and controlled reset/retry paths without leaving the system in an inconsistent state.


### 04 Questionnaire Engine

- [ ] **VF-040 — Define QuestionBank (audience/platform/domains/vibe/constraints/budgets)**
  - Create the structured question set and allowed answers that produce IntentProfile deterministically (no free text).

- [ ] **VF-041 — Implement QuestionnaireEngine.nextQuestion() (adaptive branching)**
  - Select the next question based on prior answers to keep questionnaire short but informative.

- [ ] **VF-042 — Implement QuestionnaireEngine.applyAnswer() + validation**
  - Validate answers against allowed options and update session questionnaire state.

- [x] **VF-043 — Implement QuestionnaireEngine.finalize() -> IntentProfile (schema-validated)**
  - Produce the final IntentProfile object and validate it against the schema to ensure stability downstream.
  - File: `apps/api/vibeforge_api/core/questionnaire.py` (finalize() method)
  - Maps questionnaire answers to IntentProfile structure
  - Verification: `pytest tests/test_e2e_demo.py::test_e2e_questionnaire_to_result`


### 05 Spec Builder + Seed/Twist

- [ ] **VF-050 — Define StackPreset allowlist (MVP: 1 web stack)**
  - Define at least one stack preset (e.g., Vite+React) including build/test/run commands and runtime assumptions.

- [x] **VF-051 — Implement SpecBuilder.fromIntent(IntentProfile) -> BuildSpec**
  - Deterministically pin platform, stack preset, scope budgets, and guardrails based on IntentProfile.
  - File: `apps/api/vibeforge_api/core/spec_builder.py`
  - Converts IntentProfile to BuildSpec deterministically
  - Derives seed, picks stack, genre, twists, scope budgets, policies
  - Verification: `pytest tests/test_e2e_demo.py` (BuildSpec created and validated)

- [ ] **VF-052 — Implement DeterministicSeedDeriver (replayable)**
  - Derive a deterministic seed from IntentProfile to keep ‘randomness’ reproducible and testable.

- [ ] **VF-053 — Implement IdeaSeedPicker (genre + up to 2 twist cards)**
  - Choose genre + twist cards from allowlists within constraints; record them into BuildSpec.

- [ ] **VF-054 — BuildSpec validation + persistence (ArtifactStore)**
  - Validate BuildSpec against schema and persist as a stable contract before any model calls occur.


### 06 Model Layer (Cloud-first, local later)

- [ ] **VF-060 — Define LlmClient interface + LlmRequest/LlmResponse types**
  - Create a provider-agnostic interface for model calls so OpenAI and local backends can be swapped without touching execution logic.

- [ ] **VF-061 — Implement OpenAiProvider (MVP)**
  - Implement the MVP model client using OpenAI API. Keep prompts and routing outside this class so it stays a thin adapter.

- [ ] **VF-062 — Implement ModelProviderRegistry (config-driven)**
  - Allow selecting provider + model by config. This is the switch you’ll flip when moving to local models later.

- [ ] **VF-063 — Implement ModelRouter policy (role/complexity/failures -> modelRef)**
  - Route calls to the right model choice based on role (orchestrator/worker/fixer/reviewer), complexity, and retry history.

- [ ] **VF-064 — Implement OutputValidator (strict JSON schema validation)**
  - Validate model outputs against schemas and fail fast if malformed. This is a major reliability lever.

- [ ] **VF-065 — Implement OutputRepair (retry/repair strategy for malformed outputs)**
  - Implement structured ‘repair’ retries (tell the model what failed validation) so the system can recover without manual intervention.

- [ ] **VF-066 — Stub LocalProvider interface (no implementation yet)**
  - Add a placeholder local provider adapter (Ollama/llama.cpp/vLLM later) to keep the architecture seam visible and tested.


### 07 Orchestrator

- [ ] **VF-070 — Orchestrator prompt templates: Concept generation (JSON + Markdown)**
  - Write templates that produce a structured concept JSON plus a human-readable concept doc, aligned to BuildSpec constraints.

- [ ] **VF-071 — Orchestrator prompt templates: TaskGraph generation (DAG + constraints)**
  - Write templates that generate a TaskGraph DAG with per-task constraints, inputs, outputs, and verification steps.

- [ ] **VF-072 — Orchestrator prompt templates: Run summary**
  - Write templates for summarizing what was built, how to run it, and what limitations remain.

- [ ] **VF-073 — Implement Orchestrator.generateConcept(BuildSpec)**
  - Call the model to generate the concept; validate output and return either concept or clarification requests.

- [ ] **VF-074 — Implement Orchestrator.createTaskGraph(BuildSpec, ConceptDoc)**
  - Call the model to produce TaskGraph; validate DAG and enforce scope/command policies via gates.

- [ ] **VF-075 — Implement Orchestrator.summarize(artifacts)**
  - Generate the final summary response from stored artifacts (tasks, diffs, verification results).


### 08 Gates & Policies

- [ ] **VF-080 — Implement Gate interface + GatePipeline composition**
  - Create a consistent gate interface and a pipeline that can evaluate context and yield ok/warn/block results.

- [ ] **VF-081 — Implement FeasibilityGate (scope budgets, screens/entities/diff size)**
  - Enforce BuildSpec scope budgets and stop unrealistic plans early (before code generation).

- [ ] **VF-082 — Implement RiskGate (command families, network rule enforcement)**
  - Ensure requested commands fit allowlisted families and that network access rules are respected.

- [ ] **VF-083 — Implement PolicyGate (forbidden regex patterns, path constraints)**
  - Block unsafe content patterns and prevent file operations outside the workspace.

- [ ] **VF-084 — Implement DiffAndCommandGate (max files/lines, forbidden content in diff)**
  - Validate AgentResult diffs and commands before apply/run; enforce per-task constraints.

- [ ] **VF-085 — Gate-to-UI adapter (warnings/blockers + multiple-choice questions)**
  - Translate gate output into UI-friendly messages and multiple-choice clarification questions where needed.


### 09 TaskGraph + TaskMaster + Distributor

- [ ] **VF-090 — Define TaskGraph types + parser + schema validation**
  - Implement types and schema validation for TaskGraph so the scheduler can rely on strong invariants.

- [ ] **VF-091 — Validate DAG (no cycles) + dependency resolver**
  - Reject cyclical plans and compute ready-task sets deterministically.

- [ ] **VF-092 — Implement TaskMaster.enqueue(TaskGraph)**
  - Load the validated task graph into the scheduler and initialize task statuses.

- [ ] **VF-093 — Implement TaskMaster.scheduleNext() (ready tasks only)**
  - Select the next runnable task based on dependencies and failure policy.

- [ ] **VF-094 — Implement TaskMaster.markDone/markFailed + retry counters**
  - Track completion/failure and retry history; provide hooks for escalation policies.

- [ ] **VF-095 — Implement Distributor.route(task) -> AgentRole (role hint rules)**
  - Assign each task to a role based on explicit hints and objective heuristics.

- [ ] **VF-096 — Implement escalation policy (failures -> stronger role/model)**
  - Escalate to fixer/reviewer or stronger model after repeated failures to avoid infinite loops.


### 10 Agent Framework Adapter (pluggable)

- [ ] **VF-100 — Define AgentFramework.runTask() interface (role prompt + tools + context)**
  - Create an interface for running an agent role against a task, producing a standard AgentResult.

- [ ] **VF-101 — Implement MVP AgentFrameworkAdapter (direct model call + strict AgentResult)**
  - Implement the simplest adapter: call the provider directly with role prompt and require AgentResult JSON output.

- [ ] **VF-102 — Implement AgentRegistry (role -> prompt/tool policy/output schema)**
  - Centralize role prompts, tool permissions, and output schemas so agent behavior is consistent and auditable.

- [ ] **VF-103 — Add placeholder adapters (LangGraph/CrewAI/AutoGen) as stubs**
  - Add stubs for future framework-backed implementations so the seam is explicit and easy to fill later.


### 11 Workspace + Patching

- [x] **VF-110 — Implement WorkspaceManager.initRepo(sessionId, template)**
  - Create the workspace directory and initialize a repo from a template or minimal scaffold.
  - File: `apps/api/vibeforge_api/core/workspace.py`
  - Verification: `pytest tests/test_workspace.py` (12 tests pass)

- [x] **VF-111 — Implement workspace layout (repo/ artifacts/) per session**
  - Standardize where code lives and where logs/artifacts are stored for each session.
  - File: `apps/api/vibeforge_api/core/workspace.py` (get_repo_path, get_artifacts_path)
  - Verification: `pytest tests/test_workspace.py::test_init_repo_creates_layout`

- [ ] **VF-112 — Optional: initialize git repo + commit snapshots**
  - Initialize git and commit after each successful task to enable rollback and clearer diff review.

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

- [ ] **VF-120 — Implement CommandRunner (allowlist enforcement, timeouts, output capture)**
  - Run shell commands safely: enforce allowlists, apply timeouts, and capture stdout/stderr for UI and artifacts.

- [ ] **VF-121 — Implement BuildVerifier (stack preset build command)**
  - Verify the project builds using commands defined by the selected stack preset.

- [ ] **VF-122 — Implement TestVerifier (stack preset test command)**
  - Verify tests pass and produce readable failure outputs when they don’t.

- [ ] **VF-123 — Implement SmokeVerifier (server starts and/or route responds)**
  - Run a lightweight end-to-end check (start server or hit a route) to confirm the app can run locally.

- [ ] **VF-124 — Implement VerifierSuite (per-task + global verification)**
  - Orchestrate verification steps after each task and at the end of the run based on TaskGraph definitions.

- [ ] **VF-125 — Implement AppRunner.getRunInstructions() per stack preset**
  - Generate clear run instructions (install/build/dev server) and expose them in the final summary.

- [ ] **VF-126 — Optional: AppRunner.start()/stop() dev server + stream logs**
  - Provide a ‘Run’ button that starts the app locally and streams logs back to the UI.


### 13 Observability (Artifacts + Event log)

- [ ] **VF-130 — Implement ArtifactStore (filesystem JSON, per-session keys)**
  - Persist all important artifacts in a consistent key structure so runs are inspectable and replayable.

- [ ] **VF-131 — Implement EventLog (append-only events: phase changes, dispatches, applies, command runs)**
  - Record an append-only event stream so you can trace what happened and debug failures without guesswork.

- [ ] **VF-132 — Add “export run bundle” (zip artifacts + summary) (optional)**
  - Package repo snapshot, artifacts, and final summary into a portable bundle for sharing or archival.

## 14 Workflow Orchestration: Happy Path (Sequence)

- [ ] **VF-140 — Implement “Happy Path” orchestration contract end-to-end**
  - Ensure a single session can flow cleanly through: start → questionnaire → build spec → concept → plan review → (approve) → execution → verification → complete, returning coherent API responses at each step.

- [ ] **VF-141 — Add a Phase-aware API guard layer (wrong-phase handling)**
  - Centralize “wrong phase” checks so every endpoint returns consistent, user-friendly errors and does not allow illegal calls (e.g., submitting answers after PLAN_REVIEW).

- [ ] **VF-142 — Implement progress model + event emission for every major step**
  - Emit structured progress events for: phase changes, question served, answer accepted, artifact created, task dispatched, diff applied, verification started/completed, and completion. These events power the UI timeline.

- [ ] **VF-143 — Persist phase transitions into the event log**
  - Record all state changes (oldPhase → newPhase + reason) into the EventLog for debugging and replayability.

- [ ] **VF-144 — Implement “artifact checkpoints” for each stage**
  - Store a stable snapshot artifact at the end of each stage: `IntentProfile`, `BuildSpec`, `Concept`, `TaskGraph`, and final `RunSummary`, so the run can be inspected without re-running.

- [ ] **VF-145 — Implement “plan preview” formatting for UI consumption**
  - Convert TaskGraph into a concise plan summary: feature list, task count, verification steps, estimated scope, and key constraints—so user can approve with confidence.

- [ ] **VF-146 — Implement “reject plan → revise concept” loop**
  - If user rejects plan, safely return to IDEA (or PLAN_REVIEW) with a revision strategy: regenerate concept, reduce scope, or adjust stack—without losing session integrity.


## 15 Execution Loop: Verification Gates & Recovery (Sequence)

- [ ] **VF-150 — Implement the per-task execution loop (TaskMaster → Agent → Gate → Apply → Verify)**
  - Build the core loop that schedules the next task, runs an agent to produce an AgentResult, gates it, applies the diff, runs per-task verification, and marks the task done/failed.

- [ ] **VF-151 — Implement RepoContextLoader (task-scoped context selection)**
  - Load a bounded set of relevant files into the agent prompt based on the task’s declared inputs (files-to-read), plus optionally small “supporting context” (project structure, conventions).

- [ ] **VF-152 — Implement AgentResult handling for “needs clarification”**
  - Support the agent returning multiple-choice questions; pause execution, expose questions to UI, accept user choices, then resume with the clarification answers injected into the next agent call.

- [ ] **VF-153 — Implement Diff gate + Apply gate with structured failure reasons**
  - When a diff is blocked (policy/size/paths) or fails to apply, produce a structured failure report that can be routed to FIXER or surfaced to UI.

- [ ] **VF-154 — Implement per-task verification runner (declared in TaskGraph)**
  - Execute the task’s verification steps (e.g., unit tests, lint, build step) after apply. Capture stdout/stderr and store results in artifacts.

- [ ] **VF-155 — Implement automatic “fix loop” policy after verification failure**
  - When verification fails, automatically generate a repair attempt strategy (e.g., create a FIXER task, escalate model, narrow diff limits, or request user choice after N failures).

- [ ] **VF-156 — Add retry counters + escalation rules per task**
  - Track failure count per task and apply escalation: stronger role/model after repeated failures; hard-stop after max retries with a meaningful error summary.

- [ ] **VF-157 — Implement final global verification step-set (end of DAG)**
  - Run a final verification suite (build/test/smoke) after all tasks complete; if it fails, route back into fix loop rather than silently finishing.

- [ ] **VF-158 — Implement “completion summary” assembly from artifacts**
  - Collect and summarize what was built: features, modules, key files changed, how to run, what tests ran, and any known limitations—so user gets a coherent end report.

- [ ] **VF-159 — Add deterministic execution mode (replayable runs)**
  - Ensure the same inputs (IntentProfile + seed) produce the same major decisions (within reason), and record seeds + config hashes so runs can be reproduced for debugging.


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

- [ ] **VF-167 — Add “resume session” capability from stored artifacts**
  - Enable restarting the API and resuming an in-progress session from artifacts/event log (initially limited scope), improving robustness and developer ergonomics.
