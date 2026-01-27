---
doc_type: work_packages
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T19-04-14.952Z_run-ae73"
generated_by: "into-WPs"
generated_at: "2026-01-27T21:20:00+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/tasks.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/existing_solution_map.md"
scope_filter: "MVP"
total_wps: 8
total_tasks_queued: 34
global_wp_range: "WP-0053 — WP-0060"
status: "Draft"
---

# Work Packages — IDEA-0003 (MVP scope)

> Batched from 34 MVP tasks across EPIC-001 through EPIC-006.
> WP numbering continues from the global `docs/ai/planning/WORK_PACKAGES.md` (last: WP-0052).

---

## WP-0053 — Legacy Session Removal (frontend + backend)

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-001
- **Tasks:** TASK-001, TASK-002, TASK-003, TASK-004
- **Effort:** 4S = 4 points
- **Goal:** Delete all legacy /session UI screens, session router, session-specific models, and session API client. Redirect `/` to `/control`. Leave SessionStore and Session model intact (used by /control).
- **Dependencies:** None (independent; should run first)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0053-legacy-session-removal.md

### Ordered steps
1. Delete 6 UI screen files (TASK-001)
2. Delete sessions.py router and remove from main.py (TASK-002)
3. Remove session-specific request/response Pydantic models (TASK-003)
4. Update App.tsx routes, delete client.ts, clean api.ts types (TASK-004)

### Done means
- `npm run build` succeeds (zero errors)
- `pytest` passes for remaining endpoints
- GET/POST `/sessions/*` returns 404
- `/` redirects to `/control`
- `/control/*` and `/simulation/*` endpoints unaffected

---

## WP-0054 — Agent Bridge Protocol Models + Event Types

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-002
- **Tasks:** TASK-005, TASK-006, TASK-009, TASK-013
- **Effort:** 4S = 4 points
- **Goal:** Define the 6 protocol message Pydantic models, extend EventType enum with 7 agent bridge events, add agent connection fields to Session model, and write unit tests for protocol serialization.
- **Dependencies:** None (independent; can run in parallel with WP-0053)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0054-bridge-protocol-models.md

### Ordered steps
1. Create bridge_protocol.py with 6 Pydantic message models (TASK-005)
2. Add 7 agent bridge EventType values to event_log.py (TASK-009)
3. Add agent_connections, pending_dispatches, response_buffer fields to Session (TASK-013)
4. Write unit tests for protocol serialization/deserialization (TASK-006)

### Done means
- All 6 protocol models round-trip serialize/deserialize correctly
- EventType enum includes 7 new values; existing events unaffected
- Session.to_dict() / from_dict() handles new fields
- `pytest` passes

---

## WP-0055 — WebSocket Endpoint + Connection Manager

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-002
- **Tasks:** TASK-007, TASK-010, TASK-011, TASK-008, TASK-012
- **Effort:** 2M + 1M + 2S = 7 points
- **Goal:** Build the server-side agent bridge infrastructure: WebSocket endpoint at /ws/agent-bridge, RemoteAgentConnectionManager singleton with dispatch + response buffering, heartbeat monitoring, and unit tests.
- **Dependencies:** WP-0054 (needs protocol models + event types + session fields)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0055-ws-endpoint-connection-manager.md

### Ordered steps
1. Implement /ws/agent-bridge WebSocket endpoint with register/registered handshake (TASK-007)
2. Build RemoteAgentConnectionManager singleton with register/unregister/list/status (TASK-010)
3. Add dispatch_task() and response buffering to connection manager (TASK-011)
4. Add heartbeat monitoring and stale connection detection (TASK-008)
5. Write unit tests for connection manager (TASK-012)

### Done means
- WebSocket endpoint accepts connections and performs register handshake
- Connection manager tracks agents, dispatches tasks, buffers responses
- Stale connections detected and cleaned up
- All unit tests pass
- `pytest` passes

---

## WP-0056 — Agent Bridge Standalone Service

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-003
- **Tasks:** TASK-014, TASK-015, TASK-016, TASK-017, TASK-018
- **Effort:** 3M + 2S = 8 points
- **Goal:** Build the standalone agent bridge service (`tools/agent_bridge/`) that runs on remote machines, connects to VibeForge via WebSocket, invokes Claude Code CLI, and streams results back.
- **Dependencies:** WP-0054 (needs protocol models for message format)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0056-agent-bridge-service.md

### Ordered steps
1. Build WebSocket client with registration handshake (TASK-014)
2. Add heartbeat sending and reconnection with exponential backoff (TASK-015)
3. Implement Claude Code CLI wrapper (TASK-016)
4. Wire dispatch handling to CLI execution with progress streaming (TASK-017)
5. Add argparse CLI, signal handling, and requirements.txt (TASK-018)

### Done means
- `python tools/agent_bridge/bridge.py --url ws://localhost:8000/ws/agent-bridge --agent-id test --token secret --workdir .` launches and registers
- Heartbeat sent at interval; reconnects on disconnection
- Dispatch message triggers Claude Code CLI invocation
- Response streamed back over WebSocket
- SIGINT/SIGTERM triggers graceful shutdown

---

## WP-0057 — Live Agent Control Backend Endpoints

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-004
- **Tasks:** TASK-019, TASK-020, TASK-021, TASK-022
- **Effort:** 4M = 8 points
- **Goal:** Add REST endpoints to /control for agent registration, task dispatch, follow-up, status queries, and agent-scoped SSE streaming. Write integration tests.
- **Dependencies:** WP-0055 (needs connection manager for dispatch routing)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0057-control-backend-endpoints.md

### Ordered steps
1. Add POST /control/agents/register, GET /control/agents, GET /control/agents/{id} (TASK-019)
2. Add POST dispatch, POST followup, GET task-status endpoints (TASK-020)
3. Extend SSE with agent events + add per-agent SSE endpoint (TASK-021)
4. Write integration tests for all agent control endpoints (TASK-022)

### Done means
- All 6+ new REST endpoints functional
- Agent registration creates trackable agent entry
- Dispatch routes through connection manager to remote agent
- SSE streams include agent bridge events
- Integration tests pass
- `pytest` passes

---

## WP-0058 — Async Dispatch Engine (TickEngine Extension)

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-005
- **Tasks:** TASK-023, TASK-024, TASK-025, TASK-026, TASK-027
- **Effort:** 2S + 3M = 8 points
- **Goal:** Extend TickEngine to support async dispatch to remote agents: add agent_type to AgentConfig, implement non-blocking dispatch, add response buffer checking, timeout handling, and tests.
- **Dependencies:** WP-0055 (needs connection manager for dispatch/buffering)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0058-async-dispatch-engine.md

### Ordered steps
1. Add agent_type, endpoint_url, connection_status fields to AgentConfig (TASK-023)
2. Add async dispatch path in advance_tick() for remote agents (TASK-024)
3. Add response buffer checking at start of each tick (TASK-025)
4. Add dispatch timeout handling (TASK-026)
5. Write tests for async dispatch and response buffering (TASK-027)

### Done means
- Remote agents dispatched non-blocking; simulation agents still use LLM
- Buffered responses processed on subsequent ticks
- Timed-out dispatches emit error events
- Existing simulation tests still pass (regression)
- New async dispatch tests pass
- `pytest` passes

---

## WP-0059 — Control UI: API Client + Agent Components

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-006
- **Tasks:** TASK-028, TASK-029, TASK-030, TASK-031, TASK-032, TASK-033
- **Effort:** 3S + 1S + 2M = 7 points
- **Goal:** Build the frontend components for agent control: API client functions, AgentRegistrationPanel, TaskDispatchPanel, StreamingOutputView, and AgentConnectionDashboard.
- **Dependencies:** WP-0057 (needs backend endpoints for API functions)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0059-control-ui-components.md

### Ordered steps
1. Add agent registration API functions to controlClient.ts (TASK-028)
2. Build AgentRegistrationPanel widget (TASK-029)
3. Add task dispatch + follow-up API functions (TASK-030)
4. Build TaskDispatchPanel chat-style widget (TASK-031)
5. Build StreamingOutputView with SSE subscription (TASK-032)
6. Build AgentConnectionDashboard grid widget (TASK-033)

### Done means
- controlClient.ts has typed functions for all agent endpoints
- All 4 widget components render without errors
- Registration form submits and refreshes agent list
- Task dispatch sends messages and shows conversation history
- SSE streaming displays real-time agent events
- `npm run build` succeeds

---

## WP-0060 — Control Panel Layout Rework

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-006
- **Tasks:** TASK-034
- **Effort:** 1M = 2 points
- **Goal:** Rework ControlPanel.tsx to an agent-centric layout: sidebar with AgentConnectionDashboard + AgentRegistrationPanel, main area with TaskDispatchPanel + StreamingOutputView, collapsible monitoring panels.
- **Dependencies:** WP-0059 (needs all widget components built)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0060-control-panel-rework.md

### Ordered steps
1. Rework ControlPanel.tsx layout with agent-centric sidebar + main area (TASK-034)

### Done means
- Left sidebar shows agent dashboard + registration panel
- Main area shows task panel + streaming output for selected agent
- Selecting agent in dashboard focuses task panel
- EventStream + CostAnalytics accessible as collapsible panels
- Layout responsive (sidebar collapses on small screens)
- `npm run build` succeeds

---

## Dependency Graph

```
WP-0053 (Session Removal)     ──────────────────────────────────────────┐
                                                                         │
WP-0054 (Protocol + Events) ──┬── WP-0055 (WS + ConnMgr) ──┬── WP-0057 (Control Backend) ── WP-0059 (UI Components) ── WP-0060 (Layout)
                               │                             │
                               └── WP-0056 (Bridge Service)  └── WP-0058 (Async Dispatch)
```

Parallelism opportunities:
- WP-0053 and WP-0054 can run in parallel (no dependencies)
- WP-0055 and WP-0056 can run in parallel (both depend only on WP-0054)
- WP-0057 and WP-0058 can run in parallel (both depend on WP-0055)

## Summary

| WP | Title | Epic | Tasks | Points | Status |
|----|-------|------|-------|--------|--------|
| WP-0053 | Legacy Session Removal | EPIC-001 | 4 | 4 | Queued |
| WP-0054 | Bridge Protocol Models + Events | EPIC-002 | 4 | 4 | Queued |
| WP-0055 | WebSocket Endpoint + Connection Manager | EPIC-002 | 5 | 7 | Queued |
| WP-0056 | Agent Bridge Standalone Service | EPIC-003 | 5 | 8 | Queued |
| WP-0057 | Live Agent Control Backend Endpoints | EPIC-004 | 4 | 8 | Queued |
| WP-0058 | Async Dispatch Engine | EPIC-005 | 5 | 8 | Queued |
| WP-0059 | Control UI: API Client + Components | EPIC-006 | 6 | 7 | Queued |
| WP-0060 | Control Panel Layout Rework | EPIC-006 | 1 | 2 | Queued |
| **Total** | | | **34** | **48** | |
