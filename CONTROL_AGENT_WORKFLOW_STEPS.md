# Multi-Agent Control Workflow Implementation Steps

This document outlines the concrete steps needed to support a multi-agent workflow through the control panel, covering initialization, role/model assignment, main task execution, and agent-to-agent flow organization.

## 1) Define backend data structures
- Extend the session domain model to persist agent configuration and workflow state.
  - Update `apps/api/vibeforge_api/core/session.py` with fields like `agents`, `agent_roles`, `agent_models`, `agent_graph`, and `main_task`.
  - Ensure `SessionStore` updates persist these additions.
- Introduce request/response schemas for control workflow configuration.
  - Add new Pydantic request/response models in `apps/api/vibeforge_api/models/requests.py` and `apps/api/vibeforge_api/models/responses.py`.
  - Include validation for agent counts, supported roles, and known model IDs.

## 2) Add control workflow endpoints
- Extend `/control` with endpoints that map to each workflow action.
  - `POST /control/sessions/{id}/agents/init` → create N agents for the session.
  - `POST /control/sessions/{id}/agents/assign` → assign role + model per agent.
  - `POST /control/sessions/{id}/task` → set the main task payload for orchestration.
  - `POST /control/sessions/{id}/flows` → persist agent-to-agent communication graph.
  - `GET /control/sessions/{id}/workflow` → return current configuration for UI hydration.
- Implement in `apps/api/vibeforge_api/routers/control.py`, using `session_store.update_session()` after mutating session fields.
- Add guardrails so changes are rejected if the session is in an incompatible phase.

## 3) Wire workflow config into orchestration
- Add a workflow configuration object that the orchestrator can consume.
  - Create a dedicated data model in `orchestration/models.py` (e.g., `AgentConfig`, `AgentFlowGraph`).
  - Store these in the session and expose to the orchestration stack.
- Update `orchestration/coordinator` (session lifecycle) to accept an explicit agent configuration before execution starts.
- Update `orchestration/orchestrator.py` to:
  - Use the user-selected agent roles when generating or delegating tasks.
  - Respect the configured model per agent when routing LLM calls (possibly by adding a “forced model” option to `models/router.py`).
  - Emit agent-specific events with model/role metadata for the control stream.

## 4) Add UI surfaces in the Control Panel
- Add a new “Agent Workflow” section to the control UI.
  - Update `apps/ui/src/screens/ControlPanel.tsx` to include the workflow configuration panel.
  - Create new components in `apps/ui/src/screens/control/widgets/`:
    - `AgentInitializer.tsx` (agent count selection + init call)
    - `AgentAssignment.tsx` (roles/models per agent)
    - `AgentTaskInput.tsx` (main task submission)
    - `AgentFlowEditor.tsx` (graph/edge builder for agent organization)
- Use `apps/ui/src/api/controlClient.ts` to add typed API methods for the new endpoints.
- Add client-side validation and display current workflow state from `GET /control/sessions/{id}/workflow`.

## 5) Persist and visualize agent events
- Extend event logging to record workflow events (init, assignment, task dispatch, agent-to-agent messages).
  - Update `vibeforge_api/core/event_log.py` and event producers in `orchestration/coordinator`.
- Ensure `/control/sessions/{id}/events` includes the new event metadata so the control UI can visualize agent activity.
- Update existing widgets (e.g., `AgentDashboard`, `AgentGraph`, `EventStream`) to render the new agent metadata.

## 6) Testing & verification
- Add API tests for each new control endpoint in `apps/api/tests/test_control_api.py`.
- Add UI unit tests for the new widgets (if applicable) and verify the full workflow in the running app.
- Run the existing control panel verification steps plus targeted tests for the new endpoints.

## 7) Documentation updates
- Record any new workflow schemas or orchestration decisions in `docs/ai/design/` and `docs/ai/implementation/` if they introduce new architecture or behavior.
- Update `vibeforge_master_checklist.md` once VF tasks for the workflow are verified complete.
