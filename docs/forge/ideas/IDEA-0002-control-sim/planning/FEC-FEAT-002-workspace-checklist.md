# FEAT-002 - Communication graph configuration

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-15T18-40-30.271Z_run-00a0

## Tasks
- [x] TASK-004: Update graph validation to allow cycles and bidirectional links
  - Files: `orchestration/models.py`, `apps/api/tests/test_orchestration_models.py`, `apps/api/tests/test_control_api.py`
  - Verify: `python -m pytest apps/api/tests/test_orchestration_models.py -k agent_flow_graph`
  - Files changed: `orchestration/models.py`, `apps/api/tests/test_orchestration_models.py`, `apps/api/tests/test_control_api.py`, `apps/api/vibeforge_api/routers/control.py`
  - Commands: `python -m pytest apps/api/tests/test_orchestration_models.py -k agent_flow_graph`
- [x] TASK-005: Store and retrieve link directionality
  - Files: `orchestration/models.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/tests/test_control_api.py`
  - Verify: `python -m pytest apps/api/tests/test_control_api.py -k flow`
  - Files changed: `orchestration/models.py`, `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/tests/test_control_api.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Commands: `python -m pytest apps/api/tests/test_control_api.py -k "configure_agent_flow_bidirectional_round_trip"`, `python -m pytest apps/api/tests/test_graph_gated_messaging.py -k bidirectional`
- [x] TASK-006: Return clear error messages for invalid link endpoints
  - Files: `orchestration/models.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_control_api.py`
  - Verify: `python -m pytest apps/api/tests/test_control_api.py -k invalid`
  - Files changed: `orchestration/models.py`, `apps/api/tests/test_orchestration_models.py`, `apps/api/tests/test_control_api.py`
  - Commands: `python -m pytest apps/api/tests/test_control_api.py -k "flow_validation"`

## Notes / Decisions
- 
