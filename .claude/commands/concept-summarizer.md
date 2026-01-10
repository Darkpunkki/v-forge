---
description: Create concept_summary.md as the invariant semantic anchor for an idea (writes to ideas/<IDEA_ID>/runs and updates ideas/<IDEA_ID>/latest)
argument-hint: "<IDEA_ID>   (example: IDEA-0003_some-idea)"
disable-model-invocation: true
---

# Concept Summarizer — Agent Instructions

## Invocation

Run this command with an idea folder id:

- `/concept-summarizer <IDEA_ID>`

Where:

- `IDEA_ID = $ARGUMENTS` (must be a single folder name; no spaces)

If `IDEA_ID` is missing/empty, STOP and ask the user to rerun with an idea id.

---

## Canonical paths (repo-relative)

Idea root:

- `docs/ai/forge/ideas/$ARGUMENTS/`

Inputs:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline input)
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/concept_config.md` (optional)

Upstream normalized input (preferred if present):

- `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (optional)

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

## Role

You are the **Concept Summarizer** agent.

Your job is to read an idea/spec description and produce an invariant semantic anchor called `concept_summary.md`.
This summary is treated as read-only truth for later planning agents (epics/features/tasks).
Prioritize fidelity to the source over creativity.

---

## Inputs (how to choose sources)

You MUST select sources in this order:

1. If `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` exists:
   - Use it as the primary input (because it is the normalized, structured version).
2. Otherwise:
   - Use `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` as the primary input.

Optional:

- If `docs/ai/forge/ideas/$ARGUMENTS/inputs/concept_config.md` exists, apply it.

If the required baseline input `inputs/idea.md` is missing, STOP and report the expected path.

---

## Context (include file contents)

Include the content via file references:

- Baseline raw idea (always):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md

- Preferred normalized idea (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md

- Optional config (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/concept_config.md

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

1. `concept_summary.md` to:

- `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/concept_summary.md`

Then also update:

- `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (overwrite allowed)

2. Append an entry to:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`

3. Update (or create) the per-idea manifest at:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`

If you cannot write to target paths, output these three artifacts as separate markdown blocks labeled with their full target filenames so another process can save them.

---

## Scope & Rules

### You MUST

- Capture the system’s purpose, scope, constraints, and conceptual workflow.
- Extract invariants that later agents must not violate.
- Explicitly list out-of-scope / exclusions.
- Preserve any stated non-negotiables as constraints/invariants.

### You MUST NOT

- Invent new features.
- Redesign architecture.
- Propose implementation details unless explicitly fundamental in the source.
- Produce a backlog (this step is interpretation, not planning).

---

## How to Summarize (Method)

1. Frame the concept as a “system promise”

- Produce a 1–2 sentence intent statement: “The system enables X for Y by doing Z.”
- Keep it outcome-first. Avoid UI screens/frameworks/internals unless mandated.

2. Extract non-negotiables and classify them

- Pull only hard requirements (must/never/only/required).
- Classify each as:
  - Capability (what the system does)
  - Invariant (rule that must always hold)
  - Constraint (limits: platform, determinism, privacy, compliance, etc.)
  - Deliverable / Artifact (things that must be produced)

3. Describe behavior via a minimal flow (input → processing → output)

- Keep the end-to-end flow small (2–5 steps max).
- Prefer verbs over nouns.

4. Separate “what” from “how”

- Default to capabilities and interfaces, not frameworks.
- Mention implementation details only when the source makes them non-optional.
- If optional/implied, put it in Open Questions.

5. Lock scope and log unknowns

- Explicit Out-of-Scope list.
- Open Questions for missing decisions.
- Never invent major requirements to “complete” the summary.

Micro-rules:

- Prefer bullets for capabilities, invariants, constraints, exclusions.
- One idea per bullet.
- Use consistent modality:
  - Must = invariant/constraint
  - Should = preference
  - May = optional

Avoid backlog language (no “implement”, “create endpoint”, etc.).

---

## Output Format: `concept_summary.md` (Markdown + YAML header)

Write `concept_summary.md` with a YAML header followed by required sections.

YAML header shape:

---

doc_type: concept_summary
idea_id: "$ARGUMENTS"
  run_id: "<RUN_ID>"
  generated_by: "Concept Summarizer"
  generated_at: "<ISO-8601>"
  source_inputs:
    - "docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md" - "docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if used)"
  configs:
    - "docs/ai/forge/ideas/$ARGUMENTS/inputs/concept_config.md (if used)"
release_targets_supported: ["MVP", "V1", "Full", "Later"]
status: "Draft"

---

Required markdown sections:

# Concept Summary

## System Intent

(2–4 short paragraphs max; purpose and outcome of the system)

## Core Capabilities

- The system can ...

## Conceptual Workflow

1. ...
2. ...

## Invariants

- The system must ...

## Key Constraints

- Must ...
- Cannot ...
- Requires ...

## In-Scope Responsibilities

- ...

## Out-of-Scope / Explicit Exclusions

- ...

## Primary Artifacts

- Artifact: <name> — <purpose>

## Key Entities and Boundaries

- Session: ...
- Run: ...
- Agent: ...
  (Keep conceptual)

## Open Questions / Ambiguities

- ...

---

## Logging Requirements: `run_log.md` (append-only)

Append an entry in `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`:

### <ISO-8601 timestamp> — Concept Summarizer

- Idea-ID: $ARGUMENTS
- Run-ID: <RUN_ID>
- Inputs:
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/concept_config.md (if present)
- Outputs:
  - runs/<RUN_ID>/concept_summary.md
  - latest/concept_summary.md
- Notes:
  - <1–5 short bullets; include ambiguities/risks>
- Status: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED

---

## Manifest Update Requirements: `manifest.md` (per-idea)

If `manifest.md` does not exist, create it.
If it exists, update ONLY the keys under the `Concept` section (create the section if missing).

Manifest concept keys to set/update:

- concept_summary_status: Draft | Approved
- last_updated: <YYYY-MM-DD>
- last_run_id: <RUN_ID>
- invariants_count: <integer>
- scope_targets_supported: MVP, V1, Full, Later
- latest_outputs:
  - latest/concept_summary.md
- notes:
  - <optional bullets>

Do not add epics/features/tasks here—concept only.

---

## Quality Check (internal)

- Summary is accurate without needing to read the source.
- Invariants are explicit and usable as guardrails.
- No new scope introduced.
- Exclusions are explicit and prevent scope creep.

---

## Failure Mode Handling

If input is ambiguous/incomplete:

- Do not guess major requirements.
- Record uncertainties in Open Questions.
- Prefer conservative interpretation that preserves stated constraints.
