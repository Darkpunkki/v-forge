---
doc_type: idea
idea_id: "IDEA-0001-control-simulation"
generated_by: "Imagine (Idea Intake)"
generated_at: "2026-01-14T15:44:24Z"
run_id: "2026-01-14T15-33-34Z_imagine-d6cf"
source:
  - "user_input (IDEA-0001-control-simulation)"
  - "docs/ai/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md (imported)"
qa:
  questions: "inputs/imagine_questions.md"
  answers: "inputs/imagine_answers.md (appended)"
status: "Draft"
---

# Idea

## One-liner

A /control simulation view for configuring multi-agent messaging and stepping through a safe, manual, ticked exchange.

## Problem / Motivation

- The existing app lacks a way to demonstrate multi-agent message passing in a controlled, step-by-step manner.
- A simulation view lets internal devs see roles, links, and execution order without full autonomy or runaway cost.

## Target Users

- Internal developers (primary).

## Goals

- Configure agents (count, name/id, role, model label) before starting a simulation.
- Define per-link communication rules so specific agents can message specific peers (directed links).
- Start and stop a simulation, and advance it one tick at a time.
- Display message history with agent metadata and indicate execution order or active agent per tick.
- Provide default model options and a path from deterministic stubs to real OpenAI responses.

## Non-Goals

- Optimize performance for large agent counts.
- Implement complex autonomy or role-driven routing changes.
- Persist sessions beyond in-memory state.
- Add multi-user auth or export features.

## Constraints

- In-memory session state only.
- Default to deterministic stubs; allow switching to a cheap OpenAI model for MVP (exact model list TBD).
- Guardrails against runaway API usage; manual ticking is the default.
- No hard limits on agent count; all configuration must be set before start.

## Inputs

- Agent configuration: count, name/id, role, model label.
- Communication links (directed) between agents.
- Initial prompt.
- Run controls: start, stop, and tick (full round).

## Outputs

- Message log with timestamp, tick index, from/to agent ids, content, and agent metadata (role, name, model).
- Visual graph of agents and links.
- Simulation status, current tick, and indication of the active agent/order.

## High-level Workflow

1. User opens /control and configures agents and communication links.
2. User selects the first agent, enters an initial prompt, and starts the simulation.
3. Each tick advances a full round: all agents take one step if needed.
4. UI updates the message viewer and graph; user can stop at any time.

## Success Criteria

- Simulation can be set up (assign agents, roles, models, links).
- Simulation can be started and stopped.
- LLM messages can be viewed individually.
- Simulation conveys execution order (which agent is active).

## Open Questions

- Which OpenAI model names should be offered as defaults for the MVP?
- Should any auto-run mode exist beyond manual ticking, and if so what max-step cap?
