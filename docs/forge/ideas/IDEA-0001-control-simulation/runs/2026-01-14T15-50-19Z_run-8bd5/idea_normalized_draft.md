---
doc_type: idea_normalized
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T15-50-19Z_run-8bd5"
generated_by: "Idea Normalizer"
generated_at: "2026-01-14T15:50:19Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs: []
status: "Draft"
---

# Idea (Normalized)

## Summary

A /control simulation view for internal developers to configure multi-agent messaging, define directed links, and step through a manual, ticked exchange with clear message logs and execution order, starting with deterministic stubs and a path to real OpenAI responses.

## Goals

- Must allow configuring agents (count, name/id, role, model label) before simulation start.
- Must allow defining directed links so specific agents can message specific peers.
- Must allow starting and stopping a simulation and advancing it one tick at a time.
- Must display message history with agent metadata and indicate execution order or active agent per tick.
- Should provide default model options and a path from deterministic stubs to real OpenAI responses.

## Target Users

- Internal developers.

## Primary Use Cases

- Configure agents and links, select a first agent, and start a simulation from an initial prompt.
- Step through ticks to observe message flow, active agent ordering, and metadata in the log.
- Stop a simulation to avoid runaway activity or cost.

## Inputs

- Agent configuration: count, name/id, role, model label.
- Directed communication links between agents.
- First-agent selection.
- Initial prompt.
- Run controls: start, stop, tick (full round).

## Outputs

- Message log entries with timestamp, tick index, from/to agent ids, content, and agent metadata (role, name, model).
- Visual graph of agents and links.
- Simulation status, current tick, and active agent/execution order indicator.

## Conceptual Workflow

1. User configures agents and directed links, selects the first agent, and provides an initial prompt.
2. User starts the simulation.
3. Each tick advances a full round where all agents take one step if needed.
4. UI updates the graph and message log; user can stop at any time.

## Core Capabilities

- The system can store agent metadata and display it alongside messages.
- The system can restrict messaging to configured directed links.
- The system can execute a manual, tick-based simulation with start/stop controls.
- The system can surface execution order or active agent per tick.
- The system can switch between deterministic stubs and real OpenAI responses (MVP path).

## Constraints

- Session state must be in-memory only.
- Manual ticking is the default to prevent runaway API usage.
- No hard limits on agent count; all configuration must be set before start.
- Must integrate into the existing /control view.

## Preferences

- UI should favor clarity and simplicity.
- Provide basic default model choices for MVP.
- Keep configuration simple and manually controlled.

## Out-of-Scope / Exclusions

- Performance optimization for large agent counts.
- Complex autonomy or role-driven routing changes.
- Persistence across refreshes or exports.
- Multi-user authentication.

## Terminology

- Tick: a full round where all agents advance one step if needed.
- Directed link: an allowed message path from one agent to another.
- Simulation session: the in-memory state for agents, links, and messages.

## Open Questions / Ambiguities

- Which OpenAI model names should be offered as defaults for the MVP?
- Should any auto-run mode exist beyond manual ticking, and if so what max-step cap?
