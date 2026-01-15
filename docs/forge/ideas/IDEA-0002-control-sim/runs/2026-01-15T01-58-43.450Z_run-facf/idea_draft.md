---
doc_type: idea
idea_id: "IDEA-0002-control-sim"
generated_by: "Imagine (Idea Intake)"
generated_at: "2026-01-15T03:58:52.1732522+02:00"
run_id: "2026-01-15T01-58-43.450Z_run-facf"
source:
  - "inputs/idea.md"
qa:
  questions: "inputs/imagine_questions.md"
  answers: "inputs/imagine_answers.md (appended)"
status: "Draft"
---

# Idea

## One-liner

A /control simulation view to configure multiple agents and step through their message exchange tick by tick.

## Problem / Motivation

- Provide a clear, step-by-step demo of multi-agent workflows with visible configuration and messaging.
- Make agent-to-agent communication observable and controllable for understanding and debugging.

## Target Users

- TODO: Identify the primary audience (internal team, onboarding, customer-facing demo).
- Assumption (needs confirmation): Engineers and product stakeholders who need to visualize coordination.

## Goals

- Configure a set of agents (count, role, model label).
- Configure the communication graph (who can message whom).
- Start a simulation with an initial user prompt.
- Advance the simulation one tick at a time and observe all agent messages.

## Non-Goals

- Optimize for large agent counts or performance at scale.
- Implement complex autonomy; this is a controlled demo workflow.
- Use role or model labels to alter routing logic in v1.
- Add multi-user auth if the app is currently single-user/local.

## Constraints

- Extend the existing /control backend and UI without breaking current flows.
- Keep the system testable and deterministic when desired.

## Assumptions

- Assumption (needs confirmation): In-memory session storage is sufficient for v1.
- Assumption (needs confirmation): Graph visualization can be a simple node/edge view.
- Assumption (needs confirmation): Agent responses can be stubbed or deterministic in v1.

## Inputs

- Agent definitions: id, name, role, model label.
- Communication links (graph).
- Initial prompt to start the simulation.
- User-triggered tick events.

## Outputs

- Message log entries with timestamp, from, to, content, tick index.
- Simulation status (configured, running, paused, completed) and current tick number.
- Visualized graph of agents and links.

## Data / State

- Simulation session containing agents, links, message log, status, and current tick.

## High-level Workflow

1. User configures agents and links in the setup panel.
2. User enters an initial prompt and starts the simulation.
3. System routes the initial prompt to the first agent (TODO: define selection).
4. User clicks Tick; the system produces a single step and appends messages.
5. UI updates the message viewer and status after each tick.

## Success Criteria

- A user can configure agents and links, start a simulation, and advance ticks without errors.
- Messages appear in chronological order with clear sender/receiver attribution.
- The UI shows current tick and simulation status at all times.

## Open Questions

- TODO: How is the first agent selected (user pick, fixed role, or first in list)?
- TODO: Are links directed or bidirectional, and can the user choose per link?
- TODO: What is the minimum role set, and are custom roles allowed?
- TODO: What exactly does a tick represent (single message or small sequence)?
- TODO: Should agent responses be stubbed, scripted, or real LLM calls in v1?
- TODO: Are pause/reset/rewind controls required, and should reset preserve config?
- TODO: What is the required graph visualization and message filtering for v1?
- TODO: Is in-memory-only persistence acceptable, or should sessions be stored?
