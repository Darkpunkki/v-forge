"""Tests for patch application."""

import pytest
from pathlib import Path

from vibeforge_api.core.patch import PatchApplier, PatchResultStatus


@pytest.fixture
def temp_repo(tmp_path):
    """Create a temporary repo directory."""
    repo_path = tmp_path / "repo"
    repo_path.mkdir()

    # Create some initial files
    (repo_path / "file1.txt").write_text("line1\nline2\nline3\n")
    (repo_path / "file2.txt").write_text("hello\nworld\n")

    return repo_path


@pytest.fixture
def patch_applier(temp_repo):
    """Create a patch applier for temp repo."""
    return PatchApplier(repo_root=temp_repo)


def test_validate_path_rejects_traversal(patch_applier):
    """Test VF-114: Path validation rejects .. traversal."""
    is_valid, error = patch_applier.validate_path("../etc/passwd")
    assert not is_valid
    assert "traversal" in error.lower()


def test_validate_path_rejects_absolute(patch_applier):
    """Test VF-114: Path validation rejects absolute paths."""
    is_valid, error = patch_applier.validate_path("/etc/passwd")
    assert not is_valid
    assert "outside repo root" in error.lower() or "absolute" in error.lower()


def test_validate_path_accepts_relative(patch_applier):
    """Test VF-114: Path validation accepts safe relative paths."""
    is_valid, error = patch_applier.validate_path("src/main.py")
    assert is_valid
    assert error == ""


def test_validate_path_accepts_nested(patch_applier):
    """Test VF-114: Path validation accepts nested paths."""
    is_valid, error = patch_applier.validate_path("src/utils/helper.py")
    assert is_valid
    assert error == ""


def test_parse_unified_diff(patch_applier):
    """Test VF-113: Parsing unified diff format."""
    diff = """--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3
"""

    file_patches = patch_applier._parse_unified_diff(diff)
    assert len(file_patches) == 1
    assert file_patches[0][0] == "file1.txt"
    assert len(file_patches[0][1]) > 0


def test_apply_patch_dry_run(patch_applier):
    """Test VF-114: Dry-run mode doesn't modify files."""
    diff = """--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,4 @@
 line1
+new line
 line2
 line3
"""

    result = patch_applier.apply_patch(diff, dry_run=True)

    assert result.success
    assert len(result.files) == 1
    assert result.files[0].status == PatchResultStatus.SUCCESS
    assert "Dry-run" in result.message


def test_apply_patch_counts_changes(patch_applier):
    """Test VF-113: PatchApplier counts added/removed lines."""
    diff = """--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,2 @@
 line1
-line2
 line3
+new line
"""

    result = patch_applier.apply_patch(diff, dry_run=True)

    assert result.success
    file_result = result.files[0]
    assert file_result.lines_added == 1
    assert file_result.lines_removed == 1


def test_apply_patch_rejects_unsafe_path(patch_applier):
    """Test VF-114: apply_patch rejects unsafe paths."""
    diff = """--- a/../etc/passwd
+++ b/../etc/passwd
@@ -1,1 +1,1 @@
-old
+new
"""

    result = patch_applier.apply_patch(diff)

    assert not result.success
    assert len(result.files) == 1
    assert result.files[0].status == PatchResultStatus.INVALID_PATH


def test_apply_patch_multiple_files(patch_applier):
    """Test VF-113: Applying patch to multiple files."""
    diff = """--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,4 @@
 line1
+added
 line2
 line3
--- a/file2.txt
+++ b/file2.txt
@@ -1,2 +1,3 @@
 hello
+world2
 world
"""

    result = patch_applier.apply_patch(diff, dry_run=True)

    assert result.success
    assert len(result.files) == 2
    assert result.files[0].file_path == "file1.txt"
    assert result.files[1].file_path == "file2.txt"


def test_apply_patch_empty_diff(patch_applier):
    """Test applying empty diff."""
    result = patch_applier.apply_patch("")

    assert not result.success
    assert "No valid patches" in result.message


def test_apply_patch_mixed_results(patch_applier):
    """Test patch with both valid and invalid files."""
    diff = """--- a/file1.txt
+++ b/file1.txt
@@ -1,3 +1,4 @@
 line1
+added
 line2
 line3
--- a/../etc/passwd
+++ b/../etc/passwd
@@ -1,1 +1,1 @@
-old
+new
"""

    result = patch_applier.apply_patch(diff)

    assert not result.success  # Overall failure due to one invalid file
    assert len(result.files) == 2
    assert result.files[0].status == PatchResultStatus.SUCCESS
    assert result.files[1].status == PatchResultStatus.INVALID_PATH
