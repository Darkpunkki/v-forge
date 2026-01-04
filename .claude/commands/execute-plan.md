# VibeForge Work Package Execution Assistant

Execute VibeForge development iteratively using **Work Packages (WPs)** as the driver.
This command must NOT ask for a feature name or planning doc path up front — it must discover the next unit of work automatically.

Supports optional argument:
- `/execute-plan WP-0002` to run a specific WP
- `/execute-plan` with no args to run the next Queued WP

Use `$ARGUMENTS` for the optional WP id.

---

## Inputs (Auto)
Canonical sources of truth:
- `docs/ai/planning/WORK_PACKAGES.md` (near-term queue)
- `vibeforge_master_checklist.md` (canonical backlog + progress)
- Phase docs under `docs/ai/` (requirements/design/implementation/testing)

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
   - suggest adding a new WP entry or re-queuing a blocked WP
   - STOP.

4) Extract from the WP section:
   - WP id and title
   - Status
   - VF task list
   - Goal
   - Dependencies (if present)
   - Plan Doc path
   - Verify commands

5) If WP is `Blocked`:
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

---

## Step 3 — Ensure Plan Doc Exists (or Create It)
1) Check if the WP’s Plan Doc exists.
2) If missing, create it using this template:

   - File: the WP plan doc path from WORK_PACKAGES.md
   - Content must include:
     - Title: `WP-XXXX — <name>`
     - VF tasks included (explicit list)
     - Ordered execution steps (implementation order)
     - “Done means…” section with verification commands
     - A checkbox list mirroring the VF tasks for this WP

3) The Plan Doc must reference the VF tasks exactly (IDs unchanged).

---

## Step 4 — Build the Task Queue (VF-driven)
1) Load `vibeforge_master_checklist.md` and locate each VF task referenced by the WP.
2) Build an ordered queue:
   - Prefer dependency order (e.g., API skeleton before validation; patch applier before verifiers).
3) For each VF task, extract:
   - Title
   - Intent/description bullets (what “done” means)
4) If the plan doc has its own checkbox task list:
   - treat it as the local execution checklist for this WP
   - keep it consistent with VF tasks and update it as you go

---

## Step 5 — Execute One VF Task at a Time (Iterative Loop)
For each VF task in queue:

### 5.1 — Preparation
- Identify which phase docs are relevant:
  - requirements: behavior/contracts
  - design: interfaces/components/state machine
  - implementation: patterns/conventions
  - testing: test expectations
- Only update docs if the change introduces NEW decisions or changes existing intent.

### 5.2 — Implement
- Make the smallest change that satisfies the VF task’s intent.
- Keep modifications focused and reviewable.
- Prefer small commits; include VF id(s) in commit message.

### 5.3 — Verify (local)
- Run the most relevant verification for the task (unit tests, lint, minimal smoke if applicable).
- Capture key outputs (pass/fail + short error summary if fail).

### 5.4 — Update WP Plan Doc checkbox
- Mark the VF item as complete in the WP plan doc ONLY after the task-level verification passes.
- Add 1–3 sub-bullets:
  - key files changed
  - commands run to verify

### 5.5 — If blocked or failing
- If the task fails verification:
  - attempt a focused fix
  - re-run verification
- If still blocked:
  - record blocker in the WP plan doc under the task
  - STOP further execution
  - proceed to Step 7 (Blocked handling)

---

## Step 6 — WP-level Verification + Close Out
After all VF tasks in the WP are done:

1) Run the WP Verify commands from `WORK_PACKAGES.md`.
2) If verification PASSES:
   - Update `vibeforge_master_checklist.md`:
     - change `[ ]` → `[x]` for each VF task in this WP
     - add brief sub-bullets: key files + verify commands used
   - Update `docs/ai/planning/WORK_PACKAGES.md`:
     - set WP status to `Done`
     - add:
       - `- Verified: <commands>`
       - `- Completed: <YYYY-MM-DD HH:MM> (local)`
       - `- Commits: <short hashes or PR link if applicable>`
3) If verification FAILS:
   - do NOT mark VF tasks complete in the master checklist
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
2) Do NOT mark VF tasks as complete in `vibeforge_master_checklist.md`.
3) Propose the next Queued WP (if any) as the next iteration.

---

## Step 8 — End-of-Run Summary (Always)
Print a concise summary:
- WP executed
- VF tasks completed (and which remain)
- Verification commands run + result
- Files/areas touched
- Next recommended WP (next Queued) OR blocker details if blocked

---

## Non-negotiable Rules
- Always use `WORK_PACKAGES.md` to select work (unless a WP id is provided via `$ARGUMENTS`).
- Always use `vibeforge_master_checklist.md` as the canonical source for VF task definitions and completion.
- Automatically update WP status (Queued → In Progress → Done/Blocked) as part of this command.
- Only mark VF tasks complete in the master checklist after WP verification passes.
- Ask the user only when absolutely required (e.g., destructive conflict, ambiguous blocker, missing decision).
