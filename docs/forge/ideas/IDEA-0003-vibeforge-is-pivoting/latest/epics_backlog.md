---
doc_type: epics
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T18-28-17.564Z_run-684a"
generated_by: "Epic Extractor"
generated_at: "2026-01-27T20:29:00+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/inputs/idea.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
epics:
  - id: "EPIC-001"
    title: "Legacy Session Removal"
    outcome: "The /session flow (UI screens, routes, and dedicated logic) is fully removed, leaving a clean codebase for the /control and /simulation experiences."
    description: "Remove the deprecated questionnaire-driven session flow. Delete the 6 session UI screens (Home, Questionnaire, PlanReview, Progress, Clarification, Result), remove the sessions router endpoints, clean up App.tsx routes, and remove or isolate any session-only API client code. Reusable infrastructure (session store, event log, workspace manager) is retained for /control."
    in_scope:
      - "Delete session UI screens and their imports"
      - "Remove /session routes from the API"
      - "Clean up App.tsx routing to remove session paths"
      - "Remove session-only API client functions"
      - "Retain reusable infrastructure (session store, event log, artifact store)"
    out_of_scope:
      - "Modifying /simulation or /control functionality"
      - "Deleting shared infrastructure used by other subsystems"
    key_artifacts:
      - "Cleaned App.tsx with only /control and /simulation routes"
      - "Removed sessions.py router (or gutted to redirect)"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["cleanup", "frontend", "backend"]

  - id: "EPIC-002"
    title: "Agent Bridge Protocol and Connection Manager"
    outcome: "A well-defined WebSocket protocol and server-side connection manager enable VibeForge to accept, authenticate, and manage connections from remote agent bridges."
    description: "Define the JSON-over-WebSocket protocol for agent bridge communication (register, dispatch, progress, response, heartbeat). Build the server-side RemoteAgentConnectionManager that accepts incoming WebSocket connections at /ws/agent-bridge, tracks agent state (connected/busy/idle/disconnected), routes dispatched tasks, buffers responses, and emits structured events for the control UI."
    in_scope:
      - "WebSocket protocol message types (register, registered, dispatch, progress, response, heartbeat)"
      - "Server-side /ws/agent-bridge WebSocket endpoint"
      - "RemoteAgentConnectionManager with agent state tracking"
      - "Connection authentication via simple token"
      - "Response buffering for async tick integration"
      - "Structured event emission for agent connection/disconnection/status changes"
    out_of_scope:
      - "The agent bridge client (runs on remote machine; separate epic)"
      - "UI rendering of agent status (separate epic)"
      - "Complex authentication or TLS (beyond simple token)"
    key_artifacts:
      - "Agent bridge protocol specification (message types and fields)"
      - "RemoteAgentConnectionManager class"
      - "/ws/agent-bridge WebSocket endpoint"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "protocol", "websocket"]

  - id: "EPIC-003"
    title: "Agent Bridge Service"
    outcome: "A standalone Python service can be deployed alongside any Claude Code instance to connect it to VibeForge, receive tasks, execute them via Claude Code CLI, and stream results back."
    description: "Build the agent bridge as a standalone Python script (tools/agent_bridge/bridge.py) that connects to VibeForge via WebSocket, registers with an agent_id and auth token, receives task dispatches, invokes the Claude Code CLI (claude --print --output-format json), streams progress back over WebSocket, and sends the final response when execution completes. Include configuration, error handling, reconnection logic, and a simple CLI interface."
    in_scope:
      - "WebSocket client connecting to VibeForge /ws/agent-bridge"
      - "Agent registration and handshake flow"
      - "Claude Code CLI invocation and output parsing"
      - "Progress streaming back to VibeForge"
      - "Configuration via CLI args and/or config file"
      - "Graceful shutdown and reconnection"
    out_of_scope:
      - "Server-side protocol handling (separate epic)"
      - "GUI or web interface for the bridge"
      - "Support for non-Claude-Code agents (deferred)"
    key_artifacts:
      - "tools/agent_bridge/bridge.py"
      - "tools/agent_bridge/config.py"
      - "tools/agent_bridge/requirements.txt"
    dependencies:
      - "EPIC-002"
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "standalone", "cli"]

  - id: "EPIC-004"
    title: "Live Agent Control Backend"
    outcome: "The /control backend supports agent registration, task dispatch, follow-up chat, and real-time event streaming for live agents."
    description: "Rework the /control router to support live agent management. Add endpoints for manual agent registration (by name + endpoint URL), task dispatch to connected agents, follow-up message exchange, and connection status monitoring. Extend the session model with agent connection info and response queues. Integrate with the RemoteAgentConnectionManager to dispatch tasks and receive streamed results. Emit structured events for all agent interactions."
    in_scope:
      - "Agent registration endpoint (name + endpoint URL)"
      - "Task dispatch endpoint (sends task to specific connected agent)"
      - "Follow-up chat endpoint (send follow-up message to active agent)"
      - "Connection status endpoint (list agents with status)"
      - "Session model extensions for agent connection info"
      - "Integration with RemoteAgentConnectionManager"
      - "Structured event emission for agent interactions"
    out_of_scope:
      - "UI rendering (separate epic)"
      - "Simulation-specific endpoints (already exist)"
      - "Agent bridge protocol (separate epic)"
    key_artifacts:
      - "Extended /control router with live agent endpoints"
      - "Agent registration and connection status models"
    dependencies:
      - "EPIC-002"
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "api"]

  - id: "EPIC-005"
    title: "Async Dispatch Engine"
    outcome: "The TickEngine supports asynchronous dispatch to remote agents, buffering responses across ticks and processing them when available."
    description: "Extend the TickEngine to support async dispatch to remote agents in addition to in-process LLM calls. When a message is dispatched to a remote agent, the tick returns immediately with status 'dispatched'. Subsequent ticks check the response buffer. When a response arrives (via WebSocket), it is buffered and processed on the next tick. This enables real agent interactions within the existing tick-based simulation model."
    in_scope:
      - "Async dispatch mode in TickEngine (dispatch → return immediately)"
      - "Response buffer for pending remote agent responses"
      - "Agent status tracking within simulation (dispatched/thinking/responded)"
      - "Integration with RemoteAgentConnectionManager for dispatch/receive"
      - "Backward compatibility with in-process LLM calls for simulation mode"
    out_of_scope:
      - "UI changes for async status display (handled by Control UI epic)"
      - "Agent bridge protocol (separate epic)"
    key_artifacts:
      - "Extended TickEngine with async dispatch support"
      - "Response buffer data structures"
    dependencies:
      - "EPIC-002"
    release_target: "MVP"
    priority: "P1"
    tags: ["backend", "orchestration"]

  - id: "EPIC-006"
    title: "Live Agent Control UI"
    outcome: "The /control UI provides a complete control room for registering agents, dispatching tasks, viewing streaming output, and monitoring agent status."
    description: "Rework the /control UI from a simulation-configuration view to a live agent control room. Add an agent registration panel (name + endpoint + connect button), a live task dispatch panel (text input + send), a streaming output view (chat messages, tool-call events, status updates displayed in real time), and an agent connection status dashboard. Integrate with the new /control backend endpoints and the SSE/WebSocket event stream."
    in_scope:
      - "Agent registration panel with connection status indicators"
      - "Live task dispatch panel with text input"
      - "Streaming output view (chat + tool calls + status)"
      - "Follow-up chat input"
      - "Agent connection status dashboard"
      - "Integration with controlClient.ts API functions"
    out_of_scope:
      - "Simulation-specific UI (already exists)"
      - "Remote filesystem browsing"
      - "Complex agent configuration beyond name + endpoint"
    key_artifacts:
      - "Reworked /control screen components"
      - "Extended controlClient.ts with live agent API functions"
    dependencies:
      - "EPIC-001"
      - "EPIC-004"
    release_target: "MVP"
    priority: "P0"
    tags: ["frontend", "ux"]

  - id: "EPIC-007"
    title: "Multi-Agent Real Orchestration"
    outcome: "Real agents can participate in delegation chains (orchestrator → worker → reviewer) with tasks flowing through the configured agent graph."
    description: "Enable multi-agent orchestration patterns with real agents. The orchestrator agent can delegate subtasks to worker agents, which can be reviewed by reviewer agents, all through the existing agent flow graph. Extend task dispatch to support chained delegation, where one agent's output becomes another agent's input based on the configured flow graph edges."
    in_scope:
      - "Delegation chain support (agent A dispatches subtask to agent B)"
      - "Flow graph-gated routing with real agents"
      - "Multi-agent task tracking and status aggregation"
      - "End-to-end orchestration: orchestrator → worker → reviewer → orchestrator → user"
    out_of_scope:
      - "Automatic agent selection or load balancing"
      - "Agent discovery"
      - "UI for designing new orchestration patterns (use existing flow editor)"
    key_artifacts:
      - "Extended dispatch system supporting delegation chains"
      - "Multi-agent session state tracking"
    dependencies:
      - "EPIC-002"
      - "EPIC-003"
      - "EPIC-004"
      - "EPIC-005"
    release_target: "V1"
    priority: "P1"
    tags: ["backend", "orchestration"]

  - id: "EPIC-008"
    title: "External Control Channels"
    outcome: "VibeForge can be controlled from external channels (messaging bots, cloud-hosted) beyond the local browser UI."
    description: "Add support for controlling agents through external channels such as WhatsApp or Telegram bots, and enable cloud deployment for remote access. This extends the local-first architecture with optional external connectivity while maintaining the core single-user model."
    in_scope:
      - "WhatsApp/Telegram bot integration for task dispatch and status monitoring"
      - "Cloud deployment configuration and hosting support"
      - "Auto-discovery of agents on the local network"
      - "Mobile-friendly control interface"
    out_of_scope:
      - "Multi-user collaboration"
      - "Complex authentication/authorization systems"
    key_artifacts:
      - "Bot integration service"
      - "Cloud deployment configuration"
    dependencies:
      - "EPIC-004"
      - "EPIC-006"
    release_target: "Later"
    priority: "P2"
    tags: ["integration", "deployment"]

---

# Project Epics

## EPIC-001: Legacy Session Removal

**Outcome:** The /session flow (UI screens, routes, and dedicated logic) is fully removed, leaving a clean codebase for the /control and /simulation experiences.
**Release Target:** MVP **Priority:** P0
**Description:** Remove the deprecated questionnaire-driven session flow. Delete the 6 session UI screens (Home, Questionnaire, PlanReview, Progress, Clarification, Result), remove the sessions router endpoints, clean up App.tsx routes, and remove or isolate any session-only API client code. Reusable infrastructure (session store, event log, workspace manager) is retained for /control.

**In Scope:**

- Delete session UI screens and their imports
- Remove /session routes from the API
- Clean up App.tsx routing to remove session paths
- Remove session-only API client functions
- Retain reusable infrastructure (session store, event log, artifact store)

**Out of Scope:**

- Modifying /simulation or /control functionality
- Deleting shared infrastructure used by other subsystems

**Key Artifacts:**

- Cleaned App.tsx with only /control and /simulation routes
- Removed sessions.py router (or gutted to redirect)

**Dependencies:**

- None

---

## EPIC-002: Agent Bridge Protocol and Connection Manager

**Outcome:** A well-defined WebSocket protocol and server-side connection manager enable VibeForge to accept, authenticate, and manage connections from remote agent bridges.
**Release Target:** MVP **Priority:** P0

**In Scope:**

- WebSocket protocol message types (register, registered, dispatch, progress, response, heartbeat)
- Server-side /ws/agent-bridge WebSocket endpoint
- RemoteAgentConnectionManager with agent state tracking
- Connection authentication via simple token
- Response buffering for async tick integration
- Structured event emission for agent connection/disconnection/status changes

**Out of Scope:**

- The agent bridge client (runs on remote machine; separate epic)
- UI rendering of agent status (separate epic)
- Complex authentication or TLS (beyond simple token)

**Key Artifacts:**

- Agent bridge protocol specification
- RemoteAgentConnectionManager class
- /ws/agent-bridge WebSocket endpoint

**Dependencies:**

- None

---

## EPIC-003: Agent Bridge Service

**Outcome:** A standalone Python service can be deployed alongside any Claude Code instance to connect it to VibeForge, receive tasks, execute them via Claude Code CLI, and stream results back.
**Release Target:** MVP **Priority:** P0

**In Scope:**

- WebSocket client connecting to VibeForge /ws/agent-bridge
- Agent registration and handshake flow
- Claude Code CLI invocation and output parsing
- Progress streaming back to VibeForge
- Configuration via CLI args and/or config file
- Graceful shutdown and reconnection

**Out of Scope:**

- Server-side protocol handling (separate epic)
- GUI or web interface for the bridge
- Support for non-Claude-Code agents (deferred)

**Key Artifacts:**

- tools/agent_bridge/bridge.py
- tools/agent_bridge/config.py
- tools/agent_bridge/requirements.txt

**Dependencies:**

- EPIC-002

---

## EPIC-004: Live Agent Control Backend

**Outcome:** The /control backend supports agent registration, task dispatch, follow-up chat, and real-time event streaming for live agents.
**Release Target:** MVP **Priority:** P0

**In Scope:**

- Agent registration endpoint (name + endpoint URL)
- Task dispatch endpoint
- Follow-up chat endpoint
- Connection status endpoint
- Session model extensions for agent connection info
- Integration with RemoteAgentConnectionManager

**Out of Scope:**

- UI rendering (separate epic)
- Simulation-specific endpoints (already exist)

**Dependencies:**

- EPIC-002

---

## EPIC-005: Async Dispatch Engine

**Outcome:** The TickEngine supports asynchronous dispatch to remote agents, buffering responses across ticks and processing them when available.
**Release Target:** MVP **Priority:** P1

**In Scope:**

- Async dispatch mode in TickEngine
- Response buffer for pending remote agent responses
- Agent status tracking (dispatched/thinking/responded)
- Backward compatibility with in-process LLM calls

**Out of Scope:**

- UI changes for async status display
- Agent bridge protocol (separate epic)

**Dependencies:**

- EPIC-002

---

## EPIC-006: Live Agent Control UI

**Outcome:** The /control UI provides a complete control room for registering agents, dispatching tasks, viewing streaming output, and monitoring agent status.
**Release Target:** MVP **Priority:** P0

**In Scope:**

- Agent registration panel with connection status indicators
- Live task dispatch panel
- Streaming output view (chat + tool calls + status)
- Follow-up chat input
- Agent connection status dashboard

**Out of Scope:**

- Simulation-specific UI (already exists)
- Remote filesystem browsing

**Dependencies:**

- EPIC-001
- EPIC-004

---

## EPIC-007: Multi-Agent Real Orchestration

**Outcome:** Real agents can participate in delegation chains with tasks flowing through the configured agent graph.
**Release Target:** V1 **Priority:** P1

**In Scope:**

- Delegation chain support
- Flow graph-gated routing with real agents
- Multi-agent task tracking and status aggregation
- End-to-end orchestration chain

**Out of Scope:**

- Automatic agent selection
- Agent discovery

**Dependencies:**

- EPIC-002, EPIC-003, EPIC-004, EPIC-005

---

## EPIC-008: External Control Channels

**Outcome:** VibeForge can be controlled from external channels beyond the local browser UI.
**Release Target:** Later **Priority:** P2

**In Scope:**

- WhatsApp/Telegram bot integration
- Cloud deployment support
- Auto-discovery of agents
- Mobile-friendly control interface

**Out of Scope:**

- Multi-user collaboration
- Complex authentication

**Dependencies:**

- EPIC-004, EPIC-006
