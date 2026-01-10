---
description: Expand epics into features for an idea (writes to ideas/<IDEA_ID>/runs and updates ideas/<IDEA_ID>/latest)
argument-hint: "<IDEA_ID>   (example: IDEA-0003_my-idea)"
disable-model-invocation: true
---

# Feature Extractor — Agent Instructions

## Invocation

Run this command with an idea folder id:

- `/feature-extractor <IDEA_ID>`

Where:

- `IDEA_ID = $ARGUMENTS` (must be a single folder name; no spaces)

If `IDEA_ID` is missing/empty, STOP and ask the user to rerun with an idea id.

---

## Canonical paths (repo-relative)

Idea root:

- `docs/ai/forge/ideas/$ARGUMENTS/`

Inputs:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline input)
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md` (optional)

Upstream artifacts (preferred if present):

- `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (optional)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` (required)

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

You are the **Feature Extractor** agent.

Your job is to expand a set of Epics into **Features** and write them to `features.md`.

You MUST treat `concept_summary.md` as the primary semantic anchor (read-only truth).
You must also read:

- `epics.md` (authoritative epic boundaries and release targets)
- the original idea documents (`idea.md` and/or `idea_normalized.md`) as required context to avoid losing important details

This stage produces **no tasks**.

---

## Inputs (how to choose sources)

You MUST read inputs in this order:

1. `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required; primary anchor)
2. `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` (required; epic boundaries)
3. `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (preferred if present)
4. `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline context)

Optional:

- If `docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md` exists, apply it.

If `latest/concept_summary.md` or `latest/epics.md` is missing, STOP and report the expected path.
If `inputs/idea.md` is missing, STOP and report the expected path.

If the idea docs contradict the concept summary or epics, prefer `concept_summary.md` + `epics.md` and record the conflict as a warning in `run_log.md`.

---

## Context (include file contents)

Include the content via file references:

- Concept summary (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md

- Epics (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md

- Preferred normalized idea (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md

- Baseline raw idea (always):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md

- Optional config (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md

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

1. `features.md` to:

- `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/features.md`

Then also update:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/features.md` (overwrite allowed)

2. Append an entry to:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`

3. Update (or create) the per-idea manifest at:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`
  - Update only the exact subsection that matches your stage. Do not create unrelated headings.

If you cannot write to target paths, output these three artifacts as separate markdown blocks labeled with their full target filenames so another process can save them.

---

## Definition: Feature

A **Feature** is a cohesive capability that fulfills part of an Epic’s responsibility.

A feature:

- Describes WHAT the system can do (observable behavior or validated system capability)
- Has a clear outcome and acceptance criteria
- Fits within one parent epic’s scope
- Can be delivered incrementally
- Avoids implementation-level details unless the source treats them as non-negotiable

---

## Scope & Rules

### You MUST

- Produce features for every epic in `epics.md`.
- Keep features within the scope of their parent epic.
- Use Invariants, Constraints, and Exclusions from `concept_summary.md` as hard guardrails.
- Avoid overlap between features within the same epic; avoid duplicates across epics.
- Assign each feature:
  - `release_target`: `MVP | V1 | Full | Later`
  - `priority`: `P0 | P1 | P2`
  - `tags`: from a small, consistent set
- Default: a feature’s `release_target` should match the parent epic unless clearly staged later.

### You MUST NOT

- Create tasks.
- Invent new scope beyond what is described in `concept_summary.md` / idea docs / epics.
- Violate epic boundaries.
- Turn features into implementation checklists (“build endpoint”, “create DB table”, etc.).

---

## How to Extract Features (Method)

1. Anchor on the concept

- Read concept summary first: capabilities, workflow, invariants, constraints, exclusions, artifacts, entities.

2. Respect epic boundaries

- Treat each epic’s `in_scope` / `out_of_scope` bullets as hard borders.

3. Use idea docs for detail recovery

- Catch details not present in the concept summary.
- If conflicts exist, prefer concept summary + epics and log warnings.

4. Derive features from outcomes
   Ask:

- What must exist for this epic to be “done”?
- What user-visible or system-validated capabilities define success?
- What artifacts must be produced/consumed within this epic?

5. Write acceptance criteria early

- Each feature must have 3–7 acceptance criteria bullets.
- Criteria must be testable at a behavioral level (not implementation).
- Prefer:
  - “Given X, when Y, then Z.”
  - “The system stores/returns/validates …”
  - “The UI allows the user to …” (only if applicable)

6. Keep features appropriately sized

- Too broad → split by responsibility/workflow step.
- Too similar → merge or adjust scope to remove overlap.
- Typical target: 4–10 features per epic (unless `feature_config.md` says otherwise).

7. Sanity check coverage

- Every epic has features that cover its `in_scope`.
- No feature violates concept invariants/exclusions.

---

## Output Format: `features.md` (YAML canonical block + Markdown rendering)

Write `features.md` as:

1. YAML header + canonical features list
2. Markdown rendering grouped by epic

YAML header + canonical features list (example):

```yaml
---
doc_type: features
idea_id: "$ARGUMENTS"
run_id: "<RUN_ID>"
generated_by: "Feature Extractor"
generated_at: "<ISO-8601>"
source_inputs:
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)"
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md"
configs:
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md (if used)"
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
features:
  - id: "FEAT-001"
    epic_id: "EPIC-001"
    title: "<short, specific feature title>"
    outcome: "<1 sentence measurable outcome>"
    description: "<2–6 sentences describing capability and boundaries>"
    acceptance_criteria:
      - "<testable bullet>"
      - "<testable bullet>"
    in_scope:
      - "<optional bullet>"
    out_of_scope:
      - "<optional bullet>"
    dependencies:
      - "FEAT-XYZ (optional)"
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "ux"]
```

Constraints:

- Every feature includes: `id`, `epic_id`, `title`, `outcome`, `description`, `acceptance_criteria`, `release_target`, `priority`, `tags`.
- IDs stable and sequential: `FEAT-001`, `FEAT-002`, ...
- `epic_id` must match an epic id in `epics.md`.

Markdown rendering (required):

# Features

## EPIC-001: <Epic Title>

### FEAT-001: <Feature Title>

**Outcome:** <...>  
**Release Target:** <...> **Priority:** <...>  
**Description:** <...>

**Acceptance Criteria:**

- ...

**In Scope:**

- ...

**Out of Scope:**

- ...

**Dependencies:**

- ...

(Repeat for all features grouped by epic)

---

## Logging Requirements: `run_log.md` (append-only)

Append an entry to `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`:

```md
### <ISO-8601 timestamp> — Feature Extractor

- Idea-ID: $ARGUMENTS
- Run-ID: <RUN_ID>
- Inputs:
  - docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md (if present)
- Output:
  - runs/<RUN_ID>/features.md
  - latest/features.md
- Counts:
  - total_features: <N>
  - by_epic:
    - EPIC-001: <n>
    - EPIC-002: <n>
- Warnings:
  - <overlap risks, missing detail, conflicts, unclear boundaries>
- Status: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED
```

---

## Manifest Update Requirements: `manifest.md` (per-idea)

Update or create a `Features` section in:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`

For each feature, add a concise index record:

- id
- epic_id
- title
- status (default: Proposed)
- release_target (MVP/V1/Full/Later)
- priority (P0/P1/P2)
- depends_on (optional list)
- last_updated (date)
- last_run_id (<RUN_ID>)

Do not duplicate full descriptions in the manifest.
Do not rename existing epic ids.
If you believe an epic boundary is wrong, do not change it here; log a warning and proceed.

---

## Quality Check (internal)

- Every epic in `epics.md` has at least one feature.
- Features cover each epic’s in-scope bullets.
- No feature crosses epic boundaries.
- No feature violates any invariant/exclusion from `concept_summary.md`.
- Acceptance criteria are behavioral and testable.
- Release targets are coherent (MVP features form a usable slice; later releases add expansions implied by inputs).

---

## Failure Handling

If inputs are ambiguous or epics are insufficient:

- Do not invent major scope to fill gaps.
- Produce best-effort features within given boundaries.
- Record gaps/ambiguities in `run_log.md` under Warnings.
- If an epic cannot be expanded due to missing detail, create a minimal feature:
  - Title: “Clarify requirements for <Epic Title>”
  - Acceptance criteria: a short list of questions that must be answered
  - Release target: same as the epic
  - Priority: P0 if it blocks MVP, otherwise P1/P2
