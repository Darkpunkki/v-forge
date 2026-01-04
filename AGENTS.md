# AGENTS.md — VibeForge (Codex)

This repository uses **AI DevKit** for structured AI-assisted development and **Claude Code CLI** for the primary agent workflow.

- Framework: https://github.com/codeaholicguy/ai-devkit
- Primary agent driver: Claude Code CLI (custom slash commands in `.claude/commands/`)

Codex should follow the same workflow rules as Claude and treat the documents below as the source of truth.

---

## Source of Truth

### Project instructions
- **Read `CLAUDE.md` first.** It contains the project’s rules, conventions, and the automation-first workflow for Work Packages (WPs).

### Backlog & progress tracking
- **`vibeforge_master_checklist.md` is canonical** for:
  - what work exists (VF tasks)
  - what is considered “done”
  - marking progress (`[ ]` → `[x]` only when verified)

### Near-term execution queue
- **`docs/ai/planning/WORK_PACKAGES.md`** is the near-term WP queue.
  - WPs are small batches of VF tasks intended to be executed iteratively.

---

## How work is executed (WP-driven loop)

Codex should use the WP loop rather than inventing new ad-hoc task lists:

1) **Pick next work**
   - Prefer the next **Queued** Work Package in `docs/ai/planning/WORK_PACKAGES.md`.
   - If no WPs are queued (or the queue is low), create the next WP from the canonical checklist.

2) **Plan → Implement → Verify → Update docs → Check off**
   - Create or update the WP plan doc referenced by the WP entry.
   - Implement VF tasks in small, reviewable increments.
   - Run verification commands for the task and for the WP.
   - Update `vibeforge_master_checklist.md` and mark the WP status accordingly.

> Important: WP statuses should be updated by the CLI automation workflow (see CLAUDE.md), not manually unless correcting mistakes.

---

## Commands & automation (preferred)

This repo is set up to use Claude Code CLI custom commands as the “golden path” automation.
Codex should follow the same contract:

- `/execute-plan`
  - Picks the next queued WP, sets it In Progress, implements VF tasks, verifies, then marks Done/Blocked.
  - Updates `vibeforge_master_checklist.md` only after verification passes.

- `/queue-next-wp`
  - Creates the next WP entry from the next uncompleted VF tasks (avoiding duplicates).
  - Used when no queued WPs exist or the queue needs replenishing.

If Codex is not executing these commands directly, it must still follow their behavior:
- Update WP status as part of the loop
- Only check off VF tasks after verification passes
- Keep WPs small and coherent (1–5 VF tasks)

---

## Phase docs (ai-devkit)

Phase documentation lives under `docs/ai/` and should be kept in sync when decisions change:

- `docs/ai/requirements/` — behavior, acceptance criteria, constraints
- `docs/ai/design/` — architecture, interfaces, diagrams (use Mermaid when helpful)
- `docs/ai/planning/` — Work Packages + WP plan docs
- `docs/ai/implementation/` — patterns, conventions, how-to notes
- `docs/ai/testing/` — testing strategy and test cases
- `docs/ai/deployment/` — deployment/infrastructure notes
- `docs/ai/monitoring/` — observability/telemetry notes

Rule: **Update docs when changes introduce new decisions** (don’t rewrite docs for trivial diffs).

---

## Verification rules (non-negotiable)

- Run the most relevant tests after implementing changes.
- Prefer fast unit tests frequently; run broader verification at WP boundaries.
- Do not mark VF tasks complete in `vibeforge_master_checklist.md` unless verification passes.
- When verification fails:
  - fix forward (smallest change),
  - re-run verification,
  - if still failing, mark WP Blocked with a clear blocker note.

---

## Repo hygiene

- Keep changes scoped to the active WP/VF tasks.
- Include VF ids in commit messages and PR titles when possible (e.g., `VF-120: add CommandRunner allowlist`).
- Avoid large refactors unless the VF task explicitly requires it.
- Prefer stable interfaces; add seams (interfaces/types) before swapping implementations.

---

## When in doubt

1) Re-read `CLAUDE.md`.
2) Consult `vibeforge_master_checklist.md` for the authoritative definition of “done”.
3) Use/imitate the WP automation loop described above.
