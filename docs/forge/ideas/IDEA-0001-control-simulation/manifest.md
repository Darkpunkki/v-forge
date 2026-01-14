# Manifest - IDEA-0001-control-simulation

## Idea

- idea_status: Draft
- idea_normalized_status: Draft
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T15-50-19Z_run-8bd5
- latest_inputs:
  - inputs/idea.md
  - inputs/imagine_questions.md
  - inputs/imagine_answers.md
  - inputs/normalizer_answers.md
- latest_outputs:
  - latest/idea_normalized.md
- notes:
  - Created by Imagine (Idea Intake)
  - Finalized with user answers
  - Idea normalized finalized

## Concept

- concept_summary_status: Approved
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T15-57-45Z_run-14e3
- invariants_count: 6
- scope_targets_supported: MVP, V1, Full, Later
- latest_outputs:
  - latest/concept_summary.md
- notes:
  - Concept summary generated from normalized idea
  - Concept summary approved


## Epics

- last_updated: 2026-01-14
- last_run_id: 2026-01-14T18-22-24Z_run-e188

### EPIC-001 - Session Setup & Agent Registry
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []

### EPIC-002 - Directed Communication Rules
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001]

### EPIC-003 - Manual Tick Simulation Runtime
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001, EPIC-002]

### EPIC-004 - Autorun Pacing & Request Budget
- status: Proposed
- release_target: V1
- priority: P1
- depends_on: [EPIC-003]

### EPIC-005 - Message Trace & Metadata Ledger
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-003]

### EPIC-006 - Control Room Interaction Surface
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: [EPIC-001, EPIC-003, EPIC-005]

### EPIC-007 - Topology Visualization
- status: Proposed
- release_target: V1
- priority: P2
- depends_on: [EPIC-002, EPIC-006]

### EPIC-008 - LLM Mode Switching & Provider Bridge
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-003]

## Validation

- last_updated: 2026-01-15
- last_run_id: 2026-01-14T22-39-39.893Z_run-1b5f

### Epic Validator
- validator: Epic Validator
- run_id: 2026-01-14T21-47-46Z_run-f5a3
- verdict: WARN
- report_file: latest/validators/epic_validation_report.md
- patched_file: latest/epics_backlog.md
- last_updated: 2026-01-14

### Feature Validator
- validator: Feature Validator
- run_id: 2026-01-14T22-39-39.893Z_run-1b5f
- verdict: FAIL
- report_file: latest/validators/feature_validation_report.md
- patched_file: latest/features_backlog.md
- last_updated: 2026-01-15

## Features

### FEAT-001 - Agent roster configuration
- epic_id: EPIC-001
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-002 - First agent and initial prompt selection
- epic_id: EPIC-001
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-003 - Configuration validation and lock
- epic_id: EPIC-001
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-004 - Directed link configuration
- epic_id: EPIC-002
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-005 - Link integrity validation
- epic_id: EPIC-002
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8
### FEAT-006 - Directed link enforcement during routing
- epic_id: EPIC-002
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-007 - Run lifecycle start and stop
- epic_id: EPIC-003
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-008 - Manual tick progression
- epic_id: EPIC-003
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-009 - Execution order tracking
- epic_id: EPIC-003
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-010 - Autorun pacing control
- epic_id: EPIC-004
- status: Proposed
- release_target: V1
- priority: P1
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8
### FEAT-011 - Request budget cap enforcement
- epic_id: EPIC-004
- status: Proposed
- release_target: V1
- priority: P1
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-012 - Autorun state and budget reporting
- epic_id: EPIC-004
- status: Proposed
- release_target: V1
- priority: P1
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-013 - Message log capture with metadata
- epic_id: EPIC-005
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-014 - Message history retrieval for control view
- epic_id: EPIC-005
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-015 - Control view setup panels
- epic_id: EPIC-006
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8
### FEAT-016 - Run controls and status cues
- epic_id: EPIC-006
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-017 - Message log display
- epic_id: EPIC-006
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-018 - Agent topology rendering
- epic_id: EPIC-007
- status: Proposed
- release_target: V1
- priority: P2
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-019 - Active agent highlighting
- epic_id: EPIC-007
- status: Proposed
- release_target: V1
- priority: P2
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-020 - Graph updates with configuration changes
- epic_id: EPIC-007
- status: Proposed
- release_target: V1
- priority: P2
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8
### FEAT-021 - Deterministic stub response mode
- epic_id: EPIC-008
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-022 - Provider interface and mode selection
- epic_id: EPIC-008
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8

### FEAT-023 - Model label routing for OpenAI responses
- epic_id: EPIC-008
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-14
- last_run_id: 2026-01-14T22-06-41Z_run-96a8
