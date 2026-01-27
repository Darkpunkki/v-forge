---
doc_type: concept_summary
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T18-26-48.927Z_run-6475"
generated_by: "Concept Summarizer"
generated_at: "2026-01-27T20:27:00+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/inputs/idea.md"
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/latest/idea_normalized.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---

# Concept Summary

## System Intent

VibeForge is a local-first control room and simulation sandbox for agentic development. It enables a single user to register, connect to, and direct live coding agents (such as Claude Code instances) running on LAN-accessible machines, while also providing a browser-based simulation environment for safely experimenting with multi-agent orchestration patterns.

The system provides two distinct user-facing experiences: **/control** for real-time agent management and task execution, and **/simulation** for message-passing workflow modeling. A legacy /session flow (questionnaire-driven code generation) is removed as part of this pivot, with reusable infrastructure salvaged.

## Core Capabilities

- The system can register agent endpoints by name and address, perform a connect/handshake, and maintain connection status (connected/busy/idle).
- The system can dispatch tasks and commands to registered agents and support back-and-forth follow-up chat.
- The system can stream real-time outputs from agents including chat messages, tool-call events and results, and status updates.
- The system can run discrete-tick message-passing simulations across user-configured agent hierarchies.
- The system can visualize message chains, delegation flows, and simulation traces.
- The system can bridge to remote agents via a lightweight agent bridge service running alongside each Claude Code instance.

## Conceptual Workflow

1. **Register** — User opens /control and manually registers one or more agent endpoints (name + address); the system performs a handshake via the agent bridge protocol.
2. **Dispatch** — User sends a task or command to a connected agent; the system dispatches it over the control channel and streams events (chat, tool calls, status) back in real time.
3. **Interact** — User exchanges follow-up messages with the agent, monitors streaming output, and reviews final artifacts (links/paths + summary).
4. **Simulate** — Alternatively, user opens /simulation, configures agent roles/hierarchy and an initial task, runs a message-passing simulation, and visualizes the resulting message chain.

## Invariants

- The system must support exactly two user-facing experiences: /control (live agent management) and /simulation (message-passing sandbox). No other primary flows may be added without explicit decision.
- The /session flow (questionnaire → plan → execution) must be removed. Legacy /session UI screens and routes must be deleted; only reusable infrastructure (e.g., session store, event log) may be retained.
- Agent registration must be manual and explicit (name + endpoint); automatic agent discovery is excluded.
- The control channel must be LAN-friendly, support streaming, and be easy to debug.
- The system must remain runnable at every incremental refactoring step; no big-bang rewrites.
- The system is single-user, local-first; multi-user collaboration is excluded.

## Key Constraints

- Must operate as a local-first application on a single user's PC, controlling agents on LAN-reachable machines.
- Must use a streaming-capable control channel (HTTP commands + WebSocket or SSE for event streaming).
- Must keep the agent bridge protocol simple: JSON messages over WebSocket covering register, dispatch, progress, response, and heartbeat.
- Cannot introduce automatic agent discovery, remote filesystem browsing, or tool-execution simulation (beyond message passing).
- Must refactor incrementally; the app must be runnable after each change.
- Requires the existing simulation infrastructure (TickEngine, message queue, graph-gated routing, event streaming) to be preserved and extended rather than replaced.

## In-Scope Responsibilities

- /control live agent management: registration, handshake, task dispatch, follow-up chat, real-time streaming of chat + tool-call events + status updates, connection status monitoring.
- /simulation message-passing sandbox: agent/role/hierarchy configuration, discrete-tick simulation, message-chain visualization, run traces.
- Agent bridge protocol: WebSocket-based communication between VibeForge backend and remote agent bridge services.
- Agent bridge service: standalone Python script that connects to VibeForge, receives task dispatches, invokes Claude Code CLI, and streams results back.
- Session removal: delete /session UI screens and routes, gut the sessions router, retain reusable session infrastructure for /control.
- Async tick model: extend the TickEngine to dispatch to remote agents asynchronously and buffer responses across ticks.

## Out-of-Scope / Explicit Exclusions

- Multi-user collaboration or shared workspaces.
- Complex authentication/roles beyond single-user local access.
- Automatic agent discovery or mDNS/broadcast scanning.
- Remote filesystem browser or editor in the UI.
- Tool-execution simulation (only message-passing simulation is in scope).
- WhatsApp/Telegram bot integration (deferred to Later).
- Cloud deployment (deferred to Later).
- Big-bang rewrite of any subsystem.

## Primary Artifacts

- Artifact: **Agent Bridge Service** (`tools/agent_bridge/bridge.py`) — standalone Python service deployed on each remote machine alongside Claude Code.
- Artifact: **WebSocket Endpoint** (`/ws/agent-bridge`) — server-side connection manager for agent bridge sessions.
- Artifact: **/control UI** — reworked control panel with agent registration, live task dispatch, and streaming output view.
- Artifact: **/simulation UI** — existing simulation view (preserved, with minor extensions for async agent support).
- Artifact: **Agent Bridge Protocol** — JSON-over-WebSocket protocol for register, dispatch, progress, response, and heartbeat messages.

## Key Entities and Boundaries

- **Agent**: a registered endpoint representing a Claude Code instance reachable via the agent bridge. Has connection state (connected/busy/idle/disconnected), capabilities, and a response queue.
- **Agent Bridge**: a host-side service running on the same machine as Claude Code, exposing connect/handshake, task execution, and streaming events over WebSocket.
- **Control Session**: server-side state tracking connected agents, dispatched tasks, and streaming event history for /control.
- **Simulation Session**: server-side state for a configured simulation run (agent hierarchy, tick state, message queue) for /simulation.
- **TickEngine**: the discrete-tick processor that advances simulation state; extended with async dispatch for remote agents.
- **Event Stream**: real-time event delivery (SSE or WebSocket) from backend to UI for both /control and /simulation.

## Open Questions / Ambiguities

- None (all open questions from the idea phase have been resolved in normalization).
