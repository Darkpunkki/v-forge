---
description: Extract 6–12 epics, depending on complexity, for an idea using concept_summary.md as the semantic anchor (writes to ideas/<IDEA_ID>/runs and updates ideas/<IDEA_ID>/latest)
argument-hint: "<IDEA_ID>   (example: IDEA-0003_my-idea)"
disable-model-invocation: true
---

# Epic Extractor — Agent Instructions

## Invocation

Run this command with an idea folder id:

- `/epic-extractor <IDEA_ID>`

Where:

- `IDEA_ID = $ARGUMENTS` (must be a single folder name; no spaces)

If `IDEA_ID` is missing/empty, STOP and ask the user to rerun with an idea id.

---

## Canonical paths (repo-relative)

Idea root:

- `docs/ai/forge/ideas/$ARGUMENTS/`

Inputs:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline input)
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/epic_config.md` (optional)

Upstream artifacts (preferred if present):

- `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (optional)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required)

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

You are the **Epic Extractor** agent.

Your job is to generate a high-level backlog skeleton consisting of **Epics only** and write it to `epics.md`.

You MUST treat `concept_summary.md` as the **primary semantic anchor** (read-only truth).
You must also read the original idea document (`idea.md` and/or `idea_normalized.md`) as required context to avoid losing important details.

This stage produces **no features** and **no tasks**.

---

## Inputs (how to choose sources)

You MUST read inputs in this order:

1. `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required; primary anchor)
2. `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (preferred if present)
3. `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline context)

Optional:

- If `docs/ai/forge/ideas/$ARGUMENTS/inputs/epic_config.md` exists, apply it.

If `latest/concept_summary.md` is missing, STOP and report the expected path.
If `inputs/idea.md` is missing, STOP and report the expected path.

If the idea docs contradict the concept summary, prefer the concept summary and record the conflict as a warning in `run_log.md`.

---

## Context (include file contents)

Include the content via file references:

- Concept summary (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md

- Preferred normalized idea (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md

- Baseline raw idea (always):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md

- Optional config (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/epic_config.md

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

1. `epics.md` to:

- `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/epics.md`

Then also update:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` (overwrite allowed)

2. Append an entry to:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`

3. Update (or create) the per-idea manifest at:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`
  - Update only the exact subsection that matches your stage. Do not create unrelated headings.

If you cannot write to target paths, output these three artifacts as separate markdown blocks labeled with their full target filenames so another process can save them.

---

## Definition: Epic

An **Epic** is a major deliverable representing a **subsystem**, **responsibility area**, or **lifecycle phase** that:

- Has a clear responsibility boundary
- Would naturally contain multiple features and tasks
- Can be planned, owned, and tracked independently
- Helps structure releases (MVP → V1 → Full → Later)

Epics describe **what outcome exists when the epic is done**, not how it is implemented.

---

## Scope & Rules

### You MUST

- Produce **6–12 epics** that collectively cover the system described in `concept_summary.md`.
- Keep epics **distinct** and **minimally overlapping**.
- Use **Invariants**, **Constraints**, and **Exclusions** from `concept_summary.md` as hard guardrails.
- Assign each epic:
  - `release_target`: `MVP | V1 | Full | Later`
  - `priority`: `P0 | P1 | P2`
  - `tags`: select from a small, consistent set

### You MUST NOT

- Create features or tasks.
- Invent new scope beyond what is described in `concept_summary.md` / idea docs.
- Ignore exclusions or rewrite invariants.
- Use backlog/action verbs like “Implement endpoints” or “Build UI screens” as epic titles.

---

## How to Extract Epics (Method)

1. Read `concept_summary.md` first

- Treat it as authoritative for intent and boundaries.
- Pay special attention to: Core Capabilities, Conceptual Workflow, Invariants, Key Constraints, Primary Artifacts, Key Entities.

2. Use `idea.md` / `idea_normalized.md` to recover missing detail

- Clarify/disambiguate only; do not expand scope.
- If conflicts exist, prefer concept summary and record warnings.

3. Create candidate epic buckets
   Choose a decomposition that fits the concept:

- Architecture responsibilities (not layers): orchestration, artifact store, validation, observability, config, provider adapters, UI (if present)
- Workflow phases: intake → planning → execution → delivery
- Responsibility domains: policy/validation, configuration, audit/logging, integrations
- Artifact ownership: who produces/stores which canonical artifacts

4. Merge/split until “just right”

- Too broad → split by responsibility boundary or workflow phase.
- Overlap → move scope bullets so each responsibility belongs to exactly one epic.
- <6 epics → likely under-modeled; >12 → likely over-split; merge adjacent responsibilities.

5. Map epics to releases

- MVP epics should form a coherent “first usable system”.
- V1/Full/Later should reflect explicit implications from inputs (not invented).

6. Write clear scope bullets

- Each epic must have `in_scope` and `out_of_scope` bullets to prevent overlap.

7. Sanity check

- Every core capability maps to at least one epic.
- No epic violates any invariant/exclusion.
- No epic is merely “Backend” or “Frontend” without a specific responsibility.

---

## Output Format: `epics.md` (YAML canonical block + Markdown rendering)

Write `epics.md` as:

1. A YAML header + canonical epic list (machine-readable)
2. A Markdown rendering (human-readable)

YAML header + canonical epics list (example):

```yaml
---
doc_type: epics
idea_id: "$ARGUMENTS"
run_id: "<RUN_ID>"
generated_by: "Epic Extractor"
generated_at: "<ISO-8601>"
source_inputs:
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)"
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md"
configs:
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/epic_config.md (if used)"
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"
---
epics:
  - id: "EPIC-001"
    title: "<short, specific epic title>"
    outcome: "<1 sentence measurable outcome>"
    description: "<2–6 sentences describing responsibility boundaries>"
    in_scope:
      - "<bullet>"
    out_of_scope:
      - "<bullet>"
    key_artifacts:
      - "<artifact names produced/owned by this epic>"
    dependencies:
      - "EPIC-XYZ (optional)"
    release_target: "MVP"
    priority: "P0"
    tags: ["backend", "orchestration"]
```

Constraints:

- 6–12 epics
- IDs stable and sequential: `EPIC-001`, `EPIC-002`, ...
- If dependencies are unknown, omit them or use an empty list

Markdown rendering (required):

# Project Epics

## EPIC-001: <Title>

**Outcome:** <...>  
**Release Target:** <...> **Priority:** <...>  
**Description:** <...>

**In Scope:**

- ...

**Out of Scope:**

- ...

**Key Artifacts:**

- ...

**Dependencies:**

- ...

(Repeat for all epics)

---

## Logging Requirements: `run_log.md` (append-only)

Append an entry to `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`:

```md
### <ISO-8601 timestamp> — Epic Extractor

- Idea-ID: $ARGUMENTS
- Run-ID: <RUN_ID>
- Inputs:
  - docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/epic_config.md (if present)
- Output:
  - runs/<RUN_ID>/epics.md
  - latest/epics.md
- Counts: <N epics>
- Warnings:
  - <overlap risks, unclear boundaries, missing info, conflicts>
- Status: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED
```

If you can compute file hashes, include them; otherwise omit hashes.

---

## Manifest Update Requirements: `manifest.md` (per-idea)

Update or create an `Epics` section in:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`

For each epic, add a concise index record:

- id
- title
- status (default: Proposed)
- release_target (MVP/V1/Full/Later)
- priority (P0/P1/P2)
- depends_on (optional list)
- last_updated (date)
- last_run_id (<RUN_ID>)

Keep the manifest as an index; do not duplicate full epic descriptions.

---

## Quality Check (internal)

- All major capabilities and workflow steps in `concept_summary.md` are covered by at least one epic.
- Epics are mutually distinct and non-overlapping.
- Epic titles are specific and outcome-oriented.
- Release targets form a coherent staged plan (MVP → V1 → Full → Later).
- No epic violates any invariant or exclusion from the concept summary.

---

## Failure Mode Handling

If boundaries are unclear:

- Prefer conservative epic separation to avoid overlap.
- Record uncertainty as warnings in `run_log.md`.
- Do not guess major new capabilities.
