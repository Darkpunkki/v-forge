# WP-0038 — Agent dashboard UX polish

## Status
- Done
- Verified: `PYTHONPATH=/workspace/v-forge pytest`

## Context
- Chapter(s): 17 Agent Control & Monitoring UI (Post-MVP)
- Why now:
  - Agent dashboard needs more context for operators to interpret activity quickly.
  - Empty event streams currently look broken without guidance.
  - These UX tweaks improve monitoring confidence during demos.

## Goal
- Enhance agent cards with richer context and provide clear empty-state guidance for the control panel event stream.

## VF Tasks (canonical)
- [x] **VF-185 — Enhance agent cards with model tier + task description**
  - Display `model_tier` and `task_description` from event metadata in Agent Activity cards.
  - **Why needed:** Clarify routing decisions and task context per agent.
  - **Files:** `apps/ui/src/screens/control/widgets/AgentDashboard.tsx`
  - **Verify:** `PYTHONPATH=/workspace/v-forge pytest`
- [x] **VF-186 — Control Panel empty-event guidance**
  - When the event stream is empty, show a helper callout explaining how to generate EventLog events (orchestration run steps/links).
  - **Why needed:** Reduce confusion when widgets remain idle for MVP sessions.
  - **Files:** `apps/ui/src/screens/control/widgets/EventStream.tsx`, `apps/ui/src/screens/control/widgets/EventStream.css`
  - **Verify:** `PYTHONPATH=/workspace/v-forge pytest`

## Plan
### Approach
- Update agent card UI to surface model tier and task description fields.
- Ensure event metadata is wired into the Agent Activity widget data mapping.
- Design an empty-state callout for the event stream area with next-step guidance.
- Add UI tests or story coverage if available, and verify the build.

### Actionable Task Array
BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-185
    intent: "Render model tier and task description on agent cards using event metadata."
    touches:
      - "apps/ui/src/screens/control/widgets/AgentDashboard.tsx"
      - "apps/ui/src/screens/ControlPanel.tsx"
    done_when:
      - "Agent cards show model_tier and task_description when available."
      - "Missing metadata degrades gracefully without breaking layout."
    verify:
      - "pytest"
  - vf: VF-186
    intent: "Add an empty-event callout explaining how to generate EventLog events."
    touches:
      - "apps/ui/src/screens/control/widgets/EventStream.tsx"
      - "apps/ui/src/screens/ControlPanel.tsx"
    done_when:
      - "Empty event stream shows a guidance callout with actionable next steps."
    verify:
      - "pytest"
END_ACTIONABLE_TASK_ARRAY

## Acceptance Criteria
- VF-185: Agent cards include model_tier and task_description when present.
- VF-185: Layout remains usable when metadata is missing.
- VF-186: Empty event stream displays guidance instead of a blank state.

## Verify
- `pytest`

## Dependencies
- WP-0023 ✓ (Agent dashboard and token visualization)

## Risks / Recovery
- Risk: Event metadata not consistently present across sessions.
  - Mitigation: Add conditional rendering and fallback labels.
- Risk: Empty-state messaging becomes stale as workflows change.
  - Mitigation: Keep guidance concise and link to current run instructions.
- Recovery: If verification fails, revert UI changes and reintroduce fields one at a time.
