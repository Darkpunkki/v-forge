# WP-0031 — Observability run bundle export

## VF Tasks
- VF-132 — Add "export run bundle" (zip artifacts + summary) (optional)

## Plan
1. Review existing workspace/artifact storage to decide where to generate run bundle archives.
2. Implement run bundle export helper to package workspace repo snapshot, artifacts, events, and summary metadata.
3. Add control API endpoint to request run bundle for a session.
4. Add unit tests covering bundle creation and API response behavior.

## Done Means
- Run bundle export creates a zip archive containing repo, artifacts, event log (if present), and summary metadata.
- Control API endpoint returns the bundle for valid sessions and errors for missing workspaces.
- Tests cover bundle creation and API endpoint behavior.
- Verification: `pytest`.

## Task Checklist
- [x] VF-132 — Add "export run bundle" (zip artifacts + summary) (optional)
  - Notes: Added run bundle export helper and control endpoint for downloadable archives.
  - Files: `apps/api/vibeforge_api/core/run_bundle.py`, `apps/api/vibeforge_api/routers/control.py`, `apps/api/tests/test_run_bundle.py`, `apps/api/tests/test_control_api.py`
  - Verification: `PYTHONPATH=/workspace/v-forge pytest`
