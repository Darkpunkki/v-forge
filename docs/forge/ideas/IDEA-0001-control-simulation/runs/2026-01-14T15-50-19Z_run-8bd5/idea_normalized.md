---
doc_type: idea_normalized
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T15-50-19Z_run-8bd5"
generated_by: "Idea Normalizer"
generated_at: "2026-01-14T15:54:38Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/normalizer_answers.md"
status: "Draft"
---

# Idea (Normalized)

## Summary

A /control simulation view for internal developers to configure multi-agent messaging, define directed links, and step through a manual or slowed autorun exchange with clear message logs and execution order, starting with deterministic stubs and a path to real OpenAI responses.

## Goals

- Must allow configuring agents (count, name/id, role, model label) before simulation start.
- Must allow defining directed links so specific agents can message specific peers.
- Must allow starting and stopping a simulation and advancing it one tick at a time.
- Should allow a slowed autorun mode with a user-defined max API request cap.
- Must display message history with agent metadata and indicate execution order or active agent per tick.
- Should provide default model options and a path from deterministic stubs to real OpenAI responses.

## Target Users

- Internal developers.

## Primary Use Cases

- Configure agents and links, select a first agent, and start a simulation from an initial prompt.
- Step through ticks to observe message flow, active agent ordering, and metadata in the log.
- Run a slowed autorun for readability while enforcing a max API request cap.
- Stop a simulation to avoid runaway activity or cost.

## Inputs

- Agent configuration: count, name/id, role, model label.
- Directed communication links between agents.
- First-agent selection.
- Initial prompt.
- Run controls: start, stop, tick (full round), optional autorun with speed and max API request cap.
- Default model selection (MVP: gpt-4o-mini).

## Outputs

- Message log entries with timestamp, tick index, from/to agent ids, content, and agent metadata (role, name, model).
- Visual graph of agents and links.
- Simulation status, current tick, and active agent/execution order indicator.
- Autorun state (running/paused) and remaining request budget indicator (if enabled).

## Conceptual Workflow

1. User configures agents and directed links, selects the first agent, and provides an initial prompt.
2. User starts the simulation.
3. Each tick advances a full round where all agents take one step if needed, or autorun advances with a readable pace.
4. UI updates the graph and message log; user can stop at any time.

## Core Capabilities

- The system can store agent metadata and display it alongside messages.
- The system can restrict messaging to configured directed links.
- The system can execute a manual, tick-based simulation with start/stop controls.
- The system can offer a slowed autorun with a user-defined max request cap.
- The system can surface execution order or active agent per tick.
- The system can switch between deterministic stubs and real OpenAI responses (MVP path).

## Constraints

- Session state must be in-memory only.
- Manual ticking is the default to prevent runaway API usage.
- Autorun (if enabled) must be paced for readability and capped by a user-set max request count.
- No hard limits on agent count; all configuration must be set before start.
- Must integrate into the existing /control view.

## Preferences

- UI should favor clarity and simplicity.
- Provide basic default model choices for MVP (gpt-4o-mini).
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
- Autorun: automatic advancement of ticks with a readable delay and a max request cap.

## Open Questions / Ambiguities

- None.
