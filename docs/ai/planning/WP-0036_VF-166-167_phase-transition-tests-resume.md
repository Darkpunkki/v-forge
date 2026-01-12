# WP-0036 — Phase transition tests + session resume

## Status
- Done (2026-01-12)

## Context
- Chapter(s): 16 State Machine: MVP Phases (State Diagram)
- Why now:
  - Phase transition rules require integration coverage to prevent regression.
  - Resume-from-artifacts is needed for robustness when the API restarts mid-session.
  - The control panel expects reliable session state and event continuity.

## Goal
- Add integration tests for phase transitions and implement a minimal resume-from-artifacts capability.

## VF Tasks (canonical)
- [x] **VF-166 — Add integration tests for phase transitions**
  - Write tests that simulate the main state transitions and assert the system rejects illegal transitions, emits expected events, and persists expected artifacts.
- [x] **VF-167 — Add "resume session" capability from stored artifacts**
  - Enable restarting the API and resuming an in-progress session from artifacts/event log (initially limited scope), improving robustness and developer ergonomics.

## Plan
### Approach
- Build integration tests that exercise the full transition flow and illegal transition rejection.
- Assert event emission and artifact persistence at key phases.
- Implement a minimal resume pathway that loads session state from artifacts/event log.
- Scope resume to a limited set of phases initially to keep it safe and deterministic.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-166
    intent: "Create integration tests for phase transitions, event emission, and artifact persistence."
    touches:
      - "apps/api/tests/test_session_coordinator.py"
      - "apps/api/tests/test_control_api.py"
    done_when:
      - "Tests cover valid transitions, illegal transition rejection, and expected event/artifact outputs."
      - "Transition tests run as part of the API test suite."
    verify:
      - "pytest"
  - vf: VF-167
    intent: "Implement resume-from-artifacts for in-progress sessions with limited scope."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "apps/api/vibeforge_api/core/artifacts.py"
    done_when:
      - "Session state can be reconstructed from artifacts/event log after restart."
      - "Resume scope and limitations are documented in code or tests."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-166: Integration tests cover main phase transitions and illegal transition rejection.
- VF-166: Tests assert expected events and artifacts per phase.
- VF-167: Resume flow reconstructs session state from artifacts/event log for supported phases.
- VF-167: Resume limitations are explicit and validated by tests or documentation.

## Verify
- Add tests
- `pytest`

## Dependencies
- WP-0034, WP-0035

## Risks / Recovery
- Risk: Resume logic becomes too broad and introduces inconsistent state.
  - Mitigation: Limit resume to specific phases and document unsupported paths.
- Risk: Transition tests are brittle due to event ordering or time-sensitive data.
  - Mitigation: Assert on stable event fields and use deterministic fixtures.
- Recovery: If verification fails, isolate failures to specific transitions and adjust tests or resume scope accordingly.
