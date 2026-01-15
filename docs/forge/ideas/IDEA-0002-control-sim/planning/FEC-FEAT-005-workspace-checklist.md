# FEAT-005 - Graph-gated message validation

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-15T23-36-00.234Z_run-f96a

## Tasks
- [x] TASK-016: Verify existing validate_message() covers graph constraints
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Verify: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Commands: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -v`
- [x] TASK-017: Emit blocked message events with clear format
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Verify: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Commands: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -v`
- [x] TASK-018: Ensure blocked messages do not appear as delivered
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Verify: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Commands: `python -m pytest apps/api/tests/test_graph_gated_messaging.py -v`

## Notes / Decisions
- Logged tick engine events directly to EventLog when an event_log is provided.
