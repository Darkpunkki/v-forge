# Work Package Execution Assistant (Backlog-Driven)

Execute development iteratively using **Work Packages (WPs)** as the driver.

This command must NOT ask for a feature name or planning doc path up front — it must discover the next unit of work automatically from `docs/ai/planning/WORK_PACKAGES.md`.

Supports optional argument:
- `/execute-plan WP-0002` to run a specific WP
- `/execute-plan` with no args to run the next Queued WP

Use `$ARGUMENTS` for the optional WP id.

---

## Inputs (Auto)

Canonical sources of truth:
- `docs/ai/planning/WORK_PACKAGES.md` (near-term execution queue)
- `docs/ai/forge/tasks.md` (canonical task backlog definitions)
- WP plan docs under `docs/ai/planning/` (per-WP execution checklist and notes)

Optional context (read-only, if present):
- `docs/ai/forge/features.md`
- `docs/ai/forge/epics.md`
- `docs/ai/forge/concept_summary.md`
- `docs/ai/forge/idea_normalized.md`
- `docs/ai/forge/idea.md`

Progress tracking:
- `docs/ai/forge/manifest.md` (status index for tasks/WPs; preferred place to record completion)
- `docs/ai/forge/run_log.md` (append-only run log)

---

## Step 0 — Safety & Repo Context
1) Read current repo state:
   - `git status -sb`
   - `git diff --stat`
2) If there are unrelated uncommitted changes:
   - ask the user to confirm whether to stash/commit before proceeding (do NOT proceed blindly).

---

## Step 1 — Select the Work Package
1) Open `docs/ai/planning/WORK_PACKAGES.md`.
2) Determine target WP:
   - If `$ARGUMENTS` contains a WP id, use that WP.
   - Else select the FIRST WP whose status is `Queued`.
3) If no `Queued` WP exists:
   - report “No queued WPs found”
   - suggest running `/into-wps` to enqueue new WPs
   - STOP.

4) Extract from the WP section (best-effort):
   - WP id and title
   - Status
   - Release target (if present)
   - Task list (TASK-xxx ids + titles, if present)
   - Goal
   - Dependencies (WPs and/or TASK ids, if present)
   - Plan Doc path
   - Verify commands

5) If WP status is `Blocked`:
   - do not change anything automatically
   - show blockers and ask if user wants to unblock or pick another WP
   - STOP.

---

## Step 2 — Auto-update WP status to In Progress
Edit `docs/ai/planning/WORK_PACKAGES.md`:
- If status is `Queued`, set it to `In Progress`.
- Add a small sub-bullet under the WP:
  - `- Started: <YYYY-MM-DD HH:MM> (local)`
  - `- Branch: <current-branch>`
Do this BEFORE any code changes.

Also update `docs/ai/forge/manifest.md` (best-effort):
- Set this WP’s status to `In Progress` (if WPs are tracked in manifest).
- For each task in the WP, set task status to `In Progress` only if it was previously `Proposed`/`Queued`.

---

## Step 3 — Ensure WP Plan Doc Exists (or Create It)

Planning and execution can be performed in one command for simplicity. This step ensures the planning artifact exists before implementation begins.

1) Check if the WP’s Plan Doc exists (path stored in WORK_PACKAGES.md).
2) If missing, create it using this template:

   - File: the WP plan doc path from WORK_PACKAGES.md
   - Content must include:
     - Title: `WP-XXXX — <name>`
     - Goal (from WORK_PACKAGES.md)
     - Task IDs included (explicit list)
     - Ordered execution steps (task order)
     - “Done means…” section with verification commands
     - A checkbox list mirroring the tasks for this WP

3) The Plan Doc must reference TASK ids exactly (IDs unchanged).

---

## Step 4 — Build the Task Queue (Backlog-Driven)
1) Load `docs/ai/forge/tasks.md` and locate each `TASK-...` referenced by the WP.
   - Prefer parsing the canonical YAML block.
2) For each task, extract:
   - Title
   - Description
   - Acceptance criteria
   - Dependencies (if present)
   - Release target, priority, estimate, tags (if present)

3) Order the task queue (best-effort):
   - Respect explicit `dependencies` between tasks.
   - If dependencies are unknown, use the order listed in the WP plan doc (if present).
   - If both exist and conflict, prefer explicit task dependencies and note the conflict in the plan doc.

4) If the plan doc has its own checkbox list:
   - treat it as the local execution checklist for this WP
   - keep it consistent with the canonical tasks and update it as you go

If any referenced TASK id cannot be found in `tasks.md`:
- Record a blocker in the plan doc and STOP (do not guess task definitions).

---

## Step 5 — Execute One Task at a Time (Iterative Loop)
For each task in the ordered queue:

### 5.1 — Preparation
- Identify relevant context:
  - feature/epic context (if `features.md`/`epics.md` exist)
  - concept constraints/invariants (if `concept_summary.md` exists)
- Only update documentation if the change introduces NEW decisions or changes existing intent.

### 5.2 — Implement
- Make the smallest change that satisfies the task’s acceptance criteria.
- Keep modifications focused and reviewable.
- Prefer small commits; include TASK id(s) in commit message.

### 5.3 — Verify (task-level)
- Run the most relevant verification for the task (unit tests, lint, minimal smoke if applicable).
- Capture key outputs (pass/fail + short error summary if fail).

### 5.4 — Update WP Plan Doc checkbox
- Mark the TASK item as complete in the WP plan doc ONLY after task-level verification passes.
- Add 1–3 sub-bullets:
  - key files changed
  - commands run to verify

### 5.5 — Update manifest (task status)
Update `docs/ai/forge/manifest.md` (best-effort):
- Set task status to `Done` only when its acceptance criteria are met and task-level verification passed.
- Record `last_updated` and (optionally) `commit` reference(s).

### 5.6 — If blocked or failing
- If the task fails verification:
  - attempt a focused fix
  - re-run verification
- If still blocked:
  - record blocker in the WP plan doc under the task
  - proceed to Step 7 (Blocked handling)
  - STOP further execution

---

## Step 6 — WP-level Verification + Close Out
After all tasks in the WP are checked off in the plan doc:

1) Run the WP Verify commands from `WORK_PACKAGES.md` (fallback: `pytest` if none listed).
2) If verification PASSES:
   - Update `docs/ai/planning/WORK_PACKAGES.md`:
     - set WP status to `Done`
     - add:
       - `- Verified: <commands>`
       - `- Completed: <YYYY-MM-DD HH:MM> (local)`
       - `- Commits: <short hashes or PR link if applicable>`
   - Update `docs/ai/forge/manifest.md`:
     - ensure all tasks in the WP are marked `Done`
     - mark the WP record as `Done` (if WPs are tracked)
3) If verification FAILS:
   - do NOT mark WP as Done
   - keep WP status as `In Progress`
   - write a short failure summary under the WP (errors + next steps)
   - STOP

---

## Step 7 — Blocked Handling (Auto)
If execution is blocked:

1) Update `docs/ai/planning/WORK_PACKAGES.md`:
   - set WP status to `Blocked`
   - add:
     - `- Blocker: <short description>`
     - `- What is needed: <next action>`

2) Update `docs/ai/forge/manifest.md` (best-effort):
   - set WP status to `Blocked`
   - set blocked task(s) status to `Blocked`
   - record blocker notes

3) Propose the next Queued WP (if any) as the next iteration.

---

## Step 8 — End-of-Run Summary (Always)
Print a concise summary:
- WP executed
- Tasks completed (and which remain)
- Verification commands run + result
- Files/areas touched
- Next recommended WP (next Queued) OR blocker details if blocked

---

## Non-negotiable Rules
- Always use `WORK_PACKAGES.md` to select work (unless a WP id is provided via `$ARGUMENTS`).
- Always use `tasks.md` as the canonical source for task definitions (titles, acceptance criteria, dependencies).
- Automatically update WP status (Queued → In Progress → Done/Blocked) as part of this command.
- Only mark tasks `Done` (in `manifest.md` and/or plan doc) after verification passes.
- Ask the user only when absolutely required (e.g., destructive conflict, ambiguous blocker, missing decision).

---

## Note on Planning vs Execution
For an MVP workflow, combining “ensure plan doc exists” + execution in one command is fine and keeps iteration fast.

If/when you want stricter separation:
- Add a dedicated command to *only* create/update the WP plan doc (planning-only).
- Keep this command purely for execution against an already-approved plan doc.
