"""Tests for workspace management."""

import os
import pytest
import shutil
import stat
import subprocess
import time
from pathlib import Path

from vibeforge_api.core.workspace import WorkspaceManager


def _handle_remove_readonly(func, path, exc_info):
    """Best-effort handler for Windows file locks/readonly bits during cleanup."""
    try:
        os.chmod(path, stat.S_IWRITE)
        func(path)
    except Exception:
        # Ignore cleanup failures to avoid test teardown errors.
        pass


def _safe_rmtree(path: Path, retries: int = 3, delay_seconds: float = 0.2):
    if not path.exists():
        return
    for attempt in range(retries):
        try:
            shutil.rmtree(path, onerror=_handle_remove_readonly)
            return
        except PermissionError:
            time.sleep(delay_seconds * (attempt + 1))
    shutil.rmtree(path, ignore_errors=True)


@pytest.fixture
def temp_workspace_root(tmp_path):
    """Create a temporary workspace root directory."""
    workspace_root = tmp_path / "test_workspaces"
    yield str(workspace_root)
    # Cleanup
    if workspace_root.exists():
        _safe_rmtree(workspace_root)


@pytest.fixture
def workspace_manager(temp_workspace_root):
    """Create a workspace manager with temp root."""
    return WorkspaceManager(workspace_root=temp_workspace_root)


def test_workspace_manager_creates_root(temp_workspace_root):
    """Test that WorkspaceManager creates workspace root directory."""
    manager = WorkspaceManager(workspace_root=temp_workspace_root)
    assert Path(temp_workspace_root).exists()


def test_init_repo_creates_workspace(workspace_manager):
    """Test VF-110: initRepo creates workspace directory."""
    session_id = "test-session-001"
    workspace_path = workspace_manager.init_repo(session_id)

    assert workspace_path.exists()
    assert workspace_path.name == session_id


def test_init_repo_creates_layout(workspace_manager):
    """Test VF-111: Workspace has correct layout (repo/ and artifacts/)."""
    session_id = "test-session-002"
    workspace_path = workspace_manager.init_repo(session_id)

    repo_path = workspace_path / "repo"
    artifacts_path = workspace_path / "artifacts"

    assert repo_path.exists()
    assert repo_path.is_dir()
    assert artifacts_path.exists()
    assert artifacts_path.is_dir()


def test_init_repo_creates_minimal_scaffold(workspace_manager):
    """Test that initRepo creates minimal scaffold when no template."""
    session_id = "test-session-003"
    workspace_path = workspace_manager.init_repo(session_id)

    readme_path = workspace_path / "repo" / "README.md"
    assert readme_path.exists()
    content = readme_path.read_text()
    assert "VibeForge" in content


def test_init_repo_with_template(workspace_manager, tmp_path):
    """Test initRepo with a template directory."""
    # Create a simple template
    template_dir = tmp_path / "template"
    template_dir.mkdir()
    (template_dir / "app.py").write_text("print('hello')")
    (template_dir / "config.json").write_text('{"key": "value"}')

    session_id = "test-session-004"
    workspace_path = workspace_manager.init_repo(session_id, template=str(template_dir))

    # Check that template files were copied
    repo_path = workspace_path / "repo"
    assert (repo_path / "app.py").exists()
    assert (repo_path / "config.json").exists()
    assert (repo_path / "app.py").read_text() == "print('hello')"


def test_init_repo_rejects_duplicate(workspace_manager):
    """Test that initRepo raises error if workspace already exists."""
    session_id = "test-session-005"
    workspace_manager.init_repo(session_id)

    with pytest.raises(ValueError, match="already exists"):
        workspace_manager.init_repo(session_id)


def test_get_workspace_path(workspace_manager):
    """Test getting workspace path for existing session."""
    session_id = "test-session-006"
    created_path = workspace_manager.init_repo(session_id)
    retrieved_path = workspace_manager.get_workspace_path(session_id)

    assert created_path == retrieved_path


def test_get_workspace_path_not_found(workspace_manager):
    """Test getting workspace path for non-existent session."""
    with pytest.raises(ValueError, match="not found"):
        workspace_manager.get_workspace_path("nonexistent-session")


def test_get_repo_path(workspace_manager):
    """Test VF-111: get_repo_path helper method."""
    session_id = "test-session-007"
    workspace_manager.init_repo(session_id)
    repo_path = workspace_manager.get_repo_path(session_id)

    assert repo_path.exists()
    assert repo_path.name == "repo"


def test_get_artifacts_path(workspace_manager):
    """Test VF-111: get_artifacts_path helper method."""
    session_id = "test-session-008"
    workspace_manager.init_repo(session_id)
    artifacts_path = workspace_manager.get_artifacts_path(session_id)

    assert artifacts_path.exists()
    assert artifacts_path.name == "artifacts"


def test_workspace_exists(workspace_manager):
    """Test workspace_exists check."""
    session_id = "test-session-009"

    assert not workspace_manager.workspace_exists(session_id)
    workspace_manager.init_repo(session_id)
    assert workspace_manager.workspace_exists(session_id)


def test_delete_workspace(workspace_manager):
    """Test deleting a workspace."""
    session_id = "test-session-010"
    workspace_manager.init_repo(session_id)

    assert workspace_manager.workspace_exists(session_id)
    workspace_manager.delete_workspace(session_id)
    assert not workspace_manager.workspace_exists(session_id)


def test_init_repo_with_git_creates_initial_commit(workspace_manager):
    """Test VF-112: initRepo can initialize git repo with initial commit."""
    if shutil.which("git") is None:
        pytest.skip("git not available in environment")

    session_id = "test-session-011"
    workspace_path = workspace_manager.init_repo(session_id, enable_git=True)

    repo_path = workspace_path / "repo"
    assert (repo_path / ".git").exists()

    log = subprocess.run(
        ["git", "log", "--oneline"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert log


def test_commit_snapshot_creates_commit_when_dirty(workspace_manager):
    """Test VF-112: commit snapshots are created when repo has changes."""
    if shutil.which("git") is None:
        pytest.skip("git not available in environment")

    session_id = "test-session-012"
    workspace_path = workspace_manager.init_repo(session_id, enable_git=True)
    repo_path = workspace_path / "repo"

    (repo_path / "new_file.txt").write_text("hello")
    assert workspace_manager.commit_snapshot(session_id, "Add new file")

    commit_count = subprocess.run(
        ["git", "rev-list", "--count", "HEAD"],
        cwd=repo_path,
        capture_output=True,
        text=True,
        check=True,
    ).stdout.strip()
    assert int(commit_count) >= 2


def test_commit_snapshot_skips_when_clean(workspace_manager):
    """Test VF-112: commit snapshots skip when repo is clean."""
    if shutil.which("git") is None:
        pytest.skip("git not available in environment")

    session_id = "test-session-013"
    workspace_manager.init_repo(session_id, enable_git=True)

    assert not workspace_manager.commit_snapshot(session_id, "No changes")
