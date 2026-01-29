# WP-0065 — Input Validation & Path Sandboxing

- Goal: Prevent injection attacks and directory traversal. Validate all file paths stay within workdir. Sanitize task content and agent IDs to prevent command injection.
- Idea-ID: IDEA-0003-vibeforge-is-pivoting
- Tasks: TASK-045, TASK-046
- Dependencies: WP-0064 (security foundation)

## Task queue (ordered)
1. TASK-045 — Implement path sandboxing in agent bridge
2. TASK-046 — Add input validation and sanitization for task dispatch

## Execution plan
1. Add path validation in agent bridge CLI wrapper for all filesystem operations; reject traversal and out-of-workdir paths.
2. Add tests for path validation scenarios.
3. Add dispatch input validation (content length + agent_id format) and tests for rejection.

## Done means
- `cd apps/api && python -m pytest tests/test_input_validation.py -v`
- `cd tools/agent_bridge && python -m pytest tests/test_path_validation.py -v`
- Manual: Try directory traversal (../../etc/passwd) → rejected
- Manual: Try long task content (>10,000 chars) → 400 error

## Task checklist
- [x] TASK-045 — Implement path sandboxing in agent bridge
  - Files: tools/agent_bridge/cli_wrapper.py, tools/agent_bridge/tests/test_path_validation.py
  - Verify: `cd tools/agent_bridge && python -m pytest tests/test_path_validation.py -v`
- [x] TASK-046 — Add input validation and sanitization for task dispatch
  - Files: apps/api/vibeforge_api/models/requests.py, apps/api/vibeforge_api/routers/control.py, apps/api/tests/test_input_validation.py
  - Verify: `cd apps/api && python -m pytest tests/test_input_validation.py -v`

## Notes / Decisions
- Symlink escape test may skip on Windows without elevated permissions; traversal and long-content checks covered via automated tests.
