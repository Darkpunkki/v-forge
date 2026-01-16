# FEAT-007 - Message event emission with tick metadata

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-16T00-06-54.631Z_run-df83

## Tasks
- [x] TASK-022: Verify message events include required metadata
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Verify: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -k "message" -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Commands: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -k "message" -v`
- [x] TASK-023: Verify tick events include old and new tick indices
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -k "advance_tick_emits_event" -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -k "advance_tick_emits_event" -v`
- [x] TASK-024: Ensure event consistency across single and multi-tick advances
  - Files: `apps/api/tests/test_simulation_api.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "advance_ticks" -v`
  - Files changed: `apps/api/tests/test_simulation_api.py`
  - Commands: `python -m pytest apps/api/tests/test_simulation_api.py -k "advance_ticks" -v`

## Notes / Decisions
- 
