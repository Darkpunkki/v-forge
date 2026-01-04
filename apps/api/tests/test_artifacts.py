"""Tests for artifact storage."""

import pytest
import json
from pathlib import Path

from vibeforge_api.core.artifacts import ArtifactStore, PatchMetadata


@pytest.fixture
def temp_artifacts_root(tmp_path):
    """Create a temporary artifacts directory."""
    return tmp_path / "artifacts"


@pytest.fixture
def artifact_store(temp_artifacts_root):
    """Create an artifact store with temp root."""
    return ArtifactStore(artifacts_root=temp_artifacts_root)


def test_artifact_store_creates_root(temp_artifacts_root):
    """Test that ArtifactStore creates artifacts root."""
    store = ArtifactStore(artifacts_root=temp_artifacts_root)
    assert temp_artifacts_root.exists()


def test_save_patch_metadata(artifact_store, temp_artifacts_root):
    """Test VF-115: Saving patch metadata."""
    metadata = PatchMetadata(
        task_id="task-001",
        timestamp="2026-01-04T10:00:00Z",
        diff_content="--- a/file.txt\n+++ b/file.txt\n",
        apply_outcome="success",
        affected_files=["file.txt"],
        lines_added=5,
        lines_removed=2,
    )

    file_path = artifact_store.save_patch_metadata(metadata)

    assert file_path.exists()
    assert "patch_task-001" in file_path.name
    assert file_path.suffix == ".json"


def test_save_patch_metadata_creates_subdirectory(artifact_store, temp_artifacts_root):
    """Test that save_patch_metadata creates patches subdirectory."""
    metadata = PatchMetadata(
        task_id="task-002",
        timestamp="2026-01-04T10:00:00Z",
        diff_content="diff content",
        apply_outcome="success",
        affected_files=["file.txt"],
        lines_added=1,
        lines_removed=0,
    )

    artifact_store.save_patch_metadata(metadata)

    patches_dir = temp_artifacts_root / "patches"
    assert patches_dir.exists()
    assert patches_dir.is_dir()


def test_save_patch_metadata_content(artifact_store):
    """Test VF-115: Saved metadata has correct content."""
    metadata = PatchMetadata(
        task_id="task-003",
        timestamp="2026-01-04T10:00:00Z",
        diff_content="diff content",
        apply_outcome="failed",
        affected_files=["file1.txt", "file2.txt"],
        lines_added=3,
        lines_removed=1,
        error_message="Conflict detected",
    )

    file_path = artifact_store.save_patch_metadata(metadata)

    # Read and verify content
    with open(file_path, "r") as f:
        data = json.load(f)

    assert data["task_id"] == "task-003"
    assert data["apply_outcome"] == "failed"
    assert data["affected_files"] == ["file1.txt", "file2.txt"]
    assert data["error_message"] == "Conflict detected"


def test_get_patch_metadata(artifact_store):
    """Test VF-115: Retrieving patch metadata."""
    metadata = PatchMetadata(
        task_id="task-004",
        timestamp="2026-01-04T10:00:00Z",
        diff_content="diff",
        apply_outcome="success",
        affected_files=["file.txt"],
        lines_added=2,
        lines_removed=0,
    )

    artifact_store.save_patch_metadata(metadata)

    # Retrieve it
    retrieved = artifact_store.get_patch_metadata("task-004")

    assert retrieved is not None
    assert retrieved.task_id == "task-004"
    assert retrieved.apply_outcome == "success"
    assert retrieved.affected_files == ["file.txt"]


def test_get_patch_metadata_not_found(artifact_store):
    """Test retrieving non-existent patch metadata."""
    result = artifact_store.get_patch_metadata("nonexistent-task")
    assert result is None


def test_list_patch_metadata(artifact_store):
    """Test VF-115: Listing all patch metadata."""
    # Save multiple metadata entries
    for i in range(3):
        metadata = PatchMetadata(
            task_id=f"task-{i}",
            timestamp=f"2026-01-04T10:0{i}:00Z",
            diff_content=f"diff {i}",
            apply_outcome="success",
            affected_files=[f"file{i}.txt"],
            lines_added=i,
            lines_removed=0,
        )
        artifact_store.save_patch_metadata(metadata)

    # List all
    all_metadata = artifact_store.list_patch_metadata()

    assert len(all_metadata) == 3
    # Should be sorted by timestamp (newest first)
    assert all_metadata[0].task_id == "task-2"
    assert all_metadata[1].task_id == "task-1"
    assert all_metadata[2].task_id == "task-0"


def test_save_artifact_dict(artifact_store, temp_artifacts_root):
    """Test saving a generic dict artifact."""
    data = {"key": "value", "count": 42}
    artifact_store.save_artifact("config.json", data)

    file_path = temp_artifacts_root / "config.json"
    assert file_path.exists()

    with open(file_path, "r") as f:
        loaded = json.load(f)

    assert loaded == data


def test_save_artifact_text(artifact_store, temp_artifacts_root):
    """Test saving a text artifact."""
    artifact_store.save_artifact("log.txt", "This is a log message")

    file_path = temp_artifacts_root / "log.txt"
    assert file_path.exists()
    assert file_path.read_text() == "This is a log message"


def test_save_artifact_with_subdir(artifact_store, temp_artifacts_root):
    """Test saving artifact in subdirectory."""
    artifact_store.save_artifact("data.json", {"test": "value"}, subdir="logs")

    file_path = temp_artifacts_root / "logs" / "data.json"
    assert file_path.exists()


def test_get_artifact(artifact_store):
    """Test retrieving a generic artifact."""
    artifact_store.save_artifact("test.txt", "content")

    retrieved = artifact_store.get_artifact("test.txt")
    assert retrieved == "content"


def test_get_artifact_not_found(artifact_store):
    """Test retrieving non-existent artifact."""
    result = artifact_store.get_artifact("nonexistent.txt")
    assert result is None


def test_get_artifact_with_subdir(artifact_store):
    """Test retrieving artifact from subdirectory."""
    artifact_store.save_artifact("data.txt", "test data", subdir="logs")

    retrieved = artifact_store.get_artifact("data.txt", subdir="logs")
    assert retrieved == "test data"
