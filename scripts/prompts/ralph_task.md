RALPH_MODE: true

You will be given exactly ONE task in YAML.

Execution rules:
- Complete only this task.
- Treat acceptance_criteria as the definition of done.
- Respect dependencies (assume dependencies are satisfied if this task was selected).
- Prefer edits limited to target_files unless a small additional fix is required for correctness.
- If reuse_notes mention an existing pattern/file, follow that pattern.

Verification:
- Run the most relevant verification command(s) for the changed area:
  - UI: npm run build (and/or npm test if applicable)
  - API: run the repo’s standard Python checks/tests (prefer what AGENTS.md specifies)
- Do not mark done unless verification succeeds.

Progress update:
- Update ralph_state.yaml:
  - On success: append the task id to done
  - On failure: set blocked[TASK-ID] = "reason; next action"

Output contract:
- End with exactly: RALPH_STATUS: done|blocked TASK-###
- Include a short summary before that: files_changed, tests_run
