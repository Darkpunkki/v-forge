# Manifest — IDEA-0002-control-sim

## Idea

- idea_normalized_status: Final
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T02-24-56Z_run-eae4
- latest_inputs:
  - inputs/idea.md
  - inputs/imagine_questions.md
  - inputs/imagine_answers.md
- latest_outputs:
  - latest/idea_normalized.md
- notes:
  - Imagine intake finalized for /control simulation.
  - Idea normalized; open questions resolved for rewind scope, tick ordering, graph-violation handling, and link cycles.

## Concept

- concept_summary_status: Draft
- last_updated: 2026-01-15
- last_run_id: 2026-01-15T02-37-26Z_run-039b
- invariants_count: 7
- scope_targets_supported: MVP, V1, Full, Later
- latest_outputs:
  - latest/concept_summary.md
- notes:
  - Open questions resolved for rewind scope, tick ordering, graph-violation handling, and link cycles.

## Epics

- last_updated: 2026-01-27
- last_run_id: 2026-01-15T02-51-27.209Z_run-2755

### EPIC-001 — Simulation Session Configuration
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []

### EPIC-002 — Graph-Gated Tick Progression
- status: Done
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001]

### EPIC-003 — Simulation Lifecycle Controls
- status: Done
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001, EPIC-002]

### EPIC-004 — Event Logging and Streaming
- status: Done
- release_target: MVP
- priority: P1
- depends_on: [EPIC-002]

### EPIC-005 — Control Panel Monitoring Views
- status: Partial
- release_target: MVP
- priority: P1
- depends_on: [EPIC-003, EPIC-004]
- notes: FEAT-013 + FEAT-014 done, FEAT-012 partial (graph shows workflow not sim links), FEAT-015 5/6 tasks done

## Validation

- last_updated: 2026-01-15
- last_run_id: 2026-01-15T03-39-23Z_run-f831

### Epic Validator
- run_id: 2026-01-15T03-01-40Z_run-1e7d
- verdict: WARN
- report_file: latest/validators/epic_validation_report.md
- last_updated: 2026-01-15

### Feature Validator
- run_id: 2026-01-15T03-39-23Z_run-f831
- verdict: WARN
- report_file: latest/validators/feature_validation_report.md
- last_updated: 2026-01-15


## Features

- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-001 — Agent roster configuration
- epic_id: EPIC-001
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-002 — Communication graph configuration
- epic_id: EPIC-001
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-003 — Initial prompt and first agent selection
- epic_id: EPIC-001
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-004 — Tick advancement with per-agent activity cap
- epic_id: EPIC-002
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-005 — Graph-gated message validation
- epic_id: EPIC-002
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-006 — Deterministic stubbed responses
- epic_id: EPIC-002
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-007 — Message event emission with tick metadata
- epic_id: EPIC-002
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-008 — Lifecycle state transitions and guardrails
- epic_id: EPIC-003
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810
- notes: Code-verified — start/pause/stop/reset with tick_status state validation in control.py

### FEAT-009 — Status and tick state exposure
- epic_id: EPIC-003
- status: Done
- release_target: MVP
- priority: P0
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-010 — Persisted simulation event log
- epic_id: EPIC-004
- status: Done
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810

### FEAT-011 — Event streaming for control panel
- epic_id: EPIC-004
- status: Done
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810
- notes: Code-verified — SSE endpoint with EventSourceResponse + polling fallback

### FEAT-012 — Agent graph visualization
- epic_id: EPIC-005
- status: Partial
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810
- notes: Renders configured workflow graph; simulation message link visualization (TASK-050) not implemented

### FEAT-013 — Message log view with filters
- epic_id: EPIC-005
- status: Done
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810
- notes: Code-verified — agent filter, blocked/stub detection & formatting in MultiAgentMessages.tsx

### FEAT-014 — Status and tick indicators
- epic_id: EPIC-005
- status: Done
- release_target: MVP
- priority: P1
- depends_on: []
- last_updated: 2026-01-27
- last_run_id: 2026-01-15T03-11-10Z_run-b810
- notes: Code-verified — status badge, tick counter, cost display, polling in TickControls.tsx
