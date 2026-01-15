---
doc_type: idea_normalized
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T02-24-56Z_run-eae4"
generated_by: "Idea Normalizer"
generated_at: "2026-01-15T02:33:28.592154+00:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
configs:
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/normalizer_answers.md"
status: "Final"
---

# Idea (Normalized)

## Summary

A control simulation view for internal dev demos where users configure multiple agents and a directed/bidirectional communication graph, start a run with an initial prompt and chosen first agent, and step through tick-by-tick message exchanges with a modern, clean UI and deterministic, stubbed responses using in-memory session state in v1.

## Goals

- Must let users configure agents (count, role label, model label).
- Must let users configure directed or bidirectional communication links.
- Must let users start the simulation with an initial prompt and a user-selected first agent.
- Must allow advancing the simulation one tick at a time and observing all agent messages.
- Must provide controls: start, tick, pause, stop, reset (reset clears state and messages, sets tick=0, and preserves configuration).

## Target Users

- Internal developers for demo and learning.

## Primary Use Cases

- Configure agents and links to demonstrate a multi-agent workflow.
- Start a simulation and step through ticks to observe message exchange.
- Pause, stop, rewind (if in scope), or reset the simulation to inspect behavior.
- View a graph of agents/links alongside a message log.

## Inputs

- Must accept agent definitions: id, name, role label, model label.
- Must accept communication links (directed or bidirectional per link).
- Must accept an initial user prompt.
- Must accept user-triggered tick events and control actions.

## Outputs

- Must produce message log entries with timestamp, from, to, content, tick index.
- Must include blocked system entries such as \"Blocked: A -> B not allowed\" when a send violates the graph.
- Must label stubbed content clearly in v1 outputs.
- Must surface simulation status (configured, running, paused, completed) and current tick.
- Must render a visual graph of agents and links.
- Should display any agent actions that occur during a tick.

## Conceptual Workflow

1. User configures agents and links.
2. User selects the first agent, enters an initial prompt, and starts the simulation.
3. On each tick, the system processes exactly one queued event (send or response) in FIFO order; each agent performs at most one activity per tick.
4. The system appends new messages and updates status and tick number.
5. User can pause, stop, reset (preserving config), or rewind (if in scope) as needed.

## Core Capabilities

- The system can create and maintain a simulation session with agents, links, status, and message log.
- The system can enforce the configured communication graph when sending messages.
- The system can advance the simulation in discrete ticks and record resulting messages.
- The system can display a graph view and message log for the session.
- The system can generate deterministic, stubbed responses in v1.

## Constraints

- Must extend the existing /control backend and UI without breaking current flows.
- Must remain testable and deterministic when desired.
- Must cap processing to one activity per agent per tick.
- Must process exactly one queued event per tick in FIFO order in v1.
- Must use stubbed responses in v1 and label stub content clearly.
- Must keep session state in memory for v1.
- Must clear message log entries on reset and set tick=0 while preserving configuration.
- Must allow bidirectional links and cycles; only existing edges permit sends (no DAG validation in v1).

## Preferences

- Should offer a default role list: orchestrator, worker, reviewer, fixer, foreman.
- Should keep the UI modern and clean without tight graph UI specifics.
- Should use a simple deterministic stub scheme suitable for MVP/v1.
- Should follow best practices for handling sends that violate the configured graph.

## Out-of-Scope / Exclusions

- No optimization for large agent counts or performance at scale.
- No complex autonomy beyond a controlled demo workflow.
- No routing logic changes based on role or model labels in v1.
- No multi-user authentication if the app is currently single-user/local.
- No real LLM calls in v1 (only after stubbed flow is validated).
- No rewind in v1.

## Terminology

- Agent: A simulated participant defined by id, name, role label, and model label.
- Role label: A label for display only; does not affect routing in v1.
- Model label: A label for display only; does not affect routing in v1.
- Communication graph: Directed or bidirectional links that govern which agents can message each other.
- Tick: A discrete simulation step where each agent may perform at most one activity.
- Stubbed response: Deterministic placeholder content used in v1.
- Reset: Stop the simulation, clear message log/state, and set tick to 0 while preserving configuration.
- Rewind: Out of scope for v1.

## Open Questions / Ambiguities

- None.
