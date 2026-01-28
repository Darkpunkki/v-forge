# WP-0061 - Sessionless Control Context Cleanup

## Metadata
- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-004 + EPIC-006
- **Tasks:** TASK-041, TASK-042
- **Dependencies:** None (TASK-042 depends on TASK-041)

## Goal

Remove legacy session list/status surfaces from /control, introduce a single control context id for observability, and update the control UI/API client to use that context without exposing session lists.

## Tasks Checklist

- [x] TASK-041 - Replace session list/status endpoints with control context
  - files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_control_api.py`
  - verify: `cd apps/api && python -m pytest tests/test_control_api.py -k control_context`
- [x] TASK-042 - Remove session list/status UI and wire control context
  - files: `apps/ui/src/screens/ControlPanel.tsx`, `apps/ui/src/api/controlClient.ts`, `apps/ui/src/types/api.ts`, `apps/ui/src/screens/control/widgets/SessionComparison.tsx`
  - verify: `cd apps/ui && npm run build`

## Implementation Steps

### Step 1: TASK-041 - Control context endpoint + remove session list/status endpoints

- In `apps/api/vibeforge_api/routers/control.py`:
  - Remove:
    - `GET /control/sessions`
    - `GET /control/active`
    - `GET /control/sessions/{session_id}/status`
    - `GET /control/sessions/{session_id}/bundle`
  - Add:
    - `GET /control/context` -> returns a stable `control_session_id`
      - Create once (if missing) via SessionStore
      - Return same id on subsequent calls
  - Keep all simulation endpoints and SSE event streaming intact.

- Update tests in `apps/api/tests/test_control_api.py`:
  - Remove tests for deleted endpoints
  - Add tests for `GET /control/context` (stability + shape)

### Step 2: TASK-042 - Control UI sessionless cleanup

- In `apps/ui/src/api/controlClient.ts`:
  - Remove `listAllSessions`, `getActiveSessions`, `getSessionStatus`
  - Add `getControlContext` to fetch the control session id
- In `apps/ui/src/types/api.ts`:
  - Remove session list/status response types that are no longer used
- In `apps/ui/src/screens/ControlPanel.tsx`:
  - Remove session list/sidebar/status grid usage
  - Fetch `control_session_id` via `getControlContext`
  - Use it only for SSE/event-driven widgets that still require a context
  - Remove widgets that rely on session list/status if they are no longer used

## Done Means

- /control no longer exposes session list/status/bundle endpoints
- `GET /control/context` returns a stable `control_session_id`
- ControlPanel no longer renders a session list or status grid
- controlClient.ts drops session list/status helpers; new `getControlContext()` exists
- `cd apps/ui && npm run build` succeeds
- `cd apps/api && python -m pytest` succeeds

## Verification Commands

- `cd apps/api && python -m pytest`
- `cd apps/ui && npm run build`

## Notes / Decisions

- Full `python -m pytest` run failed during teardown in `tests/test_workspace.py` due to PermissionError cleaning temp .git objects; rerun once permissions/cleanup issues are resolved.
