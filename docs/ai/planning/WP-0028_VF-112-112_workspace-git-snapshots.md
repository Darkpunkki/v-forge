# WP-0028 — Workspace git snapshots

## VF Tasks Included
- VF-112 — Optional: initialize git repo + commit snapshots

## Plan
1. Review existing WorkspaceManager and workspace layout behavior to identify the right hook for git initialization and snapshot commits.
2. Add git initialization and snapshot commit support for workspace repositories, guarded behind an optional flag/config.
3. Add tests covering git init + snapshot behavior and ensure existing workspace tests remain stable.
4. Verify with WP commands and update checklist entries.

## Done Means…
- Git initialization is optional and does not affect existing workflows when disabled.
- Snapshot commits are created after successful tasks as defined by the scope.
- Tests and verification commands pass:
  - `pytest`

## Progress Notes
- Added optional git initialization and snapshot commit helpers in WorkspaceManager.
- Added workspace git snapshot coverage to workspace tests.
- Verification: `cd apps/api && pytest`

## Task Checklist
- [x] VF-112 — Optional: initialize git repo + commit snapshots
  - Files: `apps/api/vibeforge_api/core/workspace.py`, `apps/api/tests/test_workspace.py`
  - Verify: `cd apps/api && pytest`
