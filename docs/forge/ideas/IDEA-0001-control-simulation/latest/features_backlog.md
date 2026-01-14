---
doc_type: features
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T22-06-41Z_run-96a8"
generated_by: "Feature Extractor"
generated_at: "2026-01-14T22:06:41Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics.md (fallback if backlog missing)"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
features:
  - id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "Agent roster configuration"
    outcome: "A complete agent roster is captured in-session before any run starts."
    description: "The system provides a pre-run registry for agents with id/name, role, and model label. The roster is maintained in-memory for the current session and can be adjusted until the run begins. It does not infer roles or auto-discover agents."
    acceptance_criteria:
      - "Given the setup flow, when a user adds agents with id/name, role, and model label, then the roster lists each agent with those fields."
      - "The system rejects duplicate agent ids and missing required fields with a clear validation message."
      - "The roster is stored in the in-memory session and can be updated before a run starts."
      - "The system does not enforce a hard maximum agent count beyond input validation."
    in_scope:
      - "Capture agent id/name, role, and model label prior to start."
    out_of_scope:
      - "Automatic agent discovery or role inference."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "ui"]
  - id: "FEAT-002"
    epic_id: "EPIC-001"
    title: "First agent and initial prompt selection"
    outcome: "A run initialization snapshot includes the chosen first agent and initial prompt."
    description: "Before starting a run, the user selects the first agent from the roster and provides the initial prompt. The selection is validated against the roster and stored as part of the run initialization snapshot. It does not alter runtime tick semantics."
    acceptance_criteria:
      - "The first agent must be selected from the configured roster."
      - "An initial prompt is required before the start action is enabled."
      - "On start, the system stores the first agent and initial prompt in the run initialization snapshot."
      - "If the selected agent is removed or renamed, the system requires re-selection before start."
    in_scope:
      - "Select a first agent and initial prompt before start."
    out_of_scope:
      - "Changing the first agent after the run has started."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "ui"]  - id: "FEAT-003"
    epic_id: "EPIC-001"
    title: "Configuration validation and lock"
    outcome: "Runs can only start with a complete configuration, and configuration becomes immutable after start."
    description: "The system validates that required configuration elements are complete before enabling a run start. Once a run starts, the configuration snapshot is frozen to preserve deterministic behavior. It does not support editing the roster or links mid-run."
    acceptance_criteria:
      - "Start is disabled until agents, directed links, first agent, and initial prompt are valid."
      - "When a run starts, configuration fields become read-only and cannot be edited."
      - "Attempting to change configuration during a running or stopped run is blocked with a clear message."
      - "The frozen configuration remains available for inspection during the run."
    in_scope:
      - "Validate completeness before start and lock configuration after start."
    out_of_scope:
      - "Editing the configuration mid-run."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "safety"]
  - id: "FEAT-004"
    epic_id: "EPIC-002"
    title: "Directed link configuration"
    outcome: "A directed communication graph is defined for the run before start."
    description: "The system allows users to define directed links between agents to specify allowed message paths. Links are stored as a graph in the session configuration. It does not provide graph visualization or dynamic updates during a run."
    acceptance_criteria:
      - "Users can add and remove directed links between existing agents before start."
      - "Each link records a clear source agent and target agent direction."
      - "The communication graph is stored in the session configuration for the run."
      - "Changes to the roster immediately update available link options."
    in_scope:
      - "Define a directed link graph during setup."
    out_of_scope:
      - "Graph visualization or dynamic routing changes."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["graph", "config"]  - id: "FEAT-005"
    epic_id: "EPIC-002"
    title: "Link integrity validation"
    outcome: "The link graph is validated against the agent roster before a run can start."
    description: "The system validates that every link references valid agents and that the graph structure is internally consistent. Validation errors block run start until resolved. It does not add routing policies beyond the configured links."
    acceptance_criteria:
      - "The system flags links that reference missing agent ids."
      - "Duplicate links are rejected or consolidated with a single allowed edge."
      - "Run start is blocked until link validation passes."
      - "Validation errors are surfaced in the setup flow."
    in_scope:
      - "Validate link integrity against the current roster."
    out_of_scope:
      - "Advanced routing policy enforcement beyond configured links."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["graph", "safety"]
  - id: "FEAT-006"
    epic_id: "EPIC-002"
    title: "Directed link enforcement during routing"
    outcome: "Messages are only routed along configured directed links."
    description: "During runtime, the system ensures that message generation respects the pre-configured directed link graph. Disallowed routes are skipped to enforce the communication policy. It does not introduce dynamic routing changes."
    acceptance_criteria:
      - "When an agent attempts to message another agent without a configured link, no message is emitted for that route."
      - "Messages are emitted only for source and target pairs present in the directed graph."
      - "The enforcement behavior is consistent across manual ticks and autorun."
    in_scope:
      - "Enforce directed link rules during runtime message routing."
    out_of_scope:
      - "Dynamic, role-driven routing changes during a run."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["graph", "runtime"]  - id: "FEAT-007"
    epic_id: "EPIC-003"
    title: "Run lifecycle start and stop"
    outcome: "A simulation run transitions between configured, running, and stopped states in memory."
    description: "The runtime provides start and stop actions that operate on an in-memory session. Starting a run creates a run instance based on the frozen configuration; stopping ends progression without persistence. It does not resume across refreshes."
    acceptance_criteria:
      - "When configuration is valid, start transitions the session to a running state."
      - "Stop transitions the session to a stopped state and halts further ticks."
      - "Run state is maintained in-memory and resets if the session is cleared."
      - "Starting is blocked if required configuration is incomplete."
    in_scope:
      - "Provide in-memory start and stop lifecycle transitions."
    out_of_scope:
      - "Persistence or recovery across refreshes."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["runtime", "safety"]
  - id: "FEAT-008"
    epic_id: "EPIC-003"
    title: "Manual tick progression"
    outcome: "Each manual tick advances a full round of agent steps."
    description: "The system advances the simulation only when a user triggers a manual tick. Each tick represents a full round where all configured agents advance one step as needed. It does not advance automatically."
    acceptance_criteria:
      - "When running, triggering a manual tick increments the tick index by one."
      - "Each tick advances all agents through one round using the same deterministic order each tick."
      - "Manual tick actions are ignored or rejected when the run is not in a running state."
    in_scope:
      - "Manual, user-driven tick advancement."
    out_of_scope:
      - "Automatic tick advancement or background scheduling."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["runtime", "safety"]  - id: "FEAT-009"
    epic_id: "EPIC-003"
    title: "Execution order tracking"
    outcome: "The runtime tracks and exposes execution order and active agent per tick."
    description: "For each tick, the runtime records the sequence of agent activity and the currently active agent. This data is exposed in run status for UI cues and logging. It does not define visualization."
    acceptance_criteria:
      - "For every tick, the system records the ordered list of agents that acted."
      - "The active agent for the current tick is available via run status."
      - "Execution order data is accessible to the message log subsystem and UI."
    in_scope:
      - "Track and expose execution order per tick."
    out_of_scope:
      - "UI visualization of the execution order."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["runtime", "logging"]
  - id: "FEAT-010"
    epic_id: "EPIC-004"
    title: "Autorun pacing control"
    outcome: "Autorun can advance ticks at a user-defined cadence."
    description: "The system offers an optional autorun mode that advances ticks automatically at a readable pace. It uses the same tick semantics as manual mode and can be stopped by the user. It does not run in the background without user control."
    acceptance_criteria:
      - "Users can start and stop autorun from the run controls."
      - "When autorun is active, ticks advance automatically at the configured pacing interval."
      - "Autorun uses the same tick semantics as manual ticking."
      - "Autorun stops immediately when the user requests stop."
    in_scope:
      - "Optional autorun with user-controlled pacing."
    out_of_scope:
      - "Unattended background execution."
    dependencies: []
    release_target: "V1"
    priority: "P1"
    tags: ["runtime", "safety"]  - id: "FEAT-011"
    epic_id: "EPIC-004"
    title: "Request budget cap enforcement"
    outcome: "Autorun respects a user-set maximum request budget."
    description: "The system tracks a request budget for autorun to prevent runaway usage. Each generated agent response consumes budget and autorun stops when the cap is reached. It does not bypass the cap in any mode."
    acceptance_criteria:
      - "Users can set a maximum request count before starting autorun."
      - "Each generated agent response decrements the remaining budget."
      - "Autorun stops automatically when the remaining budget reaches zero."
    in_scope:
      - "Enforce a request budget while autorun is active."
    out_of_scope:
      - "Unlimited or unbounded autorun."
    dependencies: []
    release_target: "V1"
    priority: "P1"
    tags: ["runtime", "safety"]
  - id: "FEAT-012"
    epic_id: "EPIC-004"
    title: "Autorun state and budget reporting"
    outcome: "The UI can show autorun status and remaining budget."
    description: "The system exposes autorun state and remaining request budget as part of run status. It includes a reason when autorun stops due to cap. It does not persist autorun history."
    acceptance_criteria:
      - "Run status includes whether autorun is running, paused, or stopped."
      - "Remaining request budget is available while autorun is configured or running."
      - "When autorun stops due to cap, the status indicates the stop reason."
    in_scope:
      - "Expose autorun state and remaining budget in run status."
    out_of_scope:
      - "Persisting autorun history across sessions."
    dependencies: []
    release_target: "V1"
    priority: "P1"
    tags: ["runtime", "ui"]  - id: "FEAT-013"
    epic_id: "EPIC-005"
    title: "Message log capture with metadata"
    outcome: "Each message is recorded with full metadata and tick context."
    description: "The runtime records every message exchange in a chronological log. Each entry includes from/to agent ids, role, model label, tick index, and execution order cues. The log is stored in-memory for the current run."
    acceptance_criteria:
      - "Each message entry includes from agent id, to agent id, role, model label, content, and tick index."
      - "The log records execution order cues for the tick associated with the message."
      - "Message entries are appended in chronological order as ticks progress."
      - "The message log is cleared when a new run starts."
    in_scope:
      - "Capture message entries with required metadata fields."
    out_of_scope:
      - "Log export or persistence beyond the session."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["logging", "runtime"]
  - id: "FEAT-014"
    epic_id: "EPIC-005"
    title: "Message history retrieval for control view"
    outcome: "The /control view can retrieve the full message history for the current run."
    description: "The system exposes a retrievable message history for the current run to support UI display. The history is consistent with runtime ordering and includes all recorded metadata. It does not persist or export logs."
    acceptance_criteria:
      - "The message history returns entries in chronological order."
      - "Retrieved entries match the stored metadata fields used by the log."
      - "The history is available while the run is running or stopped."
      - "The history is scoped to the in-memory session and not persisted."
    in_scope:
      - "Expose message history to the control view."
    out_of_scope:
      - "Exports, analytics, or aggregation of the message log."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["logging", "ui"]  - id: "FEAT-015"
    epic_id: "EPIC-006"
    title: "Control view setup panels"
    outcome: "The /control view supports full pre-run configuration."
    description: "The /control view presents setup panels for agent roster, directed links, first agent selection, and initial prompt. It surfaces validation status so users know when they can start. It does not provide graph visualization."
    acceptance_criteria:
      - "The /control view includes controls to add and edit agents and model labels."
      - "Users can configure directed links within the same view prior to start."
      - "The first agent and initial prompt are captured in the setup flow."
      - "Validation errors are shown inline and block the start action."
    in_scope:
      - "Expose configuration UI for setup within /control."
    out_of_scope:
      - "Topology or graph visualization."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "config"]
  - id: "FEAT-016"
    epic_id: "EPIC-006"
    title: "Run controls and status cues"
    outcome: "Users can start, stop, and tick the run while seeing live status cues."
    description: "The /control view provides run controls aligned with the simulation lifecycle. It displays current tick and active agent cues as the run progresses. It does not change runtime semantics."
    acceptance_criteria:
      - "Start, stop, and manual tick controls are visible in /control."
      - "The tick control is enabled only when the run is in a running state."
      - "The current tick count and run status are visible and update after each tick."
      - "The active agent cue updates in sync with the runtime."
    in_scope:
      - "Expose run controls and status indicators in /control."
    out_of_scope:
      - "Altering runtime tick semantics from the UI."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "runtime"]  - id: "FEAT-017"
    epic_id: "EPIC-006"
    title: "Message log display"
    outcome: "The /control view renders a readable message log with metadata."
    description: "The UI renders the message log with agent metadata and tick context to support inspection of message flow. The log updates as new messages arrive. It does not provide analytics or export."
    acceptance_criteria:
      - "Each log entry shows from/to agent ids, role, model label, and tick index."
      - "New messages appear in the log in chronological order."
      - "The log remains viewable after the run stops."
      - "The log view is scoped to the current session and clears on a new run."
    in_scope:
      - "Display the message log within /control."
    out_of_scope:
      - "Message log analytics or export features."
    dependencies: []
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "logging"]
  - id: "FEAT-018"
    epic_id: "EPIC-007"
    title: "Agent topology rendering"
    outcome: "A visual topology shows agents and directed links."
    description: "The /control view renders a graph of agent nodes and directed edges based on the configured communication graph. The rendering prioritizes readability for typical agent counts. It does not modify the underlying link rules."
    acceptance_criteria:
      - "The visualization displays one node per configured agent."
      - "Directed links are shown with clear direction from source to target."
      - "The graph renders using the current pre-run configuration."
      - "The visualization is accessible within the /control view."
    in_scope:
      - "Render a graph view of agents and directed links."
    out_of_scope:
      - "High-performance layout for large agent counts."
    dependencies: []
    release_target: "V1"
    priority: "P2"
    tags: ["ui", "graph"]  - id: "FEAT-019"
    epic_id: "EPIC-007"
    title: "Active agent highlighting"
    outcome: "The graph indicates the active agent or current tick context."
    description: "The visualization highlights the active agent as reported by the runtime to help users follow execution. Highlighting updates as ticks advance. It does not introduce new runtime behavior."
    acceptance_criteria:
      - "When a tick is running, the active agent node is visually highlighted."
      - "The highlight updates on each tick according to runtime status."
      - "When the run is stopped, no active highlight is shown."
    in_scope:
      - "Highlight active agent status within the graph."
    out_of_scope:
      - "Adding runtime logic beyond existing status reporting."
    dependencies: []
    release_target: "V1"
    priority: "P2"
    tags: ["ui", "graph"]
  - id: "FEAT-020"
    epic_id: "EPIC-007"
    title: "Graph updates with configuration changes"
    outcome: "Pre-run configuration changes are reflected in the topology view."
    description: "The visualization updates immediately when agents or links change before the run starts. Once the run begins and configuration is frozen, the graph reflects the frozen snapshot. It does not support drag-and-drop editing."
    acceptance_criteria:
      - "Adding or removing agents before start updates the graph nodes."
      - "Adding or removing links before start updates the graph edges."
      - "After start, the graph remains aligned to the frozen configuration snapshot."
    in_scope:
      - "Reflect pre-run configuration changes in the graph."
    out_of_scope:
      - "Interactive graph editing via drag-and-drop."
    dependencies: []
    release_target: "V1"
    priority: "P2"
    tags: ["ui", "graph"]  - id: "FEAT-021"
    epic_id: "EPIC-008"
    title: "Deterministic stub response mode"
    outcome: "The simulation can run with deterministic stubbed responses."
    description: "The system provides a stubbed response mode that avoids network calls and yields deterministic outputs. This mode supports testing and safe manual ticks without cost. It does not change tick semantics."
    acceptance_criteria:
      - "When stub mode is enabled, no external API calls are made."
      - "Given the same inputs and configuration, stub responses are deterministic across runs."
      - "Stubbed responses are logged with the same metadata as real responses."
    in_scope:
      - "Provide deterministic stub responses for message generation."
    out_of_scope:
      - "Non-deterministic or external response generation."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["llm", "safety"]
  - id: "FEAT-022"
    epic_id: "EPIC-008"
    title: "Provider interface and mode selection"
    outcome: "A provider interface selects stub or OpenAI response generation per run."
    description: "The runtime routes message generation through a provider interface that supports stub and OpenAI modes. The selected mode is chosen before run start and applies consistently during the run. It does not support switching modes mid-run."
    acceptance_criteria:
      - "The configuration allows selecting stub or OpenAI mode before start."
      - "The selected mode is recorded in the run configuration snapshot."
      - "All message generations for the run use the selected provider mode."
      - "Mode selection is unavailable once the run has started."
    in_scope:
      - "Select and apply provider mode during run initialization."
    out_of_scope:
      - "Switching providers mid-run."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["llm", "runtime"]  - id: "FEAT-023"
    epic_id: "EPIC-008"
    title: "Model label routing for OpenAI responses"
    outcome: "OpenAI responses use the configured model label per agent."
    description: "When OpenAI mode is enabled, the provider uses each agent's model label to select the model for responses. Invalid or missing model labels are treated as configuration errors prior to start. It does not define a broader model marketplace."
    acceptance_criteria:
      - "Each agent's model label is passed to the provider for response generation."
      - "Start is blocked if any agent has an invalid or missing model label for OpenAI mode."
      - "Responses generated in OpenAI mode are logged with the model label used."
    in_scope:
      - "Use agent model labels to route OpenAI responses."
    out_of_scope:
      - "Multi-provider marketplaces or cost optimization features."
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["llm", "runtime"]

# Features

## EPIC-001: Session Setup & Agent Registry

### FEAT-001: Agent roster configuration

**Outcome:** A complete agent roster is captured in-session before any run starts.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system provides a pre-run registry for agents with id/name, role, and model label. The roster is maintained in-memory for the current session and can be adjusted until the run begins. It does not infer roles or auto-discover agents.

**Acceptance Criteria:**

- Given the setup flow, when a user adds agents with id/name, role, and model label, then the roster lists each agent with those fields.
- The system rejects duplicate agent ids and missing required fields with a clear validation message.
- The roster is stored in the in-memory session and can be updated before a run starts.
- The system does not enforce a hard maximum agent count beyond input validation.

**In Scope:**

- Capture agent id/name, role, and model label prior to start.

**Out of Scope:**

- Automatic agent discovery or role inference.

**Dependencies:**

- (none)
### FEAT-002: First agent and initial prompt selection

**Outcome:** A run initialization snapshot includes the chosen first agent and initial prompt.  
**Release Target:** MVP **Priority:** P0  
**Description:** Before starting a run, the user selects the first agent from the roster and provides the initial prompt. The selection is validated against the roster and stored as part of the run initialization snapshot. It does not alter runtime tick semantics.

**Acceptance Criteria:**

- The first agent must be selected from the configured roster.
- An initial prompt is required before the start action is enabled.
- On start, the system stores the first agent and initial prompt in the run initialization snapshot.
- If the selected agent is removed or renamed, the system requires re-selection before start.

**In Scope:**

- Select a first agent and initial prompt before start.

**Out of Scope:**

- Changing the first agent after the run has started.

**Dependencies:**

- (none)

### FEAT-003: Configuration validation and lock

**Outcome:** Runs can only start with a complete configuration, and configuration becomes immutable after start.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system validates that required configuration elements are complete before enabling a run start. Once a run starts, the configuration snapshot is frozen to preserve deterministic behavior. It does not support editing the roster or links mid-run.

**Acceptance Criteria:**

- Start is disabled until agents, directed links, first agent, and initial prompt are valid.
- When a run starts, configuration fields become read-only and cannot be edited.
- Attempting to change configuration during a running or stopped run is blocked with a clear message.
- The frozen configuration remains available for inspection during the run.

**In Scope:**

- Validate completeness before start and lock configuration after start.

**Out of Scope:**

- Editing the configuration mid-run.

**Dependencies:**

- (none)
## EPIC-002: Directed Communication Rules

### FEAT-004: Directed link configuration

**Outcome:** A directed communication graph is defined for the run before start.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system allows users to define directed links between agents to specify allowed message paths. Links are stored as a graph in the session configuration. It does not provide graph visualization or dynamic updates during a run.

**Acceptance Criteria:**

- Users can add and remove directed links between existing agents before start.
- Each link records a clear source agent and target agent direction.
- The communication graph is stored in the session configuration for the run.
- Changes to the roster immediately update available link options.

**In Scope:**

- Define a directed link graph during setup.

**Out of Scope:**

- Graph visualization or dynamic routing changes.

**Dependencies:**

- (none)

### FEAT-005: Link integrity validation

**Outcome:** The link graph is validated against the agent roster before a run can start.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system validates that every link references valid agents and that the graph structure is internally consistent. Validation errors block run start until resolved. It does not add routing policies beyond the configured links.

**Acceptance Criteria:**

- The system flags links that reference missing agent ids.
- Duplicate links are rejected or consolidated with a single allowed edge.
- Run start is blocked until link validation passes.
- Validation errors are surfaced in the setup flow.

**In Scope:**

- Validate link integrity against the current roster.

**Out of Scope:**

- Advanced routing policy enforcement beyond configured links.

**Dependencies:**

- (none)
### FEAT-006: Directed link enforcement during routing

**Outcome:** Messages are only routed along configured directed links.  
**Release Target:** MVP **Priority:** P0  
**Description:** During runtime, the system ensures that message generation respects the pre-configured directed link graph. Disallowed routes are skipped to enforce the communication policy. It does not introduce dynamic routing changes.

**Acceptance Criteria:**

- When an agent attempts to message another agent without a configured link, no message is emitted for that route.
- Messages are emitted only for source and target pairs present in the directed graph.
- The enforcement behavior is consistent across manual ticks and autorun.

**In Scope:**

- Enforce directed link rules during runtime message routing.

**Out of Scope:**

- Dynamic, role-driven routing changes during a run.

**Dependencies:**

- (none)

## EPIC-003: Manual Tick Simulation Runtime

### FEAT-007: Run lifecycle start and stop

**Outcome:** A simulation run transitions between configured, running, and stopped states in memory.  
**Release Target:** MVP **Priority:** P0  
**Description:** The runtime provides start and stop actions that operate on an in-memory session. Starting a run creates a run instance based on the frozen configuration; stopping ends progression without persistence. It does not resume across refreshes.

**Acceptance Criteria:**

- When configuration is valid, start transitions the session to a running state.
- Stop transitions the session to a stopped state and halts further ticks.
- Run state is maintained in-memory and resets if the session is cleared.
- Starting is blocked if required configuration is incomplete.

**In Scope:**

- Provide in-memory start and stop lifecycle transitions.

**Out of Scope:**

- Persistence or recovery across refreshes.

**Dependencies:**

- (none)
### FEAT-008: Manual tick progression

**Outcome:** Each manual tick advances a full round of agent steps.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system advances the simulation only when a user triggers a manual tick. Each tick represents a full round where all configured agents advance one step as needed. It does not advance automatically.

**Acceptance Criteria:**

- When running, triggering a manual tick increments the tick index by one.
- Each tick advances all agents through one round using the same deterministic order each tick.
- Manual tick actions are ignored or rejected when the run is not in a running state.

**In Scope:**

- Manual, user-driven tick advancement.

**Out of Scope:**

- Automatic tick advancement or background scheduling.

**Dependencies:**

- (none)

### FEAT-009: Execution order tracking

**Outcome:** The runtime tracks and exposes execution order and active agent per tick.  
**Release Target:** MVP **Priority:** P0  
**Description:** For each tick, the runtime records the sequence of agent activity and the currently active agent. This data is exposed in run status for UI cues and logging. It does not define visualization.

**Acceptance Criteria:**

- For every tick, the system records the ordered list of agents that acted.
- The active agent for the current tick is available via run status.
- Execution order data is accessible to the message log subsystem and UI.

**In Scope:**

- Track and expose execution order per tick.

**Out of Scope:**

- UI visualization of the execution order.

**Dependencies:**

- (none)
## EPIC-004: Autorun Pacing & Request Budget

### FEAT-010: Autorun pacing control

**Outcome:** Autorun can advance ticks at a user-defined cadence.  
**Release Target:** V1 **Priority:** P1  
**Description:** The system offers an optional autorun mode that advances ticks automatically at a readable pace. It uses the same tick semantics as manual mode and can be stopped by the user. It does not run in the background without user control.

**Acceptance Criteria:**

- Users can start and stop autorun from the run controls.
- When autorun is active, ticks advance automatically at the configured pacing interval.
- Autorun uses the same tick semantics as manual ticking.
- Autorun stops immediately when the user requests stop.

**In Scope:**

- Optional autorun with user-controlled pacing.

**Out of Scope:**

- Unattended background execution.

**Dependencies:**

- (none)

### FEAT-011: Request budget cap enforcement

**Outcome:** Autorun respects a user-set maximum request budget.  
**Release Target:** V1 **Priority:** P1  
**Description:** The system tracks a request budget for autorun to prevent runaway usage. Each generated agent response consumes budget and autorun stops when the cap is reached. It does not bypass the cap in any mode.

**Acceptance Criteria:**

- Users can set a maximum request count before starting autorun.
- Each generated agent response decrements the remaining budget.
- Autorun stops automatically when the remaining budget reaches zero.

**In Scope:**

- Enforce a request budget while autorun is active.

**Out of Scope:**

- Unlimited or unbounded autorun.

**Dependencies:**

- (none)
### FEAT-012: Autorun state and budget reporting

**Outcome:** The UI can show autorun status and remaining budget.  
**Release Target:** V1 **Priority:** P1  
**Description:** The system exposes autorun state and remaining request budget as part of run status. It includes a reason when autorun stops due to cap. It does not persist autorun history.

**Acceptance Criteria:**

- Run status includes whether autorun is running, paused, or stopped.
- Remaining request budget is available while autorun is configured or running.
- When autorun stops due to cap, the status indicates the stop reason.

**In Scope:**

- Expose autorun state and remaining budget in run status.

**Out of Scope:**

- Persisting autorun history across sessions.

**Dependencies:**

- (none)

## EPIC-005: Message Trace & Metadata Ledger

### FEAT-013: Message log capture with metadata

**Outcome:** Each message is recorded with full metadata and tick context.  
**Release Target:** MVP **Priority:** P0  
**Description:** The runtime records every message exchange in a chronological log. Each entry includes from/to agent ids, role, model label, tick index, and execution order cues. The log is stored in-memory for the current run.

**Acceptance Criteria:**

- Each message entry includes from agent id, to agent id, role, model label, content, and tick index.
- The log records execution order cues for the tick associated with the message.
- Message entries are appended in chronological order as ticks progress.
- The message log is cleared when a new run starts.

**In Scope:**

- Capture message entries with required metadata fields.

**Out of Scope:**

- Log export or persistence beyond the session.

**Dependencies:**

- (none)
### FEAT-014: Message history retrieval for control view

**Outcome:** The /control view can retrieve the full message history for the current run.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system exposes a retrievable message history for the current run to support UI display. The history is consistent with runtime ordering and includes all recorded metadata. It does not persist or export logs.

**Acceptance Criteria:**

- The message history returns entries in chronological order.
- Retrieved entries match the stored metadata fields used by the log.
- The history is available while the run is running or stopped.
- The history is scoped to the in-memory session and not persisted.

**In Scope:**

- Expose message history to the control view.

**Out of Scope:**

- Exports, analytics, or aggregation of the message log.

**Dependencies:**

- (none)

## EPIC-006: Control Room Interaction Surface

### FEAT-015: Control view setup panels

**Outcome:** The /control view supports full pre-run configuration.  
**Release Target:** MVP **Priority:** P1  
**Description:** The /control view presents setup panels for agent roster, directed links, first agent selection, and initial prompt. It surfaces validation status so users know when they can start. It does not provide graph visualization.

**Acceptance Criteria:**

- The /control view includes controls to add and edit agents and model labels.
- Users can configure directed links within the same view prior to start.
- The first agent and initial prompt are captured in the setup flow.
- Validation errors are shown inline and block the start action.

**In Scope:**

- Expose configuration UI for setup within /control.

**Out of Scope:**

- Topology or graph visualization.

**Dependencies:**

- (none)
### FEAT-016: Run controls and status cues

**Outcome:** Users can start, stop, and tick the run while seeing live status cues.  
**Release Target:** MVP **Priority:** P1  
**Description:** The /control view provides run controls aligned with the simulation lifecycle. It displays current tick and active agent cues as the run progresses. It does not change runtime semantics.

**Acceptance Criteria:**

- Start, stop, and manual tick controls are visible in /control.
- The tick control is enabled only when the run is in a running state.
- The current tick count and run status are visible and update after each tick.
- The active agent cue updates in sync with the runtime.

**In Scope:**

- Expose run controls and status indicators in /control.

**Out of Scope:**

- Altering runtime tick semantics from the UI.

**Dependencies:**

- (none)

### FEAT-017: Message log display

**Outcome:** The /control view renders a readable message log with metadata.  
**Release Target:** MVP **Priority:** P1  
**Description:** The UI renders the message log with agent metadata and tick context to support inspection of message flow. The log updates as new messages arrive. It does not provide analytics or export.

**Acceptance Criteria:**

- Each log entry shows from/to agent ids, role, model label, and tick index.
- New messages appear in the log in chronological order.
- The log remains viewable after the run stops.
- The log view is scoped to the current session and clears on a new run.

**In Scope:**

- Display the message log within /control.

**Out of Scope:**

- Message log analytics or export features.

**Dependencies:**

- (none)
## EPIC-007: Topology Visualization

### FEAT-018: Agent topology rendering

**Outcome:** A visual topology shows agents and directed links.  
**Release Target:** V1 **Priority:** P2  
**Description:** The /control view renders a graph of agent nodes and directed edges based on the configured communication graph. The rendering prioritizes readability for typical agent counts. It does not modify the underlying link rules.

**Acceptance Criteria:**

- The visualization displays one node per configured agent.
- Directed links are shown with clear direction from source to target.
- The graph renders using the current pre-run configuration.
- The visualization is accessible within the /control view.

**In Scope:**

- Render a graph view of agents and directed links.

**Out of Scope:**

- High-performance layout for large agent counts.

**Dependencies:**

- (none)

### FEAT-019: Active agent highlighting

**Outcome:** The graph indicates the active agent or current tick context.  
**Release Target:** V1 **Priority:** P2  
**Description:** The visualization highlights the active agent as reported by the runtime to help users follow execution. Highlighting updates as ticks advance. It does not introduce new runtime behavior.

**Acceptance Criteria:**

- When a tick is running, the active agent node is visually highlighted.
- The highlight updates on each tick according to runtime status.
- When the run is stopped, no active highlight is shown.

**In Scope:**

- Highlight active agent status within the graph.

**Out of Scope:**

- Adding runtime logic beyond existing status reporting.

**Dependencies:**

- (none)
### FEAT-020: Graph updates with configuration changes

**Outcome:** Pre-run configuration changes are reflected in the topology view.  
**Release Target:** V1 **Priority:** P2  
**Description:** The visualization updates immediately when agents or links change before the run starts. Once the run begins and configuration is frozen, the graph reflects the frozen snapshot. It does not support drag-and-drop editing.

**Acceptance Criteria:**

- Adding or removing agents before start updates the graph nodes.
- Adding or removing links before start updates the graph edges.
- After start, the graph remains aligned to the frozen configuration snapshot.

**In Scope:**

- Reflect pre-run configuration changes in the graph.

**Out of Scope:**

- Interactive graph editing via drag-and-drop.

**Dependencies:**

- (none)

## EPIC-008: LLM Mode Switching & Provider Bridge

### FEAT-021: Deterministic stub response mode

**Outcome:** The simulation can run with deterministic stubbed responses.  
**Release Target:** MVP **Priority:** P0  
**Description:** The system provides a stubbed response mode that avoids network calls and yields deterministic outputs. This mode supports testing and safe manual ticks without cost. It does not change tick semantics.

**Acceptance Criteria:**

- When stub mode is enabled, no external API calls are made.
- Given the same inputs and configuration, stub responses are deterministic across runs.
- Stubbed responses are logged with the same metadata as real responses.

**In Scope:**

- Provide deterministic stub responses for message generation.

**Out of Scope:**

- Non-deterministic or external response generation.

**Dependencies:**

- (none)
### FEAT-022: Provider interface and mode selection

**Outcome:** A provider interface selects stub or OpenAI response generation per run.  
**Release Target:** MVP **Priority:** P0  
**Description:** The runtime routes message generation through a provider interface that supports stub and OpenAI modes. The selected mode is chosen before run start and applies consistently during the run. It does not support switching modes mid-run.

**Acceptance Criteria:**

- The configuration allows selecting stub or OpenAI mode before start.
- The selected mode is recorded in the run configuration snapshot.
- All message generations for the run use the selected provider mode.
- Mode selection is unavailable once the run has started.

**In Scope:**

- Select and apply provider mode during run initialization.

**Out of Scope:**

- Switching providers mid-run.

**Dependencies:**

- (none)

### FEAT-023: Model label routing for OpenAI responses

**Outcome:** OpenAI responses use the configured model label per agent.  
**Release Target:** MVP **Priority:** P0  
**Description:** When OpenAI mode is enabled, the provider uses each agent's model label to select the model for responses. Invalid or missing model labels are treated as configuration errors prior to start. It does not define a broader model marketplace.

**Acceptance Criteria:**

- Each agent's model label is passed to the provider for response generation.
- Start is blocked if any agent has an invalid or missing model label for OpenAI mode.
- Responses generated in OpenAI mode are logged with the model label used.

**In Scope:**

- Use agent model labels to route OpenAI responses.

**Out of Scope:**

- Multi-provider marketplaces or cost optimization features.

**Dependencies:**

- (none)