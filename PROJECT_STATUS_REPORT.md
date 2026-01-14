# VibeForge Project Status Report (Post-MVP)

## Scope of this report
This report reflects the current behavior and gaps observed directly from the codebase (backend, orchestration, and UI). It avoids relying on planning docs as the primary source of truth.

## How the app works today

### Session mode (end-user flow)
- **Session lifecycle & phases:** The FastAPI session router exposes the primary session endpoints (`/sessions`, `/question`, `/answers`, `/plan`, `/progress`, `/clarification`, `/result`) and enforces phase guards (e.g., result only in `COMPLETE`).
- **Questionnaire → plan → execution:** When the questionnaire completes, the coordinator builds the BuildSpec, generates a concept, and generates a task graph; plan review then gates execution with approval/decline logic.
- **Execution loop & observability:** The coordinator executes tasks and appends events to the event log; progress endpoint aggregates events into task progress summaries.
- **LLM safe-mode:** If `VIBEFORGE_LLM_MODE=stub` or `VIBEFORGE_NO_SPEND=true`, orchestration uses a deterministic stub client; otherwise it uses OpenAI when `OPENAI_API_KEY` is set.
- **Storage model:** Sessions are stored in-memory, so session data is lost on API restarts.

### Control mode (operator flow)
- **Control endpoints:** The `/control` router exposes session listing, SSE event streaming, prompt/LLM trace inspection, and workflow configuration (agents, roles, model overrides, flow graph, main task).
- **Simulation endpoints:** Simulation configuration and tick endpoints exist (`/simulation/config`, `/simulation/start`, `/simulation/tick(s)`, `/simulation/state`), but the tick advancement is currently a placeholder that only increments counters.
- **Control panel UI:** The React control panel surfaces session lists, live events, and workflow configuration widgets for agent initialization, role/model assignment, main task, and flow graph editing.

## How to run (from code behavior)

### Backend (Session + Control API)
- The API entry point is `vibeforge_api.main:app`, with routers for sessions and control, and CORS preconfigured for the local UI.

### UI (Session + Control screens)
- The UI is a Vite + React app with routes for the session flow and control panel. It defaults to talking to `http://localhost:8000` unless `VITE_API_BASE` is provided.

## Current status by epic (code-derived)

### Epic: Session orchestration & phase enforcement
- Sessions, phase guards, and questionnaire-to-plan-to-execution routing are implemented in the session router and coordinator.
- Clarification flow exists when execution needs user input.

### Epic: Orchestration + LLM integration
- The orchestrator generates concept/task graph/run summary via templated prompts, validates outputs, and logs LLM requests/responses to the event log.
- A deterministic stub LLM client is available for no-spend flows.

### Epic: Workspace + artifact management
- Workspace setup, artifact storage, and event log infrastructure are integrated into the session coordinator and progress reporting.

### Epic: Control panel observability
- Control endpoints stream events and surface prompt/response traces.
- The UI displays session status, event streams, and LLM-related widgets.

### Epic: Control-mode simulation scaffolding
- API models and endpoints exist to initialize agents, assign roles/models, set a main task, configure a flow graph, and configure simulation tick behavior.
- A tick engine exists in orchestration to model message passing and graph-gated communication, but it is not wired to the API endpoints.

### Epic: UI shell
- The UI provides routes and screens for session flow and the control panel, but it lacks simulation tick controls or agent-message views.

## What works vs. what doesn’t (from code)

### Works
- Session lifecycle endpoints with phase enforcement.
- LLM stub mode for deterministic runs without API spend.
- Event logging and SSE streaming of session events for observability.
- Control panel UI for session monitoring and workflow configuration.

### Does not work / incomplete
- Control-mode simulation ticks are placeholders; no agent-to-agent message execution occurs in the tick endpoints.
- Tick engine isn’t integrated with control endpoints, so graph-gated messaging doesn’t power the simulation API.
- UI lacks controls for simulation start/stop/tick and lacks per-agent message views.
- Workflow configuration is not persisted beyond in-memory session store lifespan.

## Duplicates or overlaps
- **Progress vs. control event streams:** `/sessions/{id}/progress` aggregates event log data while `/control/sessions/{id}/events` streams the same underlying event log, creating two paths to similar data.
- **Tick lifecycle duplication:** Session state tracks tick fields while the tick engine maintains its own message queue and tick state; these are currently parallel without API integration.

## Required control-mode simulation workflow: gaps & steps to implement
Below are the required capabilities and the concrete steps/locations to implement them. This is an enumeration only; no implementation work was done.

1. **Set number of agents, models, roles/names**
   - **Backend:** Extend `InitializeAgentsRequest` to accept optional display names + default model assignments; allow `AssignAgentRoleRequest` to capture agent display names if not already set.
   - **Session store:** Persist display names and model overrides in `Session.agents` and/or `Session.agent_models`.
   - **UI:** Expand `AgentInitializer` to capture names and default model choices; extend `AgentAssignment` to allow editing display names.
   - **Where:** `apps/api/vibeforge_api/models/requests.py`, `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/ui/src/screens/control/widgets/AgentInitializer.tsx`, `apps/ui/src/screens/control/widgets/AgentAssignment.tsx`.

2. **Set a max limit of API calls per simulation**
   - **Backend:** Introduce an API-call budget field (e.g., `api_call_budget` and `api_calls_used`) in `Session`.
   - **Enforcement:** Increment counts in `AgentFramework.runTask` or orchestration LLM call boundaries, and block/return a terminal tick state when budget is exceeded.
   - **Control endpoints:** Add fields to simulation config request/response for call limits and display them in control UI.
   - **Where:** `apps/api/vibeforge_api/core/session.py`, `models/agent_framework.py`, `orchestration/orchestrator.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/ui/src/api/controlClient.ts`, `apps/ui/src/screens/control/widgets/*`.

3. **Define agent hierarchy / communication graph**
   - **Backend:** Existing `AgentFlowGraph` already supports edges and validation, but it must be used by the simulation runtime.
   - **Integration:** Wire `TickEngine` into simulation endpoints and validate messages against `AgentFlowGraph` on every tick.
   - **Where:** `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/routers/control.py`.

4. **Set an initial prompt and simulate agent-to-agent conversations**
   - **Backend:** Add an endpoint to seed the first message or incorporate `main_task` into an initial message queue in `TickEngine`.
   - **Simulation runtime:** Implement a message handler per tick that consumes message queue entries and triggers agent responses (via `AgentFramework` or a lightweight stub for simulation).
   - **Where:** `apps/api/vibeforge_api/routers/control.py`, `orchestration/coordinator/tick_engine.py`, `models/agent_framework.py`.

5. **Simulation advances by ticks (1 tick = one action)**
   - **Backend:** Replace placeholder tick increment with `TickEngine.advance_tick()` and persist the resulting events/messages into the event log.
   - **Session state:** Store tick results/events (and message queue state) between calls for deterministic stepping.
   - **Where:** `apps/api/vibeforge_api/routers/control.py`, `orchestration/coordinator/tick_engine.py`, `apps/api/vibeforge_api/core/session.py`.

6. **UI should show messages for each agent**
   - **Backend:** Expose an endpoint to fetch messages per agent and/or stream message events via SSE.
   - **UI:** Add a control panel widget that groups messages by agent and displays tick metadata (sent/delivered/blocked).
   - **Where:** `apps/api/vibeforge_api/routers/control.py`, `apps/ui/src/api/controlClient.ts`, `apps/ui/src/screens/control/widgets/*`.

## Configuration requirements & prerequisites
- **LLM configuration:** For real model calls, provide `OPENAI_API_KEY`. For deterministic local runs, set `VIBEFORGE_LLM_MODE=stub` or `VIBEFORGE_NO_SPEND=true`.
- **UI API base:** `VITE_API_BASE` (optional) to point the UI to a non-default API host.

## Architecture check: local model replacement readiness
- The model routing system and local provider stub show a clear seam for swapping in local inference, but the `LocalProvider` is not implemented and currently raises `NotImplementedError`. The architecture is ready for a drop-in provider, but it requires concrete backend integration before it can replace OpenAI in practice.

## Open questions for the developer
1. Should simulation mode be decoupled from the production execution pipeline, or should it reuse the same `SessionCoordinator.execute_next_task()` logic with a message-driven wrapper?

- Simulation mode should be decoupled from the production execution pipeline. 

2. Is the intended control-mode simulation purely agent-to-agent messaging, or should it execute real task graph steps as well?

- The control-mode simulation is intended purely for agent to agent messaging, for now. Basically i just want to have a nice looking and convenient web UI for orchestrating agents messaging eachother. Will expand to more complex task completion later.

3. Do you want the tick engine to persist messages/events in the session store or in a dedicated simulation store (to survive API restarts)?

- tick engine doesnt need to survive API restarts, for now.

4. What should the default policy be when an API-call budget is reached mid-tick (pause, mark failed, or auto-reset)?

- One tick should only allow for one API-call to happen. A tick represents an action over one unit of time. For example if there is a message queue, one tick advances all messages by one.

5. How should “agent names” map to roles for routing—are roles optional in simulation, or mandatory for all agents?

- Agents can be freely named, per session, by the user. Not bound to anything, just nice fun names

6. Should the control panel eventually allow selecting local model backends (ollama/vLLM/etc.), or only override model IDs while keeping a single provider?

- control panel should eventually allow selecting local model backends
