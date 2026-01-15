# Feature Execution Progress — <IDEA_ID>

- last_updated: <ISO-8601>
- policy:
  - Unit of execution: 1 feature (FEAT-XXX) per run
  - Source of truth: latest/tasks.md (search by FEAT id)
  - Checklist docs live in: planning/FEC-<FEAT_ID>-workspace-checklist.md

---

## Status legend
- Queued = not started yet
- In Progress = currently being worked on
- Blocked = needs user decision / missing info / failing tests
- Done = all tasks for the feature completed and verified

---

## Features (append-only history)

> Add a new line for each status change. Do not delete old lines.

| Timestamp (ISO) | FEAT | Status | Run-ID | Checklist | Notes |
|---|---|---|---|---|---|
| <ISO-8601> | FEAT-001 | Queued | - | planning/FEC-FEAT-001-workspace-checklist.md | |
| <ISO-8601> | FEAT-001 | In Progress | <RUN_ID> | planning/FEC-FEAT-001-workspace-checklist.md | started |
| <ISO-8601> | FEAT-001 | Done | <RUN_ID> | planning/FEC-FEAT-001-workspace-checklist.md | tests passing |

---

## Current pointer

- next_feature: <FEAT-XXX>
- last_completed_feature: <FEAT-XXX or blank>
- last_run_id: <RUN_ID or blank>

---

## Blockers (optional)

- FEAT-XXX:
  - <short blocker summary>
  - decision needed: <yes/no>
  - links: <PR/issue/log links if any>
