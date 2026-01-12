# WP-0037 — Control panel session list usability

## Status
- Done

## Context
- Chapter(s): 17 Agent Control & Monitoring UI (Post-MVP)
- Why now:
  - Current control panel session list has mismatched fields and missing metadata.
  - Operators need phase and artifact visibility to monitor sessions effectively.
  - Usability improvements unblock later UX polish work.

## Goal
- Align control session list data with UI expectations and enrich the list with artifacts and active session details.

## VF Tasks (canonical)
- [x] **VF-181 — Fix control session list contract (phase/updated_at)**
  - Align `/control/sessions` response with Control Panel expectations (phase, updated_at, artifacts) or adapt UI to the actual payload.
  - **Why needed:** Avoid empty/mismatched session list fields and enable reliable filtering.
  - Updated `/control/sessions` to include phase, updated_at, and artifacts with stable sorting.
  - Verified via `PYTHONPATH=/workspace/v-forge pytest`.
- [x] **VF-182 — Add navigation link to Control Panel**
  - Add a main layout link to `/control` so the admin UI is discoverable without manual URL entry.
  - **Why needed:** Improve access to monitoring UI during orchestration runs.
  - Added Control Panel navigation link in the main layout.
  - Verified via `PYTHONPATH=/workspace/v-forge pytest`.
- [x] **VF-183 — Enrich control session list with artifact badges**
  - Show artifact badges (concept/build_spec/task_graph) and counts based on the `/control/sessions` artifacts array.
  - **Why needed:** Quick visibility into what each session has produced.
  - Rendered artifact badges with counts for concept/build_spec/task_graph.
  - Verified via `PYTHONPATH=/workspace/v-forge pytest`.
- [x] **VF-184 — Show active session details in sidebar list**
  - Display phase + active_task_id in the Active Sessions list (data already returned by `/control/active`).
  - **Why needed:** Faster at-a-glance view of in-flight work.
  - Added phase, active task, and updated timestamps to active session sidebar entries.
  - Verified via `PYTHONPATH=/workspace/v-forge pytest`.

## Plan
### Approach
- Confirm control API payloads for sessions and active sessions and reconcile with UI expectations.
- Update backend contract or UI mapping to ensure phase/updated_at/artifacts are populated.
- Add navigation link to /control in the main UI layout.
- Enhance session list UI with artifact badges and active session details.
- Add or update tests for control API responses and UI rendering expectations.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-181
    intent: "Align /control/sessions contract with UI expectations for phase, updated_at, and artifacts."
    touches:
      - "apps/api/vibeforge_api/routers/control.py"
      - "apps/ui/src/screens/ControlPanel.tsx"
    done_when:
      - "Session list displays phase and updated_at without undefined fields."
      - "Artifacts are consistently available in the list payload or mapped in UI."
    verify:
      - "pytest"
  - vf: VF-182
    intent: "Add a navigation link to /control in the main layout navigation."
    touches:
      - "apps/ui/src/components/Layout.tsx"
    done_when:
      - "Main navigation includes a Control Panel link that routes to /control."
    verify:
      - "pytest"
  - vf: VF-183
    intent: "Render artifact badges and counts in the control session list."
    touches:
      - "apps/ui/src/screens/ControlPanel.tsx"
      - "apps/ui/src/screens/control/widgets/SessionList.tsx"
    done_when:
      - "Artifact badges for concept/build_spec/task_graph display with counts."
    verify:
      - "pytest"
  - vf: VF-184
    intent: "Show phase and active_task_id in the active sessions sidebar list."
    touches:
      - "apps/ui/src/screens/ControlPanel.tsx"
      - "apps/ui/src/screens/control/widgets/ActiveSessions.tsx"
    done_when:
      - "Active sessions list shows phase and active_task_id for each session."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-181: /control/sessions contract provides phase, updated_at, and artifacts (or UI maps correctly).
- VF-182: Control Panel navigation link is present and functional.
- VF-183: Session list shows artifact badges with correct counts.
- VF-184: Active sessions list includes phase and active_task_id details.

## Verify
- `pytest`

## Outcomes
- Control session list and active session sidebar now surface phase, timestamps, and artifact badges.
- Navigation link added to make the Control Panel discoverable.

## Dependencies
- WP-0022 ✓ (Control panel foundation)

## Risks / Recovery
- Risk: Backend changes break existing control UI expectations.
  - Mitigation: Update UI mapping alongside API contract changes and add tests.
- Risk: Artifact data is incomplete for older sessions.
  - Mitigation: Add empty-state handling for missing artifacts.
- Recovery: If verification fails, revert to previous contract and reintroduce fields incrementally with UI guards.
