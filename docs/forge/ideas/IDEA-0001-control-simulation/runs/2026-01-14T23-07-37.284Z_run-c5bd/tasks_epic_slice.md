---
doc_type: tasks_epic_slice
idea_id: "IDEA-0001-control-simulation"
epic_id: "EPIC-001"
run_id: "2026-01-14T23-07-37.284Z_run-c5bd"
generated_at: "2026-01-14T23:07:37.284Z"
task_id_start: "TASK-001"
task_id_end: "TASK-010"
source_inputs:
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/concept_summary.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/features_backlog.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/epics_backlog.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/latest/idea_normalized.md"
  - "docs/forge/ideas/IDEA-0001-control-simulation/inputs/idea.md"
---
tasks:
  - id: "TASK-001"
    epic_id: "EPIC-001"
    feature_id: "FEAT-001"
    title: "Define agent roster schema and validation"
    description: "Add an agent roster model with id, name, role, and model_label fields stored in the in-memory session, including validation for required fields and unique ids."
    acceptance_criteria:
      - "Agent roster schema includes id, name, role, and model_label in the API and in-memory session."
      - "Missing or empty required fields are rejected with field-specific validation errors."
      - "Duplicate agent ids are rejected with a clear validation message."
      - "Roster updates are allowed only before a run starts."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "config", "validation"]
  - id: "TASK-002"
    epic_id: "EPIC-001"
    feature_id: "FEAT-001"
    title: "Add agent roster CRUD endpoints"
    description: "Expose endpoints to list, add, update, and remove agents in the pre-run session configuration."
    acceptance_criteria:
      - "The roster list endpoint returns the current in-memory agent roster."
      - "Add, update, and remove endpoints persist changes to the session configuration."
      - "Responses include the updated roster payload."
      - "Invalid inputs return a 4xx response with validation details."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "api", "config"]
  - id: "TASK-003"
    epic_id: "EPIC-001"
    feature_id: "FEAT-001"
    title: "Build /control agent roster panel"
    description: "Create the setup UI panel for viewing and editing the agent roster with inline validation messaging."
    acceptance_criteria:
      - "The roster panel lists agents with id, name, role, and model label fields."
      - "Users can add, edit, and remove agents before the run starts."
      - "Inline validation messaging appears for missing fields or duplicate ids."
      - "The UI does not enforce a hard maximum agent count."
    release_target: "MVP"
    priority: "P0"
    estimate: "L"
    tags: ["frontend", "ui", "config"]
  - id: "TASK-004"
    epic_id: "EPIC-001"
    feature_id: "FEAT-001"
    title: "Test agent roster validation and persistence"
    description: "Add backend tests covering roster validation and CRUD behavior."
    acceptance_criteria:
      - "Tests fail on duplicate agent ids with a validation error."
      - "Tests fail on missing required fields with field-level errors."
      - "Tests confirm roster updates persist before start."
      - "Tests confirm roster list returns current session state."
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "tests", "config"]
  - id: "TASK-005"
    epic_id: "EPIC-001"
    feature_id: "FEAT-002"
    title: "Persist first agent and initial prompt in run config"
    description: "Add configuration fields for first_agent_id and initial_prompt, validate them against the roster, and store them in the run initialization snapshot on start."
    acceptance_criteria:
      - "Configuration accepts first_agent_id and initial_prompt values before start."
      - "Validation rejects first_agent_id values not present in the roster."
      - "Validation rejects empty initial_prompt values."
      - "Run start snapshot includes the selected first agent and initial prompt."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "config", "runtime"]
  - id: "TASK-006"
    epic_id: "EPIC-001"
    feature_id: "FEAT-002"
    title: "Add first agent selection and prompt input in /control"
    description: "Provide UI controls for choosing the first agent and entering the initial prompt, and gate the start action on valid input."
    acceptance_criteria:
      - "First agent selection options are sourced from the current roster."
      - "The start control is disabled until a first agent and initial prompt are set."
      - "If the selected agent is removed or renamed, the selection is cleared and the user must reselect."
      - "The initial prompt value is persisted to the session configuration."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["frontend", "ui", "config"]
  - id: "TASK-007"
    epic_id: "EPIC-001"
    feature_id: "FEAT-002"
    title: "Test first agent and initial prompt validation"
    description: "Add backend tests for first agent selection, prompt requirements, and snapshot persistence."
    acceptance_criteria:
      - "Tests reject start when first_agent_id is missing or not in the roster."
      - "Tests reject start when initial_prompt is empty."
      - "Tests confirm the run snapshot stores first_agent_id and initial_prompt."
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "tests", "runtime"]
  - id: "TASK-008"
    epic_id: "EPIC-001"
    feature_id: "FEAT-003"
    title: "Implement configuration completeness validation for start"
    description: "Add a validation layer that checks all required configuration elements before allowing a run to start, returning structured errors for the UI."
    acceptance_criteria:
      - "Start is blocked when agents, directed links, first agent, or initial prompt are missing or invalid."
      - "Validation errors are returned with machine-readable codes and user-facing messages."
      - "Successful validation allows the start transition to running."
      - "Tests cover start being blocked for each missing configuration element."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "validation", "runtime"]
  - id: "TASK-009"
    epic_id: "EPIC-001"
    feature_id: "FEAT-003"
    title: "Freeze configuration after start and block edits"
    description: "Store a frozen configuration snapshot on start and reject config mutations while the run is running or stopped."
    acceptance_criteria:
      - "Starting a run stores an immutable configuration snapshot in session state."
      - "Roster, link, and selection updates are rejected once the run is running or stopped."
      - "Blocked updates return a clear error message indicating configuration is locked."
      - "Tests confirm configuration updates are rejected after start."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["backend", "safety", "runtime"]
  - id: "TASK-010"
    epic_id: "EPIC-001"
    feature_id: "FEAT-003"
    title: "Lock setup UI after start with read-only view"
    description: "Disable setup inputs after start and show the frozen configuration while keeping run controls active."
    acceptance_criteria:
      - "Setup inputs become read-only once the run starts and remain locked when stopped."
      - "The UI displays the frozen configuration values for inspection."
      - "Attempting to edit locked fields shows a clear message and no update is sent."
      - "Run controls remain available while configuration is locked."
    release_target: "MVP"
    priority: "P0"
    estimate: "M"
    tags: ["frontend", "ui", "safety"]

# EPIC-001: Session Setup & Agent Registry

## FEAT-001: Agent roster configuration

### TASK-001: Define agent roster schema and validation
- Description: Add an agent roster model with id, name, role, and model_label fields stored in the in-memory session, including validation for required fields and unique ids.
- Acceptance Criteria:
  - Agent roster schema includes id, name, role, and model_label in the API and in-memory session.
  - Missing or empty required fields are rejected with field-specific validation errors.
  - Duplicate agent ids are rejected with a clear validation message.
  - Roster updates are allowed only before a run starts.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: backend, config, validation

### TASK-002: Add agent roster CRUD endpoints
- Description: Expose endpoints to list, add, update, and remove agents in the pre-run session configuration.
- Acceptance Criteria:
  - The roster list endpoint returns the current in-memory agent roster.
  - Add, update, and remove endpoints persist changes to the session configuration.
  - Responses include the updated roster payload.
  - Invalid inputs return a 4xx response with validation details.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: backend, api, config

### TASK-003: Build /control agent roster panel
- Description: Create the setup UI panel for viewing and editing the agent roster with inline validation messaging.
- Acceptance Criteria:
  - The roster panel lists agents with id, name, role, and model label fields.
  - Users can add, edit, and remove agents before the run starts.
  - Inline validation messaging appears for missing fields or duplicate ids.
  - The UI does not enforce a hard maximum agent count.
- Release Target: MVP
- Priority: P0
- Estimate: L
- Tags: frontend, ui, config

### TASK-004: Test agent roster validation and persistence
- Description: Add backend tests covering roster validation and CRUD behavior.
- Acceptance Criteria:
  - Tests fail on duplicate agent ids with a validation error.
  - Tests fail on missing required fields with field-level errors.
  - Tests confirm roster updates persist before start.
  - Tests confirm roster list returns current session state.
- Release Target: MVP
- Priority: P0
- Estimate: S
- Tags: backend, tests, config

## FEAT-002: First agent and initial prompt selection

### TASK-005: Persist first agent and initial prompt in run config
- Description: Add configuration fields for first_agent_id and initial_prompt, validate them against the roster, and store them in the run initialization snapshot on start.
- Acceptance Criteria:
  - Configuration accepts first_agent_id and initial_prompt values before start.
  - Validation rejects first_agent_id values not present in the roster.
  - Validation rejects empty initial_prompt values.
  - Run start snapshot includes the selected first agent and initial prompt.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: backend, config, runtime

### TASK-006: Add first agent selection and prompt input in /control
- Description: Provide UI controls for choosing the first agent and entering the initial prompt, and gate the start action on valid input.
- Acceptance Criteria:
  - First agent selection options are sourced from the current roster.
  - The start control is disabled until a first agent and initial prompt are set.
  - If the selected agent is removed or renamed, the selection is cleared and the user must reselect.
  - The initial prompt value is persisted to the session configuration.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: frontend, ui, config

### TASK-007: Test first agent and initial prompt validation
- Description: Add backend tests for first agent selection, prompt requirements, and snapshot persistence.
- Acceptance Criteria:
  - Tests reject start when first_agent_id is missing or not in the roster.
  - Tests reject start when initial_prompt is empty.
  - Tests confirm the run snapshot stores first_agent_id and initial_prompt.
- Release Target: MVP
- Priority: P0
- Estimate: S
- Tags: backend, tests, runtime

## FEAT-003: Configuration validation and lock

### TASK-008: Implement configuration completeness validation for start
- Description: Add a validation layer that checks all required configuration elements before allowing a run to start, returning structured errors for the UI.
- Acceptance Criteria:
  - Start is blocked when agents, directed links, first agent, or initial prompt are missing or invalid.
  - Validation errors are returned with machine-readable codes and user-facing messages.
  - Successful validation allows the start transition to running.
  - Tests cover start being blocked for each missing configuration element.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: backend, validation, runtime

### TASK-009: Freeze configuration after start and block edits
- Description: Store a frozen configuration snapshot on start and reject config mutations while the run is running or stopped.
- Acceptance Criteria:
  - Starting a run stores an immutable configuration snapshot in session state.
  - Roster, link, and selection updates are rejected once the run is running or stopped.
  - Blocked updates return a clear error message indicating configuration is locked.
  - Tests confirm configuration updates are rejected after start.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: backend, safety, runtime

### TASK-010: Lock setup UI after start with read-only view
- Description: Disable setup inputs after start and show the frozen configuration while keeping run controls active.
- Acceptance Criteria:
  - Setup inputs become read-only once the run starts and remain locked when stopped.
  - The UI displays the frozen configuration values for inspection.
  - Attempting to edit locked fields shows a clear message and no update is sent.
  - Run controls remain available while configuration is locked.
- Release Target: MVP
- Priority: P0
- Estimate: M
- Tags: frontend, ui, safety
