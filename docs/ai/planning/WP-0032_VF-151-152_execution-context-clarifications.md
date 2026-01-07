# WP-0032 — Execution loop context + clarifications

## VF Tasks
- VF-151
- VF-152

## Plan
1. Review relevant execution-loop orchestration docs/implementation for task context handling and clarification flows.
2. Implement VF-151: load task-scoped context into agent prompts.
3. Implement VF-152: support clarification pause/resume flows.
4. Run WP verification commands.

## Done means
- `pytest`

## Task Checklist
- [x] VF-151
  - Added RepoContextLoader with bounded file selection and context notes.
  - Updated SessionCoordinator to inject repo_context into agent prompts.
  - Verified with `PYTHONPATH=/workspace/v-forge pytest`.
- [x] VF-152
  - Added AgentResult clarification fields + TaskMaster clarification reset.
  - SessionCoordinator pauses/resumes execution with clarification answers.
  - Verified with `PYTHONPATH=/workspace/v-forge pytest`.
