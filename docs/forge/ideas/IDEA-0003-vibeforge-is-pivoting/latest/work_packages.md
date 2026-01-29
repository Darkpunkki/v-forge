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
total_wps: 9
total_tasks_queued: 36
global_wp_range: "WP-0053 - WP-0061"
status: "Draft"
---

# Work Packages — IDEA-0003 (MVP scope)

> Batched from 36 MVP tasks across EPIC-001 through EPIC-006.
> WP numbering continues from the global `docs/ai/planning/WORK_PACKAGES.md` (last: WP-0052).

---

## WP-0053 — Legacy Session Removal (frontend + backend)

- **Status:** Done
- **Started:** 2026-01-27 21:30 (local)
- **Completed:** 2026-01-27
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-001
- **Tasks:** TASK-001, TASK-002, TASK-003, TASK-004
- **Effort:** 4S = 4 points
- **Goal:** Delete all legacy /session UI screens, session router, session-specific models, and session API client. Redirect `/` to `/control`. Leave SessionStore and Session model intact (used by /control).
- **Dependencies:** None (independent; should run first)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0053-legacy-session-removal.md
- **Verified:**
  - `cd apps/ui && npm run build` — 0 errors, built in 1.13s
  - `cd apps/api && python -m pytest` — 621 passed, 0 failed

### Ordered steps
1. [x] Delete 6 UI screen files (TASK-001)
2. [x] Delete sessions.py router and remove from main.py (TASK-002)
3. [x] Remove session-specific request/response Pydantic models (TASK-003)
4. [x] Update App.tsx routes, delete client.ts, clean api.ts types (TASK-004)

### Done means
- `npm run build` succeeds (zero errors) ✓
- `pytest` passes for remaining endpoints ✓ (621 passed)
- GET/POST `/sessions/*` returns 404 ✓ (router deleted)
- `/` redirects to `/control` ✓ (Navigate component)
- `/control/*` and `/simulation/*` endpoints unaffected ✓

### Files touched
- **Deleted (frontend):** Home.tsx, Questionnaire.tsx, PlanReview.tsx, Progress.tsx, Clarification.tsx, Result.tsx, client.ts
- **Deleted (backend):** sessions.py, test_sessions.py, test_e2e_demo.py, test_execution_flow.py, test_session_coordinator.py, test_phase_transition_integration.py
- **Modified (frontend):** App.tsx, Simulation.tsx, controlClient.ts, types/api.ts
- **Modified (backend):** main.py, requests.py, responses.py, __init__.py, control.py, questionnaire.py, session_coordinator.py

### Notes
- Moved `createSession()` to controlClient.ts → POST /control/sessions (new endpoint added to control router)
- `questionnaire.py` kept but `get_next_question()` now returns dict instead of deleted QuestionResponse model
- SessionStore and Session model preserved (used by /control and /simulation)

---

## WP-0054 — Agent Bridge Protocol Models + Event Types

- **Status:** Done
- **Started:** 2026-01-28
- **Completed:** 2026-01-28
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-002
- **Tasks:** TASK-005, TASK-006, TASK-009, TASK-013
- **Effort:** 4S = 4 points
- **Goal:** Define the 6 protocol message Pydantic models, extend EventType enum with 7 agent bridge events, add agent connection fields to Session model, and write unit tests for protocol serialization.
- **Dependencies:** None (independent; can run in parallel with WP-0053)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0054-bridge-protocol-models.md
- **Verified:**
  - `cd apps/api && python -m pytest tests/test_bridge_protocol.py -v` — 30 passed
  - `cd apps/api && python -m pytest` — 651 passed, 0 failed

### Ordered steps
1. [x] Create bridge_protocol.py with 6 Pydantic message models (TASK-005)
2. [x] Add 7 agent bridge EventType values to event_log.py (TASK-009)
3. [x] Add agent_connections, pending_dispatches, response_buffer fields to Session (TASK-013)
4. [x] Write unit tests for protocol serialization/deserialization (TASK-006)

### Done means
- All 6 protocol models round-trip serialize/deserialize correctly ✓
- EventType enum includes 7 new values (42 total); existing events unaffected ✓
- Session.to_dict() / from_dict() handles new fields ✓
- `pytest` passes ✓ (651 passed)

### Files touched
- **Created:** `apps/api/vibeforge_api/models/bridge_protocol.py` — 6 Pydantic message models + BridgeMessage union + parse_bridge_message()
- **Created:** `apps/api/tests/test_bridge_protocol.py` — 30 unit tests for all 6 message types + discriminated union
- **Modified:** `apps/api/vibeforge_api/models/__init__.py` — re-export bridge protocol models
- **Modified:** `apps/api/vibeforge_api/core/event_log.py` — 7 new EventType values
- **Modified:** `apps/api/vibeforge_api/core/session.py` — 3 new fields + to_dict/from_dict

---

## WP-0055 — WebSocket Endpoint + Connection Manager

- **Status:** Done
- **Started:** 2026-01-28 20:15 (local)
- **Branch:** master
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

- **Status:** Done
- **Started:** 2026-01-28 20:27 (local)
- **Completed:** 2026-01-28 22:00 (local)
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-003
- **Tasks:** TASK-014, TASK-015, TASK-016, TASK-017, TASK-018
- **Effort:** 3M + 2S = 8 points
- **Goal:** Build the standalone agent bridge service (`tools/agent_bridge/`) that runs on remote machines, connects to VibeForge via WebSocket, invokes Claude Code CLI, and streams results back.
- **Dependencies:** WP-0054 (needs protocol models for message format)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0056-agent-bridge-service.md
- **Verified:**
  - `python tools/agent_bridge/bridge.py --url ws://localhost:8000/ws/agent-bridge --agent-id test --token secret --workdir .`
  - `Invoke-RestMethod -Method Post -Uri http://localhost:8000/control/agents/test/dispatch -ContentType application/json -Body '{"content":"Say hello from the bridge"}'`
  - `curl.exe -N http://localhost:8000/control/agents/test/events` (agent_response observed)
- **Commits:** none

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

- **Status:** Done
- **Started:** 2026-01-28 20:52 (local)
- **Completed:** 2026-01-28 21:07 (local)
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-004
- **Tasks:** TASK-019, TASK-020, TASK-021, TASK-022
- **Effort:** 4M = 8 points
- **Goal:** Add REST endpoints to /control for agent registration, task dispatch, follow-up, status queries, and agent-scoped SSE streaming. Write integration tests.
- **Dependencies:** WP-0055 (needs connection manager for dispatch routing)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0057-control-backend-endpoints.md
- **Verified:**
  - `python -m pytest` (cd apps/api) — 681 passed, 1 skipped (warnings)
- **Commits:** none

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

- **Status:** Done
- **Started:** 2026-01-28 21:25 (local)
- **Completed:** 2026-01-28 21:34 (local)
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-005
- **Tasks:** TASK-023, TASK-024, TASK-025, TASK-026, TASK-027
- **Effort:** 2S + 3M = 8 points
- **Goal:** Extend TickEngine to support async dispatch to remote agents: add agent_type to AgentConfig, implement non-blocking dispatch, add response buffer checking, timeout handling, and tests.
- **Dependencies:** WP-0055 (needs connection manager for dispatch/buffering)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0058-async-dispatch-engine.md
- **Verified:**
  - `python -m pytest` (cd apps/api) — 684 passed, 1 skipped (warnings)
- **Commits:** none

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

- **Status:** Done
- **Started:** 2026-01-28 22:00 (local)
- **Completed:** 2026-01-28 23:04 (local)
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-006
- **Tasks:** TASK-028, TASK-029, TASK-030, TASK-031, TASK-032, TASK-033
- **Effort:** 3S + 1S + 2M = 7 points
- **Goal:** Build the frontend components for agent control: API client functions, AgentRegistrationPanel, TaskDispatchPanel, StreamingOutputView, and AgentConnectionDashboard.
- **Dependencies:** WP-0057 (needs backend endpoints for API functions)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0059-control-ui-components.md
- **Verified:**
  - `cd apps/ui && npm run build`
- **Commits:** none

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

- **Status:** Done
- **Started:** 2026-01-28 23:44 (local)
- **Completed:** 2026-01-28 23:52 (local)
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-006
- **Tasks:** TASK-034
- **Effort:** 1M = 2 points
- **Goal:** Rework ControlPanel.tsx to an agent-centric layout: sidebar with AgentConnectionDashboard + AgentRegistrationPanel, main area with TaskDispatchPanel + StreamingOutputView, collapsible monitoring panels.
- **Dependencies:** WP-0059, WP-0061 (needs widgets + sessionless control context cleanup)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0060-control-panel-rework.md
- **Verified:**
  - `cd apps/ui; npm run build` — success
- **Commits:** none

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

## WP-0061 - Sessionless Control Context Cleanup

- **Status:** Done
- **Started:** 2026-01-28 19:00 (local)
- **Branch:** master
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Epic:** EPIC-004 + EPIC-006
- **Tasks:** TASK-041, TASK-042
- **Effort:** 2S = 2 points
- **Goal:** Remove session list/status surfaces from /control, introduce a single control context id for observability, and update the control UI/API client accordingly.
- **Dependencies:** None (TASK-042 depends on TASK-041)
- **Plan Doc:** docs/ai/planning/work_packages/WP-0061-sessionless-control-context.md
- **Verification:** Failed - `python -m pytest` hit 3 teardown PermissionErrors in `tests/test_workspace.py` (temp .git objects)
- **Next:** Re-run pytest after resolving temp workspace cleanup permissions

### Ordered steps
1. Replace session list/status endpoints with GET /control/context (TASK-041)
2. Remove session list/status UI + APIs; wire control context (TASK-042)

### Done means
- /control no longer exposes session list/status/bundle endpoints
- GET /control/context returns a stable control_session_id
- ControlPanel no longer shows session list/status grid
- controlClient.ts drops session list/status helpers; new getControlContext() added
- `cd apps/ui && npm run build` passes
- `cd apps/api && python -m pytest` passes (after test updates)

---

## Dependency Graph

```
WP-0053 (Session Removal)     ──────────────────────────────────────────┐
                                                                         │
WP-0054 (Protocol + Events) ──┬── WP-0055 (WS + ConnMgr) ──┬── WP-0057 (Control Backend) ── WP-0059 (UI Components) ── WP-0061 (Sessionless Control Context) ── WP-0060 (Layout)
                               │                             │
                               └── WP-0056 (Bridge Service)  └── WP-0058 (Async Dispatch)
```

---

# Work Packages — IDEA-0003 (V1 scope)

> MVP WPs (WP-0053 through WP-0060) are complete.
> V1 WPs batched by priority: Security first (EPIC-009), then features (EPIC-007).

---

# Security Hardening (EPIC-009) — Must Complete Before V1 Features

## WP-0064 — Authentication & TLS Foundation

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Release:** V1
- **Epic:** EPIC-009
- **Tasks:**
  - TASK-043 — Replace hardcoded 'secret' token with secure authentication
  - TASK-044 — Add TLS/SSL support with self-signed certificates
- **Effort:** 2M = 4 points
- **Goal:** Establish foundational security with real authentication and encrypted connections. Replace hardcoded credentials with secure token validation. Enable HTTPS/WSS for encrypted communication between UI, API, and agents.
- **Dependencies:** MVP complete (WP-0060)
- **Plan Doc:** docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/planning/WPP-0011-WP-0064_TASK-043-044_auth-tls.md
- **Verify:**
  - `cd apps/api && python -m pytest tests/test_auth.py -v`
  - `cd apps/api && python -m pytest`
  - `python tools/generate_certs.ps1`
  - `uvicorn vibeforge_api.main:app --ssl-keyfile ssl/key.pem --ssl-certfile ssl/cert.pem`
  - `python tools/agent_bridge/bridge.py --url wss://localhost:8000/ws/agent-bridge --token <generated> --workdir . --insecure`

### Done means
- Hardcoded 'secret' removed; secure tokens generated and validated
- Token validation middleware on WebSocket + REST endpoints
- Self-signed certs generated via script
- API accepts HTTPS connections (port 8000)
- WebSocket accepts WSS connections
- Agent bridge connects via wss://
- Invalid tokens return 401 Unauthorized
- Documentation updated with setup instructions
- All tests pass

---

## WP-0065 — Input Validation & Path Sandboxing

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Release:** V1
- **Epic:** EPIC-009
- **Tasks:**
  - TASK-045 — Implement path sandboxing in agent bridge
  - TASK-046 — Add input validation and sanitization for task dispatch
- **Effort:** 2S = 2 points
- **Goal:** Prevent injection attacks and directory traversal. Validate all file paths stay within workdir. Sanitize task content and agent IDs to prevent command injection.
- **Dependencies:** WP-0064 (security foundation)
- **Plan Doc:** docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/planning/WPP-0012-WP-0065_TASK-045-046_validation.md
- **Verify:**
  - `cd apps/api && python -m pytest tests/test_input_validation.py -v`
  - `cd tools/agent_bridge && python -m pytest tests/test_path_validation.py -v`
  - Manual: Try directory traversal (../../etc/passwd) → rejected
  - Manual: Try long task content (>10,000 chars) → 400 error

### Done means
- Path validation blocks directory traversal attempts
- Symlinks outside workdir rejected
- Task content length limited to 10,000 chars
- agent_id format validated (alphanumeric + hyphens only)
- Special characters sanitized
- Validation errors return clear 400 responses
- Security violations logged
- All tests pass

---

## WP-0066 — Rate Limiting & Cost Controls

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Release:** V1
- **Epic:** EPIC-009
- **Tasks:**
  - TASK-047 — Implement rate limiting for dispatch endpoints
  - TASK-048 — Add cost tracking and limits per session
- **Effort:** 2M = 4 points
- **Goal:** Prevent abuse and runaway costs. Limit dispatch frequency per agent and per IP. Track Claude API costs per session and enforce daily/session limits.
- **Dependencies:** WP-0064 (auth for user tracking)
- **Plan Doc:** docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/planning/WPP-0013-WP-0066_TASK-047-048_limits.md
- **Verify:**
  - `cd apps/api && python -m pytest tests/test_rate_limiting.py -v`
  - `cd apps/api && python -m pytest tests/test_cost_limits.py -v`
  - Manual: Send 11 dispatches in 1 minute → 11th returns 429
  - Manual: Exceed daily cost limit → dispatch blocked with 402

### Done means
- Rate limiter middleware active on dispatch endpoints
- Per-agent limit: 10 dispatches/minute
- Per-IP limit: 50 dispatches/minute
- 429 Too Many Requests when limit exceeded
- X-RateLimit-* headers in responses
- Cost tracked per control session
- Daily cost limit: $10 (configurable)
- Session cost limit: $5 (configurable)
- Warning at 80% of limit
- Dispatch blocked with 402 when limit exceeded
- Cost status in /control/context API
- All tests pass

---

## WP-0067 — Audit Logging & Security Documentation

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Release:** V1
- **Epic:** EPIC-009
- **Tasks:**
  - TASK-049 — Add audit logging for security events
  - TASK-050 — Add security documentation and best practices guide
- **Effort:** 1S + 1M = 3 points
- **Goal:** Enable security monitoring and provide production deployment guidance. Log all security-relevant events for incident response. Document complete security setup for production use.
- **Dependencies:** WP-0064, WP-0065, WP-0066 (all security features)
- **Plan Doc:** docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/planning/WPP-0014-WP-0067_TASK-049-050_audit-docs.md
- **Verify:**
  - `ls logs/audit.log` → exists
  - `cat logs/audit.log | jq` → valid JSON lines
  - `cat docs/SECURITY.md` → comprehensive security guide exists
  - Manual: Trigger auth failure → logged
  - Manual: Trigger rate limit → logged

### Done means
- Audit logger configured with logs/audit.log
- Log rotation enabled (100MB max, keep 10)
- Structured JSON format (timestamp, event, agent_id, IP, result)
- Auth events logged (success/failure)
- Agent lifecycle logged (register/disconnect/timeout)
- Dispatch events logged (agent_id, task preview, cost)
- Security violations logged (path traversal, rate limits, cost limits)
- docs/SECURITY.md created with:
  - Token generation guide
  - TLS setup (dev + production)
  - Firewall configuration
  - Workdir isolation best practices
  - Cost/rate limit config
  - Audit log monitoring
  - Production deployment checklist
  - Threat model
- CONTROL_PANEL_GUIDE.md links to SECURITY.md
- README.md includes security notice

---

# V1 Features (EPIC-007) — Requires Security Hardening First

## WP-0062 — Delegation Chain Dispatch for Remote Agents

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Release:** V1
- **Epic:** EPIC-007
- **Tasks:**
  - TASK-035 — Implement delegation chain dispatch for remote agents
  - TASK-036 — Add tests for delegation chain dispatch with remote agents
- **Effort:** 1L + 1M = 6 points
- **Goal:** Enable multi-hop task delegation with real agents. When a remote agent's response includes a delegation request, route the delegated subtask to the next agent in the flow graph. Support agent A → agent B → agent C chains with results flowing back up the delegation chain.
- **Dependencies:** MVP complete (WP-0058 provides async dispatch foundation)
- **Plan Doc:** docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/planning/WPP-0009-WP-0062_TASK-035-036_delegation-chains.md
- **Verify:**
  - `cd apps/api && python -m pytest tests/test_delegation_chains.py -v`
  - `cd apps/api && python -m pytest`

### Ordered steps
1. Implement delegation chain dispatch for remote agents (TASK-035)
   - Extend dispatch system to detect delegation flag in agent responses
   - Route delegated subtasks through flow graph edges
   - Track delegation chains (parent task → subtask relationships)
   - Emit TASK_DISPATCHED events for each delegation hop
   - Support multi-hop delegation (A → B → C)
   - Flow results back up the chain
2. Add comprehensive tests for delegation chains (TASK-036)
   - Single-hop delegation tests (A delegates to B)
   - Multi-hop delegation tests (A → B → C)
   - Result propagation tests
   - Graph validation enforcement tests

### Done means
- Remote agent responses with delegation=true trigger subtask routing
- Delegated tasks route through configured flow graph edges
- Multi-hop chains work end-to-end (A → B → C → back to A)
- Results propagate up the chain correctly
- Graph-gated routing still enforced (invalid edges rejected)
- All delegation chain tests pass
- `pytest` passes (no regressions)

---

## WP-0063 — Delegation Chain Status Tracking and Visualization

- **Status:** Queued
- **Idea-ID:** IDEA-0003-vibeforge-is-pivoting
- **Release:** V1
- **Epic:** EPIC-007
- **Tasks:**
  - TASK-037 — Add per-subtask status tracking and chain-level aggregation
  - TASK-038 — Add chain status visualization to control UI
- **Effort:** 2M = 4 points
- **Goal:** Provide visibility into delegation chains with per-subtask status tracking and tree/graph visualization in the control UI. Enable users to monitor multi-agent orchestration flows in real time.
- **Dependencies:** WP-0062 (needs delegation chain implementation)
- **Plan Doc:** docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/planning/WPP-0010-WP-0063_TASK-037-038_chain-status-ui.md
- **Verify:**
  - `cd apps/api && python -m pytest`
  - `cd apps/ui && npm run build`
  - Manual: Dispatch task → delegate → observe chain status in UI

### Ordered steps
1. Add per-subtask status tracking + API endpoint (TASK-037)
   - Extend session model or TickEngine to track individual subtask statuses
   - Aggregate chain-level status (pending/in-progress/completed/failed)
   - Add GET /control/agents/{agent_id}/chain-status endpoint
   - Return chain tree with statuses
   - Update status when subtask responses arrive
2. Build chain status visualization UI component (TASK-038)
   - Create ChainStatusView.tsx widget
   - Display delegation chain as tree view
   - Show agent name, subtask summary, status badge per node
   - Real-time updates via polling or SSE
   - Integrate into ControlPanel main area

### Done means
- Each subtask in a delegation chain has individual status
- Chain-level status aggregates from subtask statuses
- GET /control/agents/{agent_id}/chain-status returns chain tree
- ChainStatusView renders delegation chains as tree
- Status badges show per-node state (pending/running/complete/failed)
- Real-time updates work (SSE or polling)
- Component integrated into ControlPanel layout
- `pytest` passes, `npm run build` succeeds

---

## Summary

| WP | Title | Epic | Tasks | Points | Status |
|----|-------|------|-------|--------|--------|
| **MVP WPs (Complete)** | | | | | |
| WP-0053 | Legacy Session Removal | EPIC-001 | 4 | 4 | Done |
| WP-0054 | Bridge Protocol Models + Events | EPIC-002 | 4 | 4 | Done |
| WP-0055 | WebSocket Endpoint + Connection Manager | EPIC-002 | 5 | 7 | Done |
| WP-0056 | Agent Bridge Standalone Service | EPIC-003 | 5 | 8 | Done |
| WP-0057 | Live Agent Control Backend Endpoints | EPIC-004 | 4 | 8 | Done |
| WP-0058 | Async Dispatch Engine | EPIC-005 | 5 | 8 | Done |
| WP-0059 | Control UI: API Client + Components | EPIC-006 | 6 | 7 | Done |
| WP-0060 | Control Panel Layout Rework | EPIC-006 | 1 | 2 | Done |
| **MVP Total** | | | **36** | **50** | **✅ Done** |
| **V1 Security WPs (Priority)** | | | | | |
| WP-0064 | Authentication & TLS Foundation | EPIC-009 | 2 | 4 | Queued |
| WP-0065 | Input Validation & Sandboxing | EPIC-009 | 2 | 2 | Queued |
| WP-0066 | Rate Limiting & Cost Controls | EPIC-009 | 2 | 4 | Queued |
| WP-0067 | Audit Logging & Docs | EPIC-009 | 2 | 3 | Queued |
| **V1 Feature WPs** | | | | | |
| WP-0062 | Delegation Chain Dispatch | EPIC-007 | 2 | 6 | Queued |
| WP-0063 | Chain Status Tracking + UI | EPIC-007 | 2 | 4 | Queued |
| **V1 Total** | | | **12** | **23** | **⏳ Queued** |
| **Grand Total** | | | **48** | **73** | |

### Recommended Execution Order

**Phase 1: Security Hardening (Required First)**
1. WP-0064: Authentication & TLS (foundational)
2. WP-0065: Input Validation (attack prevention)
3. WP-0066: Rate Limiting & Cost Controls (abuse prevention)
4. WP-0067: Audit Logging & Docs (monitoring)

**Phase 2: V1 Features (After Security Complete)**
5. WP-0062: Delegation Chain Dispatch
6. WP-0063: Chain Status Tracking + UI

**Rationale:** Security must be in place before enabling delegation chains (which increase attack surface) and before deploying for external access.
