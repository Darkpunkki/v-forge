# FEAT-004 - Tick advancement with per-agent activity cap

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-15T23-05-06.253Z_run-7cb8

## Tasks
- [x] TASK-011: Wire TickEngine to control API tick endpoints
  - Files: `apps/api/vibeforge_api/routers/control.py`, `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/models/responses.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "advance_tick or advance_ticks" -v`
  - Files changed: `apps/api/vibeforge_api/routers/control.py`, `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/session.py`
  - Commands: `python -m pytest apps/api/tests/test_simulation_api.py -k "advance_tick or advance_ticks" -v`
- [x] TASK-012: Implement FIFO single-event-per-tick processing
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -v`
- [x] TASK-013: Implement per-agent activity cap tracking
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -v`
- [x] TASK-014: Return tick summary from tick endpoints
  - Files: `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/ui/src/api/controlClient.ts`, `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "advance_tick or advance_ticks" -v`
  - Files changed: `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/ui/src/api/controlClient.ts`, `apps/api/tests/test_simulation_api.py`
  - Commands: `python -m pytest apps/api/tests/test_simulation_api.py -k "advance_tick or advance_ticks" -v`
- [x] TASK-015: Add tick engine unit tests for FIFO and activity cap
  - Files: `apps/api/tests/test_tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -v`
  - Files changed: `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -v`

## Notes / Decisions
- Tick summaries treat "messages_sent" as messages delivered in the tick.
