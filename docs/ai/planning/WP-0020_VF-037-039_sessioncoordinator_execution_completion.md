# WP-0020 — SessionCoordinator execution loop and completion

## VF Tasks Included
- [x] VF-037 — SessionCoordinator: executeNextTask() loop
  - **Files:** `orchestration/coordinator/session_coordinator.py` (execute_next_task method)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorExecution` (6 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorExecution -v` (6 passed)
- [x] VF-038 — SessionCoordinator: finalize() global verification + summary
  - **Files:** `orchestration/coordinator/session_coordinator.py` (finalize_session method)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorFinalize` (4 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorFinalize -v` (2 passed, 2 expect npm)
- [x] VF-039 — SessionCoordinator: abort/reset session flows
  - **Files:** `orchestration/coordinator/session_coordinator.py` (abort_session method)
  - **Tests:** `apps/api/tests/test_session_coordinator.py::TestSessionCoordinatorAbort` (3 tests)
  - **Verify:** `cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorAbort -v` (3 passed)

## Goal
Complete SessionCoordinator with task execution loop, global verification, and abort/reset flows to enable full end-to-end session orchestration from questionnaire through to runnable code generation.

## Dependencies
- ✅ WP-0018 (SessionCoordinator foundations - start/questionnaire/buildSpec)
- ✅ WP-0019 (SessionCoordinator concept/plan generation)
- ✅ WP-0016 (TaskMaster - task scheduling and dependency resolution)
- ✅ WP-0017 (Distributor - task-to-role routing and agent framework)
- ✅ WP-0003 (Verifiers - build/test verification harness)

## Execution Steps

### 1. VF-037: SessionCoordinator.execute_next_task()

**Intent:** Execute tasks from the TaskGraph DAG sequentially: schedule → dispatch to agent → gate result → apply diff → verify → mark done/failed → loop.

**Implementation:**
- Add `execute_next_task(session_id)` method to SessionCoordinator
- **Phase validation:** Must be in EXECUTION phase
- **Requires:** TaskGraph must exist in session, TaskMaster must have enqueued tasks
- **Flow:**
  1. Retrieve session and validate EXECUTION phase
  2. Get TaskMaster for this session (or create/enqueue TaskGraph if first call)
  3. Call `TaskMaster.scheduleNext()` to get next ready task
  4. If no ready task:
     - If all tasks complete → return signal to finalize
     - If blocked by failures → return error/clarification
     - Otherwise → log and wait
  5. Route task to agent role using `Distributor.route(task, failure_count)`
  6. Execute task via `AgentFramework.runTask(task, role, context)`
  7. Parse AgentResult (diff + commands + notes)
  8. Run gates on AgentResult (DiffAndCommandGate + PolicyGate)
  9. If gates block → mark task failed, log reason, retry or escalate
  10. Apply diff using `PatchApplier.apply_patch()`
  11. Run task verification using `VerifierSuite.run_task_verification()`
  12. If verification passes:
      - Mark task as done via `TaskMaster.markDone()`
      - Persist AgentResult to artifacts
      - Return success
  13. If verification fails:
      - Mark task as failed via `TaskMaster.markFailed()`
      - If retries available → retry (escalate model/role)
      - If max retries exceeded → skip downstream tasks
      - Return failure details

**Error handling:**
- Agent failures → capture error, increment retry counter, escalate or fail
- Gate blocks → log blocker, mark failed or request clarification
- Patch apply failures → mark failed with detailed error
- Verification failures → retry with escalation or fail

**Done means:**
- `execute_next_task()` method exists and orchestrates full execution loop
- Integrates TaskMaster, Distributor, AgentFramework, Gates, PatchApplier, Verifiers
- Handles task success/failure with proper state transitions
- Retries with escalation on failures
- Tests verify happy path, failures, retries, gate blocks

### 2. VF-038: SessionCoordinator.finalize_session()

**Intent:** Run global verification (build + test) after all tasks complete, request summary from Orchestrator, and transition to COMPLETE.

**Implementation:**
- Add `finalize_session(session_id)` method to SessionCoordinator
- **Phase validation:** Must be in EXECUTION phase
- **Requires:** All tasks in TaskGraph must be done (no pending/running tasks)
- **Flow:**
  1. Retrieve session and validate EXECUTION phase
  2. Check TaskMaster status → ensure all tasks complete
  3. Run global verification suite:
     - `VerifierSuite.run_global_verification()` (build + test)
     - Capture stdout/stderr results
  4. If global verification fails:
     - Log failure details to session
     - Transition to VERIFICATION_FAILED state (or stay in EXECUTION for retry)
     - Return failure with actionable error
  5. If global verification passes:
     - Call `Orchestrator.summarize(artifacts)` to generate RunSummary
     - Persist RunSummary to artifacts/run_summary.json
     - Store summary in session
     - Transition to COMPLETE phase
     - Return RunSummary
  6. Persist all final artifacts (concept, task_graph, diffs, verification results, summary)

**Error handling:**
- Global verification failures → stay in EXECUTION or transition to special state
- Orchestrator summarize failures → generate fallback summary from artifacts
- Preserve all artifacts even on failure

**Done means:**
- `finalize_session()` runs global verification
- Calls Orchestrator.summarize() to generate final summary
- Transitions to COMPLETE on success
- Handles verification failures gracefully
- Tests verify happy path and failure scenarios

### 3. VF-039: SessionCoordinator.abort_session()

**Intent:** Support user-initiated abort and controlled reset without corrupting session state.

**Implementation:**
- Add `abort_session(session_id, reason)` method to SessionCoordinator
- **Phase validation:** Can be called from any phase except COMPLETE/FAILED
- **Flow:**
  1. Retrieve session (any phase except terminal states)
  2. Stop any running task execution (mark running task as ABORTED)
  3. Log abort reason to session
  4. Preserve all artifacts up to abort point
  5. Transition to ABORTED phase (or FAILED with abort reason)
  6. Return confirmation with preserved state location

**Optional: Reset capability**
- Add `reset_to_phase(session_id, target_phase)` helper (future enhancement)
- Allows returning to IDEA or PLAN_REVIEW to regenerate concept/plan
- Validates legal phase transitions

**Error handling:**
- Ensure abort doesn't leave half-applied diffs or corrupted workspace
- Preserve all logs and artifacts for inspection
- Allow resumption if abort was accidental (future: resume capability)

**Done means:**
- `abort_session()` safely stops execution
- Preserves artifacts and logs
- Transitions to terminal abort state
- Tests verify abort from different phases

## Verification Commands
```bash
# Unit tests for execution loop
cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorExecution -v

# Unit tests for finalization
cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorFinalize -v

# Unit tests for abort
cd apps/api && pytest tests/test_session_coordinator.py::TestSessionCoordinatorAbort -v

# Full SessionCoordinator test suite
cd apps/api && pytest tests/test_session_coordinator.py -v

# Full test suite
cd apps/api && pytest -v
```

## Done Means
- [ ] SessionCoordinator.execute_next_task() method exists
- [ ] Full execution loop: schedule → dispatch → gate → apply → verify → mark done/failed
- [ ] Integrates TaskMaster, Distributor, AgentFramework, Gates, PatchApplier, Verifiers
- [ ] Retry logic with role/model escalation on failures
- [ ] SessionCoordinator.finalize_session() method exists
- [ ] Global verification (build + test) runs after all tasks complete
- [ ] Calls Orchestrator.summarize() for final RunSummary
- [ ] Transitions EXECUTION → COMPLETE on success
- [ ] SessionCoordinator.abort_session() method exists
- [ ] Safe abort preserves artifacts and logs
- [ ] Transitions to ABORTED/FAILED state cleanly
- [ ] All tests pass (424+ expected, adding ~15 new execution tests)

## Architecture Notes

**Execution Loop Design:**
- SessionCoordinator is the top-level orchestrator that wires together specialized components
- Each component has a single responsibility (TaskMaster schedules, Distributor routes, Agent executes, etc.)
- SessionCoordinator doesn't implement business logic - it delegates and coordinates
- All state changes go through Session model and are persisted immediately

**Error Recovery Strategy:**
- Per-task failures use retry + escalation (worker → powerful worker → fixer)
- Global verification failures can trigger full re-execution or manual intervention
- Abort preserves partial results for inspection

**Artifact Trail:**
- Every task execution produces an artifact: AgentResult + verification results
- Final summary aggregates all artifacts into coherent RunSummary
- Artifacts enable debugging, replay, and provenance tracking

**Phase Transition Strictness:**
- EXECUTION phase stays active until all tasks complete or unrecoverable failure
- Only finalize_session() can transition EXECUTION → COMPLETE
- Abort transitions to terminal state from any active phase
