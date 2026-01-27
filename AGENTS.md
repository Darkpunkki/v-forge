# AGENTS.md — VibeForge / AI DevKit Rules (Codex)

This file tells **Codex** (CLI/IDE) how to work effectively in this repository.

## Project Context

This repository uses custom instructions for structured AI-assisted development.

## Product Goal & Current Status

### What this app is now
VibeForge is being refocused around **two** user-facing experiences:

1) **/control — Control real agents**
   - Manage, configure, and control **real, live agentic LLM instances** (e.g., Claude Code agents) that run locally or are reachable over a control channel.
   - This screen is the primary product surface and is expected to evolve rapidly.

2) **/simulation — Simulate workflows**
   - A browser-based sandbox to simulate agentic workflows and orchestration behavior.
   - Useful for demos, testing, and developing the VibeForge methods without requiring live agents.

### What is deprecated (legacy)
- The old **session/questionnaire-driven “/session” flow** is legacy/deprecated.
- Do **not** add new features to /session.
- When touching related code, prefer **removing or isolating** legacy session logic (routes, models, UI, docs) rather than extending it.

### Current reality (status)
- **/simulation**: the original “LLM sandbox” concept is partially achieved and remains useful.
- **/control**: exists conceptually, but **needs major refactoring**. Expect significant rework in UI, state management, and backend control interfaces.

### Development principles for this pivot
- **Control + Simulation first:** prioritize changes that improve /control and /simulation. Treat anything else as support work only.
- **Reuse before rewrite:** prefer adapting existing code paths, components, stores, and utilities when they fit the new control/simulation focus.
- **Be aggressive about deletion:** if code is redundant due to the pivot (especially session-related), call it out and remove it when safe.
- **Keep diffs tight:** refactor in small, verifiable steps; leave the repo in a runnable state after each step.

VibeForge includes:

- a **Forge pipeline** (Idea → Concept → Epics → Features → Tasks)
- a **Planning/Execution loop** (Backlog items → Work Packages → Implementation)

---

## Canonical Backlog & Progress Tracking

### A) Work execution queue (near-term, canonical)

The near-term execution queue is tracked in:

- `docs/ai/planning/WORK_PACKAGES.md`

Work Package plan docs live in:

- `docs/ai/planning/work_packages/` (preferred)
- Some legacy plan docs may live directly under `docs/ai/planning/`

Rules:

- Default: pick the **first** WP with status **Queued**.
- If instructed to run a specific WP id, run **only that WP**.
- Keep WPs small and outcome-focused.
- A WP must list:
  - Status
  - Goal
  - Plan Doc path
  - Verified commands (once done)
  - Dependencies (if any)
  - Files touched (optional but encouraged)

### B) Two backlog modes (supported)

This repo may contain **both** of the following backlog styles:

1. **Legacy VF checklist mode**
- Canonical backlog: `vibeforge_master_checklist.md`
- WPs reference VF items (e.g., `VF-063`)
- Completion: mark VF items `[x]` in the checklist when WP verification passes

2. **Idea-scoped Forge mode**
- Canonical backlog (per idea): `docs/ai/forge/ideas/<IDEA_ID>/latest/tasks.md`
- WPs reference TASK items (e.g., `TASK-012`) and include `Idea-ID: <IDEA_ID>`
- Completion: update per-idea manifest/run logs as defined by the Forge pipeline

Agents MUST support whichever mode a WP uses.
If a WP includes both VF and TASK references, treat both as relevant tracking identifiers.

---

## WORK_PACKAGES.md format (align with repo)

Your `WORK_PACKAGES.md` entries follow this style (example fields):

- `## WP-0014 — <Title>`
- `- **Status:** Queued | In Progress | Blocked | Done`
- `- **Started:** YYYY-MM-DD` (optional)
- `- **Completed:** YYYY-MM-DD` (optional)
- `- **VF Tasks:** ...` (legacy mode, optional)
- `- **Idea-ID:** ...` (Forge mode, required if WP is TASK-driven)
- `- **Tasks:**` (Forge mode list, optional but recommended)
- `- **Goal:** ...`
- `- **Dependencies:** ...`
- `- **Plan Doc:** ...`
- `- **Verified:**` (commands + results)
- `- **Files touched:**` (grouped by VF id or by task, optional but encouraged)

Preserve this structure and casing when editing.

---

## Checklist rules (only if using vibeforge_master_checklist.md)

### Note on checklist size + how to filter tasks

`vibeforge_master_checklist.md` is **large**. Do not try to read it top-to-bottom during execution.
Use the WP’s referenced VF IDs to jump directly to the relevant chapter(s), then filter by checkbox state.

VF tasks in the checklist are structured as markdown checkbox items:

- Done tasks: `- [x] **VF-### — Title...**`
- Not done tasks: `- [ ] **VF-### — Title...**`

### Execution + update rules

- Before starting, identify the next relevant VF items and reference their **VF IDs** in plan/commits.
- Work in small, verifiable increments (1–3 VF tasks per iteration).
- When complete:
  - change `- [ ]` to `- [x]`
  - keep the VF title intact
  - add brief sub-bullets (key decisions, files touched, verify commands)
- If missing work is discovered:
  - add a new VF task at the end of the correct chapter
  - keep numbering consistent; do not reuse IDs
- If partially done:
  - do **not** mark complete; add a short “what remains” note

---

## Documentation Structure

- `docs/ai/design/` - System architecture and design decisions (include mermaid diagrams)
- `docs/ai/planning/` - Work Packages and planning docs
- `docs/ai/forge/` - Forge pipeline outputs (idea → concept → backlog)

---

## Codex Operating Rules (local-first)

Codex can read, edit, and run code in the current workspace. Use that power safely:

- Prefer **local execution** and **reproducible verification**.
- Create Git checkpoints before/after big changes so rollbacks are easy.
- If a change touches legacy **/session** code, prefer **deleting it** (or quarantining behind a clearly named legacy boundary).

### Safety & determinism
Keep or introduce a “safe mode” for any LLM-integrated flow so development can proceed without spending tokens:

- `stub`: no network calls; deterministic outputs sufficient to test UI/backend wiring
- optional: `record/replay`: capture one real run and replay it for tests/dev

---

## Code Style & Standards

- Follow the repository’s established style and conventions
- Write clear, self-documenting code with meaningful names
- Add comments for complex logic or non-obvious decisions
- Prefer small, reviewable changes; keep diffs tight

---

## Development Workflow (WP-driven)

1) **Select WP**
- Use `docs/ai/planning/WORK_PACKAGES.md`
- Default: pick the first WP with status `Queued`
- If a WP id is provided explicitly, execute only that WP

2) **Confirm repo safety**
- Check:
  - `git status -sb`
  - `git diff --stat`
- If unrelated uncommitted changes exist, stop and ask the user before proceeding.

3) **Load canonical backlog definitions** (based on WP mode)

### Mode A — VF checklist WP
- Use `vibeforge_master_checklist.md` as canonical definitions for referenced VF items.
- Use the WP plan doc as the step-by-step execution checklist.

### Mode B — Idea-scoped TASK WP
- WP must contain `Idea-ID: <IDEA_ID>`
- Load canonical tasks from:
  - `docs/ai/forge/ideas/<IDEA_ID>/latest/tasks.md`
- Treat those tasks as canonical (title, description, acceptance criteria, dependencies).

4) **Ensure Plan Doc exists**
- Ensure the WP plan doc exists at `**Plan Doc:** ...`
- If missing, create it with:
  - Title, Goal, included IDs (VF and/or TASK)
  - ordered steps
  - a checkbox list
  - “Done means…” + verify commands

5) **Implement**
- Execute items one at a time; smallest slice that satisfies acceptance criteria/intent.
- Prefer reuse of existing code when suitable.
- If you find redundant code because of the pivot, call it out and remove it when safe.

6) **Verify**
- Run task-level verification as you go.
- Run WP-level verification from the `**Verified:**` section (or define it at the end).

7) **Update tracking**
- Update WP status in `WORK_PACKAGES.md`: `Queued → In Progress → Done` (or `Blocked`)
- Update progress trackers:
  - VF mode: mark VF checklist items `[x]` only after verification passes.
  - Task mode: update per-idea `manifest.md` / `run_log.md` as defined by the Forge pipeline.

---

## Commit / PR Hygiene

- Include relevant IDs in commit messages:
  - VF mode: `WP-0014 VF-063: <change>`
  - Task mode: `WP-0040 TASK-012: <change>`
- Keep commits coherent and verifiable.
- If you create/modify WPs or plan docs, include the WP id in the commit message.
- The user handles final commit/push unless told otherwise.

---

## AI Interaction Guidelines

- Prefer document-first behavior:
  - read existing docs before changing code
  - update docs when decisions change or constraints appear
- Do not invent scope:
  - honor `concept_summary.md` invariants/exclusions (Forge mode)
  - keep work within the selected WP
- Ask the user only when required:
  - destructive conflicts
  - ambiguous blockers
  - missing required input files

---

## Testing & Quality

- Write tests alongside implementation when appropriate.
- Ensure verification commands pass before marking:
  - a task/VF item “Done”
  - a WP “Done”
- If full coverage is not practical, record gaps in the relevant documentation.

---

## Forge Pipeline (Idea → Tasks) — optional workflow

The Forge pipeline produces a canonical backlog (`tasks.md`) for a specific idea folder:

- `docs/ai/forge/ideas/<IDEA_ID>/`

Minimum required input:

- `docs/ai/forge/ideas/<IDEA_ID>/inputs/idea.md`

Typical sequence (idea-scoped):

- `/idea-normalizer <IDEA_ID>`
- `/concept-summarizer <IDEA_ID>`
- `/epic-extractor <IDEA_ID>`
- `/validate-epics <IDEA_ID>` (recommended)
- `/feature-extractor <IDEA_ID>`
- `/validate-features <IDEA_ID>` (recommended)
- `/task-builder <IDEA_ID>`
- `/validate-tasks <IDEA_ID>` (recommended)

Queue WPs from idea tasks:

- `/into-wps <IDEA_ID> [filters...]`

Execute WPs:

- `/work-wp [WP-####]`

Note: the “/commands” above refer to this repo’s workflow prompts/tools. If Codex is asked to run one, locate the corresponding prompt/guide in the repo (e.g., under `./prompts/` or `docs/ai/`) and follow it.

---

## Non-negotiables

- Use `WORK_PACKAGES.md` as the execution driver (unless a specific WP is provided).
- Never mark items complete unless verification passes.
- Never invent backlog items during execution; implement only what exists in the backlog/WP.
- Preserve existing `WORK_PACKAGES.md` formatting/casing when editing entries.


## Ralph mode (TASKS.md loop)

Ralph mode is used when the prompt contains `RALPH_MODE: true`.

### Driver + sources of truth
- Canonical backlog: `docs/ai/forge/ideas/<IDEA_ID>/latest/tasks.md` (this repo’s task-builder output)
- Ralph progress state: `ralph_state.yaml` at repo root

### Execution rules (Ralph)
- Do NOT use WORK_PACKAGES.md while in Ralph mode.
- Each run completes **exactly one** TASK item.
- Respect `dependencies` (only work tasks whose dependencies are already marked done in `ralph_state.yaml`).
- Use `acceptance_criteria` as “done means”.
- Prefer edits limited to `target_files` unless a small additional change is required for correctness.

### Verification
- Run the most relevant verification command(s) for the task:
  - frontend tasks: `npm run build` or `npm test`
  - backend tasks: `pytest` / `uvicorn` smoke test / etc. (use repo conventions)
- Record what you ran in the final summary.

### Progress updates
- On success: append the TASK id to `ralph_state.yaml: done`.
- On failure: write `blocked[TASK-###] = "<reason>; next action>"`.
- Never mark a task done unless verification passes.

### Output contract
End every run with:
`RALPH_STATUS: done|blocked TASK-###`

