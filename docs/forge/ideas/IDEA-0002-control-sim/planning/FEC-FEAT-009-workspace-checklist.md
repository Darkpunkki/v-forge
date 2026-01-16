# FEAT-009 - Status and tick state exposure

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-16T00-48-50.459Z_run-00e9

## Tasks
- [x] TASK-030: Verify simulation state endpoint returns complete status
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "simulation_state" -v`
  - Notes: Verified existing response fields; no code changes required.
- [x] TASK-031: Update TypeScript client types for simulation state
  - Files: `apps/ui/src/api/controlClient.ts`
  - Verify: `cd apps/ui; npx tsc --noEmit`
  - Notes: `npx tsc --noEmit` passed after the AgentDashboard typo fix.

## Notes / Decisions
- UI type check used instead of `npm run build` due to prior esbuild `spawn EPERM` issues.
