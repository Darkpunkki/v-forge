# FEAT-008 - Lifecycle state transitions and guardrails

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-16T00-14-51.667Z_run-d5b4

## Tasks
- [ ] TASK-025: Validate start prerequisites include initial prompt and first agent
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "start" -v`
- [ ] TASK-026: Enforce pause only when simulation is running
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "pause" -v`
- [ ] TASK-027: Implement reset with configuration preservation
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_simulation_api.py`, `apps/api/vibeforge_api/core/workspace.py`, `apps/api/vibeforge_api/core/event_log.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "reset" -v`
- [ ] TASK-028: Implement stop transition and tick rejection
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "tick" -v`
- [ ] TASK-029: Add lifecycle guardrail integration tests
  - Files: `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "lifecycle" -v`

## Notes / Decisions
- 
