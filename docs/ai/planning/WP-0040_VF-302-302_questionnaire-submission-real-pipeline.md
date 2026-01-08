# WP-0040 — Questionnaire submission real pipeline

## Status
- Done

## Context
- Chapter(s): 30 MVP/Placeholder Cleanup
- Why now:
  - The questionnaire flow still shortcuts to mock generation, blocking real orchestration paths.
  - Plan/progress endpoints depend on real artifacts produced after questionnaire completion.
  - Removing the mock path aligns user-facing flow with the post-MVP roadmap.

## Goal
- Route questionnaire completion into the real BuildSpec → concept → plan flow instead of the mock generator shortcut.

## VF Tasks (canonical)
- [x] **VF-302 — Replace MVP demo shortcut in questionnaire submission (mock generator → real pipeline)**
  - Remove the shortcut that generates mock files and jumps to COMPLETE inside `apps/api/vibeforge_api/routers/sessions.py` (submitAnswer handler). Route questionnaire completion into the real BuildSpec → concept → plan flow (or gate behind a feature flag) and retire `mock_generator.generate` as the default path.
  - **Status:** Done
  - **Done when:** Submitting the final questionnaire answer transitions to PLAN_REVIEW/IDEA with real artifacts instead of calling MockGenerator or auto-setting COMPLETE; tests updated to cover the new flow.
  - **Verify:** `cd apps/api && pytest tests/test_sessions.py -k questionnaire` (plus any new end-to-end test for non-mock flow).
  - **Files:** `apps/api/vibeforge_api/routers/sessions.py`, `apps/api/vibeforge_api/core/llm_provider.py`, `orchestration/coordinator/session_coordinator.py`, `apps/api/tests/test_sessions.py`
  - **Verified:** `cd apps/api && pytest tests/test_sessions.py -k questionnaire`

## Plan
### Approach
- Identify the current mock completion branch in the questionnaire submission handler and map its dependencies.
- Define the real pipeline handoff path into SessionCoordinator (BuildSpec → Concept → TaskGraph).
- Ensure phase transitions and artifacts align with state machine rules.
- Update tests to validate the non-mock flow and expected phase progression.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-302
    intent: "Replace the mock generator shortcut with the real BuildSpec → concept → plan pipeline after questionnaire completion."
    touches:
      - "apps/api/vibeforge_api/routers/sessions.py"
      - "orchestration/coordinator/session_coordinator.py"
    done_when:
      - "Final questionnaire answers transition to IDEA/PLAN_REVIEW with real artifacts instead of setting COMPLETE."
      - "Mock generator is no longer the default path for questionnaire completion."
    verify:
      - "cd apps/api && pytest tests/test_sessions.py -k questionnaire"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-302: Questionnaire completion routes into the real pipeline (BuildSpec → concept → plan) instead of mock generation.
- VF-302: Sessions no longer auto-complete after questionnaire submission.
- VF-302: Tests cover the new flow and validate phase transitions.

## Verify
- Add tests
- `cd apps/api && pytest tests/test_sessions.py -k questionnaire`

## Dependencies
- WP-0018 ✓, WP-0019 ✓, WP-0020 ✓

## Risks / Recovery
- Risk: Real pipeline introduces longer latency or additional failures during questionnaire completion.
  - Mitigation: Gate the new path behind a feature flag or add clear error handling for early failures.
- Risk: UI expectations depend on the mock COMPLETE state.
  - Mitigation: Ensure plan/progress endpoints return sensible interim states and update UI tests if needed.
- Recovery: If verification fails, reinstate the mock path behind a temporary flag while fixing pipeline transitions.
