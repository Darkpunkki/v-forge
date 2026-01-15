# Manifest — IDEA-0002-control-sim

## Idea

- idea_normalized_status: Final
- last_updated: 2026-01-15
- last_run_id: 2026-01-15T02-24-56Z_run-eae4
- latest_inputs:
  - inputs/idea.md
  - inputs/imagine_questions.md
  - inputs/imagine_answers.md
- latest_outputs:
  - latest/idea_normalized.md
- notes:
  - Imagine intake finalized for /control simulation.
  - Idea normalized; open questions remain for rewind scope, tick ordering, and graph-violation handling.

## Concept

- concept_summary_status: Draft
- last_updated: 2026-01-15
- last_run_id: 2026-01-15T02-37-26Z_run-039b
- invariants_count: 7
- scope_targets_supported: MVP, V1, Full, Later
- latest_outputs:
  - latest/concept_summary.md
- notes:
  - Open questions remain for rewind scope, tick ordering, and graph-violation handling.

## Epics

- last_updated: 2026-01-15
- last_run_id: 2026-01-15T02-51-27.209Z_run-2755

### EPIC-001 — Simulation Session Configuration
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []

### EPIC-002 — Graph-Gated Tick Progression
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001]

### EPIC-003 — Simulation Lifecycle Controls
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001, EPIC-002]

### EPIC-004 — Event Logging and Streaming
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: [EPIC-002]

### EPIC-005 — Control Panel Monitoring Views
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: [EPIC-003, EPIC-004]
