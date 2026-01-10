---
description: Queue next Work Package(s) from an idea’s backlog (tasks → WORK_PACKAGES.md), without modifying tasks.md
argument-hint: "<IDEA_ID> [N|MVP|V1|Full|Later|EPIC-###|FEAT-###|WP-####] ...  (examples: IDEA-0003_my-idea 2 | IDEA-0003_my-idea MVP | IDEA-0003_my-idea EPIC-003)"
disable-model-invocation: true
---

# VibeForge — Queue Next Work Packages from Backlog (Tasks → WPs)

Generate and enqueue the next Work Package(s) in `docs/ai/planning/WORK_PACKAGES.md`
from the canonical backlog for a specific idea:

- `docs/ai/forge/ideas/<IDEA_ID>/latest/tasks.md`

This command ONLY selects tasks and appends WP entries; it must never modify the backlog tasks.

---

## Invocation

Call with an idea folder id first:

- `/into-wps <IDEA_ID> [filters...]`

Examples:

- `/into-wps IDEA-0003_my-idea` → enqueue 1 WP (default)
- `/into-wps IDEA-0003_my-idea 3` → enqueue up to 3 new WPs
- `/into-wps IDEA-0003_my-idea MVP` → only queue tasks with `release_target: MVP`
- `/into-wps IDEA-0003_my-idea EPIC-003` → only queue tasks under an epic
- `/into-wps IDEA-0003_my-idea FEAT-014` → only queue tasks under a feature
- `/into-wps IDEA-0003_my-idea WP-0007` → force-create next WP id starting at WP-0007 (rare)

Argument parsing rules (best-effort):

- `$1` = IDEA_ID (required)
- Remaining tokens in `$ARGUMENTS` may include:
  - a count `N` (integer)
  - a release filter `MVP|V1|Full|Later`
  - `EPIC-###` and/or `FEAT-###` filters
  - a forced starting id `WP-####`

If IDEA_ID is missing, STOP and ask the user to provide it.

---

## Inputs (Auto)

Global planning index:

- `docs/ai/planning/WORK_PACKAGES.md`

Idea backlog (canonical):

- `docs/ai/forge/ideas/$1/latest/tasks.md`

## Optional Inputs (Auto if present)

For better titles/context (do not derive tasks from these):

- `docs/ai/forge/ideas/$1/latest/features.md`
- `docs/ai/forge/ideas/$1/latest/epics.md`
- `docs/ai/forge/ideas/$1/latest/concept_summary.md`

---

## Output (Auto)

Append WP entries into:

- `docs/ai/planning/WORK_PACKAGES.md`

No other files are modified by this command.

If you cannot write to the file directly, output the exact text block(s) that should be appended.

---

## Step 0 — Read context and compute queue state

1. Open `docs/ai/planning/WORK_PACKAGES.md` and parse existing WPs:

- WP ids
- Status (`Queued`, `In Progress`, `Blocked`, `Done`, etc.)
- Referenced Task IDs (`TASK-###`) if present
- Any explicit dependencies and verify commands

2. Compute:

- Next WP id = (max existing WP number + 1), unless a forced starting id is provided
- Task IDs already referenced by any existing WP (any status) to avoid duplicates

3. If there are already 4+ WPs with status `Queued`, STOP and report:

- “Queue is already full; run your WP execution flow first.”
- List the currently queued WP ids.

---

## Step 1 — Read and index the backlog (tasks.md)

1. Open `docs/ai/forge/ideas/$1/latest/tasks.md`.
2. Parse the canonical YAML block at the top (preferred). If missing, fall back to parsing the Markdown rendering.
3. Build an in-memory list of tasks with fields (best-effort):

- `task_id` (TASK-001)
- `feature_id` (FEAT-014)
- `epic_id` (EPIC-003)
- `title`
- `description`
- `release_target` (MVP/V1/Full/Later)
- `priority` (P0/P1/P2)
- `estimate` (S/M/L)
- `dependencies` (task ids, if present)
- `tags` (backend/frontend/infra/qa/etc., if present)

4. Apply optional filters from remaining args:

- Release filter: MVP/V1/Full/Later
- Epic filter: EPIC-###
- Feature filter: FEAT-###

If the backlog file is missing, STOP and report the expected path.

---

## Step 2 — Find eligible candidate tasks

Eligible tasks are tasks that:

- exist in `tasks.md`
- are NOT already referenced by any existing WP
- are not obviously blocked by missing dependencies (best-effort)

Preference order (unless filters override):

1. `release_target: MVP` first, then V1, then Full, then Later
2. Within a release target:

- priority P0 → P1 → P2
- group by `epic_id` then `feature_id`
- smaller estimates first (S then M then L), unless dependency chains require ordering

Dependency-aware selection (best-effort):

- If a task lists dependencies that are not already in any WP (any status) and not included in the current WP batch, treat it as blocked and skip.
- If dependencies are missing/unknown, be conservative: pick fewer tasks per WP.

If no eligible tasks are found, STOP and report why.

---

## Step 3 — Form appropriately sized Work Packages (WP batching heuristics)

Goal: small, focused WPs.

Default WP sizing targets:

- 3–8 tasks per WP (bias toward smaller counts unless tasks are tiny)
- Total effort per WP ~ 1–3 days (best-effort)
  - Heuristic points: S=1, M=2, L=4; aim for 4–8 points per WP

Batching heuristics (priority order):

1. Keep WPs within the same `feature_id` when possible.
2. If a feature is too large, allow spanning within the same `epic_id`, but keep it tight.
3. Prefer related tasks only if they share the same epic/feature (IDs alone are not a guarantee).
4. Avoid mixing unrelated tags (e.g., deep infra + UI polish) unless tasks are explicitly coupled.
5. Stop early if you hit a task that clearly depends on missing prerequisites.
6. If uncertain, create smaller WPs.

When a count `N` is provided:

- Repeat batching up to N times, removing selected tasks from the candidate pool each time.

---

## Step 4 — Draft WP metadata

For each WP batch selected:

1. WP Title (short, readable):

- Prefer: `<EPIC title> — <Feature title> (slice)` if `features.md`/`epics.md` are available
- Otherwise: derive from dominant `feature_id`/`epic_id` + common tags
- Keep it human-scannable

2. Goal sentence:

- Outcome-oriented: what completing the WP enables.

3. WP Task list:

- List included Task IDs and task titles.

4. Plan Doc path:

- `docs/ai/planning/work_packages/WP-XXXX_TASK-AAA-BBB_<short_slug>.md`
- `TASK-AAA-BBB` = numeric range (min/max) of included tasks
- Slug: short + stable (e.g., `orchestration_api_slice`, `ui_control_panel_basics`)

5. Status:

- `Queued`

6. Dependencies (best-effort):

- If tasks depend on other tasks not already covered by any WP (any status) and not included in this WP, list them at WP level.
- Otherwise: `None`

7. Verify commands (best-effort defaults):

- Default: `pytest`
- If clearly frontend-only: include `npm test` or minimal build if known
- If unclear: keep only `pytest`

8. Traceability:

- Include `Idea-ID: $1` in the WP entry so WPs are traceable back to the idea.

---

## Step 5 — Append to WORK_PACKAGES.md

Append each new WP section at the end of the WP list (before “Notes / Decisions Log”, if present).

Recommended WP entry format:

## WP-XXXX — <Title>

- Status: Queued
- Idea-ID: $1
- Release: MVP|V1|Full|Later
- Tasks:
  - TASK-001 — <title>
  - TASK-002 — <title>
- Goal: <goal sentence>
- Dependencies: None | WP-XXXX | TASK-YYY
- Plan Doc: docs/ai/planning/work*packages/WP-XXXX_TASK-AAA-BBB*<slug>.md
- Verify: pytest (and any extras)

---

## Step 6 — Output next actions

Print:

- New WP id(s) and tasks selected
- Plan Doc path(s)
- Suggested next step (e.g., “Run your WP execution command for WP-XXXX”)

---

## Non-negotiable Rules

- Never modify or rewrite the canonical backlog in `docs/ai/forge/ideas/$1/latest/tasks.md`.
- Never enqueue tasks already referenced by any existing WP (any status).
- Keep WPs small and focused; default to 1 WP if no count is provided.
- Do NOT mark tasks complete here.
- Prefer conservative batching when dependencies are unclear.
- Do not invent tasks; only select tasks that exist in `tasks.md`.
