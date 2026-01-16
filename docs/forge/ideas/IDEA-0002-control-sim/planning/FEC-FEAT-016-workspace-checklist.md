# FEAT-016 - Real LLM Agent Responses with Guardrails

- Idea ID: IDEA-0002-control-sim
- Run ID: 2026-01-16T05-03-35.654Z_run-8911

## Tasks
- [x] TASK-060: Add session-level LLM configuration fields
  - Files: `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/ui/src/api/controlClient.ts`
  - Verify: `python -m pytest apps/api/tests/test_session_model.py`
  - Files changed: `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/ui/src/api/controlClient.ts`
  - Commands: `python -m pytest apps/api/tests/test_session_model.py`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).
- [x] TASK-061: Add LLM cost and rate limiting guardrails to Session
  - Files: `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/routers/control.py`
  - Verify: `python -m pytest apps/api/tests/test_simulation_api.py -k "rate or cost"`
  - Files changed: `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/models/responses.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_simulation_api.py`, `apps/ui/src/api/controlClient.ts`
  - Commands: `python -m pytest apps/api/tests/test_simulation_api.py -k "rate or cost"`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).
- [x] TASK-062: Create LlmResponseGenerator service with role-based prompts
  - Files: `orchestration/coordinator/llm_response_generator.py`, `orchestration/prompts.py` (or new prompts module)
  - Verify: `python -m pytest apps/api/tests/test_llm_integration.py -k "generator"`
  - Files changed: `orchestration/coordinator/llm_response_generator.py`, `orchestration/prompts.py`, `apps/api/tests/test_llm_integration.py`
  - Commands: `python -m pytest apps/api/tests/test_llm_integration.py -k "generate_response"`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).
- [x] TASK-063: Add agent conversation history tracking to TickEngine
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/session.py`
  - Verify: `python -m pytest apps/api/tests/test_tick_engine.py -k "conversation"`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/session.py`, `apps/api/tests/test_tick_engine.py`
  - Commands: `python -m pytest apps/api/tests/test_tick_engine.py -k "conversation"`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).
- [x] TASK-064: Wire real LLM calls into TickEngine with cost tracking
  - Files: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/routers/control.py`
  - Verify: `python -m pytest apps/api/tests/test_graph_gated_messaging.py`, `python -m pytest apps/api/tests/test_tick_engine.py`
  - Files changed: `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_tick_engine.py`, `apps/api/tests/test_graph_gated_messaging.py`
  - Commands: `python -m pytest apps/api/tests/test_graph_gated_messaging.py`, `python -m pytest apps/api/tests/test_tick_engine.py`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).
- [x] TASK-065: Add UI controls for LLM mode and cost display
  - Files: `apps/ui/src/screens/control/widgets/SimulationConfig.tsx`, `apps/ui/src/screens/control/widgets/TickControls.tsx`, `apps/ui/src/api/controlClient.ts`
  - Verify: `cd apps/ui; npx tsc --noEmit`
  - Files changed: `apps/ui/src/screens/control/widgets/SimulationConfig.tsx`, `apps/ui/src/screens/control/widgets/TickControls.tsx`, `apps/ui/src/screens/Simulation.tsx`, `apps/ui/src/api/controlClient.ts`, `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/routers/control.py`
  - Commands: `cd apps/ui; npx tsc --noEmit`
  - Notes: PowerShell does not support `&&` so the verify command uses `;`.
- [x] TASK-066: Add unit tests for LLM integration and guardrails
  - Files: `apps/api/tests/test_llm_integration.py`
  - Verify: `python -m pytest apps/api/tests/test_llm_integration.py`
  - Files changed: `apps/api/tests/test_llm_integration.py`
  - Commands: `python -m pytest apps/api/tests/test_llm_integration.py`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).
- [x] TASK-067: Add integration test for end-to-end LLM simulation
  - Files: `apps/api/tests/test_llm_simulation_integration.py`
  - Verify: `python -m pytest apps/api/tests/test_llm_simulation_integration.py`
  - Files changed: `apps/api/tests/test_llm_simulation_integration.py`
  - Commands: `python -m pytest apps/api/tests/test_llm_simulation_integration.py`
  - Notes: Pytest warnings about pydantic protected_namespaces (pre-existing).

## Notes / Decisions
