---
name: Task Status
description: Generate or update task_status.md for an idea (quick reference for which tasks are complete)
argument-hint: "<IDEA_ID>   (example: IDEA-0003-vibeforge-is-pivoting)"
disable-model-invocation: true
---

# Task Status Generator

Generate or update `task_status.md` for an idea — a lightweight, human-readable summary of task completion status.

## Inputs

Required:
- `docs/forge/ideas/<IDEA_ID>/latest/tasks.md` (canonical task definitions)
- `docs/forge/ideas/<IDEA_ID>/latest/work_packages.md` (WP definitions + status)
- `docs/forge/ideas/<IDEA_ID>/manifest.md` (pipeline stage status)

Optional (for enrichment):
- `docs/forge/ideas/<IDEA_ID>/latest/epics_backlog.md` (epic summaries)
- `docs/ai/planning/WORK_PACKAGES.md` (global WP status, if tasks reference WP-#### ids)

## Output

Creates or updates:
- `docs/forge/ideas/<IDEA_ID>/task_status.md`

## Step 1 — Resolve IDEA_ID

- If `$ARGUMENTS` starts with `IDEA-`, treat it as `IDEA_REF` and resolve to `IDEA_ID`.
- If `$ARGUMENTS` is blank, STOP and ask for IDEA_ID.

## Step 2 — Load Source Data

1. Read `docs/forge/ideas/<IDEA_ID>/latest/tasks.md` (required)
   - Extract all TASK-### entries with:
     - id, title, epic_id, feature_id, release_target, priority, estimate
     - dependencies (optional)

2. Read `docs/forge/ideas/<IDEA_ID>/latest/work_packages.md` (preferred) or `docs/forge/ideas/<IDEA_ID>/latest/work_packages.md` (fallback)
   - Extract all WP-#### entries with:
     - WP id, title, status, tasks included

3. Read `docs/forge/ideas/<IDEA_ID>/manifest.md` (required)
   - Extract task completion notes (if present in the Tasks section)
   - Extract WP completion notes (if present in the Work Packages section)
   - Extract epic status summaries (if present in the Epics section)

4. (Optional) Read `docs/forge/ideas/<IDEA_ID>/latest/epics_backlog.md` or `epics.md`
   - Extract epic summaries and goals

5. (Optional) Read `docs/ai/planning/WORK_PACKAGES.md`
   - Check if any WP-#### entries reference this IDEA_ID
   - Use their status to enrich WP completion data

## Step 3 — Determine Task Status

For each task:
1. **Priority 1 (highest authority):** Check manifest.md for explicit task completion notes (e.g., "TASK-041 completed")
2. **Priority 2:** Check work_packages.md — if a WP containing this task has status "Done", mark task as Done
3. **Priority 3:** Check global WORK_PACKAGES.md — if a WP containing this task has status "Done", mark task as Done
4. **Priority 4 (fallback):** If none of the above, mark task as release_target status:
   - MVP tasks with no completion proof: ⏳ Queued
   - V1/Later tasks: 📋 Later

## Step 4 — Aggregate Completion by Epic

For each epic:
- Count total tasks in the epic
- Count completed tasks
- Calculate percentage
- Determine epic status:
  - ✅ Done (100% tasks complete)
  - 🔄 In Progress (1-99% tasks complete)
  - ⏳ Queued (0% tasks complete, release_target = MVP or V1)
  - 📋 Later (0% tasks complete, release_target = Later)

## Step 5 — Generate task_status.md

Create the output file with:

### Header
- Idea ID and title
- Last updated timestamp
- Overall status (e.g., "MVP Complete, V1 Queued")
- Total task counts by release

### Quick Summary
- High-level completion summary (e.g., "✅ MVP Complete (36/36 tasks)")

### Epic Status Table
- Table showing each epic with status, task count, progress percentage

### Work Package Status Table
- Table showing each WP with status, epic, and task list

### Task Details (grouped by Epic)
- For each epic, list all tasks with:
  - Checkbox icon (✅ Done, ⏳ Queued, 📋 Later, 🚫 Blocked)
  - Task ID + title
  - (Optional) Brief note about completion or blocker

### Next Steps Section
- List next queued epic + its tasks (if any)
- Show what capabilities will be unlocked

### Future Work Section
- List "Later" epics + tasks

### Verification Commands
- Commands to verify current state (pytest, npm build, git status)

### Key Files for Reference
- Links to canonical sources (tasks.md, work_packages.md, manifest.md)

### Legend
- Explain status icons (✅ ⏳ 📋 🚫)

## Step 6 — Write Output

Write the generated markdown to:
- `docs/forge/ideas/<IDEA_ID>/task_status.md`

If the file already exists, overwrite it (this is a generated summary, not hand-edited).

## Step 7 — Summary

Print:
- IDEA_ID and title
- Total tasks: X (MVP: Y, V1: Z, Later: W)
- MVP progress: X/Y complete
- V1 progress: X/Z complete
- Output file path
- Suggest: "View task_status.md for quick reference"

---

## Usage Examples

```bash
# Generate task status for an idea
/task-status IDEA-0003-vibeforge-is-pivoting

# Regenerate after completing tasks
/task-status IDEA-0003
```

---

## Integration with /work-wp

The `/work-wp` command should optionally auto-regenerate `task_status.md` after marking a WP as Done:
- After updating manifest.md and work_packages.md
- Before the end-of-run summary
- This keeps task_status.md always up-to-date

---

## Non-Negotiables

- Always use `latest/tasks.md` as the canonical task list (do NOT invent tasks)
- Always prefer explicit completion notes in manifest.md over inferred status
- Always overwrite the output file (it's generated, not hand-edited)
- Keep the output concise and scannable (tables + grouped lists, not walls of text)
- Use consistent icons: ✅ Done, ⏳ Queued, 📋 Later, 🚫 Blocked
