# WP-0034 — State machine transitions + phase rules

## Status
- Queued

## Context
- Chapter(s): 16 State Machine: MVP Phases (State Diagram)
- Why now:
  - SessionCoordinator lifecycle exists but lacks explicit state transition guardrails.
  - Upcoming fix-loop and resume work depends on clear phase entry/exit rules.
  - Formalized transitions reduce regressions as orchestration features expand.

## Goal
- Define and enforce explicit phase transitions with clear entry actions and exit criteria to prevent illegal session state changes.

## VF Tasks (canonical)
- [ ] **VF-160 — Encode the session state machine as a formal transition table**
  - Implement an explicit allowed-transition map (fromPhase → toPhase) to prevent accidental illegal transitions as the codebase evolves.
- [ ] **VF-161 — Implement “entry actions” per phase**
  - Define and implement what happens *on entering* each phase (e.g., BUILD_SPEC creates BuildSpec, IDEA generates concept, PLAN_REVIEW generates TaskGraph, EXECUTION starts scheduling).
- [ ] **VF-162 — Implement “exit criteria” per phase**
  - Define and enforce the condition that must be true to exit each phase (e.g., questionnaire complete, concept accepted, plan approved, all tasks done, global verification pass).

## Plan
### Approach
- Introduce a single source of truth for allowed phase transitions (table or enum map) tied to SessionCoordinator.
- Define per-phase entry actions that encapsulate existing orchestration steps in an explicit hook.
- Define per-phase exit criteria checks and enforce them before transitions.
- Wire state validation into transition calls and return structured errors on invalid moves.
- Add or update tests to validate transition rules and hook behaviors.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-160
    intent: "Define the formal phase transition table and enforce it during session phase changes."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "orchestration/coordinator/state_machine.py"
    done_when:
      - "Transitions are validated against an explicit allowed-transition map."
      - "Illegal transitions return a structured error without mutating state."
    verify:
      - "pytest"
  - vf: VF-161
    intent: "Implement entry actions that run when a session enters each phase."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "orchestration/coordinator/state_machine.py"
    done_when:
      - "Each phase has a defined entry hook invoked on transition."
      - "Entry actions align with existing orchestration steps (build spec, concept, plan, execution)."
    verify:
      - "pytest"
  - vf: VF-162
    intent: "Implement exit criteria checks that gate phase transitions."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "orchestration/coordinator/state_machine.py"
    done_when:
      - "Phase exit criteria are explicitly evaluated before leaving a phase."
      - "Transitions are blocked when exit criteria are not satisfied."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-160: A centralized transition table exists and is enforced for phase changes.
- VF-160: Invalid transitions are rejected with a clear error payload.
- VF-161: Each phase invokes its entry action on transition.
- VF-161: Entry actions map to required orchestration steps (build spec, concept, plan, execution start).
- VF-162: Exit criteria checks are defined and enforced for each phase.
- VF-162: Transitions fail cleanly when criteria are unmet.

## Verify
- Add tests
- `pytest`

## Dependencies
- WP-0020 ✓ (SessionCoordinator lifecycle)

## Risks / Recovery
- Risk: Entry actions overlap with existing coordinator methods, causing duplicated work.
  - Mitigation: Refactor entry actions to wrap existing methods instead of re-implementing.
- Risk: Exit criteria introduce blocking conditions that stall valid flows.
  - Mitigation: Add targeted tests for expected valid transitions and baseline flows.
- Recovery: If verification fails, revert to last known-good transition logic and reapply changes incrementally with focused tests.
