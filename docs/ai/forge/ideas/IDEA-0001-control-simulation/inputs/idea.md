# Idea: /control Simulation View for Multi-Agent Messaging

## Context
This is an existing codebase with a working backend and UI. I’m extending the `/control` endpoint/view to provide a simulation environment for an LLM-agent workflow. The purpose is to demonstrate how multiple agents (LLMs via API) can be configured and can exchange messages in a controlled, step-by-step simulation.

## Goal
Add a simulation view under `/control` where a user can:
1) Configure a set of agents (count, role, model label)
2) Configure a hierarchy / communication graph (who can talk to whom)
3) Start a simulation with an initial user prompt
4) Advance the simulation one “tick” at a time and observe all agent-to-agent messages

## Must-have capabilities
- Agent configuration
  - User selects number of agents
  - User assigns each agent a role (e.g., orchestrator/foreman/worker/fixer/reviewer) and a model label
  - Role/model assignment does not need to affect behavior yet beyond being stored and displayed

- Relationship / hierarchy configuration
  - User can define directed or undirected links between agents (who can message who)
  - Links represent allowed communication paths during simulation
  - UI shows the configured graph clearly (nodes + edges)

- Simulation execution
  - Simulation starts via a button click
  - User provides an initial prompt at start
  - The system sends the initial prompt to the “first” agent (definition of first agent TBD)
  - After start, agents exchange messages with each other without further user input
  - User can see the full message stream across all agents

- Tick-based progression
  - A “tick” is one unit of simulated work (e.g., one message send, one response generation, one routing step)
  - User advances the simulation by pressing a “Tick” button (manual pacing)
  - UI updates after each tick to show new messages and state changes

## Non-goals for this iteration
- No requirement to optimize for performance at large agent counts
- No requirement for complex autonomy; this is a simulation/demo workflow
- No need for role/model assignment to change routing logic yet (can be stored/display-only)
- No need for persistent multi-user auth if the app is currently single-user/local (TBD)

## Data and state requirements
- Persist (at least in-memory for now) a simulation session containing:
  - agents (id, name, role, model label)
  - communication links/graph
  - message log (timestamp, from, to, content, tick index)
  - simulation status (configured/running/paused/completed)
  - current tick number

## UI requirements
- `/control` includes:
  - Setup panel (agents, roles/models, links)
  - Simulation panel (initial prompt, start button, tick button)
  - Message viewer (filter by agent, chronological view, possibly grouped by tick)

