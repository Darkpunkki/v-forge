# VibeForge — Forge Pipeline Usage Guide

This guide explains how to run the full VibeForge “Idea → Concept → Epics → Features → Tasks → Work Packages → Execution” pipeline using your Claude Code slash commands.

---

## 1) Folder structure (canonical)

Repository-relative paths (recommended):

```
.claude/
  commands/
    idea-normalizer.md
    concept-summarizer.md
    epic-extractor.md
    feature-extractor.md
    task-builder.md
    into-wps.md
    work-wp.md
    validate-epics.md
    validate-features.md
    validate-tasks.md

docs/
  ai/
    forge/
      ideas/
        <IDEA_ID>/
          inputs/
            idea.md
            normalizer_config.md        (optional)
            concept_config.md           (optional)
            epic_config.md              (optional)
            feature_config.md           (optional)
            task_config.md              (optional)
            validator_config.md         (optional)
            attachments/                (optional)
          latest/
            idea_normalized.md
            concept_summary.md
            epics.md
            features.md
            tasks.md
            validators/
              epic_validation_report.md
              feature_validation_report.md
              task_validation_report.md
              epics.patched.md          (optional)
              features.patched.md       (optional)
              tasks.patched.md          (optional)
          runs/
            <RUN_ID>/
              idea_normalized.md
              concept_summary.md
              epics.md
              features.md
              tasks.md
              validators/
                epic_validation_report.md
                feature_validation_report.md
                task_validation_report.md
                epics.patched.md        (optional)
                features.patched.md     (optional)
                tasks.patched.md        (optional)
          manifest.md                   (rolling status/index)
          run_log.md                    (append-only)

    planning/
      WORK_PACKAGES.md                  (global WP queue/index)
      work_packages/
        WP-0001_TASK-001-007_some_slug.md
        WP-0002_TASK-008-012_other_slug.md
        ...
```

### Key conventions
- **One idea = one folder** under `docs/ai/forge/ideas/<IDEA_ID>/`.
- **inputs/** contains human-authored source files (especially `idea.md`).
- **latest/** is the current “best known” output used by downstream steps.
- **runs/<RUN_ID>/** is immutable history for traceability.
- Validators write to **latest/validators/** and **runs/<RUN_ID>/validators/**.
- Work Packages are global and live under **docs/ai/planning/**.

---

## 2) What is an IDEA_ID?

`IDEA_ID` is the **folder name** under `docs/ai/forge/ideas/`.

Example:
- `docs/ai/forge/ideas/IDEA-0003_my-idea/`

You run commands by passing the folder name:
- `/idea-normalizer IDEA-0003_my-idea`

You **do not** create `IDEA-0003_my-idea.md`. The idea is a folder, not a file.

---

## 3) Quickstart (one idea, full pipeline)

### Step A — Create the idea folder + input
1. Create:
   - `docs/ai/forge/ideas/IDEA-0003_my-idea/inputs/`
2. Put your raw idea here:
   - `docs/ai/forge/ideas/IDEA-0003_my-idea/inputs/idea.md`

Optional: add configs (see section 6).

### Step B — Run the Forge pipeline
Run these in order:

1. Normalize idea
- `/idea-normalizer IDEA-0003_my-idea`

2. Summarize concept (semantic anchor)
- `/concept-summarizer IDEA-0003_my-idea`

3. Extract epics
- `/epic-extractor IDEA-0003_my-idea`

4. Validate epics (optional but recommended)
- `/validate-epics IDEA-0003_my-idea`

5. Extract features
- `/feature-extractor IDEA-0003_my-idea`

6. Validate features (optional but recommended)
- `/validate-features IDEA-0003_my-idea`

7. Build tasks
- `/task-builder IDEA-0003_my-idea`

8. Validate tasks (optional but recommended)
- `/validate-tasks IDEA-0003_my-idea`

After this, your canonical backlog is:
- `docs/ai/forge/ideas/IDEA-0003_my-idea/latest/tasks.md`

---

## 4) Work Packages and execution

### A) Queue Work Packages from tasks
Use `/into-wps` to append one or more queued WPs into:
- `docs/ai/planning/WORK_PACKAGES.md`

**Command:**
- `/into-wps <IDEA_ID> [filters...]`

Examples:
- Queue 1 WP (default):
  - `/into-wps IDEA-0003_my-idea`
- Queue up to 3 WPs:
  - `/into-wps IDEA-0003_my-idea 3`
- Only MVP tasks:
  - `/into-wps IDEA-0003_my-idea MVP`
- Only tasks for one epic:
  - `/into-wps IDEA-0003_my-idea EPIC-003`
- Only tasks for one feature:
  - `/into-wps IDEA-0003_my-idea FEAT-014`
- Force WP numbering to start at a specific WP (rare):
  - `/into-wps IDEA-0003_my-idea WP-0007`

**Important behaviors:**
- Never modifies `tasks.md`.
- Never queues a task already referenced by any WP (any status).
- Stops if there are already **4+ queued** WPs.

### B) Execute a Work Package
Use `/work-wp` to select and execute work using WPs as the driver.

**Command:**
- `/work-wp [WP-####]`

Behaviors:
- With no args: executes the **next Queued** WP.
- With a WP id: executes **only that WP**.

Examples:
- Run the next queued WP:
  - `/work-wp`
- Run a specific WP:
  - `/work-wp WP-0040`

**Important behaviors:**
- Reads `docs/ai/planning/WORK_PACKAGES.md` to select the WP.
- Requires the WP entry to contain `Idea-ID: <IDEA_ID>` so it can locate:
  - `docs/ai/forge/ideas/<IDEA_ID>/latest/tasks.md`
- Updates WP status in `WORK_PACKAGES.md`:
  - `Queued → In Progress → Done` (or `Blocked`)
- Ensures a per-WP plan doc exists under:
  - `docs/ai/planning/work_packages/`

---

## 5) Command reference (what each takes and what it writes)

### Forge pipeline commands (idea-scoped)

1) `/idea-normalizer <IDEA_ID>`
- Reads: `ideas/<IDEA_ID>/inputs/idea.md`
- Writes: `runs/<RUN_ID>/idea_normalized.md` and updates `latest/idea_normalized.md`
- Updates: `ideas/<IDEA_ID>/manifest.md`, appends to `ideas/<IDEA_ID>/run_log.md`

2) `/concept-summarizer <IDEA_ID>`
- Reads: normalized idea if present, otherwise raw idea
- Writes: `runs/<RUN_ID>/concept_summary.md` and updates `latest/concept_summary.md`
- Updates manifest + run log

3) `/epic-extractor <IDEA_ID>`
- Reads: `latest/concept_summary.md` + idea context
- Writes: `runs/<RUN_ID>/epics.md` and updates `latest/epics.md`
- Updates manifest + run log

4) `/feature-extractor <IDEA_ID>`
- Reads: `latest/concept_summary.md` + `latest/epics.md` + idea context
- Writes: `runs/<RUN_ID>/features.md` and updates `latest/features.md`
- Updates manifest + run log

5) `/task-builder <IDEA_ID>`
- Reads: `latest/concept_summary.md` + `latest/features.md` + idea context
- Writes: `runs/<RUN_ID>/tasks.md` and updates `latest/tasks.md`
- Updates manifest + run log

### Validators (idea-scoped; write under latest/validators/)
1) `/validate-epics <IDEA_ID>`
- Subject: `latest/epics.md`
- Output: `latest/validators/epic_validation_report.md`
- Optional: `latest/validators/epics.patched.md` (only if allow_patch)

2) `/validate-features <IDEA_ID>`
- Subject: `latest/features.md`
- Output: `latest/validators/feature_validation_report.md`
- Optional: `latest/validators/features.patched.md` (only if allow_patch)

3) `/validate-tasks <IDEA_ID>`
- Subject: `latest/tasks.md`
- Output: `latest/validators/task_validation_report.md`
- Optional: `latest/validators/tasks.patched.md` (only if allow_patch)

### Planning/execution (global queue)
1) `/into-wps <IDEA_ID> [filters...]`
- Reads: `ideas/<IDEA_ID>/latest/tasks.md`
- Writes: appends WP entries to `docs/ai/planning/WORK_PACKAGES.md`

2) `/work-wp [WP-####]`
- Reads: `docs/ai/planning/WORK_PACKAGES.md` and WP plan doc
- Reads canonical tasks from idea referenced by `Idea-ID`
- Writes/updates: statuses + plan doc + manifests as described in the command

---

## 6) Optional config files (per idea)

All config files live in:
- `docs/ai/forge/ideas/<IDEA_ID>/inputs/`

Common ones:
- `normalizer_config.md` — preferred normalization sections/terminology
- `concept_config.md` — summary formatting preferences, scope emphasis
- `epic_config.md` — epic limits/tags/release targeting preferences
- `feature_config.md` — feature limits, AC style, tag presets
- `task_config.md` — sizing rules, estimates conventions, DoD rules
- `validator_config.md` — validator behavior flags

### Validator patching control (important)
To allow patched outputs (`*.patched.md`), set in:
- `inputs/validator_config.md`

Example:
```yaml
allow_patch: true
strictness: normal
```

If `allow_patch` is absent or false, validators produce **report-only** and include explicit “Proposed Patch” edits in the report.

---

## 7) Recommended “happy path” workflow

1) Write `inputs/idea.md`
2) Run normalize + concept summary
3) Run epic extraction + validate epics
4) Run feature extraction + validate features
5) Run task builder + validate tasks
6) Queue 1–3 WPs using `/into-wps <IDEA_ID> [filters]`
7) Execute WPs using `/work-wp` (or `/work-wp WP-####`)
8) Iterate: enqueue more WPs, execute, repeat

---

## 8) Troubleshooting and tips

### “Command can’t find idea.md”
Verify you created:
- `docs/ai/forge/ideas/<IDEA_ID>/inputs/idea.md`

### “Validator/Extractor can’t find concept_summary.md / epics.md / features.md”
You likely skipped a stage. Run the earlier command(s) first.

### “/into-wps says queue is full”
Run `/work-wp` to execute queued WPs (or manually adjust WP statuses if you’re intentionally pausing work).

### “/work-wp can’t locate tasks.md”
Your WP entry must include:
- `Idea-ID: <IDEA_ID>`

If it’s missing, update the WP entry or recreate WPs via:
- `/into-wps <IDEA_ID>`

### Keep IDEA_IDs stable
Renaming an idea folder later is possible, but it breaks history references. Prefer stable IDs.

---

## 9) Example end-to-end session (copy/paste)

Assume:
- `IDEA_ID = IDEA-0003_my-idea`

1) Put raw idea in:
- `docs/ai/forge/ideas/IDEA-0003_my-idea/inputs/idea.md`

2) Run:
- `/idea-normalizer IDEA-0003_my-idea`
- `/concept-summarizer IDEA-0003_my-idea`
- `/epic-extractor IDEA-0003_my-idea`
- `/validate-epics IDEA-0003_my-idea`
- `/feature-extractor IDEA-0003_my-idea`
- `/validate-features IDEA-0003_my-idea`
- `/task-builder IDEA-0003_my-idea`
- `/validate-tasks IDEA-0003_my-idea`

3) Queue work:
- `/into-wps IDEA-0003_my-idea 2`

4) Execute:
- `/work-wp` (runs next queued)
- `/work-wp WP-0002` (runs a specific one)

---

## 10) Notes on naming

Command names are derived from the filename in `.claude/commands/`:

- `.claude/commands/idea-normalizer.md` → `/idea-normalizer`
- `.claude/commands/concept-summarizer.md` → `/concept-summarizer`
- etc.

If you rename a command file, the slash command name changes accordingly.
