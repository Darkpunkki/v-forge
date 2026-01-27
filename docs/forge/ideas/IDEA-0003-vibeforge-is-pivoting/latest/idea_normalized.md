---
doc_type: idea_normalized
idea_id: "IDEA-0003-vibeforge-is-pivoting"
run_id: "2026-01-27T16-27-30.707Z_run-de3b"
generated_by: "Idea Normalizer"
generated_at: "2026-01-27T18:32:02.4602216+02:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/inputs/idea.md"
configs:
  - "docs/forge/ideas/IDEA-0003-vibeforge-is-pivoting/inputs/normalizer_answers.md"
status: "Final"
---

# Idea (Normalized)

## Summary

VibeForge is a local-first control room and simulator for agentic development, enabling a single user to connect to live coding agents, send tasks, stream outputs, and separately simulate multi-agent message-passing workflows for safe experimentation.

## Goals

- Provide /control for manual agent registration, handshake, task execution, follow-up chat, and live streaming of outputs and status.
- Provide /simulation for UI-defined agent roles/hierarchy, message-passing runs, and message-chain visualization.
- Remove /session as a product concept while salvaging reusable parts.

## Target Users

- Primary: an individual user operating a local-first setup to control multiple agents.
- Secondary (later): other developers or teams who want the same control-room + simulator experience.

## Primary Use Cases

- Connect to a laptop-hosted agent and complete a real coding task with streamed chat + tool events and interactive follow-ups.
- Configure an orchestrator and subordinate agents, then run and visualize a multi-hop message chain.

## Inputs

- /control: agent name + endpoint, task/command text, follow-up messages, and optional settings.
- /simulation: agent list + roles, hierarchy/edges, initial task, and optional per-agent system prompts.

## Outputs

- /control: streaming chat messages, tool-call events and results, status updates, optional stdout/stderr logs, and final artifacts as links/paths + summary.
- /simulation: message-chain visualization and a run trace.

## Conceptual Workflow

1. User opens /control or /simulation.
2. /control: register agent endpoint, perform handshake via agent bridge, send tasks, stream events, and exchange follow-ups while monitoring status.
3. /simulation: configure agents/hierarchy and initial task, run simulation, visualize message chain and outputs.
4. User iterates on tasks or scenarios.

## Core Capabilities

- The system can manually register agent endpoints and perform a connect/handshake.
- The system can send tasks/commands and support basic back-and-forth chat with an agent.
- The system can stream chat messages, tool calls/results, and status updates in real time.
- The system can run message-passing simulations across configured agent hierarchies.
- The system can visualize message chains and traces for simulation runs.

## Constraints

- Local-first, single-user MVP.
- Control channel must be LAN-friendly, easy to debug, and support streaming (HTTP commands + WebSocket stream).
- Keep the app runnable while aggressively deleting /session UI/routes.

## Preferences

- Start with simple, explicit manual registration; avoid discovery for MVP.
- Use UI-driven configuration for simulation scenarios.
- Prefer adding config import/export only when it reduces pain and is needed for repeatability.

## Out-of-Scope / Exclusions

- Multi-user collaboration or shared workspaces.
- Complex auth/roles beyond single-user local.
- Automatic agent discovery.
- Remote filesystem browser/editor in the UI.
- Tool-execution simulation beyond message passing.
- Big-bang rewrite; refactor incrementally.

## Terminology

- /control: live-agent control room for registration, tasks, and streaming outputs.
- /simulation: message-passing sandbox to model orchestration and delegation.
- Agent bridge: host-side service that exposes connect/handshake, run task, and streaming events.

## Open Questions / Ambiguities

- None.
