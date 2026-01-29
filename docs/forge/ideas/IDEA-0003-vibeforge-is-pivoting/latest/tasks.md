---
doc_type: tasks
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T18-54-22.539Z_run-d5fa"
generated_by: "Task Builder"
generated_at: "2026-01-27T21:10:00+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/features_backlog.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/existing_solution_map.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
tasks:
  # ──────────────────────────────────────────────
  # EPIC-001: Legacy Session Removal
  # ──────────────────────────────────────────────

  - id: "TASK-001"
    feature_id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Delete legacy session UI screen files"
    description: "Delete the 6 legacy session screen components: Home.tsx, Questionnaire.tsx, PlanReview.tsx, Progress.tsx, Clarification.tsx, and Result.tsx from apps/ui/src/screens/. Remove all import references to these files from the codebase."
    acceptance_criteria:
      - "Home.tsx, Questionnaire.tsx, PlanReview.tsx, Progress.tsx, Clarification.tsx, and Result.tsx are deleted from apps/ui/src/screens/"
      - "No import statements referencing deleted files remain in App.tsx or any other source file"
      - "npm run build succeeds with zero errors after deletion"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "cleanup", "deletion"]
    target_files:
      - "apps/ui/src/screens/Home.tsx — delete"
      - "apps/ui/src/screens/Questionnaire.tsx — delete"
      - "apps/ui/src/screens/PlanReview.tsx — delete"
      - "apps/ui/src/screens/Progress.tsx — delete"
      - "apps/ui/src/screens/Clarification.tsx — delete"
      - "apps/ui/src/screens/Result.tsx — delete"
    reuse_notes: "Pure deletion. No new code needed."

  - id: "TASK-002"
    feature_id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Delete sessions router and remove from main.py"
    description: "Delete apps/api/vibeforge_api/routers/sessions.py. Remove its import and app.include_router() call from main.py. All /sessions/* endpoints should return 404."
    acceptance_criteria:
      - "sessions.py is deleted from routers/"
      - "main.py no longer imports or mounts the sessions router"
      - "GET/POST /sessions/* return 404"
      - "All /control/* endpoints still function correctly"
      - "pytest passes for remaining endpoints"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "cleanup", "deletion"]
    target_files:
      - "apps/api/vibeforge_api/routers/sessions.py — delete"
      - "apps/api/vibeforge_api/main.py — modify (remove sessions router mount)"
    reuse_notes: "SessionStore and Session model remain untouched. Only the router and its main.py mount are removed."

  - id: "TASK-003"
    feature_id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Remove session-specific request and response models"
    description: "Remove Pydantic models that are only used by the legacy sessions router: SubmitAnswerRequest, PlanDecisionRequest, ClarificationAnswerRequest from requests.py. Remove SessionResponse, QuestionResponse, QuestionOption, PlanSummaryResponse, ProgressResponse, TaskProgress, ResultResponse, ClarificationOption, ClarificationResponse from responses.py. Verify no remaining code references them."
    acceptance_criteria:
      - "SubmitAnswerRequest, PlanDecisionRequest, ClarificationAnswerRequest removed from requests.py"
      - "SessionResponse, QuestionResponse, QuestionOption, PlanSummaryResponse, ProgressResponse, TaskProgress, ResultResponse, ClarificationOption, ClarificationResponse removed from responses.py"
      - "No remaining import references to deleted models"
      - "pytest passes"
    dependencies: ["TASK-002"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "cleanup"]
    target_files:
      - "apps/api/vibeforge_api/models/requests.py — modify (remove 3 classes)"
      - "apps/api/vibeforge_api/models/responses.py — modify (remove 9 classes)"
      - "apps/api/vibeforge_api/models/__init__.py — modify (remove re-exports)"
    reuse_notes: "All agent workflow models (InitializeAgentsRequest, etc.) remain. Only session-flow-specific models removed."

  - id: "TASK-004"
    feature_id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Update App.tsx routes and remove session API client"
    description: "Update App.tsx to only define /control and /simulation routes. Set the default route (/) to redirect to /control. Delete apps/ui/src/api/client.ts (the legacy session API client). Remove session-specific types from apps/ui/src/types/api.ts."
    acceptance_criteria:
      - "App.tsx defines only /control and /simulation routes"
      - "/ redirects to /control (via Navigate or index route)"
      - "apps/ui/src/api/client.ts is deleted"
      - "Session-specific types removed from api.ts (SessionPhase questionnaire values, QuestionResponse, AnswerRequest, PlanResponse, etc.)"
      - "npm run build succeeds"
    dependencies: ["TASK-001"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "cleanup"]
    target_files:
      - "apps/ui/src/ui/App.tsx — modify (remove session routes, add redirect)"
      - "apps/ui/src/api/client.ts — delete"
      - "apps/ui/src/types/api.ts — modify (remove session types)"
    reuse_notes: "controlClient.ts and its types remain. Only session-flow client and types removed."

  # ──────────────────────────────────────────────
  # EPIC-002: Agent Bridge Protocol and Connection Manager
  # ──────────────────────────────────────────────

  - id: "TASK-005"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Define agent bridge protocol Pydantic models"
    description: "Create Pydantic models for the 6 agent bridge protocol message types: RegisterMessage, RegisteredMessage, DispatchMessage, ProgressMessage, ResponseMessage, HeartbeatMessage. All share a 'type' discriminator field. Place in a new file apps/api/vibeforge_api/models/bridge_protocol.py."
    acceptance_criteria:
      - "6 Pydantic models defined with correct fields per protocol spec"
      - "Each model has a 'type' literal field for discrimination (e.g., type: Literal['register'])"
      - "BridgeMessage union type allows parsing any protocol message via type field"
      - "Models include field validation (non-empty agent_id, valid message_id, etc.)"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "protocol", "models"]
    target_files:
      - "apps/api/vibeforge_api/models/bridge_protocol.py — create new"
      - "apps/api/vibeforge_api/models/__init__.py — extend (re-export new models)"
    reuse_notes: "New file. No existing protocol models to extend."

  - id: "TASK-006"
    feature_id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Add unit tests for bridge protocol serialization"
    description: "Write pytest tests verifying serialization/deserialization of all 6 protocol message types. Test round-trip (model → JSON → model), type discrimination, and validation of invalid inputs."
    acceptance_criteria:
      - "Tests exist for all 6 message types"
      - "Round-trip serialization verified (model_dump → model_validate)"
      - "Type discrimination tested (parse union from raw JSON)"
      - "Validation rejects empty agent_id, missing required fields"
      - "All tests pass"
    dependencies: ["TASK-005"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "testing"]
    target_files:
      - "apps/api/tests/test_bridge_protocol.py — create new"
    reuse_notes: "Follow existing test patterns in apps/api/tests/."

  - id: "TASK-007"
    feature_id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Implement WebSocket endpoint at /ws/agent-bridge"
    description: "Create a FastAPI WebSocket endpoint at /ws/agent-bridge. Handle the connection lifecycle: accept connection, receive register message, send registered response, enter message loop (dispatch/progress/response/heartbeat). Mount in main.py."
    acceptance_criteria:
      - "WebSocket endpoint exists at /ws/agent-bridge"
      - "Connection accepted and register/registered handshake works"
      - "Message loop processes incoming JSON messages using protocol models"
      - "Invalid messages are rejected with close code and reason"
      - "Endpoint mounted in main.py"
    dependencies: ["TASK-005"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "websocket"]
    target_files:
      - "apps/api/vibeforge_api/routers/agent_bridge.py — create new"
      - "apps/api/vibeforge_api/main.py — modify (mount WS endpoint)"
    reuse_notes: "Use fastapi.WebSocket natively. No third-party WS library needed. Follows existing router pattern."

  - id: "TASK-008"
    feature_id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Add heartbeat monitoring and stale connection detection"
    description: "Implement heartbeat tracking in the WebSocket endpoint. Track last heartbeat timestamp per connection. Detect stale connections (no heartbeat within configurable timeout). Emit AGENT_DISCONNECTED event on timeout. Close stale connections."
    acceptance_criteria:
      - "Heartbeat messages update last-seen timestamp"
      - "Background task checks for stale connections at configurable interval"
      - "Connections with no heartbeat within timeout are closed"
      - "AGENT_DISCONNECTED event emitted when connection lost"
    dependencies: ["TASK-007", "TASK-010"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "websocket", "monitoring"]
    target_files:
      - "apps/api/vibeforge_api/routers/agent_bridge.py — extend"
    reuse_notes: "Extend the WS endpoint. Heartbeat logic lives in the connection manager (TASK-009)."

  - id: "TASK-009"
    feature_id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Add agent bridge event types to EventLog"
    description: "Extend the EventType enum in event_log.py with new values for agent bridge lifecycle: AGENT_CONNECTED, AGENT_DISCONNECTED, TASK_DISPATCHED, AGENT_PROGRESS, AGENT_RESPONSE, AGENT_ERROR, AGENT_HEARTBEAT_LOST. These events flow through the existing SSE pipeline automatically."
    acceptance_criteria:
      - "7 new EventType values added to the enum"
      - "Events can be created and logged using existing EventLog.log_event()"
      - "Events appear in SSE stream and filtered event queries"
      - "Existing event types and filtering still work"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "events"]
    target_files:
      - "apps/api/vibeforge_api/core/event_log.py — extend (add 7 EventType values)"
    reuse_notes: "Extend existing EventType enum. Do NOT create a separate event system."

  - id: "TASK-010"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Build RemoteAgentConnectionManager singleton"
    description: "Create a centralized connection manager as a module-level singleton in apps/api/vibeforge_api/core/agent_bridge.py. Track connected agents by agent_id with their WebSocket connection, state (connected/busy/idle/disconnected), capabilities, and metadata. Provide methods: register_agent(), unregister_agent(), get_agent(), list_agents(), get_agent_status()."
    acceptance_criteria:
      - "RemoteAgentConnectionManager class created with singleton instance"
      - "register_agent() stores connection + metadata, emits AGENT_CONNECTED event"
      - "unregister_agent() removes connection, emits AGENT_DISCONNECTED event"
      - "get_agent() returns agent info or None"
      - "list_agents() returns all tracked agents"
      - "get_agent_status() returns current state"
      - "Thread-safe for concurrent WebSocket connections"
    dependencies: ["TASK-009"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "service"]
    target_files:
      - "apps/api/vibeforge_api/core/agent_bridge.py — create new"
    reuse_notes: "New singleton service. Pattern follows session_store global instance in session.py. Integrates with EventLog for event emission."

  - id: "TASK-011"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Add dispatch and response buffering to connection manager"
    description: "Extend RemoteAgentConnectionManager with dispatch_task() that sends a DispatchMessage over WebSocket to the target agent, and buffer_response() that stores incoming ResponseMessage payloads. Provide get_buffered_responses() to drain the buffer."
    acceptance_criteria:
      - "dispatch_task(agent_id, message_id, content, context) sends dispatch over WS"
      - "Agent state transitions to 'busy' on dispatch"
      - "buffer_response() stores response with message_id key"
      - "get_buffered_responses(agent_id) returns and clears buffered responses"
      - "TASK_DISPATCHED event emitted on dispatch"
      - "AGENT_RESPONSE event emitted on response arrival"
    dependencies: ["TASK-010"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "service"]
    target_files:
      - "apps/api/vibeforge_api/core/agent_bridge.py — extend"
    reuse_notes: "Extend the connection manager. Response buffer is dict[str, list[dict]] keyed by agent_id."

  - id: "TASK-012"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Add unit tests for RemoteAgentConnectionManager"
    description: "Write pytest tests for the connection manager: registration, unregistration, dispatch, response buffering, status queries. Use mock WebSocket objects."
    acceptance_criteria:
      - "Tests cover register/unregister lifecycle"
      - "Tests cover dispatch_task with mock WebSocket"
      - "Tests cover response buffering and draining"
      - "Tests verify event emission (mock EventLog)"
      - "All tests pass"
    dependencies: ["TASK-011"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "testing"]
    target_files:
      - "apps/api/tests/test_agent_bridge.py — create new"
    reuse_notes: "Follow existing test patterns."

  - id: "TASK-013"
    feature_id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Add agent connection fields to Session model"
    description: "Extend Session class in core/session.py with fields for remote agent connections: agent_connections (dict mapping agent_id to connection metadata), pending_dispatches (dict mapping message_id to dispatch info), response_buffer (list of buffered async responses). Update to_dict() and from_dict() accordingly."
    acceptance_criteria:
      - "Session has agent_connections: dict[str, dict] field (default {})"
      - "Session has pending_dispatches: dict[str, dict] field (default {})"
      - "Session has response_buffer: list[dict] field (default [])"
      - "to_dict() serializes new fields"
      - "from_dict() deserializes new fields with defaults"
      - "Existing session functionality unaffected"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "models"]
    target_files:
      - "apps/api/vibeforge_api/core/session.py — extend (add 3 fields + serialization)"
    reuse_notes: "Extend existing Session class. Do NOT create a parallel state model."

  # ──────────────────────────────────────────────
  # EPIC-003: Agent Bridge Service
  # ──────────────────────────────────────────────

  - id: "TASK-014"
    feature_id: "FEAT-007"
    epic_id: "EPIC-003"
    title: "Build bridge WebSocket client with registration handshake"
    description: "Create tools/agent_bridge/bridge.py with a WebSocket client that connects to a configurable VibeForge URL, sends a register message with agent_id and auth_token, and receives the registered acknowledgment. Use websockets or aiohttp library."
    acceptance_criteria:
      - "Bridge connects to configurable WebSocket URL"
      - "Sends RegisterMessage on connection"
      - "Waits for RegisteredMessage response"
      - "Logs successful registration"
      - "Exits with error if registration fails or times out"
    dependencies: ["TASK-005"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "standalone", "websocket"]
    target_files:
      - "tools/agent_bridge/bridge.py — create new"
      - "tools/agent_bridge/__init__.py — create new"
    reuse_notes: "New standalone service. Reuses protocol message format from TASK-005."

  - id: "TASK-015"
    feature_id: "FEAT-007"
    epic_id: "EPIC-003"
    title: "Add heartbeat sending and reconnection with backoff"
    description: "Extend bridge.py with heartbeat sending at configurable interval (default 30s). Add reconnection logic with exponential backoff (1s → 2s → 4s → ... → max 60s) on connection loss. Resume registration after reconnect."
    acceptance_criteria:
      - "Heartbeat messages sent at configurable interval"
      - "Connection loss triggers reconnection attempt"
      - "Exponential backoff between reconnection attempts"
      - "Maximum backoff capped at 60 seconds"
      - "Successful reconnection re-registers the agent"
    dependencies: ["TASK-014"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "standalone", "reliability"]
    target_files:
      - "tools/agent_bridge/bridge.py — extend"
    reuse_notes: "Extend existing bridge client."

  - id: "TASK-016"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Implement Claude Code CLI wrapper for task execution"
    description: "Create tools/agent_bridge/cli_wrapper.py with a function that invokes 'claude --print --output-format json' with given task content and working directory. Capture stdout/stderr. Parse JSON output. Return structured result with content and usage metadata."
    acceptance_criteria:
      - "invoke_claude(task_content, workdir) function exists"
      - "Runs 'claude --print --output-format json' subprocess"
      - "Captures and parses JSON stdout"
      - "Returns structured result with content, usage, exit_code"
      - "Handles subprocess errors (timeout, non-zero exit, invalid JSON)"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "standalone", "cli"]
    target_files:
      - "tools/agent_bridge/cli_wrapper.py — create new"
    reuse_notes: "New module. No existing CLI wrapper to extend."

  - id: "TASK-017"
    feature_id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Wire dispatch handling to CLI execution with progress streaming"
    description: "Extend bridge.py to handle incoming DispatchMessage: invoke CLI wrapper, send ProgressMessage during execution, send ResponseMessage with final result. Handle errors by sending error response."
    acceptance_criteria:
      - "Incoming DispatchMessage triggers CLI invocation"
      - "ProgressMessage sent with status='running' when execution starts"
      - "ResponseMessage sent with content and usage on completion"
      - "Error response sent if CLI fails (timeout, crash, invalid output)"
      - "Agent state transitions: idle → busy → idle"
    dependencies: ["TASK-014", "TASK-016"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "standalone"]
    target_files:
      - "tools/agent_bridge/bridge.py — extend"
    reuse_notes: "Extend bridge message handler. Uses cli_wrapper for execution."

  - id: "TASK-018"
    feature_id: "FEAT-009"
    epic_id: "EPIC-003"
    title: "Add CLI interface and signal handling to bridge"
    description: "Add argparse CLI to bridge.py with --url, --agent-id, --token, --workdir arguments. Add signal handling for SIGINT/SIGTERM to trigger graceful shutdown (close WebSocket, log disconnect). Create tools/agent_bridge/requirements.txt with dependencies."
    acceptance_criteria:
      - "python bridge.py --url ws://... --agent-id ... --token ... --workdir ... launches bridge"
      - "Missing required args produce clear error messages"
      - "SIGINT/SIGTERM triggers graceful WebSocket close"
      - "requirements.txt lists websockets (or aiohttp) dependency"
      - "--help shows usage information"
    dependencies: ["TASK-014"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "standalone", "cli"]
    target_files:
      - "tools/agent_bridge/bridge.py — extend (add argparse + signal handling)"
      - "tools/agent_bridge/requirements.txt — create new"
    reuse_notes: "Extend existing bridge.py entry point."

  # ──────────────────────────────────────────────
  # EPIC-004: Live Agent Control Backend
  # ──────────────────────────────────────────────

  - id: "TASK-019"
    feature_id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Add agent registration and listing endpoints to /control"
    description: "Add REST endpoints to the control router: POST /control/agents/register (register agent by name + endpoint URL), GET /control/agents (list all agents with status), GET /control/agents/{agent_id} (get agent details). Integrate with RemoteAgentConnectionManager."
    acceptance_criteria:
      - "POST /control/agents/register accepts name and endpoint_url, returns agent_id"
      - "GET /control/agents returns list of all agents with connection status"
      - "GET /control/agents/{agent_id} returns detailed agent info or 404"
      - "Agents registered via REST are tracked in connection manager"
      - "Pydantic request/response models defined for all endpoints"
    dependencies: ["TASK-010"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "api"]
    target_files:
      - "apps/api/vibeforge_api/routers/control.py — extend (add 3 endpoints)"
      - "apps/api/vibeforge_api/models/requests.py — extend (RegisterAgentRequest)"
      - "apps/api/vibeforge_api/models/responses.py — extend (AgentListResponse, AgentDetailResponse)"
    reuse_notes: "Extend existing /control router. Follow lazy-import pattern used by existing endpoints."

  - id: "TASK-020"
    feature_id: "FEAT-011"
    epic_id: "EPIC-004"
    title: "Add task dispatch and follow-up endpoints"
    description: "Add REST endpoints: POST /control/agents/{agent_id}/dispatch (send task to agent), POST /control/agents/{agent_id}/followup (send follow-up message to active task), GET /control/agents/{agent_id}/task (get current task status). Dispatches route through connection manager."
    acceptance_criteria:
      - "POST dispatch sends task content to agent via connection manager"
      - "POST followup sends message to agent's active task"
      - "GET task returns current task status (idle/dispatched/running/completed/error)"
      - "Dispatch to disconnected agent returns 409 Conflict"
      - "Events emitted for dispatch and response"
    dependencies: ["TASK-011", "TASK-019"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "api"]
    target_files:
      - "apps/api/vibeforge_api/routers/control.py — extend (add 3 endpoints)"
      - "apps/api/vibeforge_api/models/requests.py — extend (DispatchTaskRequest, FollowUpRequest)"
      - "apps/api/vibeforge_api/models/responses.py — extend (TaskDispatchResponse, TaskStatusResponse)"
    reuse_notes: "Extend existing /control router. Dispatch goes through RemoteAgentConnectionManager."

  - id: "TASK-021"
    feature_id: "FEAT-012"
    epic_id: "EPIC-004"
    title: "Extend SSE streaming with agent-specific event types"
    description: "Ensure the existing SSE endpoint at /control/sessions/{session_id}/events delivers the new agent bridge event types (AGENT_CONNECTED, TASK_DISPATCHED, AGENT_PROGRESS, AGENT_RESPONSE, etc.). Add an agent-scoped SSE endpoint: GET /control/agents/{agent_id}/events for per-agent streaming."
    acceptance_criteria:
      - "Existing SSE endpoint delivers new agent event types"
      - "GET /control/agents/{agent_id}/events streams events for a specific agent"
      - "Multiple concurrent SSE clients supported"
      - "Events include agent_id in metadata for filtering"
    dependencies: ["TASK-009", "TASK-019"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "api", "streaming"]
    target_files:
      - "apps/api/vibeforge_api/routers/control.py — extend (add agent SSE endpoint)"
    reuse_notes: "Reuse existing EventSourceResponse + EventLog pattern. New agent events flow through existing pipeline via EventType enum extension."

  - id: "TASK-022"
    feature_id: "FEAT-012"
    epic_id: "EPIC-004"
    title: "Add integration tests for agent control endpoints"
    description: "Write pytest integration tests for the agent registration, dispatch, follow-up, and status endpoints. Use FastAPI TestClient. Mock the WebSocket connection and connection manager where needed."
    acceptance_criteria:
      - "Tests cover agent registration (success + validation errors)"
      - "Tests cover task dispatch (success + agent not found + agent disconnected)"
      - "Tests cover follow-up messages"
      - "Tests cover agent listing and status"
      - "All tests pass"
    dependencies: ["TASK-019", "TASK-020", "TASK-021"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "testing"]
    target_files:
      - "apps/api/tests/test_control_agents.py — create new"
    reuse_notes: "Follow existing test patterns in apps/api/tests/."

  - id: "TASK-041"
    feature_id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Replace session list/status endpoints with control context"
    description: "Remove session-listing endpoints from the /control router (GET /control/sessions, GET /control/active, GET /control/sessions/{id}/status, GET /control/sessions/{id}/bundle). Add a single control context endpoint (GET /control/context) that returns a stable control_session_id created on first call. Keep /control/sessions/{id}/events and all simulation endpoints intact."
    acceptance_criteria:
      - "GET /control/context returns {control_session_id} and is stable across calls"
      - "GET /control/sessions returns 404"
      - "GET /control/active returns 404"
      - "GET /control/sessions/{id}/status returns 404"
      - "GET /control/sessions/{id}/bundle returns 404"
      - "SSE stream at /control/sessions/{control_session_id}/events still works"
      - "Existing simulation endpoints still function"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "api", "cleanup"]
    target_files:
      - "apps/api/vibeforge_api/routers/control.py - modify (remove session list/status endpoints, add /control/context)"
      - "apps/api/tests/test_control_api.py - update (remove session list/status tests, add control context tests)"
    reuse_notes: "Keep SessionStore for simulation. The new control context should be a single persistent session id for /control observability."

  # ──────────────────────────────────────────────
  # EPIC-005: Async Dispatch Engine
  # ──────────────────────────────────────────────

  - id: "TASK-023"
    feature_id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Add agent_type field to AgentConfig model"
    description: "Extend AgentConfig in orchestration/models.py with agent_type: str = 'simulation' (values: 'simulation' | 'remote'). Add endpoint_url and connection_status optional fields for remote agents. This allows TickEngine to distinguish between simulation and remote agents."
    acceptance_criteria:
      - "AgentConfig has agent_type field defaulting to 'simulation'"
      - "AgentConfig has optional endpoint_url and connection_status fields"
      - "Existing simulation code unaffected (default agent_type = 'simulation')"
      - "Validation rejects unknown agent_type values"
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["backend", "models"]
    target_files:
      - "orchestration/models.py — extend (add fields to AgentConfig)"
    reuse_notes: "Extend existing AgentConfig Pydantic model. Do NOT create a parallel model."

  - id: "TASK-024"
    feature_id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Add async dispatch path in TickEngine.advance_tick()"
    description: "Extend TickEngine.advance_tick() to detect remote agents (agent_type == 'remote') and dispatch to them via RemoteAgentConnectionManager instead of calling LlmResponseGenerator. Return immediately with 'dispatched' status for remote agents. In-process LLM calls continue working for simulation agents."
    acceptance_criteria:
      - "Remote agent messages are dispatched via connection manager"
      - "advance_tick() returns immediately for remote agents (no blocking)"
      - "Tick result includes 'dispatched' status for remote messages"
      - "Simulation agents (agent_type == 'simulation') still use LlmResponseGenerator"
      - "TASK_DISPATCHED event emitted for remote dispatches"
    dependencies: ["TASK-011", "TASK-023"]
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "orchestration"]
    target_files:
      - "orchestration/coordinator/tick_engine.py — extend (add remote dispatch branch in advance_tick)"
    reuse_notes: "Extend existing advance_tick() method. Add _dispatch_to_remote_agent() helper. Do NOT replace the existing tick loop."

  - id: "TASK-025"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Add response buffer checking to TickEngine tick loop"
    description: "Extend TickEngine.advance_tick() to check RemoteAgentConnectionManager's response buffer at the start of each tick. When a buffered response is found, process it as if it were a local LLM response (convert to message, queue for delivery, track delegation)."
    acceptance_criteria:
      - "advance_tick() checks response buffer before processing message queue"
      - "Buffered responses are converted to standard messages"
      - "Converted messages enter the normal message processing pipeline"
      - "Response buffer is drained after processing"
      - "AGENT_RESPONSE event emitted for processed responses"
    dependencies: ["TASK-024"]
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "orchestration"]
    target_files:
      - "orchestration/coordinator/tick_engine.py — extend (add _check_response_buffer method)"
    reuse_notes: "Extend existing tick loop. Buffered responses flow into the existing message processing pipeline."

  - id: "TASK-026"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Add dispatch timeout handling"
    description: "Extend TickEngine to track pending dispatches with timestamps. On each tick, check for timed-out dispatches (configurable timeout, default 300s). Emit AGENT_ERROR event for timeouts. Mark timed-out agents for retry or failure."
    acceptance_criteria:
      - "Pending dispatches tracked with creation timestamp"
      - "Timeout check runs on each tick"
      - "Timed-out dispatches emit AGENT_ERROR event"
      - "Configurable timeout (default 300 seconds)"
      - "Timed-out dispatch clears pending state"
    dependencies: ["TASK-025"]
    release_target: "MVP"
    priority: "P1"
    estimate: "S"
    tags: ["backend", "orchestration", "reliability"]
    target_files:
      - "orchestration/coordinator/tick_engine.py — extend"
    reuse_notes: "Extend tick loop. Timeout tracking follows existing cost tracking pattern."

  - id: "TASK-027"
    feature_id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Add tests for async dispatch and response buffering in TickEngine"
    description: "Write pytest tests for the async dispatch path: dispatching to remote agents, response buffering, response processing on subsequent ticks, and timeout handling. Mock the connection manager."
    acceptance_criteria:
      - "Tests verify remote agent dispatch (message sent to manager)"
      - "Tests verify response buffering and processing on next tick"
      - "Tests verify timeout triggers error event"
      - "Tests verify simulation agents still use LlmResponseGenerator"
      - "All tests pass"
    dependencies: ["TASK-026"]
    release_target: "MVP"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "testing"]
    target_files:
      - "apps/api/tests/test_tick_engine_async.py — create new"
    reuse_notes: "Follow existing test patterns. Mock RemoteAgentConnectionManager."

  # ──────────────────────────────────────────────
  # EPIC-006: Live Agent Control UI
  # ──────────────────────────────────────────────

  - id: "TASK-028"
    feature_id: "FEAT-015"
    epic_id: "EPIC-006"
    title: "Add agent registration API functions to controlClient.ts"
    description: "Extend controlClient.ts with typed functions: registerAgent(name, endpointUrl), listAgents(), getAgentStatus(agentId). Add corresponding TypeScript types: RemoteAgent, AgentConnectionStatus, RegisterAgentRequest, AgentListResponse."
    acceptance_criteria:
      - "registerAgent() sends POST to /control/agents/register"
      - "listAgents() sends GET to /control/agents"
      - "getAgentStatus() sends GET to /control/agents/{agent_id}"
      - "TypeScript types defined for all request/response shapes"
      - "npm run build succeeds"
    dependencies: ["TASK-019"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "api"]
    target_files:
      - "apps/ui/src/api/controlClient.ts — extend (add 3 functions + types)"
    reuse_notes: "Extend existing controlClient.ts. Follow its existing fetch/type patterns."

  - id: "TASK-029"
    feature_id: "FEAT-015"
    epic_id: "EPIC-006"
    title: "Build AgentRegistrationPanel React component"
    description: "Create a React component with a form for registering agents (name + endpoint URL). Show validation feedback. On success, refresh agent list. Display as a card/panel in the /control layout."
    acceptance_criteria:
      - "Form accepts agent name and endpoint URL"
      - "Submit calls registerAgent() and handles success/error"
      - "Validation: name required, URL must be valid"
      - "On success, calls onRegistered callback to refresh parent"
      - "Component renders as a compact panel suitable for sidebar"
    dependencies: ["TASK-028"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "ux"]
    target_files:
      - "apps/ui/src/screens/control/widgets/AgentRegistrationPanel.tsx — create new"
    reuse_notes: "New widget. Follow styling patterns from existing AgentInitializer.tsx."

  - id: "TASK-030"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Add task dispatch and follow-up API functions"
    description: "Extend controlClient.ts with: dispatchTask(agentId, content), sendFollowUp(agentId, content), getTaskStatus(agentId). Add TypeScript types for dispatch request/response."
    acceptance_criteria:
      - "dispatchTask() sends POST to /control/agents/{agent_id}/dispatch"
      - "sendFollowUp() sends POST to /control/agents/{agent_id}/followup"
      - "getTaskStatus() sends GET to /control/agents/{agent_id}/task"
      - "TypeScript types defined for all shapes"
    dependencies: ["TASK-020"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "api"]
    target_files:
      - "apps/ui/src/api/controlClient.ts — extend (add 3 functions + types)"
    reuse_notes: "Extend existing controlClient.ts."

  - id: "TASK-031"
    feature_id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Build TaskDispatchPanel chat-style React component"
    description: "Create a chat-style panel component with text input for task dispatch and follow-up messages. Display conversation history (user messages + agent responses). Show thinking/working indicator when agent is processing."
    acceptance_criteria:
      - "Text input sends task via dispatchTask() on first message"
      - "Subsequent messages sent via sendFollowUp()"
      - "Conversation history displays user and agent messages"
      - "Thinking indicator shown when agent status is 'busy'"
      - "Component scrolls to latest message automatically"
    dependencies: ["TASK-029", "TASK-030"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["frontend", "ux"]
    target_files:
      - "apps/ui/src/screens/control/widgets/TaskDispatchPanel.tsx — create new"
    reuse_notes: "New widget. Can borrow message display patterns from MultiAgentMessages.tsx."

  - id: "TASK-032"
    feature_id: "FEAT-017"
    epic_id: "EPIC-006"
    title: "Build StreamingOutputView React component"
    description: "Create a component that subscribes to agent SSE events and renders them in real time. Support rendering of chat messages, tool-call events, status changes, and error events. Include auto-scroll with pause button."
    acceptance_criteria:
      - "Subscribes to SSE via /control/agents/{agent_id}/events"
      - "Renders chat messages with agent attribution"
      - "Renders tool-call events with name and result"
      - "Renders status change events (connected, busy, idle, error)"
      - "Auto-scrolls to latest event; pause button stops auto-scroll"
    dependencies: ["TASK-021", "TASK-028"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["frontend", "ux", "streaming"]
    target_files:
      - "apps/ui/src/screens/control/widgets/StreamingOutputView.tsx — create new"
    reuse_notes: "New widget. Reuse SSE subscription pattern from EventStream.tsx. Reuse event rendering patterns."

  - id: "TASK-033"
    feature_id: "FEAT-018"
    epic_id: "EPIC-006"
    title: "Build AgentConnectionDashboard React component"
    description: "Create a dashboard component showing a grid/list of all registered agents with their connection status. Each agent card shows name, endpoint, status badge (connected/busy/idle/disconnected), and a select action to focus the task dispatch panel on that agent."
    acceptance_criteria:
      - "Grid/list displays all agents from listAgents()"
      - "Each card shows name, endpoint URL, and status badge"
      - "Status badges use distinct colors (green=connected, blue=busy, gray=idle, red=disconnected)"
      - "Auto-refreshes at configurable interval (default 5s)"
      - "Clicking an agent card calls onSelectAgent callback"
    dependencies: ["TASK-028"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "ux"]
    target_files:
      - "apps/ui/src/screens/control/widgets/AgentConnectionDashboard.tsx — create new"
    reuse_notes: "New widget. Follow card layout patterns from existing dashboard widgets."

  - id: "TASK-034"
    feature_id: "FEAT-018"
    epic_id: "EPIC-006"
    title: "Rework ControlPanel.tsx layout for agent-centric experience"
    description: "Rework the ControlPanel screen to feature an agent-centric layout: left sidebar with AgentConnectionDashboard and AgentRegistrationPanel, main area with TaskDispatchPanel and StreamingOutputView for the selected agent. Retain EventStream and CostAnalytics as collapsible bottom panels."
    acceptance_criteria:
      - "Left sidebar shows AgentConnectionDashboard + AgentRegistrationPanel"
      - "Main area shows TaskDispatchPanel + StreamingOutputView for selected agent"
      - "Selecting an agent in dashboard focuses task panel on that agent"
      - "EventStream and CostAnalytics accessible as collapsible panels"
      - "Layout responsive (sidebar collapses on small screens)"
      - "npm run build succeeds"
    dependencies: ["TASK-029", "TASK-031", "TASK-032", "TASK-033"]
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["frontend", "ux", "layout"]
    target_files:
      - "apps/ui/src/screens/ControlPanel.tsx — rework"
    reuse_notes: "Rework existing ControlPanel.tsx. Retain reusable monitoring widgets. Replace session-centric sidebar with agent-centric components."

  - id: "TASK-042"
    feature_id: "FEAT-018"
    epic_id: "EPIC-006"
    title: "Remove session list/status UI and wire control context"
    description: "Update the control UI to stop listing sessions or showing session status grids. Fetch the control_session_id from GET /control/context and use it for SSE/event-driven widgets that still need a context. Remove session-list API calls and types from controlClient.ts and api types."
    acceptance_criteria:
      - "ControlPanel no longer renders session list or status grid"
      - "ControlPanel fetches control_session_id via /control/context when needed"
      - "Session list/status API helpers removed from controlClient.ts"
      - "Session list/status types removed from apps/ui/src/types/api.ts"
      - "npm run build succeeds"
    dependencies: ["TASK-041"]
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["frontend", "cleanup", "ux"]
    target_files:
      - "apps/ui/src/screens/ControlPanel.tsx - update (remove session list/status, add control context fetch)"
      - "apps/ui/src/api/controlClient.ts - update (remove list/status helpers, add getControlContext)"
      - "apps/ui/src/types/api.ts - update (remove session list/status types)"
    reuse_notes: "Keep simulation createSession API for /simulation. Control UI should treat context id as internal."

  # ──────────────────────────────────────────────
  # EPIC-009: Security Hardening (V1-Prerequisite)
  # ──────────────────────────────────────────────

  - id: "TASK-043"
    feature_id: "FEAT-023"
    epic_id: "EPIC-009"
    title: "Replace hardcoded 'secret' token with secure authentication system"
    description: "Replace the hardcoded 'secret' token with a proper authentication system. Generate secure random tokens for agent registration. Add token validation middleware to WebSocket and REST endpoints. Store tokens securely (environment variables or config file). Update agent bridge to accept token as parameter."
    acceptance_criteria:
      - "Hardcoded 'secret' removed from codebase"
      - "Secure token generation function (32+ byte random hex)"
      - "Token validation middleware on /ws/agent-bridge and /control/* endpoints"
      - "Agent bridge accepts --token parameter and validates on server"
      - "Invalid tokens return 401 Unauthorized"
      - "Tokens stored in environment variables or secure config"
      - "Documentation updated with token generation instructions"
    dependencies: []
    release_target: "V1"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "security", "authentication"]
    target_files:
      - "apps/api/vibeforge_api/core/auth.py — create new (token validation)"
      - "apps/api/vibeforge_api/routers/agent_bridge.py — extend (add auth middleware)"
      - "apps/api/vibeforge_api/routers/control.py — extend (add auth middleware)"
      - "apps/api/vibeforge_api/main.py — extend (configure auth)"
      - "tools/agent_bridge/bridge.py — verify (already accepts --token)"
      - "docs/CONTROL_PANEL_GUIDE.md — update (token generation instructions)"
    reuse_notes: "New auth module. Bridge already accepts --token parameter."

  - id: "TASK-044"
    feature_id: "FEAT-023"
    epic_id: "EPIC-009"
    title: "Add TLS/SSL support with self-signed certificates for testing"
    description: "Add TLS/SSL support to the API server for encrypted connections (HTTPS/WSS). Generate self-signed certificates for development/testing. Update uvicorn startup to use SSL context. Update agent bridge connection to support wss:// URLs. Add certificate verification options."
    acceptance_criteria:
      - "Self-signed certificate generation script added (tools/generate_certs.sh or .ps1)"
      - "Uvicorn server accepts --ssl-keyfile and --ssl-certfile parameters"
      - "API accessible via https://localhost:8000"
      - "WebSocket endpoint accessible via wss://localhost:8000/ws/agent-bridge"
      - "Agent bridge connects successfully to wss:// URLs"
      - "Certificate verification can be disabled for self-signed certs (--insecure flag)"
      - "Documentation updated with TLS setup instructions"
    dependencies: []
    release_target: "V1"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "security", "tls", "infrastructure"]
    target_files:
      - "tools/generate_certs.sh — create new (or .ps1 for Windows)"
      - "apps/api/vibeforge_api/main.py — extend (SSL context configuration)"
      - "tools/agent_bridge/bridge.py — extend (WSS support + cert verification options)"
      - "docs/CONTROL_PANEL_GUIDE.md — update (TLS setup section)"
    reuse_notes: "Use Python ssl module. WebSocket library (websockets) supports WSS natively."

  - id: "TASK-045"
    feature_id: "FEAT-024"
    epic_id: "EPIC-009"
    title: "Implement path sandboxing in agent bridge"
    description: "Add path validation in agent bridge to prevent directory traversal attacks. Ensure all file operations stay within the configured --workdir. Reject paths containing '..' or absolute paths outside workdir. Log and reject suspicious path access attempts."
    acceptance_criteria:
      - "Path validation function checks all file operations"
      - "Directory traversal attempts blocked (e.g., ../../etc/passwd)"
      - "Absolute paths outside workdir rejected"
      - "Symlinks outside workdir rejected"
      - "Suspicious paths logged with warning level"
      - "Agent returns error response for rejected paths"
      - "Unit tests cover traversal attack scenarios"
    dependencies: []
    release_target: "V1"
    priority: "P1"
    estimate: "S"
    tags: ["backend", "security", "validation"]
    target_files:
      - "tools/agent_bridge/cli_wrapper.py — extend (add path validation)"
      - "tools/agent_bridge/tests/test_path_validation.py — create new"
    reuse_notes: "Use os.path.realpath() and os.path.commonpath() for validation."

  - id: "TASK-046"
    feature_id: "FEAT-024"
    epic_id: "EPIC-009"
    title: "Add input validation and sanitization for task dispatch"
    description: "Add validation and sanitization for task content in dispatch endpoints. Limit task content length (e.g., 10,000 chars). Sanitize special characters that could cause command injection. Add validation for agent_id format (alphanumeric + hyphens only). Rate limit excessively long or complex inputs."
    acceptance_criteria:
      - "Task content length limited to 10,000 characters"
      - "Special characters sanitized or validated (no shell metacharacters in agent_id)"
      - "agent_id format validated (alphanumeric + hyphens, max 64 chars)"
      - "Validation errors return 400 Bad Request with clear messages"
      - "Sanitization does not break legitimate use cases"
      - "Unit tests cover injection attempt scenarios"
    dependencies: []
    release_target: "V1"
    priority: "P1"
    estimate: "S"
    tags: ["backend", "security", "validation"]
    target_files:
      - "apps/api/vibeforge_api/models/requests.py — extend (add validators to DispatchTaskRequest)"
      - "apps/api/vibeforge_api/routers/control.py — extend (input validation)"
      - "apps/api/tests/test_input_validation.py — create new"
    reuse_notes: "Use Pydantic validators (field_validator, model_validator)."

  - id: "TASK-047"
    feature_id: "FEAT-025"
    epic_id: "EPIC-009"
    title: "Implement rate limiting for dispatch endpoints"
    description: "Add rate limiting to prevent abuse of dispatch endpoints. Limit dispatches per agent to 10 per minute. Limit total dispatches per IP to 50 per minute. Return 429 Too Many Requests when limits exceeded. Add configurable rate limits via environment variables."
    acceptance_criteria:
      - "Rate limit middleware on POST /control/agents/{agent_id}/dispatch"
      - "Per-agent limit: 10 dispatches/minute"
      - "Per-IP limit: 50 dispatches/minute (for multi-agent scenarios)"
      - "429 status code returned when limit exceeded"
      - "Rate limits configurable via environment variables"
      - "Rate limit headers included in responses (X-RateLimit-*)"
      - "Integration tests verify rate limiting behavior"
    dependencies: []
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "security", "rate-limiting"]
    target_files:
      - "apps/api/vibeforge_api/middleware/rate_limiter.py — create new"
      - "apps/api/vibeforge_api/main.py — extend (add rate limit middleware)"
      - "apps/api/tests/test_rate_limiting.py — create new"
    reuse_notes: "Use slowapi library (FastAPI-compatible) or custom sliding window implementation."

  - id: "TASK-048"
    feature_id: "FEAT-025"
    epic_id: "EPIC-009"
    title: "Add cost tracking and limits per session/user"
    description: "Track Claude API costs per control session. Add configurable cost limits (daily/session). Warn when approaching limits (e.g., 80% of daily limit). Block dispatches when limit exceeded. Add cost limit configuration via environment variables or config file."
    acceptance_criteria:
      - "Cost tracking per control session (sum of all agent costs)"
      - "Daily cost limit configurable (default: $10)"
      - "Session cost limit configurable (default: $5)"
      - "Warning event emitted at 80% of limit"
      - "Dispatch blocked with 402 Payment Required when limit exceeded"
      - "Cost limit status visible in control context API"
      - "Limits reset daily at midnight UTC"
    dependencies: []
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "cost-control"]
    target_files:
      - "apps/api/vibeforge_api/core/cost_tracker.py — create new"
      - "apps/api/vibeforge_api/routers/control.py — extend (check limits before dispatch)"
      - "apps/api/vibeforge_api/models/responses.py — extend (add cost limit fields to context)"
      - "apps/api/tests/test_cost_limits.py — create new"
    reuse_notes: "Integrate with existing event log cost tracking. Use scheduled job for daily reset."

  - id: "TASK-049"
    feature_id: "FEAT-026"
    epic_id: "EPIC-009"
    title: "Add audit logging for security events"
    description: "Add structured audit logging for security-relevant events: authentication attempts (success/failure), agent registrations/disconnections, task dispatches, cost limit violations, path validation failures. Log to dedicated audit.log file with rotation. Include timestamp, event type, agent_id, IP address, result."
    acceptance_criteria:
      - "Audit logger configured with dedicated log file (logs/audit.log)"
      - "Authentication events logged (token validation success/failure)"
      - "Agent lifecycle events logged (register, disconnect, timeout)"
      - "Task dispatch events logged (agent_id, task preview, cost)"
      - "Security violations logged (path traversal, rate limit exceeded, cost limit)"
      - "Log rotation enabled (max 100MB, keep 10 files)"
      - "Structured format (JSON lines) for easy parsing"
      - "Log level configurable via environment variable"
    dependencies: []
    release_target: "V1"
    priority: "P1"
    estimate: "S"
    tags: ["backend", "security", "logging"]
    target_files:
      - "apps/api/vibeforge_api/core/audit_logger.py — create new"
      - "apps/api/vibeforge_api/routers/agent_bridge.py — extend (log auth + lifecycle events)"
      - "apps/api/vibeforge_api/routers/control.py — extend (log dispatch events)"
      - "apps/api/vibeforge_api/middleware/rate_limiter.py — extend (log violations)"
      - "tools/agent_bridge/cli_wrapper.py — extend (log path validation failures)"
    reuse_notes: "Use Python's logging.handlers.RotatingFileHandler. JSON format via logging.Formatter."

  - id: "TASK-050"
    feature_id: "FEAT-026"
    epic_id: "EPIC-009"
    title: "Add security documentation and best practices guide"
    description: "Create comprehensive security documentation covering: token generation, TLS setup, firewall configuration, workdir isolation, cost limits, rate limits, audit log monitoring. Include security checklist for production deployments. Add threat model documentation."
    acceptance_criteria:
      - "docs/SECURITY.md created with comprehensive security guide"
      - "Token generation instructions (how to create secure tokens)"
      - "TLS/WSS setup guide (self-signed for dev, Let's Encrypt for prod)"
      - "Firewall configuration examples (Windows + Linux)"
      - "Workdir isolation best practices"
      - "Cost and rate limit configuration examples"
      - "Audit log monitoring recommendations"
      - "Production deployment security checklist"
      - "Threat model documented (what attacks are mitigated)"
    dependencies: ["TASK-043", "TASK-044", "TASK-045", "TASK-046", "TASK-047", "TASK-048", "TASK-049"]
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["documentation", "security"]
    target_files:
      - "docs/SECURITY.md — create new"
      - "docs/CONTROL_PANEL_GUIDE.md — extend (add security section reference)"
      - "README.md — extend (add security notice)"
    reuse_notes: "Aggregate all security features into one guide."

  # ──────────────────────────────────────────────
  # EPIC-007: Multi-Agent Real Orchestration (V1)
  # ──────────────────────────────────────────────

  - id: "TASK-035"
    feature_id: "FEAT-019"
    epic_id: "EPIC-007"
    title: "Implement delegation chain dispatch for remote agents"
    description: "Extend the dispatch system so that when a remote agent's response includes a delegation request (delegation: true in content), the TickEngine routes the delegated subtask to the next agent in the flow graph, following the existing graph-gated routing rules."
    acceptance_criteria:
      - "Remote agent responses with delegation flag are detected"
      - "Delegated subtasks routed through flow graph edges"
      - "Multi-hop delegation works (agent A → agent B → agent C)"
      - "Results flow back up the delegation chain"
      - "TASK_DISPATCHED events emitted for each delegation hop"
    dependencies: ["TASK-024", "TASK-025"]
    release_target: "V1"
    priority: "P1"
    estimate: "L"
    tags: ["backend", "orchestration"]
    target_files:
      - "orchestration/coordinator/tick_engine.py — extend (delegation routing for remote agents)"
    reuse_notes: "Extend existing delegation chain tracking in TickEngine. Reuse simulation_delegation_tracking."

  - id: "TASK-036"
    feature_id: "FEAT-019"
    epic_id: "EPIC-007"
    title: "Add tests for delegation chain dispatch with remote agents"
    description: "Write tests verifying delegation chains work with remote agents: single delegation, multi-hop, result propagation, and graph validation."
    acceptance_criteria:
      - "Tests cover single-hop delegation (A delegates to B)"
      - "Tests cover multi-hop delegation (A → B → C)"
      - "Tests verify results flow back up the chain"
      - "Tests verify graph validation still enforced"
      - "All tests pass"
    dependencies: ["TASK-035"]
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "testing"]
    target_files:
      - "apps/api/tests/test_delegation_chains.py — create new"
    reuse_notes: "Follow existing test patterns."

  - id: "TASK-037"
    feature_id: "FEAT-020"
    epic_id: "EPIC-007"
    title: "Add per-subtask status tracking and chain-level aggregation"
    description: "Extend the session model and/or TickEngine to track individual subtask statuses within a delegation chain. Aggregate chain-level status (pending/in-progress/completed/failed). Add API endpoint GET /control/agents/{agent_id}/chain-status."
    acceptance_criteria:
      - "Each subtask in a chain has individual status tracking"
      - "Chain-level status aggregated from subtask statuses"
      - "GET /control/agents/{agent_id}/chain-status returns chain tree with statuses"
      - "Status updates when subtask responses arrive"
    dependencies: ["TASK-035"]
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["backend", "orchestration", "api"]
    target_files:
      - "orchestration/coordinator/tick_engine.py — extend"
      - "apps/api/vibeforge_api/routers/control.py — extend (add chain-status endpoint)"
    reuse_notes: "Extend existing delegation tracking."

  - id: "TASK-038"
    feature_id: "FEAT-020"
    epic_id: "EPIC-007"
    title: "Add chain status visualization to control UI"
    description: "Create a ChainStatusView component that displays the delegation chain as a tree/graph with per-subtask status badges. Integrate into the ControlPanel main area."
    acceptance_criteria:
      - "Delegation chain rendered as tree view"
      - "Each node shows agent name, subtask summary, and status badge"
      - "Status badges update in real time via polling or SSE"
      - "Component integrated into ControlPanel layout"
    dependencies: ["TASK-037"]
    release_target: "V1"
    priority: "P1"
    estimate: "M"
    tags: ["frontend", "ux"]
    target_files:
      - "apps/ui/src/screens/control/widgets/ChainStatusView.tsx — create new"
      - "apps/ui/src/screens/ControlPanel.tsx — extend"
    reuse_notes: "Borrow graph rendering patterns from AgentGraph.tsx."

  # ──────────────────────────────────────────────
  # EPIC-008: External Control Channels (Later)
  # ──────────────────────────────────────────────

  - id: "TASK-039"
    feature_id: "FEAT-021"
    epic_id: "EPIC-008"
    title: "Implement messaging bot service for WhatsApp/Telegram"
    description: "Create a bot service that connects to a messaging platform (WhatsApp or Telegram) and bridges commands to the VibeForge /control API. Support task dispatch via chat command and status updates pushed to user."
    acceptance_criteria:
      - "Bot connects to messaging platform (Telegram MVP due to simpler API)"
      - "User can send task dispatch via chat command (e.g., /dispatch agent-1 'Fix the login bug')"
      - "Status updates pushed to user when agent responds"
      - "Error messages for unknown commands or disconnected agents"
    dependencies: []
    release_target: "Later"
    priority: "P2"
    estimate: "L"
    tags: ["integration", "bot"]
    target_files:
      - "tools/bot_bridge/ — create new directory + service"
    reuse_notes: "New standalone service. Calls /control REST endpoints."

  - id: "TASK-040"
    feature_id: "FEAT-022"
    epic_id: "EPIC-008"
    title: "Add Docker configuration and deployment support"
    description: "Create Dockerfile and docker-compose.yml for VibeForge. Support WSS (WebSocket Secure) for remote agent connections. Add basic auth middleware. Write deployment documentation."
    acceptance_criteria:
      - "Dockerfile builds API + UI into container"
      - "docker-compose.yml orchestrates API + UI + reverse proxy"
      - "WSS support via nginx/traefik reverse proxy config"
      - "Basic auth middleware for non-local access"
      - "Deployment README with setup instructions"
    dependencies: []
    release_target: "Later"
    priority: "P2"
    estimate: "L"
    tags: ["deployment", "infrastructure"]
    target_files:
      - "Dockerfile — create new"
      - "docker-compose.yml — create new"
      - "nginx.conf — create new (or traefik config)"
    reuse_notes: "New infrastructure files. No existing Docker setup to extend."
