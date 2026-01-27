---
doc_type: existing_solution_map
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T18-37-15.147Z_run-ca47"
generated_by: "Existing Solution Map"
generated_at: "2026-01-27T21:05:00+02:00"
scope:
  epic: "ALL"
inputs_used:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/features_backlog.md"
status: "Draft"
---

# Existing Solution Map

## Scope
- Idea: IDEA-0003-vibeforge-is-pivoting
- Epic scope: ALL (EPIC-001 through EPIC-008)
- Features included: FEAT-001 through FEAT-022

## Existing "happy path" flow (as implemented today)

### /simulation flow (working)
1. User creates a session via `POST /control/sessions/{session_id}/agents/init`
2. Assigns roles/models via `POST .../agents/assign`
3. Configures flow graph via `POST .../flows`
4. Sets main task via `POST .../task`
5. Configures simulation via `POST .../simulation/config`
6. Starts simulation via `POST .../simulation/start`
7. Advances ticks via `POST .../simulation/tick` or `.../simulation/ticks`
8. TickEngine processes messages using graph-gated routing, generates LLM responses (stub or real), tracks delegation chains
9. UI receives events via SSE at `GET /control/sessions/{session_id}/events`
10. User can pause/stop/reset simulation

### /session flow (legacy, to be removed)
1. `POST /sessions` creates a new session
2. Questionnaire phase → build spec → concept → task graph → execution → verification → complete
3. Fully automated pipeline with clarification gates
4. 6 UI screens: Home, Questionnaire, PlanReview, Progress, Clarification, Result

### /control observability (partially working)
1. `GET /control/sessions` lists all sessions with metadata
2. `GET /control/active` lists non-terminal sessions
3. SSE event streaming for real-time monitoring
4. Filtered event queries, prompt inspection, LLM trace, debug message log
5. Session bundle export

## Reuse-first decisions (hard rules)

- **Extend `Session` model** (`core/session.py`); do NOT create a parallel state model. Add agent connection info, response queue fields to the existing class.
- **Extend `EventLog` + `EventType`** (`core/event_log.py`); do NOT create a separate event system. Add new event types for agent bridge events (AGENT_CONNECTED, AGENT_DISCONNECTED, TASK_DISPATCHED, AGENT_PROGRESS, AGENT_RESPONSE).
- **Extend `/control` router** (`routers/control.py`); do NOT create a new router for agent management. Add registration, dispatch, and status endpoints to existing router.
- **Extend `TickEngine`** (`orchestration/coordinator/tick_engine.py`); do NOT create a parallel dispatch engine. Add async dispatch mode and response buffering to the existing engine.
- **Reuse `SessionStore`** (`core/session.py`); the in-memory session store serves both /control and /simulation. Do NOT replace it.
- **Reuse SSE streaming** (`sse_starlette`); the existing `EventSourceResponse` pattern works for agent events. Do NOT switch to a different streaming mechanism for UI delivery.
- **Reuse `AgentConfig`, `AgentFlowGraph`, `AgentFlowEdge`** (`orchestration/models.py`); extend with `agent_type` field to distinguish simulation agents from remote agents.
- **Reuse `controlClient.ts`** (`apps/ui/src/api/controlClient.ts`); extend with functions for agent registration, task dispatch, and connection status queries.
- **Keep `WorkspaceManager`** (`core/workspace.py`) stable; it's used by event log paths and session isolation.

## Key extension points (by capability area)

### API/endpoint layer
- **Existing**: `/control` router at `apps/api/vibeforge_api/routers/control.py` (1257 lines) — 22+ endpoints covering session listing, SSE streaming, agent workflow config, simulation lifecycle, and tick control.
- **Extend by**: Adding agent registration endpoints (`POST /control/agents/register`, `GET /control/agents`, `GET /control/agents/{agent_id}`), task dispatch endpoints (`POST /control/agents/{agent_id}/dispatch`, `POST /control/agents/{agent_id}/followup`), and connection status endpoints. All in the existing control router.
- **Watch-outs**: The control router imports from `vibeforge_api.models` and `vibeforge_api.core.session`. New endpoints need matching request/response Pydantic models. The router currently does lazy imports inside endpoint functions — follow this pattern for new endpoints.

- **Existing**: `/sessions` router at `apps/api/vibeforge_api/routers/sessions.py` — 9 legacy endpoints. To be deleted.
- **Extend by**: N/A — delete entirely. The session store and session model remain.

- **Existing**: `main.py` mounts two routers (`sessions` prefix="/sessions", `control` no prefix). WebSocket is not yet mounted.
- **Extend by**: Remove sessions router import/mount. Add WebSocket endpoint mount for `/ws/agent-bridge`. Mount new agent bridge router if separate from control.

### Core logic / domain layer
- **Existing**: `Session` model in `core/session.py` (431 lines) — contains both questionnaire state (dead after pivot) and agent workflow/simulation state (~30 fields for agents, flow graph, tick state, LLM config, cost tracking, delegation tracking, message queue).
- **Extend by**: Adding fields for remote agent connections: `agent_connections: dict[str, dict]` (agent_id → connection info), `pending_dispatches: dict[str, dict]` (message_id → dispatch info), `response_buffer: list[dict]` (buffered async responses). Update `to_dict()` and `from_dict()` accordingly.

- **Existing**: `EventLog` in `core/event_log.py` (232 lines) — JSONL append-only event store with `EventType` enum (28 types), `Event` dataclass, multi-criteria filtering. Events have: session_id, event_type, timestamp, task_id, metadata.
- **Extend by**: Adding new EventType values: `AGENT_CONNECTED`, `AGENT_DISCONNECTED`, `TASK_DISPATCHED`, `AGENT_PROGRESS`, `AGENT_RESPONSE`, `AGENT_ERROR`, `AGENT_HEARTBEAT_LOST`. These events flow through the existing SSE pipeline automatically.

- **Existing**: `WorkspaceManager` in `core/workspace.py` (207 lines) — session-isolated directories under `workspace_root`.
- **Extend by**: No changes needed; event logs already use workspace paths.

### Models / state / schemas
- **Existing**: `orchestration/models.py` (486 lines) — `AgentConfig` (Pydantic), `AgentRole` enum (orchestrator/foreman/worker/reviewer/fixer), `AgentFlowGraph`, `AgentFlowEdge`, `SimulationConfig`, `TickState`. Also legacy: `ConceptDoc`, `Task`, `TaskGraph`, `RunSummary`.
- **Reuse by**: Extending `AgentConfig` with `agent_type: str = "simulation"` (values: "simulation" | "remote"). Adding `endpoint_url: Optional[str]`, `auth_token: Optional[str]`, `connection_status: str = "disconnected"` for remote agents.

- **Existing**: `apps/api/vibeforge_api/models/requests.py` (155 lines) — Pydantic request models. Session-specific: `SubmitAnswerRequest`, `PlanDecisionRequest`, `ClarificationAnswerRequest`. Agent workflow: `AgentInitConfig`, `InitializeAgentsRequest`, `AssignAgentRoleRequest`, `SetMainTaskRequest`, `ConfigureAgentFlowRequest`. Simulation: `SimulationConfigRequest`, `SimulationStartRequest`, `TickRequest`, `SimulationResetRequest`.
- **Reuse by**: Removing session-specific request models (FEAT-002). Adding agent bridge request models: `RegisterAgentRequest`, `DispatchTaskRequest`, `FollowUpRequest`.

- **Existing**: `apps/api/vibeforge_api/models/responses.py` (231 lines) — Pydantic response models. Session-specific: `SessionResponse`, `QuestionResponse`, `PlanSummaryResponse`, etc. Agent/simulation: `InitializeAgentsResponse`, `SimulationConfigResponse`, `TickResponse`, `SimulationStateResponse`, etc.
- **Reuse by**: Removing session-specific response models. Adding: `AgentConnectionResponse`, `TaskDispatchResponse`, `AgentStatusResponse`.

### UI layer
- **Existing**: `apps/ui/src/screens/ControlPanel.tsx` (473 lines) — observability-focused. Imports 9 monitoring widgets. Two-panel layout: sidebar for session selection, main for monitoring widgets.
- **Extend by**: Reworking to agent-centric layout. Replace session sidebar with agent registration panel. Add task dispatch panel and streaming output view. Retain event stream and cost analytics widgets.

- **Existing**: `apps/ui/src/screens/Simulation.tsx` (436 lines) — simulation sandbox. Imports 7 simulation widgets. Creates sessions, configures agents/flow, runs tick-based simulation.
- **Extend by**: No changes required for MVP. Keep as-is.

- **Existing**: 17 control/simulation widgets in `apps/ui/src/screens/control/widgets/` (~4,198 lines total). Key reusable widgets:
  - `AgentInitializer.tsx` (56 lines) — agent creation form
  - `AgentAssignment.tsx` (93 lines) — role/model assignment
  - `AgentFlowEditor.tsx` (153 lines) — flow graph edge editor
  - `AgentGraph.tsx` (220 lines) — graph visualization
  - `MultiAgentMessages.tsx` (416 lines) — message flow display
  - `EventStream.tsx` (314 lines) — real-time event log
  - `TickControls.tsx` (520 lines) — tick management
  - `SimulationConfig.tsx` (569 lines) — simulation configuration
  - `CostAnalytics.tsx` (265 lines) — cost tracking
  - `PromptInspector.tsx` (237 lines) — LLM prompt/response viewer
- **Extend by**: Creating new widgets for /control: `AgentRegistrationPanel.tsx` (register by name + URL), `TaskDispatchPanel.tsx` (chat-style task input), `StreamingOutputView.tsx` (SSE-driven real-time output), `AgentConnectionDashboard.tsx` (grid of agent cards with status).

- **Existing**: `apps/ui/src/api/controlClient.ts` (565 lines) — typed API client for all /control endpoints.
- **Extend by**: Adding functions: `registerAgent()`, `listAgents()`, `getAgentStatus()`, `dispatchTask()`, `sendFollowUp()`, `getTaskStatus()`.

- **Existing**: `apps/ui/src/api/client.ts` (162 lines) — legacy session API client.
- **Extend by**: Delete entirely (FEAT-003).

- **Existing**: `apps/ui/src/types/api.ts` (138 lines) — shared TypeScript types.
- **Extend by**: Removing session-specific types. Adding: `RemoteAgent`, `AgentConnectionStatus`, `TaskDispatch`, `AgentEvent`.

### Orchestration / simulation
- **Existing**: `orchestration/coordinator/tick_engine.py` (1057 lines) — full tick-based simulation engine. Key: `Message` dataclass, `TickEngine` class with `advance_tick()` (async), `send_message()`, `validate_message()`. Processes one message per tick in FIFO order. Graph-gated routing. Delegation chain tracking. LLM response generation (stub or real via `LlmResponseGenerator`). Cost tracking per model.
- **Extend by**: Adding async dispatch path in `advance_tick()`. When a message targets a remote agent, dispatch via `RemoteAgentConnectionManager` and return immediately with "dispatched" status. On subsequent ticks, check response buffer. Add `_dispatch_to_remote_agent()` and `_check_response_buffer()` methods.

- **Existing**: `orchestration/coordinator/llm_response_generator.py` (87 lines) — builds role-aware system prompts, calls LLM, returns structured response. Uses `AGENT_ROLE_PROMPTS` from `orchestration/prompts.py`.
- **Extend by**: No changes needed. Remote agents bypass this entirely — they use their own Claude Code instance. LlmResponseGenerator stays for simulation-only use.

- **Existing**: `orchestration/coordinator/session_coordinator.py` (2077 lines) — main session orchestration for the legacy flow. Phase transitions, task execution, clarification gates.
- **Extend by**: This is legacy. No extension needed; it's only used by the /session flow which is being deleted. Can be deleted later or left as dead code.

- **Existing**: `orchestration/coordinator/state_machine.py` (449 lines) — formal phase transition rules for the session lifecycle.
- **Extend by**: Legacy. No extension needed. Used only by session_coordinator.

- **Existing**: `orchestration/prompts.py` (357 lines) — Jinja2 prompt templates and `AGENT_ROLE_PROMPTS` dict.
- **Extend by**: No changes for MVP. AGENT_ROLE_PROMPTS used by LlmResponseGenerator for simulation only.

### Testing
- **Existing test patterns**: Tests in `apps/api/tests/` using pytest. Test files follow `test_<module>.py` naming. FastAPI TestClient for endpoint tests. Direct unit tests for domain logic.
- **Where to add tests**:
  - `tests/test_agent_bridge_protocol.py` — protocol model serialization
  - `tests/test_remote_agent_connection_manager.py` — connection lifecycle
  - `tests/test_control_agent_endpoints.py` — new /control endpoints
  - `tests/test_tick_engine_async_dispatch.py` — async dispatch mode
  - `tools/agent_bridge/tests/` — bridge client tests

## Touch list (concrete)

Priority order:

1. `apps/api/vibeforge_api/routers/sessions.py` — **delete** — legacy session router (FEAT-002)
2. `apps/api/vibeforge_api/main.py` — **modify** — remove sessions router mount, add WS endpoint mount (FEAT-002, FEAT-005)
3. `apps/ui/src/screens/Home.tsx` — **delete** — legacy screen (FEAT-001)
4. `apps/ui/src/screens/Questionnaire.tsx` — **delete** — legacy screen (FEAT-001)
5. `apps/ui/src/screens/PlanReview.tsx` — **delete** — legacy screen (FEAT-001)
6. `apps/ui/src/screens/Progress.tsx` — **delete** — legacy screen (FEAT-001)
7. `apps/ui/src/screens/Clarification.tsx` — **delete** — legacy screen (FEAT-001)
8. `apps/ui/src/screens/Result.tsx` — **delete** — legacy screen (FEAT-001)
9. `apps/ui/src/ui/App.tsx` — **modify** — remove session routes, default to /control (FEAT-003)
10. `apps/ui/src/api/client.ts` — **delete** — legacy session API client (FEAT-003)
11. `apps/api/vibeforge_api/models/requests.py` — **modify** — remove session request models, add agent bridge models (FEAT-002, FEAT-004, FEAT-010)
12. `apps/api/vibeforge_api/models/responses.py` — **modify** — remove session response models, add agent connection models (FEAT-002, FEAT-010)
13. `apps/api/vibeforge_api/core/event_log.py` — **extend** — add agent bridge EventType values (FEAT-005, FEAT-012)
14. `apps/api/vibeforge_api/core/session.py` — **extend** — add agent connection fields (FEAT-006)
15. `orchestration/models.py` — **extend** — add agent_type to AgentConfig (FEAT-004)
16. `apps/api/vibeforge_api/routers/control.py` — **extend** — add agent registration + dispatch + status endpoints (FEAT-010, FEAT-011, FEAT-012)
17. `orchestration/coordinator/tick_engine.py` — **extend** — add async dispatch mode + response buffering (FEAT-013, FEAT-014)
18. `apps/ui/src/api/controlClient.ts` — **extend** — add agent registration + dispatch functions (FEAT-010, FEAT-011, FEAT-015)
19. `apps/ui/src/types/api.ts` — **modify** — remove session types, add agent types (FEAT-003, FEAT-015)
20. `apps/ui/src/screens/ControlPanel.tsx` — **rework** — agent-centric layout with registration + task panels (FEAT-015, FEAT-016, FEAT-017, FEAT-018)

## Gaps / missing pieces

1. **Gap: WebSocket endpoint** — No WebSocket support exists in the codebase. Need `/ws/agent-bridge` endpoint using FastAPI's native WebSocket support. New file: `apps/api/vibeforge_api/routers/agent_bridge.py` or inline in control router. Constraint: must use `fastapi.WebSocket`, not a third-party WS library.

2. **Gap: RemoteAgentConnectionManager** — No centralized connection manager exists. Need a singleton service tracking connected agents, routing dispatches, and buffering responses. New file: `apps/api/vibeforge_api/core/agent_bridge.py`. Constraint: must integrate with SessionStore and EventLog.

3. **Gap: Agent Bridge Service** — No standalone bridge service exists. Need `tools/agent_bridge/bridge.py` (+ config.py + requirements.txt). Constraint: must invoke `claude --print --output-format json` CLI, handle streaming, manage connection lifecycle.

4. **Gap: Agent Bridge Protocol Models** — No protocol message models exist. Need Pydantic models for 6 message types (register, registered, dispatch, progress, response, heartbeat). Can live in `apps/api/vibeforge_api/models/` or `apps/api/vibeforge_api/core/agent_bridge.py`.

5. **Gap: New /control UI widgets** — Need 4 new React components: AgentRegistrationPanel, TaskDispatchPanel, StreamingOutputView, AgentConnectionDashboard. These are new files under `apps/ui/src/screens/control/widgets/`.

## Risks of duplication / overlap

- **Risk**: Creating a new agent state model instead of extending `Session`. **Mitigation**: All agent connection state goes into Session.agent_connections; no parallel model.
- **Risk**: Creating a new event system for agent bridge events. **Mitigation**: Extend EventType enum; all events flow through existing EventLog + SSE pipeline.
- **Risk**: Creating a new dispatch mechanism instead of extending TickEngine. **Mitigation**: TickEngine gets an async dispatch path; the core tick loop remains unchanged.
- **Risk**: Duplicating SSE streaming for agent events. **Mitigation**: Reuse existing `/control/sessions/{session_id}/events` SSE endpoint; agent events are just new EventType values.
- **Risk**: Creating new API client module instead of extending controlClient.ts. **Mitigation**: All new functions go in controlClient.ts.

## Search breadcrumbs

Keywords/phrases that reliably find the relevant areas:
- `TickEngine` — tick-based simulation engine (tick_engine.py)
- `EventType` — event type enum (event_log.py)
- `EventLog` — event persistence and filtering (event_log.py)
- `session_store` — global session store instance (session.py)
- `AgentConfig` — agent configuration model (orchestration/models.py)
- `AgentFlowGraph` — agent communication topology (orchestration/models.py)
- `advance_tick` — tick advancement logic (tick_engine.py, control.py)
- `EventSourceResponse` — SSE streaming setup (control.py)
- `send_message` — message sending in tick engine (tick_engine.py)
- `LlmResponseGenerator` — LLM response generation (llm_response_generator.py)
- `controlClient` — frontend API client (controlClient.ts)
- `simulation_mode` — simulation configuration (session.py, requests.py)
- `/control` — control panel router prefix (control.py)
- `router = APIRouter` — router definitions (control.py, sessions.py)
