# FEAT-001 - Agent roster configuration

- Idea: IDEA-0002-control-sim
- Run: 2026-01-15T17-28-40.056Z_run-3b71

## Tasks
- [x] TASK-001 - Verify existing agent roster endpoint returns full roster with labels
  - Files: apps/api/vibeforge_api/routers/control.py, apps/api/vibeforge_api/models/responses.py, apps/api/tests/test_control_api.py
  - Verify: pytest apps/api/tests/test_control_api.py -k "initialize_agents or simulation_state"
  - Notes: Simulation state now returns roster entries with display_name, role, and model_id.
- [x] TASK-002 - Add validation for duplicate and empty agent IDs
  - Files: apps/api/vibeforge_api/models/requests.py, apps/api/vibeforge_api/routers/control.py, apps/api/tests/test_control_api.py
  - Verify: pytest apps/api/tests/test_control_api.py -k "initialize_agents or simulation_state"
  - Notes: Initialize endpoint accepts explicit roster and returns 400 for duplicates/empty IDs.
- [x] TASK-003 - Expose default role list constant for assignment UI
  - Files: apps/api/vibeforge_api/routers/control.py, apps/api/vibeforge_api/models/responses.py, apps/ui/src/api/controlClient.ts, apps/ui/src/screens/ControlPanel.tsx, apps/ui/src/screens/control/widgets/AgentAssignment.tsx
  - Verify: pytest apps/api/tests/test_control_api.py -k "initialize_agents or simulation_state"
  - Notes: UI prefers available_roles from simulation state with fallback to defaults.

## Notes / Decisions
- 
