---
doc_type: epics
idea_id: "IDEA-0001-control-simulation"
run_id: "2026-01-14T18-22-24Z_run-e188"
generated_by: "Epic Extractor"
generated_at: "2026-01-14T18:22:24Z"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
configs: []
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
epics:
  - id: "EPIC-001"
    title: "Session Setup & Agent Registry"
    outcome: "A run can be initialized with a validated agent roster, model labels, and a chosen first agent plus initial prompt, locked before start."
    description: "This epic owns the pre-run configuration boundary for the simulation session. It defines what must be collected and validated before a run can begin and ensures configuration is frozen once execution starts. It does not manage runtime progression or message generation."
    in_scope:
      - "Capture agent count, ids/names, roles, and model labels before start."
      - "Select the first agent and initial prompt as part of run setup."
      - "Validate configuration completeness before enabling start."
      - "Freeze configuration once a run starts."
    out_of_scope:
      - "Editing the agent roster after a run has started."
      - "Persisting configurations beyond the in-memory session."
      - "Automatic agent discovery or role inference."
    key_artifacts:
      - "Agent configuration"
      - "Run initialization snapshot"
    dependencies: []
    release_target: "MVP"
    priority: "P0"
    tags: ["config", "ui"]
  - id: "EPIC-002"
    title: "Directed Communication Rules"
    outcome: "Each run has a directed communication graph that governs which agents may message each other."
    description: "This epic defines and validates the directed link structure that constrains message routing. It ensures the runtime only allows exchanges permitted by the configured graph. It does not provide visualization or dynamic routing changes."
    in_scope:
      - "Define directed links between agents before start."
      - "Validate link integrity against the configured agent set."
      - "Enforce directed link rules during message routing."
    out_of_scope:
      - "Dynamic, role-driven routing changes during a run."
      - "Broadcast or undirected messaging defaults."
      - "Advanced policy engines or autonomy layers."
    key_artifacts:
      - "Communication graph"
    dependencies:
      - "EPIC-001"
    release_target: "MVP"
    priority: "P0"
    tags: ["graph", "runtime"]
  - id: "EPIC-003"
    title: "Manual Tick Simulation Runtime"
    outcome: "A run progresses deterministically via explicit start/stop and manual tick advancement where each tick is a full round."
    description: "This epic owns the in-memory run lifecycle, tick semantics, and execution order tracking. It advances agent steps per tick and records which agent is active each round. It excludes autorun pacing and persistence."
    in_scope:
      - "Start and stop a simulation run with in-memory session state."
      - "Advance a run by manual ticks where a tick represents a full round."
      - "Track execution order and active agent per tick."
    out_of_scope:
      - "Autorun pacing or request budget enforcement."
      - "Persistence or recovery across refreshes."
      - "Performance optimization for large agent counts."
    key_artifacts:
      - "Simulation run status"
      - "Tick progression state"
    dependencies:
      - "EPIC-001"
      - "EPIC-002"
    release_target: "MVP"
    priority: "P0"
    tags: ["runtime", "safety"]
  - id: "EPIC-004"
    title: "Autorun Pacing & Request Budget"
    outcome: "Optional autorun advances ticks at a readable cadence with a user-set request cap and safe stop conditions."
    description: "This epic adds a paced autorun mode that advances the same tick semantics as manual mode. It exposes a request budget and enforces a cap to prevent runaway usage. It does not change tick semantics or add background scheduling."
    in_scope:
      - "Enable autorun with a readable pacing control."
      - "Honor a user-defined max request count and stop on cap."
      - "Expose autorun state and remaining request budget."
    out_of_scope:
      - "Unbounded or unattended background execution."
      - "High-speed batch simulation."
      - "Non-deterministic scheduling changes."
    key_artifacts:
      - "Autorun state"
      - "Request budget"
    dependencies:
      - "EPIC-003"
    release_target: "V1"
    priority: "P1"
    tags: ["safety", "runtime"]
  - id: "EPIC-005"
    title: "Message Trace & Metadata Ledger"
    outcome: "A chronological message log with tick index, agent metadata, and execution order is captured and retrievable."
    description: "This epic defines the message trace structure and guarantees that each exchange is recorded with full metadata. It provides the data contract the UI consumes for log display. It excludes analytics, exports, and persistence."
    in_scope:
      - "Record message entries with from/to agent ids, role, model label, and tick index."
      - "Preserve execution order cues alongside each message."
      - "Expose message history for display in the /control view."
    out_of_scope:
      - "Exporting or persisting logs beyond the session."
      - "Aggregations, analytics, or summarization."
      - "Multi-run history views."
    key_artifacts:
      - "Message log"
    dependencies:
      - "EPIC-003"
    release_target: "MVP"
    priority: "P0"
    tags: ["logging", "runtime"]
  - id: "EPIC-006"
    title: "Control Room Interaction Surface"
    outcome: "The /control view provides configuration, run controls, and status cues aligned with the simulation lifecycle."
    description: "This epic integrates the simulation experience into the existing /control view. It focuses on user interactions and visibility for setup, start/stop, ticks, and status indicators. It does not introduce authentication or persistence features."
    in_scope:
      - "Integrate simulation setup and run controls into /control."
      - "Provide controls for start, stop, and manual tick advancement."
      - "Display simulation status, current tick, and active agent cues."
    out_of_scope:
      - "Multi-user authentication or access control."
      - "Persistent sessions or cross-run navigation."
      - "Major UI theming overhauls."
    key_artifacts:
      - "Control view state"
      - "Run control settings"
    dependencies:
      - "EPIC-001"
      - "EPIC-003"
      - "EPIC-005"
    release_target: "MVP"
    priority: "P1"
    tags: ["ui", "runtime"]
  - id: "EPIC-007"
    title: "Topology Visualization"
    outcome: "A visual map of agents and directed links helps users understand allowed message paths and current activity."
    description: "This epic renders a clear graph of agents and directed links for the control view. It focuses on readability and highlights activity cues without advanced layout or performance optimizations. It does not change link rules or runtime behavior."
    in_scope:
      - "Render agent nodes and directed link edges based on configuration."
      - "Indicate active agent or current tick context when available."
      - "Update the view to reflect pre-run configuration changes."
    out_of_scope:
      - "High-performance layout for large agent counts."
      - "Interactive graph editing via drag-and-drop."
      - "Analytics or path-finding features."
    key_artifacts:
      - "Graph visualization view model"
    dependencies:
      - "EPIC-002"
      - "EPIC-006"
    release_target: "V1"
    priority: "P2"
    tags: ["ui", "graph"]
  - id: "EPIC-008"
    title: "LLM Mode Switching & Provider Bridge"
    outcome: "Runs can execute in deterministic stub mode with a controlled path to OpenAI-backed responses using model labels."
    description: "This epic defines the provider interface and deterministic stub behavior that keeps simulations safe and predictable. It enables switching between stubbed responses and OpenAI-backed responses without changing core runtime semantics. It excludes complex autonomy or multi-provider expansion."
    in_scope:
      - "Provide deterministic stub responses for simulation steps."
      - "Define a provider interface that can route to OpenAI when enabled."
      - "Respect configured model labels when selecting a response mode."
    out_of_scope:
      - "Complex autonomy or role-driven routing changes."
      - "Multiple provider marketplaces or cost optimization features."
      - "Long-term caching or replay systems."
    key_artifacts:
      - "LLM mode configuration"
      - "Provider adapter settings"
    dependencies:
      - "EPIC-003"
    release_target: "MVP"
    priority: "P0"
    tags: ["llm", "runtime"]

# Project Epics

## EPIC-001: Session Setup & Agent Registry

**Outcome:** A run can be initialized with a validated agent roster, model labels, and a chosen first agent plus initial prompt, locked before start.  
**Release Target:** MVP **Priority:** P0  
**Description:** This epic owns the pre-run configuration boundary for the simulation session. It defines what must be collected and validated before a run can begin and ensures configuration is frozen once execution starts. It does not manage runtime progression or message generation.

**In Scope:**

- Capture agent count, ids/names, roles, and model labels before start.
- Select the first agent and initial prompt as part of run setup.
- Validate configuration completeness before enabling start.
- Freeze configuration once a run starts.

**Out of Scope:**

- Editing the agent roster after a run has started.
- Persisting configurations beyond the in-memory session.
- Automatic agent discovery or role inference.

**Key Artifacts:**

- Agent configuration
- Run initialization snapshot

**Dependencies:**

- (none)

## EPIC-002: Directed Communication Rules

**Outcome:** Each run has a directed communication graph that governs which agents may message each other.  
**Release Target:** MVP **Priority:** P0  
**Description:** This epic defines and validates the directed link structure that constrains message routing. It ensures the runtime only allows exchanges permitted by the configured graph. It does not provide visualization or dynamic routing changes.

**In Scope:**

- Define directed links between agents before start.
- Validate link integrity against the configured agent set.
- Enforce directed link rules during message routing.

**Out of Scope:**

- Dynamic, role-driven routing changes during a run.
- Broadcast or undirected messaging defaults.
- Advanced policy engines or autonomy layers.

**Key Artifacts:**

- Communication graph

**Dependencies:**

- EPIC-001

## EPIC-003: Manual Tick Simulation Runtime

**Outcome:** A run progresses deterministically via explicit start/stop and manual tick advancement where each tick is a full round.  
**Release Target:** MVP **Priority:** P0  
**Description:** This epic owns the in-memory run lifecycle, tick semantics, and execution order tracking. It advances agent steps per tick and records which agent is active each round. It excludes autorun pacing and persistence.

**In Scope:**

- Start and stop a simulation run with in-memory session state.
- Advance a run by manual ticks where a tick represents a full round.
- Track execution order and active agent per tick.

**Out of Scope:**

- Autorun pacing or request budget enforcement.
- Persistence or recovery across refreshes.
- Performance optimization for large agent counts.

**Key Artifacts:**

- Simulation run status
- Tick progression state

**Dependencies:**

- EPIC-001
- EPIC-002

## EPIC-004: Autorun Pacing & Request Budget

**Outcome:** Optional autorun advances ticks at a readable cadence with a user-set request cap and safe stop conditions.  
**Release Target:** V1 **Priority:** P1  
**Description:** This epic adds a paced autorun mode that advances the same tick semantics as manual mode. It exposes a request budget and enforces a cap to prevent runaway usage. It does not change tick semantics or add background scheduling.

**In Scope:**

- Enable autorun with a readable pacing control.
- Honor a user-defined max request count and stop on cap.
- Expose autorun state and remaining request budget.

**Out of Scope:**

- Unbounded or unattended background execution.
- High-speed batch simulation.
- Non-deterministic scheduling changes.

**Key Artifacts:**

- Autorun state
- Request budget

**Dependencies:**

- EPIC-003

## EPIC-005: Message Trace & Metadata Ledger

**Outcome:** A chronological message log with tick index, agent metadata, and execution order is captured and retrievable.  
**Release Target:** MVP **Priority:** P0  
**Description:** This epic defines the message trace structure and guarantees that each exchange is recorded with full metadata. It provides the data contract the UI consumes for log display. It excludes analytics, exports, and persistence.

**In Scope:**

- Record message entries with from/to agent ids, role, model label, and tick index.
- Preserve execution order cues alongside each message.
- Expose message history for display in the /control view.

**Out of Scope:**

- Exporting or persisting logs beyond the session.
- Aggregations, analytics, or summarization.
- Multi-run history views.

**Key Artifacts:**

- Message log

**Dependencies:**

- EPIC-003

## EPIC-006: Control Room Interaction Surface

**Outcome:** The /control view provides configuration, run controls, and status cues aligned with the simulation lifecycle.  
**Release Target:** MVP **Priority:** P1  
**Description:** This epic integrates the simulation experience into the existing /control view. It focuses on user interactions and visibility for setup, start/stop, ticks, and status indicators. It does not introduce authentication or persistence features.

**In Scope:**

- Integrate simulation setup and run controls into /control.
- Provide controls for start, stop, and manual tick advancement.
- Display simulation status, current tick, and active agent cues.

**Out of Scope:**

- Multi-user authentication or access control.
- Persistent sessions or cross-run navigation.
- Major UI theming overhauls.

**Key Artifacts:**

- Control view state
- Run control settings

**Dependencies:**

- EPIC-001
- EPIC-003
- EPIC-005

## EPIC-007: Topology Visualization

**Outcome:** A visual map of agents and directed links helps users understand allowed message paths and current activity.  
**Release Target:** V1 **Priority:** P2  
**Description:** This epic renders a clear graph of agents and directed links for the control view. It focuses on readability and highlights activity cues without advanced layout or performance optimizations. It does not change link rules or runtime behavior.

**In Scope:**

- Render agent nodes and directed link edges based on configuration.
- Indicate active agent or current tick context when available.
- Update the view to reflect pre-run configuration changes.

**Out of Scope:**

- High-performance layout for large agent counts.
- Interactive graph editing via drag-and-drop.
- Analytics or path-finding features.

**Key Artifacts:**

- Graph visualization view model

**Dependencies:**

- EPIC-002
- EPIC-006

## EPIC-008: LLM Mode Switching & Provider Bridge

**Outcome:** Runs can execute in deterministic stub mode with a controlled path to OpenAI-backed responses using model labels.  
**Release Target:** MVP **Priority:** P0  
**Description:** This epic defines the provider interface and deterministic stub behavior that keeps simulations safe and predictable. It enables switching between stubbed responses and OpenAI-backed responses without changing core runtime semantics. It excludes complex autonomy or multi-provider expansion.

**In Scope:**

- Provide deterministic stub responses for simulation steps.
- Define a provider interface that can route to OpenAI when enabled.
- Respect configured model labels when selecting a response mode.

**Out of Scope:**

- Complex autonomy or role-driven routing changes.
- Multiple provider marketplaces or cost optimization features.
- Long-term caching or replay systems.

**Key Artifacts:**

- LLM mode configuration
- Provider adapter settings

**Dependencies:**

- EPIC-003
