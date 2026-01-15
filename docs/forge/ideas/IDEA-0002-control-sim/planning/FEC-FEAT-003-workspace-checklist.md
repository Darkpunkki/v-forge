# FEAT-003 - Initial prompt and first agent selection

- Idea: IDEA-0002-control-sim
- Run: 2026-01-15T19-44-19.716Z_run-ca96

## Tasks
- [x] TASK-007: Add initial_prompt and first_agent_id fields to Session model
  - Files: apps/api/vibeforge_api/core/session.py
  - Commands: pytest apps/api/tests/test_simulation_api.py (pass)
  - Notes: Persisted start context fields in session serialization.
- [x] TASK-008: Extend simulation start endpoint to require initial prompt and first agent
  - Files: apps/api/vibeforge_api/routers/control.py, apps/api/vibeforge_api/models/requests.py, apps/api/vibeforge_api/models/__init__.py, apps/api/tests/test_simulation_api.py
  - Commands: pytest apps/api/tests/test_simulation_api.py (pass)
  - Notes: Added validation + request schema for start context.
- [x] TASK-009: Add start context fields to simulation state response
  - Files: apps/api/vibeforge_api/models/responses.py, apps/api/vibeforge_api/routers/control.py, apps/ui/src/api/controlClient.ts, apps/api/tests/test_simulation_api.py
  - Commands: pytest apps/api/tests/test_simulation_api.py (pass)
  - Notes: State response now includes initial_prompt and first_agent_id.
- [x] TASK-010: Add initial prompt and first agent UI inputs to SimulationConfig widget
  - Files: apps/ui/src/screens/control/widgets/SimulationConfig.tsx, apps/ui/src/screens/control/widgets/TickControls.tsx, apps/ui/src/screens/ControlPanel.tsx, apps/ui/src/api/controlClient.ts
  - Commands: npm --prefix apps/ui run build (pass; required escalated permissions)
  - Notes: Start button disables until prompt/agent set.

## Notes / Decisions
- 
