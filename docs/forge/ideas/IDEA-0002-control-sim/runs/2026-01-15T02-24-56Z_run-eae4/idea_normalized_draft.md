---
doc_type: idea_normalized
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T02-24-56Z_run-eae4"
generated_by: "Idea Normalizer"
generated_at: "2026-01-15T02:24:56.312805+00:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
configs: []
status: "Draft"
---

# Idea (Normalized)

## Summary

A control simulation view for internal dev demos where a user configures multiple agents and a directed/bidirectional communication graph, starts a run with an initial prompt and chosen first agent, and steps through tick-by-tick message exchanges with controls and graph visualization, using deterministic, stubbed responses and in-memory session state in v1.

## Goals

- Must let users configure agents (count, role label, model label).
- Must let users configure directed or bidirectional communication links.
- Must let users start the simulation with an initial prompt and a user-selected first agent.
- Must allow advancing the simulation one tick at a time and observing all agent messages.
- Must provide controls: start, tick, pause, stop, reset, rewind.

## Target Users

- Internal developers for demo and learning.

## Primary Use Cases

- Configure agents and links to demonstrate a multi-agent workflow.
- Start a simulation and step through ticks to observe message exchange.
- Pause, stop, rewind, or reset the simulation to inspect behavior.
- View a graph of agents/links alongside a message log.

## Inputs

- Must accept agent definitions: id, name, role label, model label.
- Must accept communication links (directed or bidirectional per link).
- Must accept an initial user prompt.
- Must accept user-triggered tick events and control actions.

## Outputs

- Must produce message log entries with timestamp, from, to, content, tick index.
- Must label stubbed content clearly in v1 outputs.
- Must surface simulation status (configured, running, paused, completed) and current tick.
- Must render a visual graph of agents and links.

## Conceptual Workflow

1. User configures agents and links.
2. User selects the first agent, enters an initial prompt, and starts the simulation.
3. On each tick, each agent performs at most one activity (for example, one message send or response).
4. The system appends new messages and updates status and tick number.
5. User can pause, stop, reset (preserving config), or rewind as needed.

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
- Must use stubbed responses in v1 and label stub content clearly.
- Must keep session state in memory for v1.

## Preferences

- Should prioritize a clean UI.
- Should confirm detailed UI specifics during implementation.

## Out-of-Scope / Exclusions

- No optimization for large agent counts or performance at scale.
- No complex autonomy beyond a controlled demo workflow.
- No routing logic changes based on role or model labels in v1.
- No multi-user authentication if the app is currently single-user/local.
- No real LLM calls in v1 (only after stubbed flow is validated).

## Terminology

- Agent: A simulated participant defined by id, name, role label, and model label.
- Role label: A label for display only; does not affect routing in v1.
- Model label: A label for display only; does not affect routing in v1.
- Communication graph: Directed or bidirectional links that govern which agents can message each other.
- Tick: A discrete simulation step where each agent may perform at most one activity.
- Stubbed response: Deterministic placeholder content used in v1.
- Reset: Stop the simulation and clear session state while preserving configuration.
- Rewind: Move the simulation back in time; exact semantics to be defined.

## Open Questions / Ambiguities

- Should role names be freeform labels, or should the UI offer a default role list? If a default list is desired, which roles?
- How should the system handle an attempted send that violates the configured graph (block, drop, log error, warn, other)?
- What are the intended UI specifics for graph visualization and filtering (layout, filters, grouping)?
- What is the exact rewind behavior (step back one tick vs reset), and how does it affect message log and status?
- How should stubbed responses be generated and labeled to stay deterministic (fixed templates, per-agent templates, other)?
- When multiple agents can act in a tick, what is the deterministic scheduling or ordering rule?
