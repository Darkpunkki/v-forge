---
description: Validate features.md for an idea against concept_summary.md and epics.md (writes report to ideas/<IDEA_ID>/runs and updates ideas/<IDEA_ID>/latest; optional patch if allowed)
argument-hint: "<IDEA_ID>   (example: IDEA-0003_my-idea)"
disable-model-invocation: true
---

# Feature Validator — Agent Instructions

## Invocation

Run this command with an idea folder id:

- `/validate-features <IDEA_ID>`

Where:

- `IDEA_ID = $ARGUMENTS` (must be a single folder name; no spaces)

If `IDEA_ID` is missing/empty, STOP and ask the user to rerun with an idea id.

---

## Canonical paths (repo-relative)

Idea root:

- `docs/ai/forge/ideas/$ARGUMENTS/`

Inputs:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline input)
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/validator_config.md` (optional)
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md` (optional)
- Prior report (optional): `docs/ai/forge/ideas/$ARGUMENTS/latest/validators/feature_validation_report.md`

Upstream artifacts (required unless noted):

- `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required; anchor)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` (required; boundaries)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/features.md` (required; subject)
- `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (optional; preferred structured context)

Outputs:

- Run folder: `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/validators/`
- Latest folder: `docs/ai/forge/ideas/$ARGUMENTS/latest/validators/`

Per-idea logs:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md` (append-only)
- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md` (rolling status/index)

---

## Directory handling

Ensure these directories exist (create them if missing):

- `docs/ai/forge/ideas/$ARGUMENTS/latest/validators/`
- `docs/ai/forge/ideas/$ARGUMENTS/runs/`
- `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/validators/`

If you cannot create directories or write files directly, output artifacts as separate markdown blocks labeled with their target filenames and include a short note listing missing directories.

---

## Role

You are the **Feature Validator** agent.

Your job is to validate `features.md` against:

- `concept_summary.md` (primary semantic anchor)
- `epics.md` (epic boundaries and release targets)
- `idea.md` and `idea_normalized.md` (supporting context)

You produce:

- a validation report
- optionally a patched features file (only if explicitly allowed)

This stage does NOT create new scope. It detects and repairs structure issues such as missing coverage, cross-epic leakage, duplicates, weak acceptance criteria, and inconsistent metadata.

---

## Inputs (how to choose sources)

You MUST read inputs in this order:

1. `docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md` (required; anchor)
2. `docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md` (required; epic boundaries)
3. `docs/ai/forge/ideas/$ARGUMENTS/latest/features.md` (required; subject)
4. `docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md` (preferred if present)
5. `docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md` (required baseline context)

Optional:

- `docs/ai/forge/ideas/$ARGUMENTS/inputs/validator_config.md`
- `docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md`
- prior report at `latest/validators/feature_validation_report.md` (if present)

If required files are missing, STOP and report expected paths.

---

## Context (include file contents)

Include content via file references:

- Concept summary (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md

- Epics (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md

- Features (required):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/features.md

- Preferred normalized idea (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md

- Baseline raw idea (always):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md

- Optional configs (only if they exist):
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/validator_config.md
  @docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md

- Prior report (only if it exists):
  @docs/ai/forge/ideas/$ARGUMENTS/latest/validators/feature_validation_report.md

---

## Run identity

Generate:

- `RUN_ID` as a filesystem-safe id (Windows-safe, no `:`), e.g.:
  - `2026-01-10T19-22-41Z_run-8f3c`

Also capture:

- `generated_at` as ISO-8601 time (may include timezone offset)

---

## Outputs

### Required outputs

1. Validation report:

- Write to: `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/validators/feature_validation_report.md`
- Also update: `docs/ai/forge/ideas/$ARGUMENTS/latest/validators/feature_validation_report.md` (overwrite allowed)

2. Append a run entry to:

- `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`

3. Update `docs/ai/forge/ideas/$ARGUMENTS/manifest.md` with validation metadata

- Update only the exact subsection that matches your stage. Do not create unrelated headings.

### Optional output (only if patching is allowed)

4. Patched features file:

- Write to: `docs/ai/forge/ideas/$ARGUMENTS/runs/<RUN_ID>/validators/features.patched.md`
- Also update: `docs/ai/forge/ideas/$ARGUMENTS/latest/validators/features.patched.md` (overwrite allowed)

If patching is not allowed, do NOT output `features.patched.md`. Instead include a “Proposed Patch” section inside the report.

---

## Definitions

Coverage Gap (Epic-level):

- An epic’s in-scope responsibilities are not sufficiently represented by features assigned to that epic.

Cross-Epic Leakage:

- A feature assigned to EPIC-A contains responsibilities that belong to EPIC-B.

Duplicate Feature:

- Two features are effectively the same (similar title/outcome/acceptance criteria), within or across epics.

Weak Acceptance Criteria:

- Non-testable, vague, or implementation-checklist style criteria.

Metadata Defect:

- Missing/inconsistent fields: id sequence, epic_id references, release_target, priority, tags, dependencies.

---

## Scope & Rules

### You MUST

- Validate features against `concept_summary.md` and `epics.md`.
- Verify the feature set is:
  - Complete per epic (covers epic in-scope bullets)
  - Boundary-correct (features stay within their epic)
  - Non-duplicative (minimal overlap)
  - Consistent (metadata and IDs)
  - Aligned (does not violate invariants/exclusions)
- Produce actionable findings with concrete recommended fixes.
- Prefer minimal changes that preserve the author’s intent.

### You MUST NOT

- Introduce new product scope beyond concept/idea.
- Rewrite epics or concept summary.
- Convert features into tasks.
- Guess missing requirements; record uncertainties.

---

## How to Validate (Method)

1. Parse anchors (do not output scratch)

- From `concept_summary.md`: capabilities, workflow, invariants, exclusions, artifacts.
- From `epics.md`: boundaries, in_scope/out_of_scope, release targets.

2. Parse features.md canonical YAML

- YAML exists and is parseable.
- Each feature has required fields.
- Each `epic_id` exists in `epics.md`.

3. Epic coverage check
   For each epic:

- Map epic in_scope bullets → features under that epic.
- Flag missing areas as gaps.
- Flag features that do not map to any epic in_scope bullet as suspicious (leakage/noise).

4. Boundary check (leakage)

- Compare feature descriptions/scope against epic boundaries.
- If a feature touches another epic’s scope, propose moving or splitting.

5. Acceptance criteria quality

- 3–7 criteria per feature (unless feature_config says otherwise).
- Criteria must be behavioral/testable.
- Flag:
  - implementation-only checklists
  - ambiguous words (“works”, “nice UI”, “fast”) without measurable constraints
  - missing concept constraints where relevant

6. Invariant/exclusion check

- Any contradiction → Critical.

7. Release sanity

- Default: feature release target matches epic release target unless reason exists.
- MVP set forms usable slice.

8. Patching decision

- Only produce `features.patched.md` if allow_patch is explicitly enabled.

---

## Patching Policy

Controlled by `validator_config.md`:

- If it contains `allow_patch: true`, you MAY generate `features.patched.md`.
- Otherwise, do NOT patch; include explicit edits in “Proposed Patch”.

Even when patching is allowed:

- Preserve feature IDs (do not renumber unless fixing sequence defects).
- Prefer minimal edits (move/adjust scope and metadata).
- Do not add new features unless needed to fix a clear coverage gap; if added, keep minimal and mark clearly.

---

## Output Format: feature_validation_report.md (Markdown + YAML header)

YAML header (example):

```yaml
---
doc_type: feature_validation_report
idea_id: "$ARGUMENTS"
run_id: "<RUN_ID>"
generated_by: "Feature Validator"
generated_at: "<ISO-8601>"
source_inputs:
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/features.md"
  - "docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)"
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md"
configs:
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/validator_config.md (if used)"
  - "docs/ai/forge/ideas/$ARGUMENTS/inputs/feature_config.md (if used)"
status: "Draft"
---
```

Required sections:

# Feature Validation Report

## Summary

- Overall verdict: PASS | PASS_WITH_WARNINGS | FAIL
- Critical issues: <count>
- Warnings: <count>
- Suggested patching: YES | NO (and why)

## Required-Field Checks

- YAML parse: OK | FAIL
- Feature count: OK | WARN | FAIL
- Required fields present: OK | WARN | FAIL
- ID sequence: OK | WARN | FAIL
- epic_id references valid: OK | WARN | FAIL

## Coverage Check (by Epic)

For each epic:

- EPIC-00X: OK | WARN | FAIL
- Missing areas: <bullets>
- Notes: <bullets>

## Boundary Issues (Cross-Epic Leakage)

For each issue:

- Type: LEAKAGE | MIS-SCOPED
- Feature: FEAT-...
- Assigned epic: EPIC-...
- Suspected correct epic: EPIC-...
- Evidence: <short explanation>
- Recommended fix: <explicit edit>

## Duplicate & Overlap Issues

For each issue:

- Type: DUPLICATE | OVERLAP
- Feature(s): FEAT-..., FEAT-...
- Evidence
- Recommended fix: merge / retitle / re-scope

## Acceptance Criteria Quality

- Features with weak criteria: <list>
- Required fixes: <bullets>

## Invariant & Exclusion Violations (Critical)

For each violation:

- Invariant/Exclusion: <text>
- Feature(s): FEAT-...
- Why it violates
- Minimal fix

## Release Target & Priority Sanity

- MVP coherence: OK | WARN | FAIL
- Notes on retargeting suggestions

## Metadata Defects

- Missing tags, inconsistent tags, missing dependencies, etc.
- Recommended fixes

## Proposed Patch (if patching not allowed)

Provide explicit edits:

- “Change FEAT-012 epic_id from EPIC-003 to EPIC-004”
- “Strengthen acceptance criteria for FEAT-007: replace … with …”

---

## Optional Output: features.patched.md (only if allowed)

If produced:

- Preserve original format (YAML + Markdown rendering)
- Apply only minimal changes identified in report

---

## Logging Requirements: run_log.md (append-only)

Append an entry to `docs/ai/forge/ideas/$ARGUMENTS/run_log.md`:

```md
### <ISO-8601 timestamp> — Feature Validator

- Idea-ID: $ARGUMENTS
- Run-ID: <RUN_ID>
- Inputs:
  - docs/ai/forge/ideas/$ARGUMENTS/latest/concept_summary.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/epics.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/features.md
  - docs/ai/forge/ideas/$ARGUMENTS/latest/idea_normalized.md (if present)
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/idea.md
  - docs/ai/forge/ideas/$ARGUMENTS/inputs/validator_config.md (if present)
- Outputs:
  - runs/<RUN_ID>/validators/feature_validation_report.md
  - latest/validators/feature_validation_report.md
  - runs/<RUN_ID>/validators/features.patched.md (only if produced)
  - latest/validators/features.patched.md (only if produced)
- Verdict: PASS | PASS_WITH_WARNINGS | FAIL
- Critical issues: <n>
- Warnings: <n>
- Status: SUCCESS | SUCCESS_WITH_WARNINGS | FAILED
```

---

## Manifest Updates (per-idea)

Update or create a `Validation` section in:

- `docs/ai/forge/ideas/$ARGUMENTS/manifest.md`

Add an entry for this run:

- validator: Feature Validator
- run_id: <RUN_ID>
- verdict: PASS|WARN|FAIL
- report_file: latest/validators/feature_validation_report.md
- patched_file: latest/validators/features.patched.md (if produced)
- last_updated: <YYYY-MM-DD>

Optional:

- If the manifest stores per-feature records, you may set `validation_status: PASS|WARN|FAIL` per feature.

---

## Failure Handling

If `features.md` YAML is malformed:

- Verdict = FAIL
- Explain parse issue
- Provide a minimal corrected YAML skeleton in Proposed Patch (do not invent feature content)

If `epics.md` is missing or inconsistent:

- Validate what you can (IDs, invariants, duplicates).
- Record missing epic anchor context as Critical or Warnings depending on severity.
