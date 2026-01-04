---
phase: planning
title: VibeForge Planning — Work Packages & Task Breakdown
description: Turn VF checklist items into small Work Packages (plan → execute → verify → update docs/checklist)
---

# VibeForge Planning — Work Packages & Task Breakdown

This project uses **ai-devkit** phase docs under `docs/ai/` and Claude Code workflow commands (e.g., `/execute-plan`, `/writing-test`, `/code-review`). :contentReference[oaicite:2]{index=2}  
The canonical backlog and completion tracker is **`vibeforge_master_checklist.md`**. Always pick work from there first. :contentReference[oaicite:3]{index=3}

---

## Source of Truth

### Backlog & Progress
- `vibeforge_master_checklist.md` (VF tasks with checkboxes) :contentReference[oaicite:4]{index=4}

### Work Package Index
- `docs/ai/planning/WORK_PACKAGES.md`
  - This is the “queue” of near-term work that Claude (and humans) iterate through.

---

## What is a Work Package?

A **Work Package (WP)** is a small, verifiable batch of work that:
- covers **1–5 VF tasks** from `vibeforge_master_checklist.md`
- has a clear “done means…” section with commands to run
- results in code + tests (when applicable)
- updates the relevant phase docs if design/behavior changes
- ends with checklist updates (mark VF tasks complete only when truly done)

**Rule of thumb:** prefer WPs that can be completed in one focused iteration without needing a large refactor.

---

## Workflow (repeat per Work Package)

### Step 1 — Select VF tasks (from checklist)
Pick the next **unchecked** VF tasks that are currently unblocked. :contentReference[oaicite:5]{index=5}  
If unsure, choose tasks that unblock execution flow: API → workspace/patching → runner/verifiers → gates → execution loop.

### Step 2 — Add a WP entry to WORK_PACKAGES.md
Create/append a WP entry with:
- WP ID (WP-0001, WP-0002…)
- VF IDs included
- goal statement
- status (Queued / In Progress / Done / Blocked)
- verification commands
- links to any WP plan docs

### Step 3 — Create a WP plan doc
Create a dedicated plan doc:
- `docs/ai/planning/WP-XXXX_VF-AAA-BBB_<short_name>.md`

Include:
- Scope: the VF tasks included and what “complete” means for each
- Implementation plan: steps in execution order
- Verification: exact commands to run
- Risk notes: what could break / rollback plan

### Step 4 — Execute with Claude Code commands
Recommended sequence:
1) `/review-requirements` (only if behavior/constraints change) :contentReference[oaicite:6]{index=6}  
2) `/review-design` (only if structure/interfaces change) :contentReference[oaicite:7]{index=7}  
3) `/execute-plan` (implement in small commits) :contentReference[oaicite:8]{index=8}  
4) `/writing-test` (tests for new behavior) :contentReference[oaicite:9]{index=9}  
5) `/check-implementation` (sanity check vs design) :contentReference[oaicite:10]{index=10}  
6) `/code-review` (final pass) :contentReference[oaicite:11]{index=11}  

### Step 5 — Update docs + checklist
- Update phase docs if needed:
  - requirements/design/implementation/testing
- Update `vibeforge_master_checklist.md`:
  - set `[ ]` → `[x]` for completed VF tasks
  - add short sub-bullets: key files changed + commands run :contentReference[oaicite:12]{index=12}
- Update `WORK_PACKAGES.md` status and verification notes.

---

## How to Choose a Good Work Package

### Good WP patterns
- “Add a small set of endpoints + validation + tests”
- “Implement PatchApplier with safety checks + unit tests”
- “Add GatePipeline + one gate + tests”
- “Add CommandRunner allowlist enforcement + tests”

### Avoid in a single WP
- “Implement entire system end-to-end” (too large)
- “Refactor everything” (too risky)
- “Many unrelated VF tasks” (hard to verify)

---

## Milestones (VibeForge)
Use these as checkpoints, not strict deadlines:

- [ ] Milestone A: UI ↔ API questionnaire loop is stable
- [ ] Milestone B: BuildSpec + Concept + Plan review works with gates
- [ ] Milestone C: Task execution loop applies diffs safely
- [ ] Milestone D: Verifiers (build/test/smoke) run reliably
- [ ] Milestone E: Full happy path completes with final summary

---

## Risks & Mitigation
- Prompt drift / malformed agent output → strict schemas + validator/repair loop
- Unsafe diffs/commands → gates + allowlists + sandboxed workspace
- Infinite fix loops → retries + escalation + hard-stop with actionable report
- “Too big plan” → feasibility gate + scope budget enforcement

---

## Resources Needed
- Claude Code CLI configured + CLAUDE.md rules
- ai-devkit commands under `.claude/commands/` :contentReference[oaicite:13]{index=13}  
- The VF checklist + WP plan docs + tests
