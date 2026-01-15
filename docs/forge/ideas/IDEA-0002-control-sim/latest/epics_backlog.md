---
doc_type: epics
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T02-51-27.209Z_run-2755"
generated_by: "Epic Extractor"
generated_at: "2026-01-15T02:51:53.936013+00:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
epics:
  - id: "EPIC-001"
    title: "Simulation Session Configuration"
    outcome: "Users can define agents, roles, model labels, and a communication graph plus the initial prompt and first agent selection for a control simulation session."
    description: "Covers capturing and validating simulation setup inputs for a session, including the default role list and graph link definitions. Focuses on configuration completeness and correctness before a run starts. Does not include tick progression or message execution."
    in_scope:
      - "Agent definitions with id, name, role label, and model label."
      - "Default role list and role assignment rules that remain display-only in v1."
      - "Communication graph configuration with directed or bidirectional links."
      - "Initial prompt and first-agent selection as part of session setup."
    out_of_scope:
      - "Tick advancement, message execution, or stubbed response generation."
      - "Role- or model-based routing behavior in v1."
    key_artifacts:
      - "Agent configuration"
      - "Communication graph configuration"
      - "Initial prompt metadata"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "api", "simulation"]
  - id: "EPIC-002"
    title: "Graph-Gated Tick Progression"
    outcome: "Each tick advances deterministic, stubbed message exchange with graph validation and one-activity-per-agent enforcement."
    description: "Owns the tick engine and message queue behavior for simulation mode. Enforces communication graph rules, records message log entries, and labels stubbed content. Keeps deterministic ordering and caps activity per agent per tick."
    in_scope:
      - "Graph-gated message validation with explicit block reasons."
      - "Per-tick processing with one activity per agent."
      - "Deterministic stubbed response generation and labeling in v1."
      - "Message log entries with sender, receiver, timestamp, and tick index."
    out_of_scope:
      - "Real LLM calls in v1."
      - "Complex autonomy or multi-step agent loops within a tick."
    key_artifacts:
      - "Message log entries"
      - "Tick events"
      - "Blocked message records"
    dependencies:
      - "EPIC-001"
    release_target: "MVP"
    priority: "P0"
    tags: ["simulation", "orchestration", "observability"]
  - id: "EPIC-003"
    title: "Simulation Lifecycle Controls"
    outcome: "Simulation can be started, paused, stopped, and reset with status/tick state exposed to the UI, and rewind supported only if scope is confirmed."
    description: "Owns lifecycle state transitions, guardrails, and status reporting for the simulation session. Ensures configuration is preserved on reset and status/tick is always available. Covers the control surface that invokes lifecycle actions."
    in_scope:
      - "Lifecycle controls for start, tick, pause, stop, and reset."
      - "Simulation status and tick state reporting to the UI."
      - "Preservation of configuration on reset."
    out_of_scope:
      - "Rewind semantics unless explicitly confirmed in scope."
      - "Changes to non-control session phases or user-facing flows."
    key_artifacts:
      - "Simulation status snapshot"
      - "Tick state"
    dependencies:
      - "EPIC-001"
      - "EPIC-002"
    release_target: "MVP"
    priority: "P0"
    tags: ["api", "simulation", "ui"]
  - id: "EPIC-004"
    title: "Event Logging and Streaming"
    outcome: "Simulation events are persisted and streamable for inspection with consistent metadata."
    description: "Covers event log persistence for ticks and messages and exposes streams for UI consumption. Ensures metadata includes tick index, sender/receiver, and block reasons as required by inspection views."
    in_scope:
      - "Event records for ticks, messages, and blocked sends."
      - "Event streaming support for control panel inspection views."
      - "Consistent metadata fields for message log views."
    out_of_scope:
      - "Long-term analytics or cross-session dashboards."
      - "Retention guarantees beyond session-local logs."
    key_artifacts:
      - "Event log entries"
      - "Event stream payloads"
    dependencies:
      - "EPIC-002"
    release_target: "MVP"
    priority: "P1"
    tags: ["observability", "api", "simulation"]
  - id: "EPIC-005"
    title: "Control Panel Monitoring Views"
    outcome: "Users can inspect the agent graph, message log, and current simulation status in a modern, clean control panel."
    description: "Owns the monitoring and inspection experience in the control panel. Surfaces graph view, message list with tick context, and status/tick indicators. Focuses on clarity and determinism rather than performance or stylistic experimentation."
    in_scope:
      - "Graph visualization of agents and links."
      - "Message log view with tick context and blocked-message visibility."
      - "Status and tick indicators aligned with simulation state."
    out_of_scope:
      - "Heavy customization of visualization beyond a clean, modern baseline."
      - "Performance optimization for large agent counts."
    key_artifacts:
      - "Agent graph view"
      - "Message log view"
      - "Status display"
    dependencies:
      - "EPIC-003"
      - "EPIC-004"
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "observability", "simulation"]

# Project Epics

## EPIC-001: Simulation Session Configuration

**Outcome:** Users can define agents, roles, model labels, and a communication graph plus the initial prompt and first agent selection for a control simulation session.  
**Release Target:** MVP **Priority:** P0  
**Description:** Covers capturing and validating simulation setup inputs for a session, including the default role list and graph link definitions. Focuses on configuration completeness and correctness before a run starts. Does not include tick progression or message execution.

**In Scope:**

- Agent definitions with id, name, role label, and model label.
- Default role list and role assignment rules that remain display-only in v1.
- Communication graph configuration with directed or bidirectional links.
- Initial prompt and first-agent selection as part of session setup.

**Out of Scope:**

- Tick advancement, message execution, or stubbed response generation.
- Role- or model-based routing behavior in v1.

**Key Artifacts:**

- Agent configuration
- Communication graph configuration
- Initial prompt metadata

**Dependencies:**

- None

## EPIC-002: Graph-Gated Tick Progression

**Outcome:** Each tick advances deterministic, stubbed message exchange with graph validation and one-activity-per-agent enforcement.  
**Release Target:** MVP **Priority:** P0  
**Description:** Owns the tick engine and message queue behavior for simulation mode. Enforces communication graph rules, records message log entries, and labels stubbed content. Keeps deterministic ordering and caps activity per agent per tick.

**In Scope:**

- Graph-gated message validation with explicit block reasons.
- Per-tick processing with one activity per agent.
- Deterministic stubbed response generation and labeling in v1.
- Message log entries with sender, receiver, timestamp, and tick index.

**Out of Scope:**

- Real LLM calls in v1.
- Complex autonomy or multi-step agent loops within a tick.

**Key Artifacts:**

- Message log entries
- Tick events
- Blocked message records

**Dependencies:**

- EPIC-001

## EPIC-003: Simulation Lifecycle Controls

**Outcome:** Simulation can be started, paused, stopped, and reset with status/tick state exposed to the UI, and rewind supported only if scope is confirmed.  
**Release Target:** MVP **Priority:** P0  
**Description:** Owns lifecycle state transitions, guardrails, and status reporting for the simulation session. Ensures configuration is preserved on reset and status/tick is always available. Covers the control surface that invokes lifecycle actions.

**In Scope:**

- Lifecycle controls for start, tick, pause, stop, and reset.
- Simulation status and tick state reporting to the UI.
- Preservation of configuration on reset.

**Out of Scope:**

- Rewind semantics unless explicitly confirmed in scope.
- Changes to non-control session phases or user-facing flows.

**Key Artifacts:**

- Simulation status snapshot
- Tick state

**Dependencies:**

- EPIC-001
- EPIC-002

## EPIC-004: Event Logging and Streaming

**Outcome:** Simulation events are persisted and streamable for inspection with consistent metadata.  
**Release Target:** MVP **Priority:** P1  
**Description:** Covers event log persistence for ticks and messages and exposes streams for UI consumption. Ensures metadata includes tick index, sender/receiver, and block reasons as required by inspection views.

**In Scope:**

- Event records for ticks, messages, and blocked sends.
- Event streaming support for control panel inspection views.
- Consistent metadata fields for message log views.

**Out of Scope:**

- Long-term analytics or cross-session dashboards.
- Retention guarantees beyond session-local logs.

**Key Artifacts:**

- Event log entries
- Event stream payloads

**Dependencies:**

- EPIC-002

## EPIC-005: Control Panel Monitoring Views

**Outcome:** Users can inspect the agent graph, message log, and current simulation status in a modern, clean control panel.  
**Release Target:** MVP **Priority:** P1  
**Description:** Owns the monitoring and inspection experience in the control panel. Surfaces graph view, message list with tick context, and status/tick indicators. Focuses on clarity and determinism rather than performance or stylistic experimentation.

**In Scope:**

- Graph visualization of agents and links.
- Message log view with tick context and blocked-message visibility.
- Status and tick indicators aligned with simulation state.

**Out of Scope:**

- Heavy customization of visualization beyond a clean, modern baseline.
- Performance optimization for large agent counts.

**Key Artifacts:**

- Agent graph view
- Message log view
- Status display

**Dependencies:**

- EPIC-003
- EPIC-004
