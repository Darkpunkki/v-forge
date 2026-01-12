# WP-0019 — SessionCoordinator concept and plan generation

## VF Tasks Included
- [x] VF-035 — SessionCoordinator: concept generation stage
  - **Files:** `orchestration/coordinator/session_coordinator.py` (generate_concept method)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorConcept` (4 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorConcept -v` (4 passed)
- [x] VF-036 — SessionCoordinator: plan proposal + plan approval stage
  - **Files:** `orchestration/coordinator/session_coordinator.py` (generate_plan, get_plan_summary, approve_plan, reject_plan methods)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorPlan` (5 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorPlan -v` (5 passed)

## Goal
Enable SessionCoordinator to generate concepts and TaskGraphs, run gates, and present plan summaries for user approval.

## Dependencies
- ✅ WP-0018 (SessionCoordinator foundations - start/questionnaire/buildSpec)
- ✅ WP-0015 (Orchestrator - generateConcept, createTaskGraph)
- ✅ WP-0004 (Gates pipeline)

## Configuration Points for Future Testing

When you're ready to test the full system, these are the key configuration areas:

### 1. **Orchestrator Prompts** (`orchestration/prompts.py`)
- **What:** Jinja2 templates that instruct the LLM how to generate concepts and plans
- **Why configure:** Adjust concept creativity, plan complexity, task granularity
- **Templates:**
  - `CONCEPT_GENERATION_TEMPLATE` - controls how concepts are generated from BuildSpec
  - `TASKGRAPH_GENERATION_TEMPLATE` - controls how TaskGraph DAGs are created

### 2. **Model Routing** (`configs/models/routing.json`)
- **What:** Defines which models are used for orchestrator vs worker roles
- **Why configure:** Control cost vs quality tradeoffs
- **Key fields:**
  - `orchestrator.default_model` - model for concept/plan generation (currently gpt-4o)
  - `orchestrator.temperature` - creativity level (0.0-1.0)

### 3. **Gate Policies** (configured in code for MVP)
- **What:** Safety checks before concept/plan execution
- **Future config file:** `configs/policies/gates.json` (not yet externalized)
- **Key gates:**
  - PolicyGate - forbidden patterns
  - FeasibilityGate - scope budgets
  - RiskGate - command allowlists

### 4. **BuildSpec Scope Budgets** (`vibeforge_api/core/spec_builder.py`)
- **What:** Limits on plan complexity (max screens, entities, files)
- **Why configure:** Control generated code size
- **Current location:** `_build_scope_budget()` function (hardcoded)
- **Future:** Should move to `configs/scope_budgets.json`

## Execution Steps

### 1. VF-035: SessionCoordinator.generateConcept()

**Intent:** Call Orchestrator to generate concept doc and structured concept JSON, then run gates and request clarifications if needed.

**Implementation:**
- Add `generate_concept(session_id)` method to SessionCoordinator
- **Phase validation:** Must be in IDEA phase
- **Requires:** BuildSpec must exist in session
- **Flow:**
  1. Retrieve session and validate IDEA phase
  2. Get BuildSpec from session
  3. Call `Orchestrator.generateConcept(build_spec)` → returns ConceptDoc
  4. Run gates on concept (optional for MVP - can defer complex gate logic)
  5. Store concept in session.concept
  6. Transition to PLAN_REVIEW phase
  7. Return concept

**Error handling:**
- If Orchestrator fails → capture error, remain in IDEA phase
- If gates block → transition to clarification state (deferred to later WP)

**Done means:**
- `generate_concept()` method exists and works
- Calls Orchestrator.generateConcept() correctly
- Stores concept in session
- Transitions IDEA → PLAN_REVIEW
- Tests verify happy path and error handling

### 2. VF-036: SessionCoordinator.generatePlan() + getPlanSummary()

**Intent:** Generate TaskGraph, run plan gates, present plan summary, and wait for explicit approval.

**Implementation Part A: generatePlan()**
- Add `generate_plan(session_id)` method to SessionCoordinator
- **Phase validation:** Must be in PLAN_REVIEW phase
- **Requires:** Concept must exist in session
- **Flow:**
  1. Retrieve session and validate PLAN_REVIEW phase
  2. Get BuildSpec and Concept from session
  3. Call `Orchestrator.createTaskGraph(build_spec, concept)` → returns TaskGraph
  4. Validate TaskGraph via `TaskGraph.validate_dag()`
  5. Run gates on TaskGraph (optional for MVP)
  6. Store task_graph in session.task_graph
  7. Remain in PLAN_REVIEW phase (waiting for user approval)
  8. Return task_graph

**Implementation Part B: getPlanSummary()**
- Add `get_plan_summary(session_id)` method to SessionCoordinator
- **Purpose:** Format TaskGraph into user-friendly summary for UI
- **Returns:** Dictionary with:
  - `task_count` - total tasks in plan
  - `task_list` - list of task descriptions
  - `verification_steps` - what will be verified
  - `estimated_scope` - files/screens from BuildSpec
  - `constraints` - key policies/budgets

**Implementation Part C: approvePlan() / rejectPlan()**
- Add `approve_plan(session_id)` method
  - Validates PLAN_REVIEW phase
  - Transitions to EXECUTION phase
  - Returns confirmation
- Add `reject_plan(session_id, reason)` method
  - Validates PLAN_REVIEW phase
  - Logs rejection reason
  - Transitions back to IDEA phase for regeneration
  - Returns confirmation

**Done means:**
- `generate_plan()` creates TaskGraph from concept
- `get_plan_summary()` formats plan for UI display
- `approve_plan()` transitions to EXECUTION
- `reject_plan()` transitions back to IDEA
- Tests verify all flows and phase transitions

## Verification Commands
```bash
# Unit tests for concept generation
cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorConcept -v

# Unit tests for plan generation
cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorPlan -v

# Full SessionCoordinator test suite
cd apps/api && pytest tests/test_session_coordinator.py -v

# Full test suite
cd apps/api && pytest -v
```

## Done Means
- [x] SessionCoordinator.generate_concept() method exists
- [x] Calls Orchestrator.generateConcept(BuildSpec) correctly
- [x] Concept stored in session and persisted as artifact
- [x] Phase transition IDEA → PLAN_REVIEW works
- [x] SessionCoordinator.generate_plan() method exists
- [x] Calls Orchestrator.createTaskGraph(BuildSpec, Concept) correctly
- [x] TaskGraph validation via validate_dag()
- [x] TaskGraph stored in session
- [x] get_plan_summary() formats plan for UI
- [x] approve_plan() transitions PLAN_REVIEW → EXECUTION
- [x] reject_plan() transitions PLAN_REVIEW → IDEA
- [x] All tests pass (415+ expected)

## Notes on Testing Strategy

When testing for real:

1. **Start with mock Orchestrator responses** - bypass LLM costs initially
2. **Test phase transitions** - ensure state machine is strict
3. **Validate BuildSpec → Concept → TaskGraph flow** - end-to-end integration
4. **Test gate integration** - ensure gates can block/warn appropriately
5. **Test plan approval/rejection** - bidirectional flow works

## Key Architectural Points

**SessionCoordinator is stateless** - all state lives in Session object
- This means you can restart the API and resume sessions
- Session is persisted via SessionStore
- Artifacts (BuildSpec, Concept, TaskGraph) persist to disk

**Phase transitions are strict** - invalid transitions raise ValueError
- This prevents UI bugs from corrupting session state
- Each method validates current phase before executing

**Orchestrator calls are isolated** - SessionCoordinator just delegates
- If you want to swap Orchestrator implementation, SessionCoordinator doesn't change
- If you want to add retry logic, add it in Orchestrator layer

**Error handling is defensive** - failures don't corrupt session state
- Errors logged to session.error_history
- Phase remains unchanged on failure
- User can retry or abort cleanly
