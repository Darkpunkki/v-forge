# WP-0041 — TaskGraph-backed plan/progress endpoints

## Status
- Queued

## Context
- Chapter(s): 30 MVP/Placeholder Cleanup
- Why now:
  - Plan/progress endpoints still return mocked data that does not reflect TaskGraph artifacts.
  - Control panel and UI flows need accurate, event-backed state for monitoring and approval.
  - Aligning these endpoints with artifacts is required before deeper observability work.

## Goal
- Replace mocked plan and progress responses with TaskGraph and event-derived data plus clear empty states.

## VF Tasks (canonical)
- [ ] **VF-303 — Replace mocked plan/progress responses with TaskGraph/event data**
  - Swap the hardcoded plan summary and progress scaffolding in `apps/api/vibeforge_api/routers/sessions.py` with data derived from stored TaskGraph and recent events (no fabricated feature lists or task timelines when not in EXECUTION).
  - **Status:** Planned
  - **Done when:** GET /plan and GET /progress pull from persisted artifacts/event log with sensible empty states; mock data paths removed; coverage added for both endpoints in non-EXECUTION phases.
  - **Verify:** `cd apps/api && pytest tests/test_sessions.py -k "plan or progress"` (extend with new cases for TaskGraph-backed responses).

## Plan
### Approach
- Inspect current plan/progress response scaffolding and identify mocked fields.
- Map TaskGraph and EventLog data into the existing response schemas.
- Define empty-state behavior when artifacts are not yet available.
- Extend tests for plan/progress in multiple phases with real artifacts.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-303
    intent: "Back plan/progress endpoints with TaskGraph artifacts and EventLog data, removing mock scaffolding."
    touches:
      - "apps/api/vibeforge_api/routers/sessions.py"
      - "apps/api/vibeforge_api/core/artifacts.py"
    done_when:
      - "Plan/progress responses reflect TaskGraph artifacts and event data with clear empty states."
      - "Mocked plan/progress data paths are removed."
    verify:
      - "cd apps/api && pytest tests/test_sessions.py -k \"plan or progress\""
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-303: GET /plan returns TaskGraph-backed summaries (or explicit empty state) instead of mock data.
- VF-303: GET /progress returns event-derived status (or explicit empty state) instead of mock data.
- VF-303: Tests cover plan/progress responses across relevant phases.

## Verify
- Add tests
- `cd apps/api && pytest tests/test_sessions.py -k "plan or progress"`

## Dependencies
- WP-0016 ✓, WP-0019 ✓, WP-0021 ✓

## Risks / Recovery
- Risk: TaskGraph artifacts or events may be missing in some phases, leading to incomplete responses.
  - Mitigation: Define explicit empty states and guard for missing artifacts.
- Risk: UI expects the previous mocked shape, causing regressions.
  - Mitigation: Ensure schema compatibility or coordinate UI updates with clear empty-state messaging.
- Recovery: If verification fails, reintroduce temporary fallback responses while correcting artifact/event mapping.
