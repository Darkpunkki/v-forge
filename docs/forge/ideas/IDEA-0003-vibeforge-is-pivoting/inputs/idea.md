---
doc_type: idea
idea_id: "IDEA-0003-vibeforge-is-pivoting-into-a-browser-based-contr"
generated_by: "Imagine (Idea Intake)"
generated_at: "2026-01-27T18:08:48.4418060+02:00"
run_id: "2026-01-27T15-40-24.315Z_run-1f99"
source:
  - "user_input (initial idea text)"
qa:
  questions: "inputs/imagine_questions.md"
  answers: "inputs/imagine_answers.md (appended)"
status: "Draft"
---

# Idea

## One-liner

A local-first control room to manage live coding agents plus a simulation sandbox for multi-agent orchestration.

## Problem / Motivation

- Coordinating multiple live agents requires a single UI to connect, monitor, and direct them.
- Orchestration patterns are risky or expensive to test live; a simulation environment enables safe experimentation.

## Target Users

- Primary: an individual user operating a local-first setup to control multiple agents.
- Secondary (later): other developers or teams who want the same control-room + simulator experience.

## Goals

- /control: manual registration of agent endpoints, connect/handshake, send tasks or commands, follow-up chat, stream outputs (chat + tool calls/results), and show status (connected/busy/idle + last activity).
- /simulation: UI-driven setup of agents/roles, hierarchy, and initial task; run message-passing simulation; visualize message chains.
- Remove /session UI/routes and migrate any reusable parts into the new architecture.

## Non-Goals

- Multi-user collaboration or shared workspaces.
- Complex auth/roles beyond single-user local.
- Automatic agent discovery.
- Remote filesystem browser/editor in the UI.
- Tool-execution simulation beyond message passing.
- Big-bang rewrite; refactor incrementally.

## Constraints

- Local-first, single-user MVP.
- Control channel must be LAN-friendly, easy to debug, and support streaming (HTTP commands + WebSocket or SSE stream).
- Keep the app runnable while aggressively deleting /session surface.

## Inputs

- /control: manual agent registration (name + endpoint), task/command text, follow-up messages, and optional settings.
- /simulation: UI-driven agent list + roles, hierarchy/edges, initial task, and optional per-agent system prompts.

## Outputs

- /control: streaming chat messages, tool-call events and results, status updates, optional stdout/stderr logs if available; final artifacts as links/paths + summary.
- /simulation: message-chain visualization and run trace.

## High-level Workflow

1. User opens /control or /simulation.
2. /control: register agent endpoint; app performs handshake via the agent bridge; send task; stream events; exchange follow-ups; monitor status.
3. /simulation: configure agents/hierarchy and initial task; run; visualize message chain and outputs.
4. User iterates on tasks or scenarios.

## Success Criteria

- Control demo: from the PC, connect to a laptop agent and complete a real task (read file X, modify file Y, run verification, commit), with streamed chat + tool events and interactive follow-ups.
- Simulation demo: configure an orchestrator and subordinate agents; run a multi-hop message chain (orchestrator -> laptop agent -> pico agent -> laptop agent -> orchestrator -> user) with clear visualization.

## Open Questions

- Choose streaming transport for MVP: WebSocket vs SSE.
- Decide when to add config import/export for agent registration and simulation scenarios.
