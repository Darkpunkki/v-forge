# CLAUDE.md — VibeForge / AI DevKit Rules

## Project Context

This repository uses custom instructions for structured AI-assisted development.
All phase documentation is located in `docs/ai/`.

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

Agents should preserve this structure and casing when editing.

---

## Checklist rules (only if using vibeforge_master_checklist.md)

### Note on checklist size + how to filter tasks

`vibeforge_master_checklist.md` is **large**. Do not try to “read it all” top-to-bottom during execution.
Instead, use the WP’s referenced VF IDs to jump directly to the relevant chapter(s), then filter by checkbox state.

VF tasks in the checklist are structured as markdown checkbox items:

- Done tasks: `- [x] **VF-### — Title...**`
- Not done tasks: `- [ ] **VF-### — Title...**`


### Execution + update rules

- Before starting work, identify the next relevant VF items and reference their **VF IDs** in your plan and commits.
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

- `docs/ai/requirements/` - Problem understanding and requirements
- `docs/ai/design/` - System architecture and design decisions (include mermaid diagrams)
- `docs/ai/planning/` - Work Packages and planning docs
- `docs/ai/implementation/` - Implementation guides and notes
- `docs/ai/testing/` - Testing strategy and test cases
- `docs/ai/deployment/` - Deployment and infrastructure docs
- `docs/ai/monitoring/` - Monitoring and observability setup
- `docs/ai/forge/` - Forge pipeline outputs (idea → concept → backlog)

---

## Code Style & Standards

- Follow the repository’s established code style and conventions
- Write clear, self-documenting code with meaningful names
- Add comments for complex logic or non-obvious decisions
- Prefer small, reviewable changes; keep diffs tight

---

## Development Workflow (WP-driven)

1. **Select WP**

- Use `docs/ai/planning/WORK_PACKAGES.md`
- Default: pick the first WP with status `Queued`
- If a WP id is provided explicitly, execute only that WP

2. **Confirm repo safety**

- Check:
  - `git status -sb`
  - `git diff --stat`
- If unrelated uncommitted changes exist, ask the user before proceeding.

3. **Load canonical backlog definitions**
   Depending on WP mode:

### Mode A — VF checklist WP

- Use `vibeforge_master_checklist.md` as canonical definitions for the referenced VF items.
- Use the WP plan doc as the step-by-step execution checklist.

### Mode B — Idea-scoped TASK WP

- WP must contain `Idea-ID: <IDEA_ID>`
- Load canonical tasks from:
  - `docs/ai/forge/ideas/<IDEA_ID>/latest/tasks.md`
- Treat those tasks as canonical: title, description, acceptance criteria, dependencies.

4. **Ensure Plan Doc exists**

- Ensure the WP plan doc exists at `**Plan Doc:** ...`
- If missing, create it with:
  - Title, Goal, included IDs (VF and/or TASK)
  - ordered steps
  - a checkbox list
  - “Done means…” + verify commands

5. **Implement**

- Execute items one at a time; smallest slice that satisfies acceptance criteria / intent.
- Prefer small commits.

6. **Verify**

- Run task-level verification as you go.
- Run WP-level verification from the `**Verified:**` section (or set it at the end).

7. **Update tracking**

- Update WP status in `WORK_PACKAGES.md`:
  - `Queued → In Progress → Done` (or `Blocked`)
- Update progress trackers:
  - VF mode: mark VF checklist items `[x]` only after verification passes.
  - Task mode: update per-idea `manifest.md` / `run_log.md` as defined by the Forge pipeline.

---

## Commit / PR Hygiene

- Provide relevant IDs in commit messages:
  - VF mode example: `WP-0014 VF-063: model routing`
  - Task mode example: `WP-0040 TASK-012: implement <thing>`
- Keep commits coherent and verifiable.
- If you create/modify WPs or plan docs, include the WP id in the commit message.
- User will handle the final commit / push to remote.

---

## AI Interaction Guidelines

- Prefer document-first behavior:
  - read existing docs before changing code
  - update docs when decisions change or new constraints appear
- Do not invent scope:
  - honor `concept_summary.md` invariants/exclusions (Forge mode)
  - keep work within the selected WP
- Ask the user only when required:
  - destructive conflicts
  - ambiguous blockers
  - missing required input files

---

## Testing & Quality

- Write tests alongside implementation when appropriate
- Follow `docs/ai/testing/` strategy
- Ensure verification commands pass before marking:
  - a task/VF item “Done”
  - a WP “Done”
- If full coverage is not practical, record gaps in `docs/ai/testing/`

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

---

## Key Commands (Claude Code)

### Forge (idea-scoped)

- `/idea-normalizer <IDEA_ID>`
- `/concept-summarizer <IDEA_ID>`
- `/epic-extractor <IDEA_ID>`
- `/feature-extractor <IDEA_ID>`
- `/task-builder <IDEA_ID>`

### Validators (idea-scoped)

- `/validate-epics <IDEA_ID>`
- `/validate-features <IDEA_ID>`
- `/validate-tasks <IDEA_ID>`

### Planning & Execution (global queue)

- `/into-wps <IDEA_ID> [N|MVP|V1|Full|Later|EPIC-###|FEAT-###|WP-#### ...]`
- `/work-wp [WP-####]`

---

## Non-negotiables

- Use `WORK_PACKAGES.md` as the execution driver (unless a specific WP is provided).
- Never mark items complete unless verification passes.
- Never invent backlog items during execution; implement only what exists in the backlog/WP.
- Preserve existing `WORK_PACKAGES.md` formatting/casing when editing entries.
