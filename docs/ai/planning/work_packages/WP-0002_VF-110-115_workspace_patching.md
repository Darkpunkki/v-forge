# WP-0002 — Workspace + Patch Apply Safety

## VF Tasks Included
- VF-110: Implement WorkspaceManager.initRepo(sessionId, template)
- VF-111: Implement workspace layout (repo/ artifacts/) per session
- VF-113: Implement PatchApplier (unified diff apply)
- VF-114: PatchApplier safety: restrict paths to repo root + dry-run mode
- VF-115: Persist patch metadata per task (ArtifactStore)

## Goal
Safely create workspace per session and apply unified diffs with path restrictions and dry-run capabilities.

## Ordered Execution Steps

### 1. VF-110: Implement WorkspaceManager.initRepo(sessionId, template)
- Create WorkspaceManager class to manage session workspaces
- Initialize workspace directory structure for each session
- Support template-based initialization (minimal scaffold for MVP)
- Return workspace path for session
- Files: `apps/api/vibeforge_api/core/workspace.py`

### 2. VF-111: Implement workspace layout (repo/ artifacts/) per session
- Define standard workspace layout:
  - `workspaces/{sessionId}/repo/` - code repository
  - `workspaces/{sessionId}/artifacts/` - logs, metadata, results
- Create directory structure on workspace init
- Provide helper methods to get standard paths
- Files: `apps/api/vibeforge_api/core/workspace.py`

### 3. VF-113: Implement PatchApplier (unified diff apply)
- Create PatchApplier class to apply unified diffs
- Parse unified diff format
- Apply changes to target files
- Return detailed results (success/failure per file)
- Files: `apps/api/vibeforge_api/core/patch.py`

### 4. VF-114: PatchApplier safety: restrict paths to repo root + dry-run mode
- Validate all file paths are within workspace repo directory
- Prevent path traversal attacks (../, absolute paths)
- Implement dry-run mode to detect conflicts without modification
- Return validation errors before applying
- Files: `apps/api/vibeforge_api/core/patch.py`

### 5. VF-115: Persist patch metadata per task (ArtifactStore)
- Create ArtifactStore for persisting session artifacts
- Store patch metadata: diff content, apply outcome, affected files
- Save to artifacts directory with structured naming
- Provide retrieval methods for debugging
- Files: `apps/api/vibeforge_api/core/artifacts.py`

## Done Means...

### Verification Commands
1. Run unit tests: `cd apps/api && pytest tests/test_workspace.py tests/test_patch.py -v`
2. Verify workspace creation: Test creates workspace with correct layout
3. Verify patch apply: Test applies valid diffs successfully
4. Verify path safety: Test rejects path traversal attempts
5. Verify dry-run: Test detects conflicts without modifying files
6. Verify artifact storage: Test saves and retrieves patch metadata

### Task Checklist
- [x] VF-110: WorkspaceManager.initRepo implemented
  - Creates workspace directory per session
  - Initializes from template
  - File: `apps/api/vibeforge_api/core/workspace.py`
  - Verified: `pytest tests/test_workspace.py::test_init_repo_creates_workspace`
- [x] VF-111: Workspace layout standardized
  - repo/ and artifacts/ directories created
  - Helper methods for standard paths (get_repo_path, get_artifacts_path)
  - File: `apps/api/vibeforge_api/core/workspace.py`
  - Verified: `pytest tests/test_workspace.py::test_init_repo_creates_layout`
- [x] VF-113: PatchApplier core functionality working
  - Parses unified diffs
  - Applies changes to files
  - Returns detailed results (PatchResult with file-level status)
  - File: `apps/api/vibeforge_api/core/patch.py`
  - Verified: `pytest tests/test_patch.py::test_parse_unified_diff`, `test_apply_patch_counts_changes`
- [x] VF-114: PatchApplier safety features working
  - Path validation prevents traversal (..)
  - Path validation rejects absolute paths
  - Dry-run mode detects conflicts without modification
  - All paths restricted to workspace repo root
  - File: `apps/api/vibeforge_api/core/patch.py`
  - Verified: `pytest tests/test_patch.py::test_validate_path_rejects_traversal`, `test_apply_patch_dry_run`
- [x] VF-115: ArtifactStore persisting metadata
  - Saves patch metadata to artifacts/patches/
  - Structured file naming (patch_{task_id}_{timestamp}.json)
  - Retrieval methods working (get_patch_metadata, list_patch_metadata)
  - File: `apps/api/vibeforge_api/core/artifacts.py`
  - Verified: `pytest tests/test_artifacts.py::test_save_patch_metadata`, `test_get_patch_metadata`

## Implementation Notes
- Use pathlib for safe path operations
- Workspace root should be configurable (default: ./workspaces)
- MVP: Simple template copy, no git init yet (VF-112 is optional)
- Patch format: standard unified diff (output from `diff -u`)
- Error handling: Return structured errors, don't raise exceptions for apply failures
