---
doc_type: concept_summary
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T15-57-45Z_run-14e3"
generated_by: "Concept Summarizer"
generated_at: "2026-01-14T15:57:45Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Approved"
---

# Concept Summary

## System Intent

The system enables internal developers to configure and run a controlled multi-agent messaging simulation within /control, so they can observe execution order and message flow without runaway costs.

It supports manual tick-based progression and an optional slowed autorun with a request cap, while keeping a clear path from deterministic stubs to OpenAI-backed responses.

## Core Capabilities

- The system can configure agents (count, name/id, role, model label) before a run starts.
- The system can define directed links that restrict which agents can message each other.
- The system can start, stop, and advance a simulation via tick or autorun.
- The system can log and display messages with agent metadata and execution order.
- The system can operate in deterministic stub mode and switch to OpenAI responses.

## Conceptual Workflow

1. Configure agents and directed links, choose the first agent, and provide an initial prompt.
2. Start the simulation.
3. Advance by manual ticks or slowed autorun while recording message flow and active agent order.
4. Stop the simulation at any time.

## Invariants

- The system must allow configuring agents (count, name/id, role, model label) before start.
- The system must allow configuring directed links that constrain messaging.
- The system must allow selecting a first agent and initial prompt before start.
- The system must support start/stop and tick-based progression where a tick is a full round.
- The system must expose message history with agent metadata and execution order/active agent.
- The system must support deterministic stubs and a path to OpenAI responses.

## Key Constraints

- Must keep session state in-memory only.
- Must default to manual ticking to prevent runaway API usage.
- Must pace autorun for readability and cap it by a user-set max request count.
- Must integrate into the existing /control view.
- Must avoid hard limits on agent count; all configuration is set before start.

## In-Scope Responsibilities

- Capture agent configuration, including role and model label, before starting.
- Enforce directed communication rules between agents.
- Provide run controls for start, stop, tick, and optional autorun pacing.
- Surface simulation status, current tick, and execution order cues.
- Present a readable message log with full agent metadata.

## Out-of-Scope / Explicit Exclusions

- Performance optimization for large agent counts.
- Complex autonomy or role-driven routing changes.
- Persistence across refreshes or exports.
- Multi-user authentication.

## Primary Artifacts

- Artifact: Agent configuration — roles, model labels, and first-agent selection for a run.
- Artifact: Communication graph — directed links that define allowed message paths.
- Artifact: Message log — chronological record with tick index and agent metadata.
- Artifact: Simulation run status — current tick, active agent/execution order, and autorun state.

## Key Entities and Boundaries

- Session: in-memory simulation state for a single configured run.
- Run: one execution instance with start/stop and tick progression.
- Agent: a participant with id, role, and model label.
- Link: a directed allowance for messages from one agent to another.
- Message: a single exchange with content, metadata, and tick index.
- Tick: a full round where all agents advance one step if needed.
- Autorun: automatic tick advancement with pacing and a request cap.

## Open Questions / Ambiguities

- None.
