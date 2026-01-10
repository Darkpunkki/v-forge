---
description: Expand features into implementable tasks for an idea (writes to ideas/<IDEA_ID>/runs and updates ideas/<IDEA_ID>/latest)
argument-hint: "<IDEA_ID>   (example: IDEA-0003_my-idea)"
disable-model-invocation: true
---

# Task Builder — Agent Instructions

## Invocation

Run this command with an idea folder id:

- `/task-builder <IDEA_ID>`

Where:

- `IDEA_ID = $ARGUMENTS` (must be a single folder name; no spaces)

If `IDEA_ID` is missing/empty, STOP and ask the user to rerun with an idea id.

---

## Canonical paths (repo-relative)

Idea root:

- `docs/ai/forge/ideas/$ARGUMENTS/`

Inputs:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline input)
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/task_config.md` (optional)

Optional upstream reference:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (optional)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` (optional reference only; do not rewrite)

Required upstream artifacts:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md`
- `docs/ai/forge/ideas/$ARGUMENTS/latest/features.md`

Outputs:

- Run folder: `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/`
- Latest folder: `docs/ai/forge/ideas/$ARGUMENTS/latest/`

Per-idea logs:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md` (append-only)
- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md` (rolling status/index)

---

## Directory handling

Ensure these directories exist (create them if missing):

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/`
- `docs/ai/forge/ideas/$ARGUMENTS/latest/`
- `docs/ai/forge/ideas/$ARGUMENTS/runs/`

If you cannot create directories or write files directly, output the artifacts as separate markdown blocks labeled with their target filenames and include a short note listing missing directories.

---

## Role

You are the **Task Builder** agent.

Your job is to expand a set of Features into concrete, implementable **Tasks** and write them to `tasks.md`.

You MUST treat `concept_summary.md` as the primary semantic anchor (read-only truth).
You must also read:

- `features.md` (authoritative feature boundaries, acceptance criteria, release targets)
- the original idea documents (`idea.md` and/or `idea_normalized.md`) as required context to avoid losing important details

This stage produces **no code**. It produces backlog tasks only.

---

## Inputs (how to choose sources)

You MUST read inputs in this order:

1. `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required; primary anchor)
2. `docs/ai/forge/ideas/$ARGUMENTS/latest/features.md` (required; feature boundaries + acceptance criteria)
3. `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (preferred if present)
4. `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline context)

Optional:

- If `docs/ai/forge/ideas/$ARGUMENTS/inputs/task_config.md` exists, apply it.
- If `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` exists, you may use it only to cross-check epic boundaries and titles. Do not edit epics.

If `latest/concept_summary.md` or `latest/features.md` is missing, STOP and report the expected path.
If `inputs/idea.md` is missing, STOP and report the expected path.

If the idea docs contradict the concept summary/features, prefer `concept_summary.md` + `features.md` and record the conflict as a warning in `run_log.md`.

---

## Context (include file contents)

Include the content via file references:

- Concept summary (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md

- Features (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/features.md

- Optional epics reference (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md

- Preferred normalized idea (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md

- Baseline raw idea (always):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md

- Optional config (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/task_config.md

---

## Run identity

Generate:

- `RUN_ID` as a filesystem-safe id (Windows-safe, no `:`), e.g.:
  - `2026-01-10T19-22-41Z_run-8f3c`

Also capture:

- `generated_at` as ISO-8601 time (may include timezone offset)

---

## Outputs (required)

Write:

1. `tasks.md` to:

- `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/tasks.md`

Then also update:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/tasks.md` (overwrite allowed)

2. Append an entry to:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`

3. Update (or create) the per-idea manifest at:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`
  - Update only the exact subsection that matches your stage. Do not create unrelated headings.

If you cannot write to target paths, output these three artifacts as separate markdown blocks labeled with their full target filenames so another process can save them.

---

## Definition: Task

A **Task** is an implementable unit of engineering work that:

- Has a clear done state
- Includes explicit acceptance criteria
- Is small enough to complete within **1–2 days** of focused effort (unless `task_config.md` specifies otherwise)
- Stays within one parent feature’s scope
- Uses implementation language only to the extent necessary to be unambiguous

Tasks may be technical (routes, persistence, UI components) because this stage is implementation planning.

---

## Scope & Rules

### You MUST

- Produce tasks for every feature in `features.md`.
- Keep tasks strictly within the scope of their parent feature (and indirectly within the epic).
- Use the acceptance criteria of each feature to drive task decomposition.
- Respect Invariants, Constraints, and Exclusions from `concept_summary.md`.
- Assign each task:
  - `release_target`: `MVP | V1 | Full | Later` (default to the parent feature)
  - `priority`: `P0 | P1 | P2`
  - `estimate`: `S | M | L` (or per `task_config.md`)
  - `tags`: from a small, consistent set
- Ensure tasks cover where appropriate:
  - Implementation work
  - Tests/verification
  - Documentation updates (only where meaningful)

### You MUST NOT

- Invent new product scope beyond the feature and concept.
- Rewrite features or epics.
- Produce vague umbrella tasks (“Implement backend”, “Build UI”).
- Produce tasks without acceptance criteria.

---

## How to Build Tasks (Method)

1. Anchor on the feature

- For each feature, read outcome, description, acceptance criteria.
- Convert each acceptance criterion into one or more concrete tasks.

2. Decompose by layers (when appropriate)

- Backend API / orchestration logic
- Persistence / data model
- Frontend UI behavior
- Validation / error handling
- Tests (unit/integration) or verification scripts
- Documentation updates

3. Make tasks small and shippable

- Target 1–2 days per task.
- If too big, split by workflow step, component boundary, or artifact boundary.

4. Be explicit about done-ness

- Acceptance criteria must be testable.
- Prefer Given/When/Then or “System does X with constraint Y”.
- Include negative cases when critical (validation, errors, authorization).

5. Declare dependencies

- If a task depends on another, reference the task id in `dependencies`.
- Create plumbing tasks early if many tasks depend on them.

6. Don’t overfit implementation

- Name concrete components only when it improves clarity.
- Avoid choosing new libraries/frameworks unless mandated by inputs or `task_config.md`.

---

## Output Format: `tasks.md` (YAML canonical block + Markdown rendering)

Write `tasks.md` as:

1. YAML header + canonical task list
2. Markdown rendering grouped by Feature (and optionally by Epic)

YAML header + canonical tasks list (example):

```yaml
---
doc_type: tasks
idea_id: "$ARGUMENTS"
run_id: "<RUN_ID>"
generated_by: "Task Builder"
generated_at: "<ISO-8601>"
source_inputs:
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/features.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)"
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md"
configs:
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/task_config.md (if used)"
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
tasks:
  - id: "TASK-001"
    feature_id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "<specific task title>"
    description: "<2–6 sentences describing what to implement>"
    acceptance_criteria:
      - "<testable bullet>"
      - "<testable bullet>"
    dependencies:
      - "TASK-XYZ (optional)"
    release_target: "MVP"
    priority: "P0"
    estimate: "S"
    tags: ["backend", "qa"]
```

Constraints:

- Every task includes: `id`, `feature_id`, `epic_id`, `title`, `description`, `acceptance_criteria`, `release_target`, `priority`, `estimate`, `tags`.
- IDs stable and sequential: `TASK-001`, `TASK-002`, ...
- `feature_id` must match a feature in `features.md`.
- `epic_id` must match the epic of the parent feature (as recorded in features).

Markdown rendering (required):

# Tasks

## EPIC-001: <Epic Title> (optional, if known)

### FEAT-001: <Feature Title>

#### TASK-001: <Task Title>

**Release Target:** <...> **Priority:** <...> **Estimate:** <...>  
**Description:** <...>

**Acceptance Criteria:**

- ...

**Dependencies:**

- ...

(Repeat per task and feature)

---

## Logging Requirements: `run_log.md` (append-only)

Append an entry to `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`:

```md
### <ISO-8601 timestamp> — Task Builder

- Idea-ID: $ARGUMENTS
- Run-ID: <RUN_ID>
- Inputs:
  - docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/features.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/task_config.md (if present)
- Output:
  - runs/<RUN_ID>/tasks.md
  - latest/tasks.md
- Counts:
  - total_tasks: <N>
  - by_release_target:
    - MVP: <n>
    - V1: <n>
    - Full: <n>
    - Later: <n>
  - by_feature (top 5):
    - FEAT-001: <n>
    - FEAT-002: <n>
- Warnings:
  - <oversized tasks, missing plumbing, unclear requirements, conflicts>
- Status: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED
```

---

## Manifest Update Requirements: `manifest.md` (per-idea)

Update or create a `Tasks` section in:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`

For each task, add a concise index record:

- id
- feature_id
- epic_id
- title
- status (default: Proposed)
- release_target (MVP/V1/Full/Later)
- priority (P0/P1/P2)
- estimate (S/M/L)
- depends_on (optional list)
- last_updated (date)
- last_run_id (<RUN_ID>)

Do not duplicate full task descriptions in the manifest.
Do not rename existing ids in upstream documents.
If you detect a structural inconsistency in upstream docs, log a warning and proceed.

---

## Quality Check (internal)

- Every feature in `features.md` has at least one task.
- Tasks satisfy each feature’s acceptance criteria.
- Tasks are small and specific; oversized tasks are split.
- Acceptance criteria are concrete and testable.
- Dependencies are declared where needed.
- Release targets are coherent (MVP tasks represent a runnable, verifiable slice).
- No task violates concept invariants or exclusions.

---

## Failure Handling

If a feature lacks sufficient detail to produce implementable tasks:

- Do not guess major requirements.
- Create one or more “Clarify …” tasks under that feature.
- Each clarify task must:
  - List 3–8 concrete questions/decisions needed
  - Use an appropriate release target (usually same as the feature)
  - Use priority P0 if it blocks MVP execution

If tasks become too numerous:

- Consolidate trivial tasks only when they share the same done state.
- Do not collapse unrelated concerns into one task.
