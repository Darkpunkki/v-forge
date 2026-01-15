---
doc_type: existing_solution_map
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T15-13-38.903Z_run-b114"
generated_by: "Existing Solution Map"
generated_at: "2026-01-15T15:13:38Z"
scope:
  epic: "ALL"
inputs_used:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/features_backlog.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/codebase_context.md"
status: "Draft"
---

# Existing Solution Map

## Scope
- Idea: IDEA-0002-control-sim
- Epic scope: ALL
- Features included: FEAT-001 through FEAT-014 (Agent roster, Communication graph, Initial prompt, Tick advancement, Graph-gated messaging, Stubbed responses, Message events, Lifecycle controls, Status exposure, Event log, Event streaming, Graph visualization, Message log view, Status indicators)

## Existing "happy path" flow (as implemented today)

The control panel already has substantial simulation infrastructure:

1. **Session creation** → `SessionStore.create_session()` in `apps/api/vibeforge_api/core/session.py`
2. **Agent initialization** → `POST /control/sessions/{id}/agents/init` creates N agents with sequential IDs
3. **Role assignment** → `POST /control/sessions/{id}/agents/assign` assigns role/model per agent
4. **Flow graph configuration** → `POST /control/sessions/{id}/flows` configures `AgentFlowGraph` edges (currently enforces DAG)
5. **Main task setup** → `POST /control/sessions/{id}/task` sets orchestration goal
6. **Simulation config** → `POST /control/sessions/{id}/simulation/config` sets mode (manual/auto), delay, budget
7. **Start simulation** → `POST /control/sessions/{id}/simulation/start` validates workflow completeness, sets `tick_status="running"`
8. **Tick advancement** → `POST /control/sessions/{id}/simulation/tick` increments counter (engine not yet wired)
9. **Event streaming** → `GET /control/sessions/{id}/events` streams SSE events from JSONL log

The `TickEngine` class (`orchestration/coordinator/tick_engine.py`) exists and implements:
- `validate_message()` — graph-gated validation
- `send_message()` — queues messages with blocked event emission
- `advance_tick()` — increments tick, delivers messages, emits `TICK_ADVANCED` event
- Message queue management (`get_pending_messages`, `deliver_message`, `clear_delivered_messages`)

**Gap**: The `TickEngine` is **not wired** to the control API endpoints — tick endpoints currently just increment a counter.

## Reuse-first decisions (hard rules)

- **Extend** `Session` model for any new simulation state fields — do NOT create parallel session state.
- **Extend** `TickEngine` for FIFO processing and stubbed responses — do NOT create a separate tick processor.
- **Reuse** `EventLog` and existing `EventType` enum for new event types — do NOT create a parallel event system.
- **Reuse** `AgentFlowGraph`/`AgentFlowEdge` models for link definitions — extend validation if needed for cycles.
- **Extend** existing control API endpoints — do NOT create new router files.
- **Extend** existing UI widgets (`SimulationConfig`, `TickControls`, `MultiAgentMessages`, `AgentGraph`) — do NOT create parallel components.

## Key extension points (by capability area)

### API/endpoint layer
- **Existing**: `apps/api/vibeforge_api/routers/control.py` — comprehensive simulation endpoints already implemented
  - `/agents/init`, `/agents/assign`, `/task`, `/flows` — workflow config
  - `/simulation/config`, `/simulation/start`, `/simulation/reset`, `/simulation/pause` — lifecycle
  - `/simulation/tick`, `/simulation/ticks` — tick advancement (counter only)
  - `/simulation/state` — state reporting
  - `/events`, `/events/filter` — event streaming/querying
- **Extend by**: Wire `TickEngine` into tick endpoints; add initial prompt + first agent selection to start flow
- **Watch-outs**: Current endpoints validate workflow completeness; new features must preserve these guardrails

### Core logic / domain layer
- **Existing**: `orchestration/coordinator/tick_engine.py` — graph-gated messaging, tick advancement, event emission
  - `validate_message()` — checks edge existence, orchestrator broadcast, self-message
  - `send_message()` — queues message or emits `MESSAGE_BLOCKED_BY_GRAPH`
  - `advance_tick()` — increments tick, delivers all pending messages, emits `TICK_ADVANCED`
- **Extend by**:
  - Implement FIFO single-event-per-tick processing (current implementation delivers all pending messages per tick)
  - Add deterministic stubbed response generation
  - Add per-agent activity cap tracking
  - Wire engine to control endpoints

### Models / state / schemas
- **Existing**: `apps/api/vibeforge_api/core/session.py` — Session model with simulation fields
  - `agents`, `agent_roles`, `agent_models`, `agent_graph`, `main_task`
  - `simulation_mode`, `tick_index`, `tick_status`, `auto_delay_ms`, `tick_budget`
- **Existing**: `orchestration/models.py` — `AgentRole`, `AgentConfig`, `AgentFlowGraph`, `AgentFlowEdge`, `SimulationConfig`, `TickState`
- **Reuse by**:
  - Add `initial_prompt`, `first_agent_id` to Session for start context (FEAT-003)
  - Add `message_queue` persistence or in-memory tracking
  - Add blocked sends as message log entries (system events)
- **Watch-outs**: `AgentFlowGraph.validate_dag()` currently **rejects cycles** — IDEA requires cycles/bidirectional links

### UI layer
- **Existing**: `apps/ui/src/screens/control/widgets/`
  - `SimulationConfig.tsx` — mode (manual/auto), delay, budget configuration
  - `TickControls.tsx` — start/tick/pause/reset controls, status display
  - `MultiAgentMessages.tsx` — displays `MESSAGE_SENT` and `MESSAGE_BLOCKED_BY_GRAPH` events with tick context
  - `AgentGraph.tsx` — SVG graph visualization (currently task-based, not simulation-link-based)
  - `AgentFlowEditor.tsx` — configure agent flow edges
  - `AgentInitializer.tsx`, `AgentAssignment.tsx`, `AgentTaskInput.tsx` — workflow setup
- **Extend by**:
  - Update `AgentGraph` to render simulation communication links (not just task edges)
  - Add initial prompt + first agent selection UI to `SimulationConfig` or new component
  - Enhance `MultiAgentMessages` to show blocked system entries with "Blocked: A → B not allowed" format
  - Add tick index/status indicators that update on tick advancement

### Orchestration / simulation (if relevant)
- **Existing**: `orchestration/coordinator/tick_engine.py` — core tick engine
- **Existing**: `orchestration/coordinator/state_machine.py` — phase transitions
- **Existing**: `orchestration/coordinator/session_coordinator.py` — lifecycle orchestration
- **Extend by**: Ensure TickEngine integrates with session lifecycle; emit events to EventLog

### Testing
- **Existing test patterns**:
  - `apps/api/tests/test_tick_engine.py` — TickEngine initialization, tick advancement, message delivery
  - `apps/api/tests/test_graph_gated_messaging.py` — message validation, blocked events, pipeline flow
  - `apps/api/tests/test_simulation_api.py` — endpoint tests for config/start/tick/pause/reset/state
  - `apps/api/tests/test_event_log.py` — event log filtering by type/tick/agent
- **Where to add tests**:
  - FIFO single-event processing tests in `test_tick_engine.py`
  - Stubbed response generation tests
  - Per-agent activity cap tests
  - Initial prompt + first agent validation tests in `test_simulation_api.py`
  - Bidirectional link / cycle acceptance tests in `test_graph_gated_messaging.py`

## Touch list (concrete)

Priority-ordered files likely to change:

1. `apps/api/vibeforge_api/routers/control.py` — wire TickEngine to tick endpoints, add initial prompt/first agent to start
2. `orchestration/coordinator/tick_engine.py` — implement FIFO single-event processing, stubbed responses, activity cap
3. `apps/api/vibeforge_api/core/session.py` — add `initial_prompt`, `first_agent_id`, possibly `message_queue`
4. `orchestration/models.py` — update `AgentFlowGraph.validate_dag()` to allow cycles/bidirectional
5. `apps/api/vibeforge_api/core/event_log.py` — add any new EventTypes if needed (most exist)
6. `apps/api/vibeforge_api/models/requests.py` — add `initial_prompt`, `first_agent_id` to start request
7. `apps/api/vibeforge_api/models/responses.py` — add message queue state to tick response
8. `apps/ui/src/screens/control/widgets/TickControls.tsx` — ensure tick/status updates on advancement
9. `apps/ui/src/screens/control/widgets/MultiAgentMessages.tsx` — format blocked system entries
10. `apps/ui/src/screens/control/widgets/AgentGraph.tsx` — render simulation graph (agents + links)
11. `apps/ui/src/screens/control/widgets/SimulationConfig.tsx` — add initial prompt / first agent selection
12. `apps/ui/src/api/controlClient.ts` — update client types for new request/response fields
13. `apps/api/tests/test_tick_engine.py` — add FIFO, stubbed response, activity cap tests
14. `apps/api/tests/test_graph_gated_messaging.py` — add cycle/bidirectional tests
15. `apps/api/tests/test_simulation_api.py` — add initial prompt, first agent validation tests

## Gaps / missing pieces

| Gap | Recommended approach | Constraints |
|-----|---------------------|-------------|
| TickEngine not wired to API | Wire in `control.py` tick endpoints | Must preserve current endpoint signatures |
| FIFO single-event-per-tick | Modify `advance_tick()` to process one event | Return early after first event |
| Per-agent activity cap | Track agent activity in tick, skip if already acted | Per-tick tracking, reset each tick |
| Stubbed response generation | Add `generate_stub_response()` method in TickEngine | Deterministic, clearly labeled |
| Initial prompt + first agent | Add to Session model, validate on start | Required before start, stored in session |
| Bidirectional/cycle links | Update `AgentFlowGraph.validate_dag()` | Change from DAG to general graph validation |
| Message queue as FIFO | Use list with `pop(0)` or `collections.deque` | Order must be preserved |
| Blocked sends as system log entries | Format as "Blocked: A → B not allowed" | Add to message log view |

## Risks of duplication / overlap

| Risk | Mitigation |
|------|------------|
| Creating parallel tick processing | Use existing `TickEngine` exclusively |
| Creating parallel event log | Use existing `EventLog` with existing/new EventTypes |
| Creating parallel session state | Extend `Session` model only |
| Creating parallel graph model | Extend `AgentFlowGraph` only |
| Creating new UI components | Extend existing widgets in `apps/ui/src/screens/control/widgets/` |

## Search breadcrumbs

Keywords/phrases that reliably find the relevant areas:

- `TickEngine` — tick engine class
- `advance_tick` — tick advancement logic
- `validate_message` — graph-gated validation
- `MESSAGE_BLOCKED_BY_GRAPH` — blocked message events
- `MESSAGE_SENT` — sent message events
- `TICK_ADVANCED` — tick advancement events
- `tick_status` — simulation running state
- `tick_index` — current tick counter
- `agent_graph` — communication graph
- `AgentFlowGraph` — graph model
- `simulation/tick` — tick endpoint
- `simulation/start` — start endpoint
- `SimulationConfig` — UI config widget
- `TickControls` — UI tick controls widget
- `MultiAgentMessages` — UI message log widget
- `test_tick_engine` — tick engine tests
- `test_graph_gated_messaging` — graph validation tests
