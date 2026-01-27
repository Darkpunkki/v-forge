---
doc_type: features
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T18-31-07.584Z_run-3db8"
generated_by: "Feature Extractor"
generated_at: "2026-01-27T20:32:00+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/inputs/idea.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
features:
  - id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Delete Session UI Screens"
    outcome: "The 6 legacy session screens are removed from the frontend codebase."
    description: "Delete the Home, Questionnaire, PlanReview, Progress, Clarification, and Result screen components and their associated imports."
    acceptance_criteria:
      - "Home.tsx, Questionnaire.tsx, PlanReview.tsx, Progress.tsx, Clarification.tsx, and Result.tsx are deleted"
      - "No import references to deleted screens remain in the codebase"
      - "The UI build succeeds (npm run build) with zero errors"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "cleanup"]
  - id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Remove Session API Routes"
    outcome: "The /sessions router endpoints are removed from the API, and /session paths return 404."
    description: "Remove or gut the sessions.py router. Delete all 9 session endpoints. Remove the router include from main.py. Retain the session store and session model."
    acceptance_criteria:
      - "All /sessions/* endpoints return 404"
      - "sessions.py router file is deleted or emptied"
      - "main.py no longer includes the sessions router"
      - "Session store and session model remain functional for /control use"
      - "Existing /control and /simulation tests still pass"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "cleanup"]
  - id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Clean Up Frontend Routing and API Client"
    outcome: "App.tsx routes only include /control and /simulation; the session API client is removed."
    description: "Update App.tsx to remove session route definitions. Set default route to /control. Remove session API client."
    acceptance_criteria:
      - "App.tsx defines only /control and /simulation routes"
      - "Default route (/) redirects to /control"
      - "Session-specific API client functions are removed"
      - "npm run build succeeds"
    dependencies: ["FEAT-001"]
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "cleanup"]
  - id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Agent Bridge Protocol Specification"
    outcome: "A formal protocol definition exists for all message types exchanged between VibeForge and agent bridges."
    description: "Define the JSON-over-WebSocket protocol with 6 message types. Implement Pydantic models."
    acceptance_criteria:
      - "Pydantic models exist for all 6 protocol message types"
      - "Message type discrimination works via 'type' field"
      - "Unit tests verify serialization/deserialization"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "protocol"]
  - id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "WebSocket Endpoint and Connection Lifecycle"
    outcome: "VibeForge accepts incoming WebSocket connections from agent bridges at /ws/agent-bridge."
    description: "Implement /ws/agent-bridge endpoint. Handle register/registered handshake, heartbeat, and disconnection."
    acceptance_criteria:
      - "WebSocket endpoint exists at /ws/agent-bridge"
      - "Register/registered handshake works"
      - "Heartbeat monitoring detects stale connections"
      - "AGENT_CONNECTED and AGENT_DISCONNECTED events are emitted"
    dependencies: ["FEAT-004"]
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "websocket"]
  - id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Remote Agent Connection Manager"
    outcome: "A centralized manager tracks connected agents, routes dispatches, and buffers responses."
    description: "Build RemoteAgentConnectionManager as singleton service. Track agent state, dispatch tasks, buffer responses."
    acceptance_criteria:
      - "Manager tracks multiple concurrent connections"
      - "Agent state transitions tracked"
      - "dispatch_task() routes to correct agent"
      - "Response buffering works"
      - "Status query methods return current state"
    dependencies: ["FEAT-005"]
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "service"]
  - id: "FEAT-007"
    epic_id: "EPIC-003"
    title: "Bridge WebSocket Client and Registration"
    outcome: "Agent bridge connects, registers, and maintains persistent WebSocket connection."
    description: "WebSocket client in bridge.py. Registration handshake. Heartbeat. Reconnection with backoff."
    acceptance_criteria:
      - "Bridge connects to configurable WebSocket URL"
      - "Registration handshake completes"
      - "Heartbeats sent at configurable interval"
      - "Reconnection with exponential backoff"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "standalone"]
  - id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Claude Code CLI Wrapper and Task Execution"
    outcome: "Bridge receives dispatch, executes via Claude Code CLI, streams results back."
    description: "Task execution flow. Invoke claude --print --output-format json. Stream progress. Send final response."
    acceptance_criteria:
      - "Dispatch messages trigger CLI invocation"
      - "Progress messages sent during execution"
      - "Final response includes content and usage"
      - "Errors reported as error responses"
    dependencies: ["FEAT-007"]
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "standalone", "cli"]
  - id: "FEAT-009"
    epic_id: "EPIC-003"
    title: "Bridge Configuration and CLI Interface"
    outcome: "Bridge runs as CLI tool with configurable arguments."
    description: "CLI interface with --url, --agent-id, --token, --workdir. Signal handling for graceful shutdown."
    acceptance_criteria:
      - "Runs with --url, --agent-id, --token, --workdir"
      - "Missing args produce clear errors"
      - "SIGINT/SIGTERM triggers graceful shutdown"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "standalone", "cli"]
  - id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Agent Registration and Connection Status Endpoints"
    outcome: "/control API allows registering and querying agents."
    description: "REST endpoints for agent registration, listing, and status queries."
    acceptance_criteria:
      - "POST /control/agents/register works"
      - "GET /control/agents lists all agents"
      - "GET /control/agents/{agent_id} returns details"
      - "Integration with RemoteAgentConnectionManager"
    dependencies: ["FEAT-006"]
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "api"]
  - id: "FEAT-011"
    epic_id: "EPIC-004"
    title: "Task Dispatch and Follow-Up Endpoints"
    outcome: "/control API sends tasks and follow-ups to agents."
    description: "REST endpoints for task dispatch, follow-up messages, and task status."
    acceptance_criteria:
      - "POST dispatch sends task to agent"
      - "POST followup sends message to active task"
      - "GET task returns current status"
      - "Events emitted for all actions"
    dependencies: ["FEAT-010"]
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "api"]
  - id: "FEAT-012"
    epic_id: "EPIC-004"
    title: "Live Agent Event Streaming"
    outcome: "Real-time agent events streamed to UI via SSE."
    description: "Extend SSE streaming with agent-specific event types."
    acceptance_criteria:
      - "SSE endpoint delivers agent events"
      - "Event types: dispatch, progress, response, tool_call, status_change"
      - "Multiple concurrent clients supported"
    dependencies: ["FEAT-010"]
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "api", "streaming"]
  - id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Async Dispatch Mode in TickEngine"
    outcome: "TickEngine dispatches to remote agents and returns immediately."
    description: "Extend TickEngine message processing for remote agents."
    acceptance_criteria:
      - "Remote agent messages dispatched via manager"
      - "Tick returns immediately with dispatched status"
      - "In-process LLM calls still work"
    dependencies: ["FEAT-006"]
    release_target: "MVP"
    priority: "P1"
    tags: ["backend", "orchestration"]
  - id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Response Buffering and Tick Integration"
    outcome: "Remote agent responses buffered and processed on subsequent ticks."
    description: "Response buffer for async agent responses. Tick checks buffer and processes."
    acceptance_criteria:
      - "Responses buffered on arrival"
      - "advance_tick() processes buffered responses"
      - "Timeout triggers failure event"
    dependencies: ["FEAT-013"]
    release_target: "MVP"
    priority: "P1"
    tags: ["backend", "orchestration"]
  - id: "FEAT-015"
    epic_id: "EPIC-006"
    title: "Agent Registration Panel"
    outcome: "UI panel for registering agents and viewing connection status."
    description: "React component with registration form and agent card list."
    acceptance_criteria:
      - "Form accepts name and endpoint URL"
      - "Registered agents display as cards with status"
      - "Status indicators use distinct colors"
      - "npm run build succeeds"
    dependencies: ["FEAT-010"]
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "ux"]
  - id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Task Dispatch and Chat Panel"
    outcome: "Chat-style panel for sending tasks and follow-up messages."
    description: "Chat panel with text input, conversation history, and thinking indicator."
    acceptance_criteria:
      - "Text input for task dispatch"
      - "Follow-up messages during agent processing"
      - "Conversation history display"
      - "Thinking indicator"
    dependencies: ["FEAT-015", "FEAT-011"]
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "ux"]
  - id: "FEAT-017"
    epic_id: "EPIC-006"
    title: "Streaming Output View"
    outcome: "Real-time display of agent events."
    description: "SSE subscription, chat/tool-call/status rendering, auto-scroll."
    acceptance_criteria:
      - "SSE subscription for agent events"
      - "Chat, tool call, and status rendering"
      - "Auto-scroll with pause button"
    dependencies: ["FEAT-012"]
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "ux", "streaming"]
  - id: "FEAT-018"
    epic_id: "EPIC-006"
    title: "Agent Connection Dashboard"
    outcome: "Overview dashboard of all registered agents."
    description: "Grid/list of agents with status, auto-refresh, selection."
    acceptance_criteria:
      - "Grid/list of all agents with status"
      - "Auto-refresh"
      - "Agent selection for task panel"
    dependencies: ["FEAT-015"]
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "ux"]
  - id: "FEAT-019"
    epic_id: "EPIC-007"
    title: "Delegation Chain Dispatch"
    outcome: "Agents delegate subtasks through the flow graph."
    description: "Dispatch system routes delegations through flow graph edges."
    acceptance_criteria:
      - "Delegation follows flow graph edges"
      - "Multi-hop delegation works"
      - "Results flow back up the chain"
    dependencies: ["FEAT-006", "FEAT-011"]
    release_target: "V1"
    priority: "P1"
    tags: ["backend", "orchestration"]
  - id: "FEAT-020"
    epic_id: "EPIC-007"
    title: "Multi-Agent Task Tracking and Status Aggregation"
    outcome: "Chain-level task tracking with aggregated status."
    description: "Per-subtask status tracking. Chain-level aggregation. API endpoint."
    acceptance_criteria:
      - "Per-subtask status tracking"
      - "Chain-level aggregation"
      - "API endpoint for chain status"
    dependencies: ["FEAT-019"]
    release_target: "V1"
    priority: "P1"
    tags: ["backend", "orchestration"]
  - id: "FEAT-021"
    epic_id: "EPIC-008"
    title: "Messaging Bot Integration"
    outcome: "Control VibeForge via WhatsApp or Telegram."
    description: "Bot service for task dispatch and status monitoring."
    acceptance_criteria:
      - "Bot connects to messaging platform"
      - "Task dispatch via chat command"
      - "Status updates sent to user"
    dependencies: []
    release_target: "Later"
    priority: "P2"
    tags: ["integration", "bot"]
  - id: "FEAT-022"
    epic_id: "EPIC-008"
    title: "Cloud Deployment Support"
    outcome: "VibeForge deployable to cloud for remote access."
    description: "Docker config, WSS support, basic auth, deployment docs."
    acceptance_criteria:
      - "Dockerfile and docker-compose.yml"
      - "WSS support"
      - "Basic authentication"
      - "Deployment documentation"
    dependencies: []
    release_target: "Later"
    priority: "P2"
    tags: ["deployment", "infrastructure"]
