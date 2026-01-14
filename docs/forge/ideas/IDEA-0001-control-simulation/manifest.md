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

- last_updated: 2026-01-14
- last_run_id: 2026-01-14T21-47-46Z_run-f5a3

### Epic Validator
- validator: Epic Validator
- run_id: 2026-01-14T21-47-46Z_run-f5a3
- verdict: WARN
- report_file: latest/validators/epic_validation_report.md
- patched_file: latest/epics_backlog.md
- last_updated: 2026-01-14
