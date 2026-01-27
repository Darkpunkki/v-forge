# Manifest â€” IDEA-0003-vibeforge-is-pivoting-into-a-browser-based-contr

## Idea

- idea_normalized_status: Final
- last_updated: 2026-01-27
- last_run_id: 2026-01-27T16-27-30.707Z_run-de3b
- latest_outputs:
  - latest/idea_normalized.md
- notes:
  - Normalizer finalized with WebSocket preference.

## Concept

- concept_summary_status: Draft
- last_updated: 2026-01-27
- last_run_id: 2026-01-27T18-26-48.927Z_run-6475
- invariants_count: 6
- scope_targets_supported: MVP, V1, Full, Later
- latest_outputs:
  - latest/concept_summary.md
- notes:
  - Session removal captured as invariant
  - WhatsApp/phone control marked as Later scope
  - Existing simulation infrastructure preserved as extension point

## Epics

- last_updated: 2026-01-27
- last_run_id: 2026-01-27T18-28-17.564Z_run-684a

### EPIC-001 — Legacy Session Removal
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []

### EPIC-002 — Agent Bridge Protocol and Connection Manager
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: []

### EPIC-003 — Agent Bridge Service
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-002]

### EPIC-004 — Live Agent Control Backend
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-002]

### EPIC-005 — Async Dispatch Engine
- status: Proposed
- release_target: MVP
- priority: P1
- depends_on: [EPIC-002]

### EPIC-006 — Live Agent Control UI
- status: Proposed
- release_target: MVP
- priority: P0
- depends_on: [EPIC-001, EPIC-004]

### EPIC-007 — Multi-Agent Real Orchestration
- status: Proposed
- release_target: V1
- priority: P1
- depends_on: [EPIC-002, EPIC-003, EPIC-004, EPIC-005]

### EPIC-008 — External Control Channels
- status: Proposed
- release_target: Later
- priority: P2
- depends_on: [EPIC-004, EPIC-006]

## Features

- last_updated: 2026-01-27
- last_run_id: 2026-01-27T18-31-07.584Z_run-3db8
- total_features: 22
- by_release: MVP=18, V1=2, Later=2
- latest_outputs:
  - latest/features_backlog.md

## Existing Solution Map

- last_updated: 2026-01-27
- last_run_id: 2026-01-27T18-37-15.147Z_run-ca47
- scope: ALL (EPIC-001 through EPIC-008)
- touch_list_entries: 20
- gaps_identified: 5
- reuse_decisions: 9
- latest_outputs:
  - latest/existing_solution_map.md
- notes:
  - 20 files in prioritized touch list
  - 5 gaps: WebSocket endpoint, RemoteAgentConnectionManager, Agent Bridge Service, Protocol Models, UI widgets
  - 9 reuse-first hard rules established
  - 5 duplication risks documented with mitigations

## Tasks

- last_updated: 2026-01-27
- last_run_id: 2026-01-27T18-54-22.539Z_run-d5fa
- total_tasks: 40
- by_release: MVP=34, V1=4, Later=2
- by_epic: EPIC-001=4, EPIC-002=9, EPIC-003=5, EPIC-004=4, EPIC-005=5, EPIC-006=7, EPIC-007=4, EPIC-008=2
- latest_outputs:
  - latest/tasks.md
- notes:
  - All 22 features covered with implementable tasks
  - Every task includes target_files and reuse_notes grounded in existing_solution_map
  - 34 MVP tasks across 6 epics; 4 V1 tasks; 2 Later tasks

## Work Packages

- last_updated: 2026-01-27
- last_run_id: 2026-01-27T19-04-14.952Z_run-ae73
- scope_filter: MVP
- total_wps: 8
- global_wp_range: WP-0053 — WP-0060
- total_tasks_queued: 34
- total_effort_points: 48
- latest_outputs:
  - latest/work_packages.md
- notes:
  - 8 WPs batched from 34 MVP tasks across EPIC-001 through EPIC-006
  - WP-0053 (Session Removal) and WP-0054 (Protocol Models) can run in parallel
  - WP-0055+WP-0056 parallelizable; WP-0057+WP-0058 parallelizable
  - WP-0060 (Layout Rework) is final WP in dependency chain
