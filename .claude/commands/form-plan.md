---
description: VibeForge — Create/update the WP Plan Doc for the next queued WP (or a given WP id) using canonical VF text and required filename convention.
argument-hint: "[WP-XXXX] (optional) | default: oldest Queued WP"
---

# VibeForge — Form Plan Doc (WP)

Generate (or update) the WP plan document referenced by `docs/ai/planning/WORK_PACKAGES.md`, using canonical VF task text from `vibeforge_master_checklist.md`.

Supports optional argument:
- /form-plan           -> pick the oldest Queued WP
- /form-plan WP-0007   -> generate plan doc for that WP id

Use $ARGUMENTS to read optional input.

---

## Inputs (Auto)
- docs/ai/planning/WORK_PACKAGES.md
- vibeforge_master_checklist.md

---

## Step 0 — Read context
1) Open docs/ai/planning/WORK_PACKAGES.md and parse all existing WPs:
   - WP ids, titles, statuses
   - VF task list per WP
   - Dependencies (if present)
   - Plan Doc path (if present)
   - Verify commands (if present)
2) Resolve target WP:
   - If $ARGUMENTS contains "WP-XXXX", select that WP
   - Else select the oldest WP with Status = "Queued"
3) If no Queued WP exists, STOP and report:
   - "No Queued WPs found. Run /queue-next-wp first."

---

## Step 1 — Resolve VF tasks (canonical) + compute VF range
1) From the selected WP entry, extract VF ids (e.g., VF-151, VF-152, VF-155).
2) Open vibeforge_master_checklist.md and locate each VF task:
   - Capture the exact checkbox line "- [ ] **VF-... — ...**" (verbatim)
   - Capture any immediate indented detail bullets under it (verbatim), stopping at the next VF task or heading
   - Capture the nearest chapter heading "## <num> <title>" for context
3) If any VF task cannot be found, STOP and report which VF ids are missing.
4) Compute numeric VF range using min/max:
   - VF-AAA = minimum VF numeric id in the WP
   - VF-BBB = maximum VF numeric id in the WP
   Note: use min/max even if tasks are non-consecutive.

---

## Step 2 — Determine Plan Doc path (required naming convention)
Goal: enforce this exact path format:
- docs/ai/planning/WP-XXXX_VF-AAA-BBB_<short_slug>.md

1) Prefer the Plan Doc path from the WP entry ONLY IF it already matches the required format AND VF-AAA/VF-BBB match the current VF task set.
2) Otherwise, set Plan Doc to:
   - docs/ai/planning/WP-XXXX_VF-AAA-BBB_<short_slug>.md
3) short_slug rules:
   - derive from WP title
   - lowercase
   - spaces -> dashes
   - remove punctuation
   - keep it short (2–6 words)
4) If Plan Doc path changes, update the WP entry in WORK_PACKAGES.md to the new Plan Doc path.

---

## Step 3 — Draft the Plan Doc content (single cohesive document)
Create or update the Plan Doc with the following structure and headings EXACTLY:

# WP-XXXX — <Title>

## Status
- <mirror status from WORK_PACKAGES.md>

## Context
- Chapter(s): <one line listing the checklist chapters that contain these VFs>
- Why now: <1–3 bullets describing what this unlocks>

## Goal
- <one sentence describing what completion enables>

## VF Tasks (canonical)
Include each VF task in order:
- The checkbox line (verbatim)
- Its key detail bullets (verbatim, if present)

## Plan
### Approach
- 3–6 bullets describing the strategy and any constraints/decisions

### Actionable Task Array
Provide an execution-ready array aligned to VF tasks.

BEGIN_ACTIONABLE_TASK_ARRAY
steps:
  - vf: VF-AAA
    intent: "<what will be done for this VF task>"
    touches:
      - "<likely file/module path (best-effort)>"
    done_when:
      - "<verifiable outcome>"
    verify:
      - "<command or TBD>"
  - vf: VF-...
    intent: "..."
    touches:
      - "..."
    done_when:
      - "..."
    verify:
      - "..."
END_ACTIONABLE_TASK_ARRAY

Rules:
- Keep 1 step per VF task unless a VF is clearly huge; if so, split into 2–3 substeps under the same vf id.
- "touches" is best-effort and may be empty if unknown.
- "verify" should prefer WP Verify commands; if none exist, use "pytest" or "TBD" if this is not a Python project area.
- Do not invent repo structure; infer from context if available.

## Acceptance Criteria
- 3–8 bullets tied to VF tasks (reference VF ids inline)

## Verify
- List the exact verification commands to run.
- Prefer Verify commands from WORK_PACKAGES.md.
- If missing, default to:
  - pytest

## Dependencies
- Mirror from WORK_PACKAGES.md (or "None")

## Risks / Recovery
- Risk -> mitigation
- If verification fails: describe the recovery approach (do not execute it)

---

## Step 4 — Write/update the Plan Doc
1) If the Plan Doc file does not exist, create it with the drafted content.
2) If it exists:
   - update it without deleting useful notes
   - enforce the section ordering above
   - ensure VF tasks remain verbatim

---

## Step 5 — Output next actions
Print:
- Selected WP id and VF tasks
- Plan Doc path created/updated (and whether WORK_PACKAGES.md was updated)
- Suggested next step: run /execute-plan

---

## Non-negotiable Rules
- Never modify VF numbering or VF task text in vibeforge_master_checklist.md.
- Never mark VF tasks complete here — only /execute-plan can close WPs and update completion after verification.
- If the WP’s VF tasks are incoherent, STOP and recommend splitting into 2 WPs.
- Do not add triple-backtick code fences to outputs; use the BEGIN_/END_ markers provided.
