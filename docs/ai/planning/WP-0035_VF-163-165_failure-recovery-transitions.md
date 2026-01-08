# WP-0035 — Failure recovery + fix loop transitions

## Status
- Queued

## Context
- Chapter(s): 16 State Machine: MVP Phases (State Diagram)
- Why now:
  - The state machine needs explicit failed/abort behaviors to avoid ambiguous terminal states.
  - Fix-loop behavior must be encoded to prevent infinite loops and ensure safe recovery paths.
  - Upcoming transition tests depend on a clear failure and abort model.

## Goal
- Define and implement failure, fix-loop return, and abort behaviors within the session phase state machine.

## VF Tasks (canonical)
- [ ] **VF-163 — Implement FAILED terminal behavior + recovery options**
  - Define what constitutes unrecoverable failure; ensure the system transitions to FAILED cleanly, emits a final error artifact, and offers safe recovery options (restart session, reduce scope, export logs).
- [ ] **VF-164 — Implement controlled “return transitions” for fix loops**
  - Support the state-machine loop VERIFICATION → EXECUTION when final checks fail, with clear guardrails to avoid infinite loops.
- [ ] **VF-165 — Implement session abort and cleanup behavior**
  - Allow user to abort; stop active execution safely, mark session as FAILED (or ABORTED if you add it), and preserve artifacts/logs for inspection.

## Plan
### Approach
- Define explicit FAILED (and optional ABORTED) terminal semantics in the phase model.
- Implement failure recovery artifacts and metadata emission on terminal failure.
- Encode fix-loop return transitions with a bounded retry guardrail.
- Add explicit abort flow that halts execution and preserves artifacts/logs.
- Validate behaviors through coordinator-level tests and event assertions.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-163
    intent: "Define FAILED terminal behavior and recovery artifacts for unrecoverable failures."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "orchestration/coordinator/state_machine.py"
    done_when:
      - "Sessions transition to FAILED with a final error artifact and recovery options."
      - "Failure metadata is persisted for UI/diagnostics."
    verify:
      - "pytest"
  - vf: VF-164
    intent: "Implement controlled VERIFICATION → EXECUTION return transitions for fix loops."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "runtime/task_master.py"
    done_when:
      - "Verification failures trigger a bounded return to EXECUTION with guardrails."
      - "Loop limits prevent infinite retries and emit clear errors."
    verify:
      - "pytest"
  - vf: VF-165
    intent: "Add a session abort flow that stops execution and preserves artifacts/logs."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "apps/api/vibeforge_api/routers/sessions.py"
    done_when:
      - "Abort requests safely stop active work and record terminal state."
      - "Artifacts/logs remain accessible for inspection after abort."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-163: FAILED terminal state is explicit, emits a final error artifact, and exposes recovery options.
- VF-164: Fix-loop return transition is allowed with bounded retries and guardrails.
- VF-164: Infinite verification loops are prevented with clear error output.
- VF-165: Abort flow halts execution safely and preserves artifacts/logs.
- VF-165: Abort transitions are validated by the state machine.

## Verify
- Add tests
- `pytest`

## Dependencies
- WP-0034 (state machine rules)

## Risks / Recovery
- Risk: Failure states conflict with existing COMPLETE/FAILED semantics used by the UI.
  - Mitigation: Align terminal state naming with current API response models or add a compatible mapping layer.
- Risk: Fix-loop guardrails are too strict, blocking valid retries.
  - Mitigation: Use configurable retry limits and test the expected retry count.
- Recovery: If verification fails, revert to baseline failure handling and reintroduce transitions incrementally with focused tests.
