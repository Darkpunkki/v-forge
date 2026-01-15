---
doc_type: concept_summary
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T02-37-26Z_run-039b"
generated_by: "Concept Summarizer"
generated_at: "2026-01-15T02:37:26.834364+00:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/idea_normalized.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---

# Concept Summary

## System Intent

The system enables internal developers to run a controlled multi-agent simulation that makes configuration and message exchange visible and stepwise for demos, learning, and debugging. It provides a clear, tick-by-tick view of agent interactions so behavior can be observed rather than inferred.

It delivers deterministic, stubbed interactions in v1 with explicit controls and a visual graph of agents and links, avoiding real LLM calls or persistent storage until the flow is validated.

## Core Capabilities

- The system can configure multiple agents with id, name, role label, and model label.
- The system can configure directed or bidirectional communication links between agents.
- The system can start a simulation with an initial user prompt and a user-selected first agent.
- The system can advance the simulation in discrete ticks and record resulting messages.
- The system can render a message log, graph view, and current status/tick.
- The system can provide controls for start, tick, pause, stop, reset.
- The system can generate deterministic, stubbed responses in v1.
- The system can record blocked sends as system message log entries.

## Conceptual Workflow

1. Users define agents and their communication links.
2. Users select the first agent, provide an initial prompt, and start the simulation.
3. On each tick, the system processes exactly one queued event (send or response) in FIFO order; each agent performs at most one activity per tick and messages are recorded.
4. The system updates status/tick and displays the graph and message log.
5. Users pause, stop, reset (preserving configuration), or rewind if in scope.

## Invariants

- The system must cap processing to one activity per agent per tick.
- The system must process exactly one queued event per tick in FIFO order in v1.
- The system must label stubbed content clearly in v1 outputs.
- The system must keep session state in memory for v1.
- The system must preserve configuration on reset.
- The system must clear message log entries and reset tick index to 0 on reset.
- The system must log blocked sends as system events and message log entries.
- The system must not use real LLM calls in v1.
- The system must not change routing logic based on role or model labels in v1.
- The system must surface current status and tick number to the UI.
- The system must allow bidirectional links and cycles; only existing edges permit sends.

## Key Constraints

- Must extend the existing /control backend and UI without breaking current flows.
- Must remain testable and deterministic when desired.
- Requires stubbed responses in v1 until validated.
- Requires a modern, clean UI with no tight graph visualization specifics.

## In-Scope Responsibilities

- Provide agent and link configuration for the simulation.
- Maintain a simulation session with status, tick, and message log.
- Enforce the configured communication graph when sending messages.
- Display the graph and the message log alongside controls.
- Offer a default role list: orchestrator, worker, reviewer, fixer, foreman.
- Record blocked sends as system events in the message log.
- Process tick events in FIFO order with a single event per tick in v1.

## Out-of-Scope / Explicit Exclusions

- Optimization for large agent counts or performance at scale.
- Complex autonomy beyond a controlled demo workflow.
- Routing logic changes based on role or model labels in v1.
- Multi-user authentication if the app is currently single-user/local.
- Real LLM calls in v1 (only after stubbed flow is validated).
- Rewind behavior in v1.

## Primary Artifacts

- Artifact: Message log entries — record timestamp, from, to, content, and tick index (stub-marked in v1), including blocked system entries.
- Artifact: Simulation status — configured/running/paused/completed with current tick.
- Artifact: Agent graph view — visual representation of agents and links.

## Key Entities and Boundaries

- Session: In-memory state containing agents, links, message log, status, and current tick.
- Agent: Identified by id and name with role/model labels for display only in v1.
- Link: Directed or bidirectional connection that governs allowed communication.
- Message: Entry with timestamp, sender, receiver, content, and tick index.
- Tick: Discrete simulation step where each agent can perform at most one activity.

## Open Questions / Ambiguities

- None.
