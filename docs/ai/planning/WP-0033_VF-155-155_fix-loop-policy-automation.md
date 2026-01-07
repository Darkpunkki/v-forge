# WP-0033 — Fix loop policy automation

## VF Tasks
- VF-155: Automate repair-loop policy when verification fails to generate fix attempts or user choices.

## Plan
1) Review existing verification failure handling and retry escalation behavior.
2) Implement fix-loop policy automation for verification failures.
3) Add/adjust tests covering fix-loop decision logic.
4) Run WP verification commands.

## Done means…
- Verification failure paths trigger fix-loop policy decisions (auto-repair vs user choice).
- Tests cover the new behavior.
- Verification commands:
  - `pytest`

## Checklist
- [x] VF-155
  - Files: `orchestration/coordinator/session_coordinator.py`, `runtime/task_master.py`, `apps/api/vibeforge_api/core/session.py`
  - Tests: `PYTHONPATH=/workspace/v-forge pytest`
