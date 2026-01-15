# FEAT-006 - Deterministic stubbed responses

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-15T23-50-29.119Z_run-f5b8

## Tasks
- [x] TASK-019: Implement deterministic stub response generator
  - Files: `orchestration/coordinator/tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -k "stub" -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -k "stub" -v`
- [x] TASK-020: Integrate stub response generation into tick processing
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -k "stub" -v`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -k "stub" -v`
- [x] TASK-021: Add stub response tests for determinism
  - Files: `apps/api/tests/test_tick_engine.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -k "stub" -v`
  - Files changed: `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -k "stub" -v`

## Notes / Decisions
- Stub responses are queued with `is_stub` metadata and bypass validation to keep deterministic replies flowing.
