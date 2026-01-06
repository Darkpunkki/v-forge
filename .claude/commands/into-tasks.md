---
description: VibeForge — Turn a feature idea into new VF tasks and a paste-ready checklist block (canonical format).
argument-hint: "<feature/idea> | optional: target chapter number (e.g., 15) or keyword (e.g., execution loop)"
---

# VibeForge — Into Tasks (Checklist-first)

Convert a feature idea into PR-sized VF tasks and output a paste-ready block that matches the canonical style in `vibeforge_master_checklist.md`.

Use $ARGUMENTS as the feature/theme plus optional hints.

## Inputs (Auto)
- vibeforge_master_checklist.md
- Optional supporting docs if the user references them (e.g., @docs/..., @CLAUDE.md, @README.md)

## Step 0 — Read checklist conventions (non-negotiable)
1) Open vibeforge_master_checklist.md and infer conventions:
   - Chapter heading pattern: "## <num> <title> (optional suffix)"
   - Task line pattern: "- [ ] **VF-151 — <title>**"
   - Detail bullets under tasks:
     - indented two spaces
     - use "-" bullet
     - may include fields like **Priority:**, **Status:**, **Implementation:**, **Verify:**
2) Parse all existing VF ids:
   - max_vf_id
   - next_vf_id = max_vf_id + 1
3) Parse chapter numbers:
   - max_chapter_num
   - next_chapter_num = max_chapter_num + 1

## Step 1 — Make the request actionable (ask questions only if needed)
Interpret $ARGUMENTS as a real request, but do not invent details that change scope.

If the request is too generic to create correct tasks, ask up to 5 questions and STOP (do not generate tasks).
Prioritize:
1) Target location in the repo: which chapter number/title OR which path/package?
2) User-visible outcome: what changes when done?
3) MVP constraints: stack, no-new-deps, required tests/verify commands
4) Definition of done: 2–4 bullet outcomes
5) Non-goals: what to explicitly exclude

If the user does not answer, proceed with explicit assumptions (label them in output).

## Step 2 — Choose insertion location (prefer existing chapter)
1) Try to match to an existing chapter by:
   - explicit chapter number mentioned in $ARGUMENTS (e.g., "15")
   - keywords (e.g., "execution loop", "verification gates", "recovery", "UI shell")
2) If a suitable chapter exists:
   - Insert tasks under that chapter
3) If no suitable chapter exists:
   - Propose a new chapter:
     - "## <next_chapter_num> <Feature Name> (MVP)"
   - Keep naming consistent with the repo style (short, descriptive)

## Step 3 — Reuse vs create tasks
### 3.1 Reuse first (avoid duplicates)
Scan for existing unchecked VF tasks that already cover the request.
- If found, list them under "Reuse VF tasks"
- Only create new tasks for real gaps

### 3.2 Create new VF tasks for gaps (canonical style)
Create tasks that are:
- PR-sized
- verifiable
- ordered by dependency

For each new task, emit:

- [ ] **VF-<id> — <imperative title>**
  - <1–2 sentence build description (what changes)>
  - **Status:** Planned
  - **Verify:** <best-effort command> (or "TBD" if unknown)

Guidelines:
- Include **Priority:** Post-MVP enhancement only if clearly not MVP.
- Include **Implementation:** only if you can name likely modules/files (best-effort ok).
- If dependencies are unclear, keep the batch small and sequential.

## Step 4 — Output a paste-ready checklist update block (NO code fences)
Output a single block the user can paste into vibeforge_master_checklist.md.

If inserting into an existing chapter:
- Include a marker: "INSERT UNDER: ## <num> <title>"
- Then list the new tasks in canonical format.

If creating a new chapter:
- Include the new "## <next_chapter_num> ..." heading followed by tasks.

## Output format (must follow exactly)

## 1) Assumptions (if any)

## 2) Target insertion location
- Existing chapter: yes/no
- Insert under: <exact heading text OR "new chapter: ## <n> ...">

## 3) Reuse VF tasks (if any)
- VF-...

## 4) New VF tasks (if needed)
- VF-...

## 5) Checklist Update Block (paste-ready)
BEGIN_CHECKLIST_BLOCK
INSERT UNDER: <exact heading OR "APPEND NEW CHAPTER">
<lines to paste, exactly as markdown>
END_CHECKLIST_BLOCK

## 6) Notes on ordering / dependencies

## Non-negotiable Rules
- Never renumber, rewrite, or reformat existing VF tasks or headings.
- Prefer reuse; only add tasks for genuine gaps.
- Keep tasks MVP-focused and PR-sized.
- Do NOT mark tasks complete here.
