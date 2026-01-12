# VibeForge — Queue Next Work Package (WP)

Generate and enqueue the next Work Package in `docs/ai/planning/WORK_PACKAGES.md` from the canonical task list in `vibeforge_master_checklist.md`.

Supports optional argument:
- `/queue-next-wp 3` → try to enqueue up to 3 new WPs (default: 1)
- `/queue-next-wp WP-0007` → force-create the next WP id starting at WP-0007 (rare; only if numbering got out of sync)

Use `$ARGUMENTS` to read optional input.

---

## Inputs (Auto)
- `docs/ai/planning/WORK_PACKAGES.md`
- `vibeforge_master_checklist.md`

---

## Step 0 — Read context
1) Open `docs/ai/planning/WORK_PACKAGES.md` and parse all existing WPs:
   - WP ids, statuses, VF task lists
2) Compute:
   - next WP id = (max existing WP number + 1)
   - VF tasks already referenced in any WP (Queued/In Progress/Blocked/Done) to avoid duplicates

3) If there are already 4+ `Queued` WPs, STOP and report:
   - “Queue is already full; run `/execute-plan` first.”

---

## Step 1 — Find candidate VF tasks
1) Open `vibeforge_master_checklist.md` and scan in order for unchecked tasks (`- [ ] **VF-...`).
2) Skip any VF already referenced by an existing WP.
3) Select a coherent batch of 1–5 VF tasks using these heuristics (in priority order):
   - Prefer tasks in the same chapter/subchapter (keep the WP focused).
   - Prefer consecutive VF ids when possible.
   - Stop early if you encounter a task that clearly depends on earlier unchecked tasks (e.g., execution-loop tasks before workspace/runner/gates exist).
   - If you cannot infer dependencies, pick the next 1–3 VF tasks only (safer).

If no eligible VF tasks are found, STOP and report why (e.g., “all remaining tasks are already queued or complete”).

---

## Step 2 — Draft the WP metadata
For the selected VF batch:
1) Create WP title from the chapter/subchapter heading in the master checklist (shorten to a readable phrase).
2) Create a **Goal** sentence that explains what completion enables.
3) Create a **Plan Doc** path:
   - `docs/ai/planning/WP-XXXX_VF-AAA-BBB_<short_slug>.md`
   - Use `VF-AAA-BBB` as the numeric range covered (even if non-consecutive; use min/max).
4) Set **Status** to `Queued`.

5) Set **Dependencies** (best-effort):
   - If the WP is about workspace/patching, depend on the API foundation WP(s) if present.
   - If the WP is about command running or verifications, depend on workspace WP(s) if present.
   - If the WP is about gates, depend on workspace + command runner WP(s) if present.
   - Otherwise use `None`.

6) Set **Verify** commands (best-effort):
   - Default: `pytest`
   - If the WP affects the API layer: add `uvicorn ... --reload` + minimal `/docs` smoke
   - If unclear: keep only `pytest`

---

## Step 3 — Append to WORK_PACKAGES.md
1) Append a new WP section at the end of the WP list (before “Notes / Decisions Log”).
2) Ensure formatting matches existing entries:
   - `## WP-XXXX — <Title>`
   - bullet list for Status, VF Tasks, Goal, Dependencies, Plan Doc, Verify

---

## Step 4 — Create plan document and output next actions

1) Check if the WP’s Plan Doc exists at vibeforge_skeleton/docs/ai/planning/
2) If missing, create it using this template:

   - File: the WP plan doc path from WORK_PACKAGES.md
   - Content must include:
     - Title: `WP-XXXX — <name>`
     - VF tasks included (explicit list)
     - Ordered execution steps (implementation order)
     - “Done means…” section with verification commands
     - A checkbox list mirroring the VF tasks for this WP

3) The Plan Doc must reference the VF tasks exactly (IDs unchanged).

Print:
- The new WP id and VF tasks selected
- The Plan Doc path that will be created by `/execute-plan` if missing
- Suggest running `/execute-plan` next

---

## Non-negotiable Rules
- Never modify VF numbering or text in `vibeforge_master_checklist.md`.
- Never enqueue VF tasks that are already referenced by any existing WP.
- Keep WPs small and focused; default to 1 WP if `$ARGUMENTS` is empty.
- Do NOT mark any VF tasks complete here — only `/execute-plan` can close WPs and update completion after verification.
