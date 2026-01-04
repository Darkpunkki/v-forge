# Work Packages (VibeForge)

This file is the near-term work queue. Each Work Package (WP) references VF tasks from `vibeforge_master_checklist.md` (canonical backlog).
Use WPs to run an iterative loop: plan → implement → verify → update docs → check off VF tasks → mark WP done.

## Status Legend
- Queued: selected and ready to start
- In Progress: currently being implemented
- Blocked: cannot proceed (missing dependency/decision)
- Done: merged + verified + VF tasks checked off

## Operating Rules
- Keep WPs small (typically 1–5 VF tasks).
- Only mark a WP “Done” after:
  1) verification commands succeed,
  2) relevant docs updated (if needed),
  3) VF tasks checked off in `vibeforge_master_checklist.md`.

---

## WP-0001 — Local UI API completion
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-020, VF-021, VF-022, VF-023, VF-024, VF-025, VF-026, VF-029 (all complete ✓)
- **Goal:** Make the session API stable and phase-safe so UI can drive the flow reliably.
- **Dependencies:** None (should be safe to start immediately)
- **Plan Doc:** docs/ai/planning/WP-0001_VF-020-029_local_api_core.md
- **Verified:**
  - `cd apps/api && pip install -r requirements.txt` - All dependencies installed
  - `pytest` - 10 tests passed
  - `uvicorn vibeforge_api.main:app --reload` - Server starts successfully
  - `/health` endpoint returns 200 OK
  - `/docs` OpenAPI documentation loads
  - Session creation flow tested (POST /sessions → GET /question → POST /answers)
- **Files touched:**
  - `apps/api/requirements.txt` (dependencies)
  - `apps/api/vibeforge_api/main.py` (FastAPI app)
  - `apps/api/vibeforge_api/models/` (types, requests, responses)
  - `apps/api/vibeforge_api/core/` (session store, questionnaire engine)
  - `apps/api/vibeforge_api/routers/sessions.py` (all endpoints)
  - `apps/api/tests/test_sessions.py` (10 unit tests)

## WP-0002 — Workspace + Patch apply safety
- **Status:** Done
- **Started:** 2026-01-04 (local)
- **Completed:** 2026-01-04 (local)
- **Branch:** master
- **VF Tasks:** VF-110, VF-111, VF-113, VF-114, VF-115 (all complete ✓)
- **Goal:** Safely create workspace per session and apply unified diffs with path restrictions + dry-run.
- **Dependencies:** WP-0001 recommended (API plumbing helps), but can be built in parallel
- **Plan Doc:** docs/ai/planning/WP-0002_VF-110-115_workspace_patching.md
- **Verified:**
  - `pytest tests/test_workspace.py tests/test_patch.py tests/test_artifacts.py -v` - 36 tests passed
  - Workspace creation with correct layout (repo/, artifacts/)
  - Patch application with unified diff parsing
  - Path traversal prevention (.. and absolute paths rejected)
  - Dry-run mode without file modification
  - Patch metadata persistence to artifacts/
- **Files touched:**
  - `apps/api/vibeforge_api/core/workspace.py` (WorkspaceManager)
  - `apps/api/vibeforge_api/core/patch.py` (PatchApplier with safety)
  - `apps/api/vibeforge_api/core/artifacts.py` (ArtifactStore)
  - `apps/api/tests/test_workspace.py` (12 tests)
  - `apps/api/tests/test_patch.py` (11 tests)
  - `apps/api/tests/test_artifacts.py` (13 tests)

## WP-0003 — Command runner + verification harness
- **Status:** Queued
- **VF Tasks:** VF-120, VF-121, VF-122, VF-124
- **Goal:** Allowlisted command execution with captured outputs; per-task + global verifier runner.
- **Dependencies:** WP-0002 recommended (needs workspace), but can scaffold interfaces early
- **Plan Doc:** docs/ai/planning/WP-0003_VF-120-124_command_verification.md
- **Verify:**
  - Unit tests + one real run against a tiny fixture project

## WP-0004 — Gates pipeline (core safety checks)
- **Status:** Queued
- **VF Tasks:** VF-080, VF-081, VF-082, VF-083, VF-084, VF-085
- **Goal:** Enforce safety/feasibility policies before diffs/commands touch disk.
- **Dependencies:** WP-0002 + WP-0003 recommended (gates protect those flows)
- **Plan Doc:** docs/ai/planning/WP-0004_VF-080-085_gates_pipeline.md
- **Verify:**
  - Unit tests for allowlist/forbidden patterns + blocked diff cases

---

## Notes / Decisions Log
- (Add short bullets here when you make planning-level decisions that affect multiple WPs.)
- Example: “MVP test runner is pytest only; add integration tests starting WP-0003.”
