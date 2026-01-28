# WP-0058 - Async Dispatch Engine (TickEngine Extension)

## Goal
Extend TickEngine to support async dispatch to remote agents, response buffering, timeout handling, and tests.

## Idea-ID
IDEA-0003-vibeforge-is-pivoting

## Included Tasks
- TASK-023 - Add agent_type, endpoint_url, connection_status fields to AgentConfig
- TASK-024 - Add async dispatch path in TickEngine.advance_tick()
- TASK-025 - Add response buffer checking to TickEngine tick loop
- TASK-026 - Add dispatch timeout handling
- TASK-027 - Add tests for async dispatch and response buffering in TickEngine

## Ordered Execution Steps
1. Implement TASK-023 (AgentConfig fields + validation)
2. Implement TASK-024 (remote dispatch path + event emission)
3. Implement TASK-025 (response buffer processing)
4. Implement TASK-026 (timeout handling for pending dispatches)
5. Implement TASK-027 (async dispatch/response buffer tests)

## Done Means
- Verification commands:
  - cd apps/api && python -m pytest

## Checklist
- [x] TASK-023 - Add agent_type, endpoint_url, connection_status fields to AgentConfig
  - Files: `orchestration/models.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine_async.py -v`
- [x] TASK-024 - Add async dispatch path in TickEngine.advance_tick()
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/connection_manager.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine_async.py -v`
- [x] TASK-025 - Add response buffer checking to TickEngine tick loop
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/connection_manager.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine_async.py -v`
- [x] TASK-026 - Add dispatch timeout handling
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/connection_manager.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine_async.py -v`
- [x] TASK-027 - Add tests for async dispatch and response buffering in TickEngine
  - Files: `apps/api/tests/test_tick_engine_async.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine_async.py -v`

## Notes / Decisions
- None yet.
