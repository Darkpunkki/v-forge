# VibeForge — Queue Next Work Packages from Backlog (Tasks → WPs)

Generate and enqueue the next Work Package(s) in `docs/ai/planning/WORK_PACKAGES.md` from the canonical backlog in `docs/ai/forge/tasks.md`.

Supports optional argument:

- `/into-wps 3` → try to enqueue up to 3 new WPs (default: 1)
- `/into-wps WP-0007` → force-create the next WP id starting at WP-0007 (rare; only if numbering got out of sync)
- `/into-wps MVP` → only queue tasks with `release_target: MVP` (default: queue MVP first, then V1)
- `/into-wps EPIC-003` → only queue tasks under a specific epic (optional filter)
- `/into-wps FEAT-014` → only queue tasks under a specific feature (optional filter)

Use `$ARGUMENTS` to read optional input.

---

## Inputs (Auto)

- `docs/ai/planning/WORK_PACKAGES.md`
- `docs/ai/forge/tasks.md`

## Optional Inputs (Auto if present)

- `docs/ai/forge/features.md` (for better titles/context)
- `docs/ai/forge/epics.md` (for better titles/context)
- `docs/ai/forge/concept_summary.md` (for context only; do not derive tasks from it here)

---

## Step 0 — Read context and compute queue state

1. Open `docs/ai/planning/WORK_PACKAGES.md` and parse all existing WPs:
   - WP ids
   - Status (`Queued`, `In Progress`, `Blocked`, `Done`, etc.)
   - Referenced Task IDs (e.g., `TASK-0xx`) if present
   - Any explicit dependency fields and verify commands

2. Compute:
   - Next WP id = (max existing WP number + 1), unless `$ARGUMENTS` forces a starting id
   - Task IDs already referenced in any WP with status in {Queued, In Progress, Blocked, Done} to avoid duplicates

3. If there are already 4+ `Queued` WPs, STOP and report:
   - “Queue is already full; run your WP execution flow first.”

---

## Step 1 — Read and index the backlog (tasks.md)

1. Open `docs/ai/forge/tasks.md`.
2. Parse the canonical YAML block at the top (preferred). If missing, fall back to parsing the Markdown rendering.
3. Build an in-memory list of tasks with fields (best-effort):
   - `task_id` (e.g., TASK-001)
   - `feature_id` (e.g., FEAT-014)
   - `epic_id` (e.g., EPIC-003)
   - `title`
   - `description`
   - `release_target` (MVP/V1/Full/Later)
   - `priority` (P0/P1/P2)
   - `estimate` (S/M/L)
   - `dependencies` (task ids, if present)
   - `tags` (backend/frontend/infra/qa/etc., if present)

4. Apply optional filters from `$ARGUMENTS`:
   - Release filter: MVP/V1/Full/Later
   - Epic filter: EPIC-xxx
   - Feature filter: FEAT-xxx

---

## Step 2 — Find eligible candidate tasks

Eligible tasks are tasks that:

- Are present in `tasks.md`
- Are NOT already referenced by any existing WP
- Are not obviously blocked by missing dependencies (best-effort)

Process:

1. Consider tasks in the following preference order (unless filters override):
   - `release_target: MVP` first
   - then `V1`, then `Full`, then `Later`
2. Within a release target, prefer:
   - `priority: P0` over P1 over P2
   - Tasks grouped by `epic_id` then `feature_id`
   - Tasks with smaller estimates first (S then M then L), unless dependency chains require ordering

3. Dependency-aware selection (best-effort):
   - If a task lists dependencies that are not yet Done/Queued/In Progress (i.e., not referenced by WPs or not included in the current WP batch), treat it as blocked and skip for now.
   - If dependencies are missing/unknown, be conservative: pick fewer tasks per WP.

If no eligible tasks are found, STOP and report why (e.g., “all remaining tasks are already queued or blocked by dependencies”).

---

## Step 3 — Form appropriately sized Work Packages (WP batching heuristics)

The goal is small, focused WPs.

Default WP sizing targets:

- 3–8 tasks per WP, biased toward smaller counts unless tasks are tiny
- Total estimated effort per WP ~ 1–3 days (best-effort using S/M/L)
  - Example heuristic: S=1, M=2, L=4 “points”; aim for 4–8 points per WP

Batching heuristics (in priority order):

1. Keep WPs within the same `feature_id` when possible.
2. If a feature is too large, allow the WP to span within the same `epic_id`, but keep it tight.
3. Prefer consecutive/related Task IDs only if they share the same epic/feature (IDs alone are not a guarantee).
4. Avoid mixing unrelated tags (e.g., do not mix deep infra + UI polish in the same WP) unless the tasks are explicitly coupled.
5. Stop early if you encounter a task that clearly depends on missing prerequisites.
6. If uncertain, create smaller WPs rather than larger ones.

When `/into-wps N` is used:

- Repeat batching up to N times, each time removing selected tasks from the candidate pool.

---

## Step 4 — Draft WP metadata

For each WP batch selected:

1. WP Title (short, readable):
   - Prefer: `EPIC title — Feature title (slice)` if `features.md`/`epics.md` are available
   - Otherwise: derive from the dominant `feature_id`/`epic_id` + common tags
   - Keep it human-scannable

2. Goal sentence:
   - Explain what completing the WP enables in the system (outcome-oriented).
   - Derived from the tasks’ shared outcome (not implementation trivia).

3. WP Task list:
   - List all included Task IDs and task titles.

4. Plan Doc path:
   - `docs/ai/planning/WP-XXXX_TASK-AAA-BBB_<short_slug>.md`
   - Use `TASK-AAA-BBB` as the numeric range (min/max) of included tasks.
   - Slug should be short and stable (e.g., `orchestration_api_slice`, `ui_control_panel_basics`).

5. Status:
   - Set to `Queued`.

6. Dependencies (best-effort):
   - If tasks have dependencies on other tasks, and those tasks are not already covered by Done/In Progress/Queued WPs, list those dependencies at WP level.
   - Otherwise `None`.

7. Verify commands (best-effort defaults):
   - Default: `pytest`
   - If tasks are primarily frontend-only: include `npm test` or a minimal build command if known; otherwise keep `pytest` only.
   - If unclear: keep only `pytest`.

---

## Step 5 — Append to WORK_PACKAGES.md

1. Append each new WP section at the end of the WP list (before “Notes / Decisions Log”, if present).
2. Ensure formatting matches existing entries:
   - `## WP-XXXX — <Title>`
   - Bullet list for:
     - Status
     - Release Target (dominant or explicit)
     - Task IDs (with titles)
     - Goal
     - Dependencies
     - Plan Doc
     - Verify

Recommended WP entry format:

- `## WP-XXXX — <Title>`
- `- Status: Queued`
- `- Release: MVP|V1|Full|Later`
- `- Tasks:`
  - `- TASK-001 — <title>`
  - `- TASK-002 — <title>`
- `- Goal: <goal sentence>`
- `- Dependencies: None | WP-XXXX | TASK-YYY`
- `- Plan Doc: docs/ai/planning/WP-XXXX_TASK-AAA-BBB_<slug>.md`
- `- Verify: pytest (and any extras)`

---

## Step 6 — Output next actions

Print:

- The new WP id(s) and tasks selected
- The Plan Doc path(s) that will be created/updated by your WP execution flow
- Suggested next step (e.g., “Run your plan execution command for WP-XXXX”)

---

## Non-negotiable Rules

- Never modify or rewrite the canonical backlog in `docs/ai/forge/tasks.md`.
- Never enqueue tasks that are already referenced by any existing WP (any status).
- Keep WPs small and focused; default to 1 WP if `$ARGUMENTS` is empty.
- Do NOT mark tasks complete here — completion happens only via the WP execution/verification workflow.
- Prefer conservative batching when dependencies are unclear.
- Do not invent tasks. Only select from tasks that exist in `tasks.md`.

---
