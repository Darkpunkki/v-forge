---
doc_type: idea
idea_id: "IDEA-0002-control-sim"
generated_by: "Imagine (Idea Intake)"
generated_at: "2026-01-15T04:10:22.5933008+02:00"
run_id: "2026-01-15T01-58-43.450Z_run-facf"
source:
  - "inputs/idea.md"
  - "user answers (imagine)"
qa:
  questions: "inputs/imagine_questions.md"
  answers: "inputs/imagine_answers.md (appended)"
status: "Draft"
---

# Idea

## One-liner

A /control simulation view for internal dev demos that configures multiple agents and steps through their message exchange tick by tick.

## Problem / Motivation

- Provide a clear, step-by-step demo of multi-agent workflows with visible configuration and messaging.
- Make agent-to-agent communication observable and controllable for understanding and debugging.

## Target Users

- Internal developers (demo/learning).

## Goals

- Configure a set of agents (count, role, model label).
- Configure the communication graph per link (directed or bidirectional).
- Start a simulation with an initial user prompt and a user-selected first agent.
- Advance the simulation one tick at a time and observe all agent messages.
- Provide controls: start, tick, pause, stop, reset, rewind (reset preserves configuration).

## Non-Goals

- Optimize for large agent counts or performance at scale.
- Implement complex autonomy; this is a controlled demo workflow.
- Use role or model labels to alter routing logic in v1.
- Add multi-user auth if the app is currently single-user/local.
- Real LLM calls in v1 (introduce only after stubbed flow is validated).

## Constraints

- Extend the existing /control backend and UI without breaking current flows.
- Keep the system testable and deterministic when desired.
- Tick processing caps at one activity per agent per tick to avoid loops or excessive API calls.
- v1 uses stubbed responses; outputs must clearly indicate stubbed content.
- Clean UI is a priority; confirm specific UI details at implementation time.

## Inputs

- Agent definitions: id, name, role (label-only), model label.
- Communication links (directed or bidirectional per link).
- Initial prompt to start the simulation.
- User-triggered tick events and control actions.

## Outputs

- Message log entries with timestamp, from, to, content (stub-marked in v1), tick index.
- Simulation status (configured, running, paused, completed) and current tick number.
- Visualized graph of agents and links.

## Data / State

- Simulation session containing agents, links, message log, status, and current tick.
- In-memory session state only for v1.

## High-level Workflow

1. User configures agents (roles are labels only) and links.
2. User selects the first agent, enters an initial prompt, and starts the simulation.
3. On each Tick, each agent can perform at most one activity (e.g., one message send or response).
4. The system appends new messages and updates status.
5. User can pause, stop, reset (preserving config), or rewind as needed.

## Success Criteria

- A user can configure agents and links, start a simulation, and advance ticks without errors.
- Messages appear in chronological order with clear sender/receiver attribution.
- The UI shows current tick and simulation status at all times.
- Stubbed responses are clearly labeled as stubs.

## Open Questions

- Default role list vs freeform role names (roles are label-only in v1).
- Handling of attempted sends that violate the configured graph.
- UI specifics for graph visualization and filtering to confirm during implementation.
- Rewind behavior details (e.g., step back one tick vs reset to start).
