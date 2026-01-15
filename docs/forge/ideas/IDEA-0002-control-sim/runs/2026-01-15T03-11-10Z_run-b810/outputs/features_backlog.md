---
doc_type: features
idea_id: "IDEA-0002-control-sim"
run_id: "2026-01-15T03-11-10Z_run-b810"
generated_by: "Feature Extractor"
generated_at: "2026-01-15T03:11:10.625264+00:00"
source_inputs:
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0002-control-sim/inputs/idea.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
features:
  - id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Agent roster configuration"
    outcome: "Simulation sessions maintain an agent roster with ids and display labels."
    description: "Captures agent count and per-agent identifiers, names, role labels, and model labels for the simulation session. Roles are display-only in v1 and do not affect routing."
    acceptance_criteria:
      - "Given a session, when agents are defined with ids and labels, then the system stores and returns the full roster."
      - "Given duplicate or empty agent ids, the system rejects the configuration with a clear error."
      - "The default role list (orchestrator, worker, reviewer, fixer, foreman) is available for assignment."
      - "Assigned role and model labels are stored and retrievable without affecting routing in v1."
    in_scope:
      - "Agent roster capture and validation."
    out_of_scope:
      - "Role- or model-based routing changes in v1."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "simulation", "api"]
  - id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "Communication graph configuration"
    outcome: "Sessions capture link definitions with directionality and validate them against the agent roster."
    description: "Defines directed or bidirectional links between agents and validates references against the configured roster. Surfaces validation failures with clear reasons."
    acceptance_criteria:
      - "Given a roster, when links are provided between agents, then the system stores directionality per link."
      - "Links referencing unknown agents are rejected with a reason."
      - "When link validation fails due to graph constraints, the system returns a clear validation error."
      - "Stored links are retrievable as the current communication graph."
    in_scope:
      - "Directed and bidirectional link definitions."
    out_of_scope:
      - "Changing graph validation policy unless explicitly approved."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "simulation", "api"]
  - id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Initial prompt and first agent selection"
    outcome: "Simulation start context includes a user prompt and first agent selection."
    description: "Captures the initial user prompt and the selected first agent as required start inputs for the simulation."
    acceptance_criteria:
      - "The system requires an initial prompt before starting a simulation."
      - "The system requires a first agent selection that exists in the roster."
      - "The prompt and first agent selection are stored and retrievable as session start context."
      - "Starting without required start context is rejected with a clear error."
    in_scope:
      - "Start context capture and validation."
    out_of_scope:
      - "Execution of prompts or message generation."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "simulation", "api"]
  - id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Tick advancement with per-agent activity cap"
    outcome: "Ticks advance deterministically with a per-agent activity cap."
    description: "Advancing a tick increments the tick index, processes at most one activity per agent, and produces per-tick results."
    acceptance_criteria:
      - "When a tick is advanced, the tick index increases by one and is reflected in session state."
      - "In a single tick, each agent performs at most one activity."
      - "Given identical configuration and the same tick sequence, the resulting tick outcomes are deterministic."
      - "Each tick returns a summary of activities and messages processed."
    in_scope:
      - "Tick advancement and activity caps."
    out_of_scope:
      - "Multi-step agent loops within a single tick."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["simulation", "orchestration"]
  - id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Graph-gated message validation"
    outcome: "Messages are allowed only along configured links with blocked sends recorded."
    description: "Validates messages against the configured communication graph and surfaces blocked sends with reasons."
    acceptance_criteria:
      - "When a message is sent along a configured link, it is accepted for delivery."
      - "When a message violates graph constraints, the system records a blocked event with a reason."
      - "Blocked messages do not appear as delivered messages."
      - "Validation applies consistently across ticks."
    in_scope:
      - "Graph validation and blocked handling."
    out_of_scope:
      - "Dynamic routing based on role or model labels in v1."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["simulation", "orchestration", "observability"]
  - id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Deterministic stubbed responses"
    outcome: "Simulation responses are deterministic stubs labeled as such in v1."
    description: "Generates placeholder responses without real LLM calls and marks them clearly as stubbed outputs."
    acceptance_criteria:
      - "The system produces stubbed responses without making real LLM calls."
      - "Stubbed responses are clearly labeled in message content or metadata."
      - "Given the same inputs, stubbed outputs are identical across runs."
      - "Stubbed responses appear in the message log with tick context."
    in_scope:
      - "Stub response generation and labeling."
    out_of_scope:
      - "Real LLM provider calls in v1."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["simulation", "orchestration"]
  - id: "FEAT-007"
    epic_id: "EPIC-002"
    title: "Message event emission with tick metadata"
    outcome: "Message and tick events include required metadata for downstream logging and UI."
    description: "Emits message and tick events with sender, receiver, tick index, and status metadata for observability."
    acceptance_criteria:
      - "Message events include sender, receiver, and tick index metadata."
      - "Blocked message events include a block reason and tick index metadata."
      - "Tick events include old and new tick indices."
      - "Event payloads are consistent across single-tick and multi-tick advances."
    in_scope:
      - "Event emission metadata for ticks and messages."
    out_of_scope:
      - "Event persistence and streaming (owned by EPIC-004)."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["observability", "simulation"]
  - id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Lifecycle state transitions and guardrails"
    outcome: "Simulation lifecycle controls transition state with guardrails."
    description: "Start, pause, stop, reset, and tick actions update simulation state with validation and preserve configuration on reset."
    acceptance_criteria:
      - "Start is rejected when required configuration or start context is missing."
      - "Pause is only allowed when the simulation is running; other states are rejected with a reason."
      - "Reset returns tick index to zero and preserves configuration when requested."
      - "Stop transitions to a non-running state and rejects further ticks until restarted."
    in_scope:
      - "Lifecycle control behavior and guardrails."
    out_of_scope:
      - "Rewind semantics unless explicitly approved."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["api", "simulation"]
  - id: "FEAT-009"
    epic_id: "EPIC-003"
    title: "Status and tick state exposure"
    outcome: "Current simulation status and tick state are available to the UI."
    description: "Provides a consistent snapshot of tick status, mode, and progress for the control panel."
    acceptance_criteria:
      - "The system returns the current tick index and tick status at any time."
      - "The system returns the current simulation mode and any configured tick budget or delay."
      - "Status updates reflect lifecycle actions within a short polling interval."
      - "When no simulation is configured, the system reports an idle or unconfigured state clearly."
    in_scope:
      - "Status and tick state reporting."
    out_of_scope:
      - "Long-term analytics beyond session scope."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["api", "simulation", "ui"]
  - id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Persisted simulation event log"
    outcome: "Simulation events are persisted per session with required metadata."
    description: "Stores tick and message events in a session-scoped log for later retrieval."
    acceptance_criteria:
      - "Each tick emits a persisted event record with timestamps and tick metadata."
      - "Message sent and blocked events are persisted with sender, receiver, and reason when blocked."
      - "Event records are retrievable for a session in chronological order."
      - "Event logging failures do not change simulation behavior (best effort)."
    in_scope:
      - "Persisted event log for ticks and messages."
    out_of_scope:
      - "Cross-session analytics or aggregation."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["observability", "api"]
  - id: "FEAT-011"
    epic_id: "EPIC-004"
    title: "Event streaming for control panel"
    outcome: "Control panel can stream simulation events as they occur."
    description: "Provides a real-time stream of session events with consistent metadata for UI consumption."
    acceptance_criteria:
      - "The event stream delivers new events for a session without requiring a full log reload."
      - "Streamed events include the same metadata fields as persisted events."
      - "The stream handles empty sessions without errors."
      - "Stream reconnection yields consistent event ordering."
    in_scope:
      - "Real-time event streaming."
    out_of_scope:
      - "Guaranteed delivery under all network failures."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["observability", "api", "ui"]
  - id: "FEAT-012"
    epic_id: "EPIC-005"
    title: "Agent graph visualization"
    outcome: "UI displays configured agents and links in a graph view."
    description: "Renders agent nodes and communication links based on current configuration."
    acceptance_criteria:
      - "The graph view renders all configured agents with labels."
      - "Links show directionality and reflect current configuration."
      - "The graph remains visible during simulation and after reset."
      - "An empty state is shown when no agents are configured."
    in_scope:
      - "Agent graph view."
    out_of_scope:
      - "Advanced layout customization or performance optimization."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "simulation"]
  - id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Message log view with filters"
    outcome: "UI displays message log entries with tick context and blocked status."
    description: "Shows messages in chronological order with basic filtering and blocked-message indicators."
    acceptance_criteria:
      - "Message log shows sender, receiver, tick index, timestamp, and content."
      - "Blocked messages are labeled and show the block reason when present."
      - "Users can filter the log by agent."
      - "An empty state is shown when no messages exist."
    in_scope:
      - "Message log viewing and filtering."
    out_of_scope:
      - "Full-text search or complex analytics."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "observability"]
  - id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Status and tick indicators"
    outcome: "UI surfaces current simulation status and tick index."
    description: "Displays live status and tick indicators aligned with simulation state."
    acceptance_criteria:
      - "Status indicator reflects running, paused, idle, and completed states."
      - "Tick index is visible and updates as ticks advance."
      - "Status remains visible when switching between sessions."
      - "Errors or disconnections are surfaced to the user."
    in_scope:
      - "Status and tick indicators."
    out_of_scope:
      - "Custom theming beyond a clean baseline."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "simulation"]

# Features

## EPIC-001: Simulation Session Configuration

### FEAT-001: Agent roster configuration

**Outcome:** Simulation sessions maintain an agent roster with ids and display labels.  
**Release Target:** MVP **Priority:** P0  
**Description:** Captures agent count and per-agent identifiers, names, role labels, and model labels for the simulation session. Roles are display-only in v1 and do not affect routing.

**Acceptance Criteria:**

- Given a session, when agents are defined with ids and labels, then the system stores and returns the full roster.
- Given duplicate or empty agent ids, the system rejects the configuration with a clear error.
- The default role list (orchestrator, worker, reviewer, fixer, foreman) is available for assignment.
- Assigned role and model labels are stored and retrievable without affecting routing in v1.

**In Scope:**

- Agent roster capture and validation.

**Out of Scope:**

- Role- or model-based routing changes in v1.

**Dependencies:**

- None

### FEAT-002: Communication graph configuration

**Outcome:** Sessions capture link definitions with directionality and validate them against the agent roster.  
**Release Target:** MVP **Priority:** P0  
**Description:** Defines directed or bidirectional links between agents and validates references against the configured roster. Surfaces validation failures with clear reasons.

**Acceptance Criteria:**

- Given a roster, when links are provided between agents, then the system stores directionality per link.
- Links referencing unknown agents are rejected with a reason.
- When link validation fails due to graph constraints, the system returns a clear validation error.
- Stored links are retrievable as the current communication graph.

**In Scope:**

- Directed and bidirectional link definitions.

**Out of Scope:**

- Changing graph validation policy unless explicitly approved.

**Dependencies:**

- None

### FEAT-003: Initial prompt and first agent selection

**Outcome:** Simulation start context includes a user prompt and first agent selection.  
**Release Target:** MVP **Priority:** P0  
**Description:** Captures the initial user prompt and the selected first agent as required start inputs for the simulation.

**Acceptance Criteria:**

- The system requires an initial prompt before starting a simulation.
- The system requires a first agent selection that exists in the roster.
- The prompt and first agent selection are stored and retrievable as session start context.
- Starting without required start context is rejected with a clear error.

**In Scope:**

- Start context capture and validation.

**Out of Scope:**

- Execution of prompts or message generation.

**Dependencies:**

- None

## EPIC-002: Graph-Gated Tick Progression

### FEAT-004: Tick advancement with per-agent activity cap

**Outcome:** Ticks advance deterministically with a per-agent activity cap.  
**Release Target:** MVP **Priority:** P0  
**Description:** Advancing a tick increments the tick index, processes at most one activity per agent, and produces per-tick results.

**Acceptance Criteria:**

- When a tick is advanced, the tick index increases by one and is reflected in session state.
- In a single tick, each agent performs at most one activity.
- Given identical configuration and the same tick sequence, the resulting tick outcomes are deterministic.
- Each tick returns a summary of activities and messages processed.

**In Scope:**

- Tick advancement and activity caps.

**Out of Scope:**

- Multi-step agent loops within a single tick.

**Dependencies:**

- None

### FEAT-005: Graph-gated message validation

**Outcome:** Messages are allowed only along configured links with blocked sends recorded.  
**Release Target:** MVP **Priority:** P0  
**Description:** Validates messages against the configured communication graph and surfaces blocked sends with reasons.

**Acceptance Criteria:**

- When a message is sent along a configured link, it is accepted for delivery.
- When a message violates graph constraints, the system records a blocked event with a reason.
- Blocked messages do not appear as delivered messages.
- Validation applies consistently across ticks.

**In Scope:**

- Graph validation and blocked handling.

**Out of Scope:**

- Dynamic routing based on role or model labels in v1.

**Dependencies:**

- None

### FEAT-006: Deterministic stubbed responses

**Outcome:** Simulation responses are deterministic stubs labeled as such in v1.  
**Release Target:** MVP **Priority:** P0  
**Description:** Generates placeholder responses without real LLM calls and marks them clearly as stubbed outputs.

**Acceptance Criteria:**

- The system produces stubbed responses without making real LLM calls.
- Stubbed responses are clearly labeled in message content or metadata.
- Given the same inputs, stubbed outputs are identical across runs.
- Stubbed responses appear in the message log with tick context.

**In Scope:**

- Stub response generation and labeling.

**Out of Scope:**

- Real LLM provider calls in v1.

**Dependencies:**

- None

### FEAT-007: Message event emission with tick metadata

**Outcome:** Message and tick events include required metadata for downstream logging and UI.  
**Release Target:** MVP **Priority:** P0  
**Description:** Emits message and tick events with sender, receiver, tick index, and status metadata for observability.

**Acceptance Criteria:**

- Message events include sender, receiver, and tick index metadata.
- Blocked message events include a block reason and tick index metadata.
- Tick events include old and new tick indices.
- Event payloads are consistent across single-tick and multi-tick advances.

**In Scope:**

- Event emission metadata for ticks and messages.

**Out of Scope:**

- Event persistence and streaming (owned by EPIC-004).

**Dependencies:**

- None

## EPIC-003: Simulation Lifecycle Controls

### FEAT-008: Lifecycle state transitions and guardrails

**Outcome:** Simulation lifecycle controls transition state with guardrails.  
**Release Target:** MVP **Priority:** P0  
**Description:** Start, pause, stop, reset, and tick actions update simulation state with validation and preserve configuration on reset.

**Acceptance Criteria:**

- Start is rejected when required configuration or start context is missing.
- Pause is only allowed when the simulation is running; other states are rejected with a reason.
- Reset returns tick index to zero and preserves configuration when requested.
- Stop transitions to a non-running state and rejects further ticks until restarted.

**In Scope:**

- Lifecycle control behavior and guardrails.

**Out of Scope:**

- Rewind semantics unless explicitly approved.

**Dependencies:**

- None

### FEAT-009: Status and tick state exposure

**Outcome:** Current simulation status and tick state are available to the UI.  
**Release Target:** MVP **Priority:** P0  
**Description:** Provides a consistent snapshot of tick status, mode, and progress for the control panel.

**Acceptance Criteria:**

- The system returns the current tick index and tick status at any time.
- The system returns the current simulation mode and any configured tick budget or delay.
- Status updates reflect lifecycle actions within a short polling interval.
- When no simulation is configured, the system reports an idle or unconfigured state clearly.

**In Scope:**

- Status and tick state reporting.

**Out of Scope:**

- Long-term analytics beyond session scope.

**Dependencies:**

- None

## EPIC-004: Event Logging and Streaming

### FEAT-010: Persisted simulation event log

**Outcome:** Simulation events are persisted per session with required metadata.  
**Release Target:** MVP **Priority:** P1  
**Description:** Stores tick and message events in a session-scoped log for later retrieval.

**Acceptance Criteria:**

- Each tick emits a persisted event record with timestamps and tick metadata.
- Message sent and blocked events are persisted with sender, receiver, and reason when blocked.
- Event records are retrievable for a session in chronological order.
- Event logging failures do not change simulation behavior (best effort).

**In Scope:**

- Persisted event log for ticks and messages.

**Out of Scope:**

- Cross-session analytics or aggregation.

**Dependencies:**

- None

### FEAT-011: Event streaming for control panel

**Outcome:** Control panel can stream simulation events as they occur.  
**Release Target:** MVP **Priority:** P1  
**Description:** Provides a real-time stream of session events with consistent metadata for UI consumption.

**Acceptance Criteria:**

- The event stream delivers new events for a session without requiring a full log reload.
- Streamed events include the same metadata fields as persisted events.
- The stream handles empty sessions without errors.
- Stream reconnection yields consistent event ordering.

**In Scope:**

- Real-time event streaming.

**Out of Scope:**

- Guaranteed delivery under all network failures.

**Dependencies:**

- None

## EPIC-005: Control Panel Monitoring Views

### FEAT-012: Agent graph visualization

**Outcome:** UI displays configured agents and links in a graph view.  
**Release Target:** MVP **Priority:** P1  
**Description:** Renders agent nodes and communication links based on current configuration.

**Acceptance Criteria:**

- The graph view renders all configured agents with labels.
- Links show directionality and reflect current configuration.
- The graph remains visible during simulation and after reset.
- An empty state is shown when no agents are configured.

**In Scope:**

- Agent graph view.

**Out of Scope:**

- Advanced layout customization or performance optimization.

**Dependencies:**

- None

### FEAT-013: Message log view with filters

**Outcome:** UI displays message log entries with tick context and blocked status.  
**Release Target:** MVP **Priority:** P1  
**Description:** Shows messages in chronological order with basic filtering and blocked-message indicators.

**Acceptance Criteria:**

- Message log shows sender, receiver, tick index, timestamp, and content.
- Blocked messages are labeled and show the block reason when present.
- Users can filter the log by agent.
- An empty state is shown when no messages exist.

**In Scope:**

- Message log viewing and filtering.

**Out of Scope:**

- Full-text search or complex analytics.

**Dependencies:**

- None

### FEAT-014: Status and tick indicators

**Outcome:** UI surfaces current simulation status and tick index.  
**Release Target:** MVP **Priority:** P1  
**Description:** Displays live status and tick indicators aligned with simulation state.

**Acceptance Criteria:**

- Status indicator reflects running, paused, idle, and completed states.
- Tick index is visible and updates as ticks advance.
- Status remains visible when switching between sessions.
- Errors or disconnections are surfaced to the user.

**In Scope:**

- Status and tick indicators.

**Out of Scope:**

- Custom theming beyond a clean baseline.

**Dependencies:**

- None
