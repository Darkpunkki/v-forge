# WP-0057 - Live Agent Control Backend Endpoints

## Goal
Add REST endpoints to /control for agent registration, task dispatch, follow-up, status queries, and agent-scoped SSE streaming, with integration tests.

## Idea-ID
IDEA-0003-vibeforge-is-pivoting

## Included Tasks
- TASK-019 - Add agent registration and listing endpoints to /control
- TASK-020 - Add task dispatch and follow-up endpoints
- TASK-021 - Extend SSE streaming with agent-specific event types
- TASK-022 - Add integration tests for agent control endpoints

## Ordered Execution Steps
1. Implement TASK-019 (agent registration/list/detail endpoints + models)
2. Implement TASK-020 (dispatch, follow-up, task status endpoints + models)
3. Implement TASK-021 (agent event streaming + per-agent SSE endpoint)
4. Implement TASK-022 (integration tests)

## Done Means
- Verification commands:
  - cd apps/api && python -m pytest

## Checklist
- [x] TASK-019 - Add agent registration and listing endpoints to /control
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/vibeforge_api/models/__init__.py`, `apps/api/vibeforge_api/core/connection_manager.py`
  - Verify: `python -m pytest apps/api/tests/test_control_agents.py -v`
- [x] TASK-020 - Add task dispatch and follow-up endpoints
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/core/connection_manager.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/models/responses.py`
  - Verify: `python -m pytest apps/api/tests/test_control_agents.py -v`
- [x] TASK-021 - Extend SSE streaming with agent-specific event types
  - Files: `apps/api/vibeforge_api/routers/control.py`
  - Verify: `python -m pytest apps/api/tests/test_control_agents.py -v`
- [x] TASK-022 - Add integration tests for agent control endpoints
  - Files: `apps/api/tests/test_control_agents.py`
  - Verify: `python -m pytest apps/api/tests/test_control_agents.py -v`

## Notes / Decisions
- None yet.
