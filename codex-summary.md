# Codex Summary

Updated AI phase documentation to align with VibeForge's current FastAPI-based Local UI API and safety-focused workflows.

## Changes
- Tailored requirements to emphasize structured questionnaires, workspace isolation, and provider-agnostic model usage.
- Documented architecture with Mermaid diagram showing UI → API → session coordinator → workspace/model interactions, plus component responsibilities.
- Expanded implementation guidance for project layout, setup commands, core modules, and security/performance practices.
- Refined deployment strategy for local-first runs with future containerized targets, environment handling, secrets, and rollback steps.
- Defined monitoring metrics, logging strategy, and incident playbook anchored to session, patch, and model behaviors.
- Clarified testing objectives and scenarios covering session lifecycle, workspace safety, and planned UI/E2E coverage.
- Updated architecture index to point to diagrams, schemas, configs, and AI phase docs for VF-linked changes.

## Project Status Log — 2026-01-07
- **End-to-end goal:** move the UI flow from questionnaire answers → deterministic BuildSpec → concept + TaskGraph generation → agent execution, while the control panel monitors live events and agent interactions end to end.
- **Current readiness:** the session coordinator pipeline covers BuildSpec, concept, and plan generation, but the API still needs to route questionnaire completion through it and surface real plan/progress artifacts for the control UI.
- **Control UI direction:** the control endpoint UI is positioned to become the live operations console once questionnaire submission, plan review, and execution events are fully wired into EventLog streams and TaskGraph artifacts.

## Control Panel Audit — 2026-01-07
### 1) Current State: What works today
- **Control Panel route + layout (VF-170)**
  - **UI surface:** `/control` route renders `ControlPanelScreen` with a left session sidebar and a right-hand dashboard of widgets (status, agent activity, token usage, graph, timeline, event stream).
  - **Data:** Session list + active sessions + per-session status + SSE event stream.
  - **Endpoints:** `GET /control/sessions`, `GET /control/active`, `GET /control/sessions/{id}/status`, `GET /control/sessions/{id}/events`.
  - **Limitations:** No navigation link in the main Layout; session list expects `phase`/`updated_at` but `/control/sessions` returns only `session_id`, `created_at`, and `artifacts`.

- **Session status panel**
  - **UI surface:** Control Panel main header “Session Status” grid.
  - **Data shown:** session_id, phase, active_task_id, completed_tasks, failed_tasks, updated_at.
  - **Endpoint:** `GET /control/sessions/{id}/status` (SessionStore-backed).
  - **Limitations:** SessionStore is in-memory; if the API restarts, active/completed task counts reset.

- **Agent Activity Dashboard (VF-171)**
  - **UI surface:** “Agent Activity” grid widget.
  - **Data shown:** agent role, status (idle/thinking/executing/error), current task, model (from event metadata), last update timestamp.
  - **Event source:** SSE `session_event` stream; statuses derived from `agent_invoked`, `task_started`, `task_completed`, `task_failed`, `agent_completed` events.
  - **Limitations:** Status depends on event ordering; no explicit elapsed time or agent identity beyond role.

- **Token Usage Visualization (VF-172)**
  - **UI surface:** “Token Usage” widget with totals, pie by role, cumulative line, budget meter.
  - **Data shown:** prompt/completion/total tokens + estimated cost by model (hard-coded pricing map).
  - **Event source:** `llm_response_received` events with `prompt_tokens`, `completion_tokens`, `total_tokens`, `agent_role`, `model` metadata.
  - **Limitations:** No server-side cost config; pricing is hard-coded; no per-session budget settings.

- **Agent Relationship Graph (VF-173)**
  - **UI surface:** “Agent Relationship Graph” widget (SVG graph).
  - **Data shown:** agent nodes + task edges from orchestrator to agent role; node status derived from events.
  - **Event source:** `task_started`, `task_completed`, `task_failed`, `agent_invoked`, `agent_completed` events.
  - **Limitations:** Edges are inferred from task assignment; no message-direction view or real agent-to-agent links.

- **Execution Timeline (VF-174)**
  - **UI surface:** “Execution Timeline” widget (swim lanes per role).
  - **Data shown:** task spans with status colors.
  - **Event source:** `task_started`, `task_completed`, `task_failed`, `agent_invoked` events.
  - **Limitations:** No retries/escalations visualized; requires reliable timestamps; no zoom controls.

- **Event Stream Feed**
  - **UI surface:** “Event Stream” list in Control Panel.
  - **Data shown:** event_type, timestamp, message, phase, task_id.
  - **Event source:** `GET /control/sessions/{id}/events` SSE that polls the EventLog every second.
  - **Limitations:** No filtering, auto-scroll, or export; SSE polling only (not push-based); current API constructs EventLog from `events.jsonl` path rather than workspace root.

### 2) Current State: What can be tested now (step-by-step)
- **Basic Control Panel shell + session list**
  1. Start API server and UI.
  2. Create a session via `POST /sessions` (or run the questionnaire flow).
  3. Visit `/control` in the UI.
  4. Confirm sidebar lists “Active” and “All Sessions” entries.
  - **Expected:** session_id appears; active sessions list includes any non-COMPLETE/FAILED sessions.
  - **Notes:** `/control/sessions` is artifact-based and may return sessions that do not exist in SessionStore; `/control/active` uses SessionStore only.

- **Session status panel**
  1. In `/control`, click a session ID.
  2. Verify “Session Status” loads from `/control/sessions/{id}/status`.
  - **Expected:** phase, active_task_id, completed/failed counts render; updated_at shows timestamp.
  - **Notes:** status panel depends on in-memory SessionStore; no persisted history.

- **Event-driven widgets (Agent Activity / Tokens / Graph / Timeline / Event Stream)**
  1. Ensure a session has an `events.jsonl` log with EventLog entries (generated by `SessionCoordinator` in orchestration runs).
  2. Select that session in `/control`.
  3. Observe widgets and event stream update as new events arrive.
  - **Expected:** widgets update when EventLog emits `agent_invoked`, `task_started`, `task_completed`, `task_failed`, `agent_completed`, and `llm_response_received` events.
  - **Notes:** the MVP `/sessions` endpoints do not emit EventLog entries, so the widgets remain idle unless the orchestration path is used.

### 3) Ready Additions (UI-only / Backend-ready)
- **(UI-only) Session list enrichment from artifacts**
  - **What:** Show artifact badges (concept/build_spec/task_graph) and counts based on `/control/sessions` response.
  - **Data:** `artifacts` array already returned by SessionArtifactQuery; UI can infer flags.
  - **Pattern:** badges/chips in session list; hover for artifact names.
  - **Effort/Risks:** **S**; low risk (UI parsing only).

- **(Backend-ready) Active session detail rows**
  - **What:** Show active_task_id and phase in the sidebar list for active sessions.
  - **Data:** `/control/active` already returns `active_task_id` and `phase`.
  - **Pattern:** list rows with secondary text and status chips.
  - **Effort/Risks:** **S**; risk: SessionStore resets on restart.

- **(Backend-ready) Event stream filters (client-side)**
  - **What:** Filter event stream by phase, agent_role, event_type, search term.
  - **Data:** SSE event payload already contains `event_type`, `phase`, `task_id`, `metadata.agent_role`.
  - **Pattern:** filter bar + checkbox chips + search input; filter in-memory.
  - **Effort/Risks:** **M**; risk: no server-side filtering for large sessions.

- **(Backend-ready) Agent cards show model tier + task description**
  - **What:** display `model_tier` and `task_description` from event metadata.
  - **Data:** emitted in `task_started` + `agent_invoked` metadata from SessionCoordinator.
  - **Pattern:** expandable card rows or tooltip details.
  - **Effort/Risks:** **S**; risk: metadata missing for older sessions.

- **(UI-only) “No events yet” helper with instructions**
  - **What:** if SSE stream is empty, show instructions for generating EventLog events.
  - **Data:** no backend change needed.
  - **Pattern:** inline callout with steps and links.
  - **Effort/Risks:** **S**.

### 4) Backend-Dependent Additions (needs backend work)
- **Gate decision log (VF-175)**
  - **Needed:** new `gate_evaluated` EventLog entries with gate name, decision, reason, artifact.
  - **Where to emit:** GatePipeline evaluation in `vibeforge_api.core.gates` or SessionCoordinator gate section.
  - **Endpoint:** existing SSE stream can carry it once events are logged.
  - **Schema:** add metadata fields like `gate_type`, `decision`, `artifact`, `reason`.

- **Model router decisions (VF-176)**
  - **Needed:** `model_routed` events that capture model selection, routing rules, failure_count, reason.
  - **Where to emit:** Distributor routing in `runtime/distributor.py` or AgentFramework call site.
  - **Endpoint:** SSE event stream; optional dedicated `/control/models` table if needed.

- **Prompt inspector (VF-179)**
  - **Needed:** `llm_request_sent` events with prompt, template ID, variables, and context reference.
  - **Where to emit:** AgentFramework adapter before LLM call.
  - **Endpoint:** SSE stream for quick view + optional `/control/sessions/{id}/prompts` for paging.
  - **Schema:** prompt payload likely needs redaction rules and size limits.

- **Cost analytics (VF-180)**
  - **Needed:** pricing config on backend + aggregation endpoints for cost per session/role/model.
  - **Where to emit:** pricing registry + EventLog aggregation service.
  - **Endpoint:** `/control/analytics/costs` (new) or extend `/control/sessions/{id}/status` with cost summary.

- **Event stream server-side filters (VF-178)**
  - **Needed:** query params for event type/phase/agent role; EventLog indexing.
  - **Where to implement:** `GET /control/sessions/{id}/events` with filter args + async generator.
  - **Schema:** no changes; use existing event fields.

### 5) “In Principle” Roadmap (bigger vision)
- **Visualization**
  - Multi-session comparison dashboard (VF-177) with side-by-side token, duration, failure rates.
  - Relationship graph with message-direction arrows + per-edge throughput.

- **Messaging**
  - Threaded agent message timeline (request/response pairs) using `llm_request_sent` + `llm_response_received`.
  - Conversation replay per task with stitched prompt/response + tool calls.

- **Debugging**
  - Gate decision explorer (VF-175) with gate config diffs and “why blocked” drill-down.
  - Model routing audit (VF-176) including escalation path visualization.

- **Configuration**
  - Control panel settings page for budgets, per-role model overrides, and feature flags.

- **Observability**
  - Live health/latency metrics for agent calls, verification runs, and patch application.
  - Long-term event persistence + full-text search across sessions/events.

### 6) Data/Endpoint Map
- **Session list (sidebar)** → `GET /control/sessions` → `SessionArtifactQuery.query_sessions_by_date()` → workspace directories + ArtifactStore contents.
- **Active sessions list** → `GET /control/active` → `session_store.list_sessions()` + `Session` phase/active_task_id.
- **Session status grid** → `GET /control/sessions/{id}/status` → `Session` fields (phase, active/completed/failed tasks).
- **Event stream + widgets** → `GET /control/sessions/{id}/events` → EventLog JSONL (`events.jsonl`) → `SessionCoordinator` event emission (task lifecycle + LLM usage).
- **Agent activity** → `SessionEvent.metadata.agent_role` + `model` + `task_id` from EventLog.
- **Token usage** → `SessionEvent.metadata.prompt_tokens/completion_tokens/total_tokens` + model metadata.

### 7) Recommendations (top 5)
1. **Fix session list data contract** (UI expects `phase`/`updated_at`; API returns artifacts only) to avoid empty UI fields and enable reliable filtering.
2. **Add client-side event filters + auto-scroll** (VF-178-lite) to make the event stream usable without backend changes.
3. **Expose model tier + task description in agent cards** to clarify role routing and relationships.
4. **Instrument gate decisions (VF-175)** to explain why tasks block/fail—critical for debugging.
5. **Add prompt/request logging (VF-179)** with redaction to make message direction and prompt provenance visible.
