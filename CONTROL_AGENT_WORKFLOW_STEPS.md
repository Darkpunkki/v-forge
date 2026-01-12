# Multi-Agent Control Workflow Implementation Steps

This document outlines the concrete steps needed to support a **UI-driven multi-agent simulation** through the Control Panel, covering initialization, role/model assignment, hierarchy/flow setup, tick-based simulation control, agent-to-agent messaging visualization, and event persistence.

---

## Goal statement (UI-driven simulation + multi-agent messaging)

**The application must support a UI-configured simulation that demonstrates how agents coordinate work.**

Before starting the simulation, the Control Panel must allow the user to:

1) **Select agent pool**
- Choose **N agents** to participate in the session.
- Choose a **model per agent** (from supported model IDs).

2) **Build an agent hierarchy (communication graph)**
- Arrange agents into a **hierarchy/graph** by drawing links (edges).
- **Linked agents may communicate directly**. Messages should be allowed only along configured edges unless explicitly permitted by orchestration rules (e.g., system broadcast).

3) **Control simulation pace**
- Set simulation pace to:
  - **Manual ticks** (advance step-by-step)
  - (Optional later) **Auto-run** with a configurable delay

4) **Visualize agent-to-agent messaging**
- The UI must display a **multi-agent conversation view** where messages are grouped by agent and include:
  - sender agent
  - recipient agent (or broadcast/system)
  - timestamp and/or tick index
  - agent role + model used
  - message/event type (plan / task / review / fix / etc.)

---

## 1) Define backend data structures

### 1.1 Extend the session domain model
- Extend the session domain model to persist agent configuration and simulation state.
  - Update `apps/api/vibeforge_api/core/session.py` with fields like:
    - `agents` (list of agent ids / agent objects)
    - `agent_roles` (role per agent)
    - `agent_models` (model per agent)
    - `agent_graph` (edge list / adjacency structure for communication)
    - `main_task` (the simulation’s main task payload)
    - **Simulation control fields**
      - `simulation_mode`: `"manual" | "auto"`
      - `tick_index`: `int` (starts at 0)
      - `tick_status`: `"idle" | "running" | "blocked" | "completed"`
      - (Optional) `auto_delay_ms`: `int`
      - (Optional) `tick_budget`: max events/messages per tick for safety
- Ensure `SessionStore` updates persist these additions.

### 1.2 Introduce request/response schemas
- Add new Pydantic request/response models in:
  - `apps/api/vibeforge_api/models/requests.py`
  - `apps/api/vibeforge_api/models/responses.py`
- Include validation for:
  - agent counts (min/max bounds)
  - supported roles
  - known model IDs
  - graph edges (valid agent ids, no self-edge unless allowed, no duplicates)
  - simulation configuration (mode and delay constraints)

---

## 2) Add control workflow endpoints

Extend `/control` with endpoints that map to each workflow action.

### 2.1 Agent configuration endpoints (existing + refined)
- `POST /control/sessions/{id}/agents/init` → create N agents for the session.
- `POST /control/sessions/{id}/agents/assign` → assign role + model per agent.
- `POST /control/sessions/{id}/task` → set the main task payload for orchestration.
- `POST /control/sessions/{id}/flows` → persist agent-to-agent communication graph (directed edges recommended).
- `GET /control/sessions/{id}/workflow` → return current configuration for UI hydration.

Implement in `apps/api/vibeforge_api/routers/control.py`, using `session_store.update_session()` after mutating session fields.

### 2.2 Simulation lifecycle endpoints (new)
- `POST /control/sessions/{id}/simulation/config`
  - sets `simulation_mode` and (optional) `auto_delay_ms`
- `POST /control/sessions/{id}/simulation/start`
  - validates the session is “ready to simulate” (agents+roles+models+graph+main_task)
  - locks configuration to prevent edits during a run (unless reset)
- `POST /control/sessions/{id}/simulation/reset`
  - clears tick index and pending queues; optionally preserves the configured workflow

### 2.3 Tick control endpoints (new)
- `POST /control/sessions/{id}/simulation/tick`
  - advances exactly **one** tick
  - returns events/messages produced + updated tick state
- `POST /control/sessions/{id}/simulation/ticks`
  - advances **N** ticks (bounded by safety limits)
- `POST /control/sessions/{id}/simulation/pause`
  - pauses auto-run (optional; relevant if auto-run is implemented)
- `GET /control/sessions/{id}/simulation/state`
  - returns `tick_index`, `simulation_mode`, `tick_status`, and queued-work summary

### 2.4 Event/message retrieval endpoints (recommended for UI)
- Option A: Extend the existing events endpoint with filtering:
  - `GET /control/sessions/{id}/events?tick=…&agent=…&type=…`
- Option B: Add a message-shaped endpoint for UI convenience:
  - `GET /control/sessions/{id}/messages?tick=…&agent=…`

### 2.5 Guardrails
- Reject changes if the session is in an incompatible phase/state (e.g., after simulation start).
- Reject ticks unless the session is “ready” and started.
- Enforce graph constraints (messages only allowed along configured edges unless explicitly permitted).

---

## 3) Wire workflow config into orchestration

### 3.1 Add a workflow configuration object
- Create a dedicated data model in `orchestration/models.py` (e.g., `AgentConfig`, `AgentFlowGraph`, `SimulationConfig`, `TickState`).
- Store these in the session and expose to the orchestration stack.

### 3.2 Introduce tick semantics (Tick Engine)
- Add a “tick engine” in `orchestration/coordinator/` that:
  - reads session state + pending queues
  - performs **one discrete unit of progress** per tick
  - emits events/messages for everything it did
- Define what “one tick” means in your system (pick one, then standardize it):
  - one scheduling cycle, or
  - one agent message exchange batch, or
  - one state-machine transition batch

### 3.3 Graph-gated messaging
- Enforce that a message from agent A → agent B is allowed only if:
  - an edge A→B exists in `agent_graph`, **or**
  - the message is a system/orchestrator broadcast explicitly allowed by rules
- If blocked, emit a specific event (e.g., `MESSAGE_BLOCKED_BY_GRAPH`) so UI can show why nothing happened.

### 3.4 Model routing must respect UI selections
- Update `orchestration/orchestrator.py` to:
  - use the user-selected roles when generating/delegating tasks
  - respect the configured model per agent when routing LLM calls
- Optionally add a “forced model” option to `models/router.py`:
  - routing should check `agent.model_override` first, then fall back to policy routing.

### 3.5 Emit agent-specific events for the control stream
- Events should include consistent metadata:
  - `tick_index`
  - `agent_id`, `agent_role`, `agent_model`
  - `event_type`
  - `payload` (message text, task refs, review results, etc.)

---

## 4) Add UI surfaces in the Control Panel

### 4.1 Agent Workflow section (existing + expanded)
- Add a new “Agent Workflow” section to the control UI.
  - Update `apps/ui/src/screens/ControlPanel.tsx` to include the workflow configuration panel.
  - Create new components in `apps/ui/src/screens/control/widgets/`:
    - `AgentInitializer.tsx` (agent count selection + init call)
    - `AgentAssignment.tsx` (roles/models per agent)
    - `AgentTaskInput.tsx` (main task submission)
    - `AgentFlowEditor.tsx` (graph/edge builder for agent organization; directional edges recommended)

### 4.2 Simulation section (new)
- Add a “Simulation” panel to control pace and ticks:
  - `SimulationConfig.tsx` (manual vs auto, optional delay)
  - `TickControls.tsx` (run 1 tick, run N ticks, pause, reset; show current tick + status)

### 4.3 Messaging visualization (new or enhanced)
- Add/extend widgets to display multi-agent messaging clearly:
  - `MultiAgentMessages.tsx` (conversation-style grouped by agent)
  - Enhance `EventStream` to support filters by tick/agent/type

### 4.4 Typed API client updates
- Use `apps/ui/src/api/controlClient.ts` to add typed API methods for:
  - init/assign/task/flows/workflow hydration
  - simulation config/start/reset/state
  - tick endpoints
  - event/message feed filtering

### 4.5 Client-side validation
- Validate agent counts, model IDs, and graph integrity before sending payloads.
- Display “locked” state after simulation start to prevent confusion.

---

## 5) Persist and visualize agent events

### 5.1 Extend event logging
- Extend event logging to record workflow + simulation events:
  - init, assignment, flow updates
  - simulation start/reset
  - tick start/completed/blocked
  - agent-to-agent messages
- Update:
  - `vibeforge_api/core/event_log.py`
  - event producers in `orchestration/coordinator`

### 5.2 Event schema additions
- Ensure each event includes:
  - `session_id`
  - `tick_index` (when applicable)
  - `agent_id` (when applicable)
  - `event_type`
  - `payload`
- Recommended event types:
  - `SIMULATION_STARTED`, `SIMULATION_RESET`
  - `TICK_STARTED`, `TICK_COMPLETED`, `TICK_BLOCKED`
  - `AGENT_MESSAGE_SENT`
  - `MESSAGE_BLOCKED_BY_GRAPH`

### 5.3 Efficient querying/filtering for UI
- Ensure server-side filtering is supported by:
  - tick index
  - agent id
  - event type
- For responsiveness, have tick endpoints return:
  - `events_in_tick: [...]`
  - optionally `messages_in_tick: [...]` (UI convenience)

---

## 6) Testing & verification

### 6.1 API tests
- Add tests for each new control endpoint in `apps/api/tests/test_control_api.py` (or split into control + simulation tests).
- Add tests that verify core behavior:
  - cannot `simulation/start` without agents + roles/models + graph + main task
  - `tick` increments `tick_index` exactly once
  - messages blocked when no edge exists
  - messages allowed when edge exists
  - forced model override is applied (can be verified via stubbed provider / call args)

### 6.2 UI tests (as applicable)
- Unit tests for widgets:
  - graph editor produces correct edge payload
  - tick button appends messages/events to UI view
  - filters by tick/agent work as expected

### 6.3 Manual verification checklist
- Configure agents + models
- Draw graph edges
- Set main task
- Start simulation
- Run ticks manually and observe:
  - state progression
  - messages/events produced
  - blocked ticks reported clearly (if no legal moves)

---

## 7) Documentation updates

- Record any new workflow schemas, tick semantics, and orchestration decisions in:
  - `docs/ai/design/`
- Add a brief “Simulation contract” section documenting:
  - what a tick means
  - what “blocked” means
  - minimum message/event fields the UI must display
- Update `vibeforge_master_checklist.md` once VF tasks for the workflow are verified complete.
