# WP-0030 — Phase transition event logging

## Status
- Queued

## Context
- Chapter(s): 14 Workflow Orchestration: Happy Path (Sequence)
- Why now:
  - Phase transition visibility is required for reliable replay/debugging in the control UI.
  - EventLog is already available and needs consistent phase change entries.
  - Aligns with observability goals for post-MVP monitoring.

## Goal
- Record every phase transition in the EventLog with before/after metadata for replayability and debugging.

## VF Tasks (canonical)
- [ ] **VF-143 — Persist phase transitions into the event log**
  - Record all state changes (oldPhase → newPhase + reason) into the EventLog for debugging and replayability.
  - **Depends on:** VF-131 (EventLog implementation)

## Plan
### Approach
- Identify all phase transition points in SessionCoordinator and ensure they emit structured events.
- Add or extend EventLog payloads to include old/new phase and reason.
- Add tests covering representative phase transitions and event payloads.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-143
    intent: "Emit phase transition events with old/new phase and reason metadata."
    touches:
      - "orchestration/coordinator/session_coordinator.py"
      - "apps/api/vibeforge_api/core/event_log.py"
      - "apps/api/tests/test_session_coordinator.py"
    done_when:
      - "Every phase change logs an event containing old phase, new phase, and reason metadata."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-143: Phase transitions are recorded in EventLog with before/after values and reason.
- Event payloads are queryable for debugging and replay use cases.
- Tests cover at least one transition path and validate event contents.

## Verify
- `pytest`

## Dependencies
- WP-0021 ✓ (EventLog)

## Risks / Recovery
- Risk: Missing some transition points -> Mitigation: centralize phase updates and instrument a single transition helper.
- Risk: Event payload shape drifts from UI expectations -> Mitigation: document payload fields and add test assertions.
- Recovery: If verification fails, focus on adding targeted unit tests for event emission and retry `pytest`.
