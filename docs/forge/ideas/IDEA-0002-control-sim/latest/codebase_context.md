---
doc_type: codebase_context
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T02-41-17.238Z_run-0fbb"
generated_by: "Codebase Context"
generated_at: "2026-01-15T02:45:20.274068+00:00"
sources:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/idea_normalized.md"
status: "Draft"
---

# Codebase Context

## Purpose of this map

Provide a focused map of where the current control simulation capabilities live (API, orchestration, UI), so new work extends existing seams instead of assuming a greenfield design.

## High-level architecture boundaries (as observed)

- Boundary: API layer — FastAPI routers in `apps/api/vibeforge_api/routers/` — separates control panel endpoints (`control.py`) from end-user session flow (`sessions.py`).
- Boundary: Core session/state — `apps/api/vibeforge_api/core/` — session model/store, event log, and workspace management.
- Boundary: Orchestration/simulation — `orchestration/coordinator/` and `orchestration/models.py` — phase orchestration plus tick engine and agent graph models.
- Boundary: UI control panel — `apps/ui/src` — `ControlPanel` and widgets plus typed API client.
- Boundary: Tests — `apps/api/tests` — control API, tick engine, event log, and graph-gating coverage.

## Likely extension points

- Area: Control simulation endpoints — `apps/api/vibeforge_api/routers/control.py` — wire real tick processing and emit simulation events.
- Area: Tick engine logic — `orchestration/coordinator/tick_engine.py` — implement per-tick activity, message queue behavior, and event emission.
- Area: Session simulation state — `apps/api/vibeforge_api/core/session.py` — add or persist simulation fields (message queue, ordering, per-agent actions).
- Area: Event stream — `apps/api/vibeforge_api/core/event_log.py` + SSE in `control.py` — align emitted metadata with UI widgets.
- Area: UI widgets — `apps/ui/src/screens/control/widgets/` — update SimulationConfig, TickControls, AgentFlowEditor, AgentGraph, MultiAgentMessages as behavior evolves.

## Key existing concepts to reuse

- Concept/Model: Session + SessionPhase — `apps/api/vibeforge_api/core/session.py`, `apps/api/vibeforge_api/models/types.py` — phase-aware guardrails and shared lifecycle state.
- Concept/Model: AgentConfig/AgentRole/AgentFlowGraph — `orchestration/models.py` — agent definitions and graph validation.
- Concept/Model: SimulationConfig/TickState — `orchestration/models.py` — simulation configuration surface.
- Concept/Model: Event and EventType — `apps/api/vibeforge_api/core/event_log.py` — standardized events for UI and log persistence.
- Concept/Model: Deterministic stub LLM — `apps/api/vibeforge_api/core/llm_provider.py` — safe mode for token-free runs.

## Constraints implied by current architecture

- Constraint: Session storage is in-memory (`SessionStore`), so simulation state is not persisted across restarts.
- Constraint: Control endpoints enforce phase guardrails; terminal phases block simulation changes (`control.py` + `state_machine.py`).
- Constraint: Agent flow graph validation enforces a DAG (no cycles), which conflicts with true bidirectional links unless validation changes.
- Constraint: Tick endpoints in `control.py` currently only increment counters; `TickEngine` exists but is not wired to API flow (no `TickEngine` usage found).
- Constraint: Event log is JSONL per session under workspace root and is the source for SSE updates.
- Constraint: UI widgets expect `MESSAGE_SENT` and `MESSAGE_BLOCKED_BY_GRAPH` event metadata (`from_agent`, `to_agent`, `content`, `tick_index`).

## Candidate file/module touch list (max ~25)

- `apps/api/vibeforge_api/routers/control.py` — control endpoints, simulation lifecycle, tick actions.
- `apps/api/vibeforge_api/routers/sessions.py` — phase-aware session flow and progress polling.
- `apps/api/vibeforge_api/core/session.py` — session fields for agents and simulation status.
- `apps/api/vibeforge_api/core/event_log.py` — event types and JSONL log persistence.
- `apps/api/vibeforge_api/core/workspace.py` — per-session workspace paths used by event logs/artifacts.
- `apps/api/vibeforge_api/core/llm_provider.py` — deterministic stub and safe mode toggles.
- `apps/api/vibeforge_api/models/requests.py` — control/simulation request shapes.
- `apps/api/vibeforge_api/models/responses.py` — control/simulation response shapes.
- `apps/api/vibeforge_api/models/types.py` — SessionPhase and AgentRole enums.
- `orchestration/models.py` — AgentRole, AgentFlowGraph, SimulationConfig, TickState.
- `orchestration/coordinator/tick_engine.py` — graph-gated messaging and tick advancement.
- `orchestration/coordinator/state_machine.py` — allowed phase transitions and exit criteria.
- `orchestration/coordinator/session_coordinator.py` — lifecycle orchestration and event emission.
- `apps/ui/src/api/controlClient.ts` — typed client for control endpoints.
- `apps/ui/src/screens/ControlPanel.tsx` — control panel layout and widget composition.
- `apps/ui/src/screens/control/widgets/SimulationConfig.tsx` — simulation config UI.
- `apps/ui/src/screens/control/widgets/TickControls.tsx` — tick/pause/reset controls and status display.
- `apps/ui/src/screens/control/widgets/AgentFlowEditor.tsx` — configure graph edges.
- `apps/ui/src/screens/control/widgets/MultiAgentMessages.tsx` — expects message/block events.
- `apps/ui/src/screens/control/widgets/AgentGraph.tsx` — currently visualizes task/agent events.
- `apps/api/tests/test_control_api.py` — control endpoint coverage.
- `apps/api/tests/test_tick_engine.py` — tick engine behavior coverage.
- `apps/api/tests/test_graph_gated_messaging.py` — graph validation and blocked message events.
- `apps/api/tests/test_event_log.py` — event types and filtering behavior.

## Unknowns / where to look next

- Unknown: Where to integrate `TickEngine` into control endpoints — search for `advance_tick` usage or `TickEngine(` in repo to confirm no existing wiring.
- Unknown: Expected event metadata for simulation messages beyond `from_agent`/`to_agent` — check `apps/ui/src/screens/control/widgets/MultiAgentMessages.tsx` and `apps/ui/src/screens/control/widgets/AgentGraph.tsx` for required fields.
- Unknown: Graph visualization expectations for simulation vs task graph — inspect `apps/ui/src/screens/control/widgets/AgentGraph.tsx` and `apps/ui/src/screens/control/widgets/AgentFlowEditor.tsx`.
- Unknown: Tick ordering or scheduling policy — search for `tick_status`, `tick_budget`, or `pending_work_summary` usage outside `control.py` and `tick_engine.py`.
