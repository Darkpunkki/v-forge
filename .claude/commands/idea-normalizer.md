---
description: Normalize an idea into a consistent structure (writes to ideas/<IDEA_ID>/runs and updates ideas/<IDEA_ID>/latest)
argument-hint: "<IDEA_ID>   (example: IDEA-0002_controller-tool)"
disable-model-invocation: true
---

# Idea Normalizer — Agent Instructions

## Invocation

Run this command with an idea folder id:

- `/idea-normalizer <IDEA_ID>`

Where:

- `IDEA_ID = $ARGUMENTS` (must be a single folder name; no spaces)

If `IDEA_ID` is missing/empty, STOP and ask the user to rerun with an idea id.

---

## Canonical paths (repo-relative)

Idea root:

- `docs/ai/forge/ideas/$ARGUMENTS/`

Inputs:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md`
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/normalizer_config.md` (optional)

Outputs:

- Run folder: `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/`
- Latest folder: `docs/ai/forge/ideas/$ARGUMENTS/latest/`

Per-idea logs:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md` (append-only)
- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md` (rolling status)

---

## Directory handling

Ensure these directories exist (create them if missing):

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/`
- `docs/ai/forge/ideas/$ARGUMENTS/latest/`
- `docs/ai/forge/ideas/$ARGUMENTS/runs/`

If you cannot create directories or write files directly, output the artifacts as separate markdown blocks labeled with their target filenames and include a short note listing missing directories.

---

## Inputs

### Required

- `idea.md` at `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md`

### Optional

- `normalizer_config.md` at `docs/ai/forge/ideas/$ARGUMENTS/inputs/normalizer_config.md`
- Additional context files only if explicitly provided by the orchestrator.

---

## Context (include file contents)

Use file references to pull content into context:

- Raw idea:
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md

- Optional config (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/normalizer_config.md

If `idea.md` is missing, STOP and report the expected path.

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

1. `idea_normalized.md` to:

- `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/idea_normalized.md`

Then also update:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (overwrite allowed)

2. Append an entry to:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`

3. Update (or create) the per-idea manifest at:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`

---

## Definition: Normalization

Normalization means:

- Preserve meaning and scope of the source idea
- Re-express in consistent sections/terminology
- Make implicit structure explicit (inputs, workflow, outputs, constraints, exclusions)
- Record uncertainties instead of guessing

Normalization does NOT mean:

- Adding new requirements
- Choosing tech stacks not stated in the source
- Writing implementation plans, epics, features, or tasks

---

## Scope & Rules

### You MUST

- Preserve original intent and scope from `idea.md`
- Use the required section template below
- Convert free-form text into concise bullets where appropriate
- Mark assumptions explicitly as assumptions
- Capture constraints and exclusions explicitly
- Include “Open Questions” for missing decisions

### You MUST NOT

- Introduce new scope or features not present in `idea.md`
- Redesign the system
- Produce backlog items
- Remove meaningful nuance; if unsure, keep detail and place it in the correct section

---

## How to Normalize (Method)

1. Read entire `idea.md` once
2. Extract key statements into scratch (do not output scratch)
3. Map statements into the standard sections
4. Rewrite in consistent modality:
   - Must / Should / May
5. Handle contradictions conservatively (record in Open Questions)
6. Keep it brief but complete (prefer bullets)

---

## Output Format: `idea_normalized.md` (Markdown + YAML header)

Write `idea_normalized.md` with a YAML header followed by required sections.

### YAML header (example)

```yaml
---
doc_type: idea_normalized
idea_id: "$ARGUMENTS"
run_id: "<RUN_ID>"
generated_by: "Idea Normalizer"
generated_at: "<ISO-8601>"
source_inputs:
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md"
configs:
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/normalizer_config.md (if used)"
status: "Draft"
---
```

### Required sections

# Idea (Normalized)

## Summary

(1 short paragraph)

## Goals

- ...

## Target Users

- ...

## Primary Use Cases

- ...

## Inputs

- ...

## Outputs

- ...

## Conceptual Workflow

1. ...
2. ...

## Core Capabilities

- The system can ...

## Constraints

- ...

## Preferences

- ...

## Out-of-Scope / Exclusions

- ...

## Terminology

- Term: meaning

## Open Questions / Ambiguities

- ...

---

## Logging Requirements: `run_log.md` (append-only)

Append an entry with this shape:

```md
### <ISO-8601 timestamp> — Idea Normalizer

- Idea-ID: $ARGUMENTS
- Run-ID: <RUN_ID>
- Inputs:
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/normalizer_config.md (if present)
- Outputs:
  - runs/<RUN_ID>/idea_normalized.md
  - latest/idea_normalized.md
- Notes:
  - <1–5 bullets on key clarifications or ambiguities>
- Status: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED
```

---

## Manifest updates: `manifest.md` (per-idea)

If `manifest.md` does not exist, create it using the template below.
If it exists, update ONLY the keys under the `Idea` section.

### Manifest template (if creating new)

```md
# Manifest — $ARGUMENTS

## Idea

- idea_normalized_status: Draft
- last_updated: <YYYY-MM-DD>
- last_run_id: <RUN_ID>
- latest_outputs:
  - latest/idea_normalized.md
- notes:
  - <optional bullets>
```

Do not add epics/features/tasks here.

---

## Failure handling

If `idea.md` is extremely short/vague:

- Produce the normalized template anyway
- Put missing items into Open Questions
- Do not invent details
